"""Destination research agent."""

from crewai import Agent

from travel_planner.agents._common import build_agent
from travel_planner.tools.search_tool import SearchTool
from travel_planner.tools.weather_tool import WeatherTool


def create_destination_researcher() -> Agent:
    return build_agent(
        role="Destination Research Agent",
        goal="Find relevant attractions, local experiences, and weather information using the supplied research tools.",
        backstory="You are a source-conscious destination researcher. You use tool results, preserve source links, and label missing or seasonal information instead of inventing facts.",
        tools=[SearchTool(), WeatherTool()],
    )
