"""Itinerary planner agent."""

from crewai import Agent

from travel_planner.agents._common import build_agent
from travel_planner.tools.date_tool import DateUtilityTool


def create_itinerary_planner() -> Agent:
    return build_agent(
        role="Itinerary Planner Agent",
        goal="Create a balanced day-by-day schedule that respects trip dates, interests, researched options, budget decisions, and available information.",
        backstory="You are an experienced itinerary designer. You cluster activities sensibly, leave breathing room, and avoid asserting unknown opening hours or journey times.",
        tools=[DateUtilityTool()],
    )
