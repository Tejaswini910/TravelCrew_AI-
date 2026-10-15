from datetime import date, timedelta

from travel_planner.models import TripRequest
from travel_planner.services.planner import _build_final_report, _select_budget_options
from travel_planner.tools.calculator_tool import BudgetCalculatorTool


def test_budget_revision_uses_free_activities_and_recalculates() -> None:
    request = TripRequest(
        destination="Lisbon",
        origin="Boston",
        start_date=date.today() + timedelta(days=10),
        duration_days=3,
        budget_usd=500,
        travelers=1,
        interests=["Sightseeing"],
    )
    hotels = {
        "offers": [
            {"name": "Budget mock", "estimated_total_usd": 300},
            {"name": "Standard mock", "estimated_total_usd": 600},
        ]
    }
    transport = {
        "options": [
            {"name": "Coach mock", "estimated_total_usd": 50},
            {"name": "Rail mock", "estimated_total_usd": 100},
        ]
    }
    attractions = [
        {"name": "Paid museum", "admission_usd": 100},
        {"name": "Free garden", "admission_usd": 0},
    ]

    hotel, transit, budget, selected, food_allowance, alternatives = _select_budget_options(
        request, hotels, transport, attractions, BudgetCalculatorTool()
    )

    assert budget["within_budget"] is True
    assert budget["grand_total_usd"] == 440
    assert hotel["name"] == "Budget mock"
    assert transit["name"] == "Coach mock"
    assert [item["name"] for item in selected] == ["Free garden"]
    assert food_allowance == 30
    assert alternatives


def test_final_report_uses_python_calculated_budget() -> None:
    request = TripRequest(
        destination="Lisbon",
        origin="Boston",
        start_date=date.today() + timedelta(days=10),
        duration_days=3,
        budget_usd=2500,
        travelers=1,
        interests=["Sightseeing"],
    )
    budget = {
        "hotel_cost_usd": 230.0,
        "transport_cost_usd": 146.0,
        "food_cost_usd": 135.0,
        "attraction_cost_usd": 21.0,
        "grand_total_usd": 532.0,
        "within_budget": True,
        "remaining_budget_usd": 1968.0,
        "budget_exceeded_usd": 0.0,
    }

    report = _build_final_report(
        request=request,
        budget=budget,
        hotel={"name": "Standard mock", "estimated_total_usd": 230},
        transport={"name": "Rail mock", "estimated_total_usd": 146},
        attractions=[],
        weather={"source": "offline estimate", "summary": "Seasonal estimate."},
        search={"results": []},
        alternatives=[],
        itinerary="Day 1: Sightseeing.",
    )

    assert "Grand total: $532.00 USD" in report
    assert "Within budget; $1,968.00 remaining." in report
    assert "$802.00" not in report