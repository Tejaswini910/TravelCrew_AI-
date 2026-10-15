"""Tool-backed planning, budget revision, and Ollama preflight."""

from __future__ import annotations

import json
import logging
import time
from itertools import product
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from travel_planner.config.settings import get_settings
from travel_planner.crew.travel_crew import run_travel_crew
from travel_planner.models import PlanningResult, TripRequest
from travel_planner.tools.calculator_tool import BudgetCalculatorTool
from travel_planner.tools.date_tool import DateUtilityTool
from travel_planner.tools.hotel_tool import HotelTool
from travel_planner.tools.search_tool import SearchTool
from travel_planner.tools.transport_tool import TransportTool
from travel_planner.tools.weather_tool import WeatherTool

logger = logging.getLogger(__name__)


class OllamaUnavailableError(RuntimeError):
    """Raised when the configured Ollama service or model is unavailable."""


class PlanningToolError(RuntimeError):
    """Raised when a required local planning tool fails."""


def check_ollama() -> None:
    """Verify that Ollama responds and the requested model is installed."""
    settings = get_settings()
    payload: dict[str, Any] | None = None
    last_error: Exception | None = None
    headers = {"Authorization": f"Bearer {settings.ollama_api_key}"} if settings.ollama_api_key else {}
    for attempt in range(2):
        try:
            request = Request(f"{settings.ollama_base_url}/api/tags", headers=headers)
            with urlopen(request, timeout=settings.ollama_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(0.25)
    if payload is None:
        raise OllamaUnavailableError(
            f"Cannot reach Ollama at {settings.ollama_base_url}. Start Ollama and run `ollama pull {settings.model}`. "
            "For Streamlit Cloud, localhost refers to the cloud container, not your computer."
        ) from last_error

    requested = settings.model.removeprefix("ollama/").split(":", 1)[0]
    available = [str(item.get("name", "")) for item in payload.get("models", [])]
    if not any(name.split(":", 1)[0] == requested for name in available):
        raise OllamaUnavailableError(
            f"Ollama is running, but model '{settings.model}' is not installed. Run `ollama pull {settings.model}`."
        )


def _tool_json(tool: Any, **kwargs: object) -> dict[str, Any]:
    """Run a CrewAI tool and parse its JSON response with a useful error boundary."""
    try:
        parsed = json.loads(str(tool.run(**kwargs)))
    except Exception as exc:
        logger.exception("Required planning tool failed: %s", getattr(tool, "name", type(tool).__name__))
        raise PlanningToolError(f"Planning tool '{getattr(tool, 'name', type(tool).__name__)}' failed") from exc
    if not isinstance(parsed, dict):
        raise PlanningToolError(f"Planning tool '{tool.name}' returned an unexpected response")
    return parsed


def _budget_result(
    calculator: BudgetCalculatorTool,
    request: TripRequest,
    hotel: dict[str, Any],
    transport: dict[str, Any],
    attractions: list[dict[str, Any]],
    food_per_person_per_day: float,
) -> dict[str, Any]:
    ticket_cost = sum(float(item.get("admission_usd", 0)) for item in attractions)
    return json.loads(
        calculator.run(
            hotel_cost_usd=float(hotel["estimated_total_usd"]),
            transport_cost_usd=float(transport["estimated_total_usd"]),
            food_per_person_per_day_usd=food_per_person_per_day,
            attraction_cost_per_person_usd=ticket_cost,
            travelers=request.travelers,
            duration_days=request.duration_days,
            budget_usd=request.budget_usd,
        )
    )


def _select_budget_options(
    request: TripRequest,
    hotel_data: dict[str, Any],
    transport_data: dict[str, Any],
    attractions: list[dict[str, Any]],
    calculator: BudgetCalculatorTool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]], float, list[str]]:
    hotels = sorted(hotel_data["offers"], key=lambda item: item["estimated_total_usd"])
    transports = sorted(transport_data["options"], key=lambda item: item["estimated_total_usd"])
    if not hotels or not transports:
        raise PlanningToolError("Hotel or transport tool returned no usable options")

    selected_attractions = list(attractions[: request.duration_days * 2])
    food_allowance = 45.0
    hotel = hotels[min(1, len(hotels) - 1)]
    transport = transports[min(1, len(transports) - 1)]
    budget = _budget_result(calculator, request, hotel, transport, selected_attractions, food_allowance)
    alternatives: list[str] = []
    if budget["within_budget"]:
        return hotel, transport, budget, selected_attractions, food_allowance, alternatives

    alternatives.append("The initial standard option exceeded budget; comparing lower-cost hotel and transport combinations.")
    candidates = []
    for candidate_hotel, candidate_transport in product(hotels, transports):
        candidate_budget = _budget_result(
            calculator, request, candidate_hotel, candidate_transport, selected_attractions, food_allowance
        )
        candidates.append((candidate_budget["grand_total_usd"], candidate_hotel, candidate_transport, candidate_budget))
    feasible = [candidate for candidate in candidates if candidate[3]["within_budget"]]
    if feasible:
        _, hotel, transport, budget = min(feasible, key=lambda candidate: candidate[0])
        alternatives.append(f"Selected {hotel['name']} and {transport['name']} to meet the budget.")
        return hotel, transport, budget, selected_attractions, food_allowance, alternatives

    alternatives.append("No hotel/transport combination fit; switching to free activities and a leaner food allowance.")
    selected_attractions = [item for item in selected_attractions if float(item.get("admission_usd", 0)) == 0]
    food_allowance = 30.0
    reduced_candidates = []
    for candidate_hotel, candidate_transport in product(hotels, transports):
        candidate_budget = _budget_result(
            calculator, request, candidate_hotel, candidate_transport, selected_attractions, food_allowance
        )
        reduced_candidates.append((candidate_budget["grand_total_usd"], candidate_hotel, candidate_transport, candidate_budget))
    feasible = [candidate for candidate in reduced_candidates if candidate[3]["within_budget"]]
    _, hotel, transport, budget = min(feasible or reduced_candidates, key=lambda candidate: candidate[0])
    if budget["within_budget"]:
        alternatives.append("The revised plan fits with free activities and a $30 per-person daily food allowance.")
    else:
        alternatives.append("The lowest-cost mock combination still exceeds the supplied budget.")
    return hotel, transport, budget, selected_attractions, food_allowance, alternatives


def _build_final_report(
    request: TripRequest,
    budget: dict[str, Any],
    hotel: dict[str, Any],
    transport: dict[str, Any],
    attractions: list[dict[str, Any]],
    weather: dict[str, Any],
    search: dict[str, Any],
    alternatives: list[str],
    itinerary: str,
) -> str:
    lines = [
        "## Trip Summary",
        f"- Destination: {request.destination}",
        f"- Starting location: {request.origin}",
        f"- Travel dates: {request.start_date.isoformat()} to {request.end_date.isoformat()}",
        f"- Duration: {request.duration_days} days for {request.travelers} traveler(s)",
        f"- Budget: ${request.budget_usd:,.2f} USD",
        "",
        "## Recommended Attractions",
    ]
    if attractions:
        lines.extend(
            f"- {item.get('name', 'Research result')} (estimated admission: ${float(item.get('admission_usd', 0)):,.2f} per person)"
            for item in attractions
        )
    else:
        lines.append("- No verified attractions were found in the available research.")

    lines.extend(
        [
            "",
            "## Hotel Recommendation",
            f"- {hotel.get('name', 'Unavailable')}: ${float(hotel.get('estimated_total_usd', 0)):,.2f} USD estimated total",
            "- Mock estimate only; confirm real availability, taxes, and fees.",
            "",
            "## Transport Recommendation",
            f"- {transport.get('name', 'Unavailable')}: ${float(transport.get('estimated_total_usd', 0)):,.2f} USD estimated total",
            "- Mock estimate only; confirm actual schedules and fares.",
            "",
            "## Weather",
            str(weather.get("summary", "No weather summary is available.")),
            f"- Source: {weather.get('source', 'unknown')}",
            "",
            "## Day-by-Day Itinerary",
            itinerary or "No itinerary was returned by the itinerary planner.",
            "",
            "## Expense Breakdown",
            f"- Hotel: ${float(budget['hotel_cost_usd']):,.2f} USD",
            f"- Transport: ${float(budget['transport_cost_usd']):,.2f} USD",
            f"- Food: ${float(budget['food_cost_usd']):,.2f} USD",
            f"- Attractions: ${float(budget['attraction_cost_usd']):,.2f} USD",
            f"- Grand total: ${float(budget['grand_total_usd']):,.2f} USD",
            "",
            "## Budget Comparison",
        ]
    )
    if budget["within_budget"]:
        lines.append(f"- Within budget; ${float(budget['remaining_budget_usd']):,.2f} remaining.")
    else:
        lines.append(f"- Budget exceeded by ${float(budget['budget_exceeded_usd']):,.2f}.")

    lines.extend(["", "## Alternatives"])
    lines.extend(f"- {alternative}" for alternative in alternatives) if alternatives else lines.append("- No budget alternatives were needed.")
    lines.extend(["", "## Research Sources"])
    sources = [str(item.get("url")) for item in search.get("results", []) if isinstance(item, dict) and item.get("url")]
    lines.extend(f"- {source}" for source in sources) if sources else lines.append("- No online research sources were used.")
    return "\n".join(lines)


def plan_trip(request: TripRequest) -> PlanningResult:
    """Gather tool evidence, revise costs if needed, then run the sequential agent crew."""
    check_ollama()
    settings = get_settings()
    search = _tool_json(SearchTool(), destination=request.destination, query="attractions local experiences activities")
    weather = _tool_json(
        WeatherTool(), destination=request.destination, start_date=request.start_date.isoformat(), duration_days=request.duration_days
    )
    hotel_data = _tool_json(
        HotelTool(), destination=request.destination, nights=max(0, request.duration_days - 1), travelers=request.travelers
    )
    transport_data = _tool_json(
        TransportTool(),
        origin=request.origin,
        destination=request.destination,
        duration_days=request.duration_days,
        travelers=request.travelers,
    )
    date_schedule = _tool_json(
        DateUtilityTool(), start_date=request.start_date.isoformat(), duration_days=request.duration_days
    )

    attractions = [item for item in search.get("results", []) if isinstance(item, dict)]
    hotel, transport, budget, selected_attractions, food_allowance, alternatives = _select_budget_options(
        request, hotel_data, transport_data, attractions, BudgetCalculatorTool()
    )
    trip_requirements = {
        "destination": request.destination,
        "origin": request.origin,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "duration_days": request.duration_days,
        "travelers": request.travelers,
        "budget_usd": request.budget_usd,
        "interests": request.interests,
    }
    planning_facts = {
        "selected_hotel": hotel,
        "selected_transport": transport,
        "budget": budget,
        "food_allowance_per_person_per_day_usd": food_allowance,
        "selected_attractions": selected_attractions,
        "weather": weather,
        "alternatives": alternatives,
        "notices": [
            "Hotel and transport offers are mock estimates, not live quotes.",
            "Verify venue prices, availability, opening hours, and routes before booking.",
        ],
    }
    crew_inputs = {
        "trip_requirements": json.dumps(trip_requirements, ensure_ascii=False),
        "search_results": json.dumps(search, ensure_ascii=False),
        "weather_summary": json.dumps(weather, ensure_ascii=False),
        "logistics_data": json.dumps({"hotel": hotel, "transport": transport}, ensure_ascii=False),
        "budget_data": json.dumps(budget, ensure_ascii=False),
        "date_schedule": json.dumps(date_schedule, ensure_ascii=False),
        "planning_facts": json.dumps(planning_facts, ensure_ascii=False),
    }
    logger.info(
        "Starting CrewAI plan: destination=%s days=%d web_search=%s",
        request.destination,
        request.duration_days,
        settings.enable_web_search,
    )
    itinerary = run_travel_crew(crew_inputs)
    report = _build_final_report(
        request,
        budget,
        hotel,
        transport,
        selected_attractions,
        weather,
        search,
        alternatives,
        itinerary,
    )
    return PlanningResult(
        request=request,
        report=report,
        budget=budget,
        selected_hotel=hotel,
        selected_transport=transport,
        attractions=selected_attractions,
        weather=weather,
        search=search,
        alternatives=alternatives,
    )
