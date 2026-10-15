"""Construct and run the sequential CrewAI planning workflow."""

from crewai import Crew, Process

from travel_planner.agents.budget_analyst import create_budget_analyst
from travel_planner.agents.coordinator import create_coordinator
from travel_planner.agents.destination_researcher import create_destination_researcher
from travel_planner.agents.hotel_transport import create_hotel_transport_agent
from travel_planner.agents.itinerary_planner import create_itinerary_planner
from travel_planner.tasks.travel_tasks import create_travel_tasks


def run_travel_crew(inputs: dict[str, str]) -> str:
    coordinator = create_coordinator()
    researcher = create_destination_researcher()
    hotel_transport = create_hotel_transport_agent()
    budget_analyst = create_budget_analyst()
    itinerary_planner = create_itinerary_planner()
    tasks = create_travel_tasks(coordinator, researcher, hotel_transport, budget_analyst, itinerary_planner)
    crew = Crew(
        agents=[coordinator, researcher, hotel_transport, budget_analyst, itinerary_planner],
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
        memory=False,
    )
    crew_output = crew.kickoff(inputs=inputs)
    if len(crew_output.tasks_output) < 2:
        raise RuntimeError("The travel crew did not return its itinerary task output")
    return str(crew_output.tasks_output[-2].raw).strip()
