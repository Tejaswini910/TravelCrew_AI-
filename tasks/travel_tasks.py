"""Sequential CrewAI tasks and explicit inter-task context."""

from crewai import Agent, Task


def create_travel_tasks(
    coordinator: Agent,
    researcher: Agent,
    hotel_transport: Agent,
    budget_analyst: Agent,
    itinerary_planner: Agent,
) -> list[Task]:
    research = Task(
        description=(
            "Use the supplied destination search and weather results as your research evidence: "
            "{search_results}; {weather_summary}. Customer brief: {trip_requirements}. "
            "These tool results were freshly retrieved; do not repeat the calls unless a required value is missing. "
            "Return relevant attractions and experiences with source URLs and admission estimates where supplied. "
            "Keep the summary under 120 words. State unknowns; do not invent venues or live forecasts."
        ),
        expected_output="A concise, source-backed attraction summary and any data limitations.",
        agent=researcher,
        async_execution=True,
    )
    logistics = Task(
        description=(
            "Compare the freshly retrieved hotel and transport tool results: {logistics_data}. "
            "Customer brief: {trip_requirements}. Do not repeat tool calls unless a required value is missing. "
            "Keep the comparison under 100 words and label all prices as mock estimates, not live inventory."
        ),
        expected_output="A practical hotel and transport comparison using the supplied estimates.",
        agent=hotel_transport,
        async_execution=True,
    )
    budget = Task(
        description=(
            "The Python budget calculator has already calculated the authoritative totals: {budget_data}. "
            "Use those exact amounts and the research/logistics task outputs to explain budget status and applied trade-offs. "
            "Do not repeat calculations or change totals. Keep your report under 100 words."
        ),
        expected_output="An itemized budget assessment consistent with the calculator output.",
        agent=budget_analyst,
        context=[research, logistics],
    )
    itinerary = Task(
        description=(
            "Build the day-by-day itinerary using the validated dates {date_schedule} and approved facts {planning_facts}. "
            "The date utility has already supplied exact dates; do not call it again. Respect interests and budget decisions. "
            "Keep each day concise. If research is empty, use flexible time instead of inventing attractions."
        ),
        expected_output="A date-specific itinerary with a morning, afternoon, and optional evening plan for every trip day.",
        agent=itinerary_planner,
        context=[research, logistics, budget],
    )
    final_report = Task(
        description=(
            "As Travel Coordinator, synthesize the specialist task outputs and exact facts: {planning_facts}. "
            "Include trip summary, dates, attractions, lodging, transport, weather, every itinerary day, expenses, budget status, alternatives, and sources. "
            "Use supplied totals exactly. Clearly label mock estimates and distinguish seasonal estimates from live forecasts. "
            "Be concise and do not repeat research or tool calls."
        ),
        expected_output="A complete customer-ready travel plan with every requested section and no unsupported claims.",
        agent=coordinator,
        context=[research, logistics, budget, itinerary],
    )
    return [research, logistics, budget, itinerary, final_report]
