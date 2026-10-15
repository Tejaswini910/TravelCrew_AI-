"""Hotel and transport research agent."""

from crewai import Agent

from travel_planner.agents._common import build_agent
from travel_planner.tools.hotel_tool import HotelTool
from travel_planner.tools.transport_tool import TransportTool


def create_hotel_transport_agent() -> Agent:
    return build_agent(
        role="Hotel and Transport Agent",
        goal="Compare accommodation and transport options, explain their trade-offs, and report supplied mock estimates accurately.",
        backstory="You are a practical travel logistics specialist. You never represent prototype estimates as real availability, booking inventory, or live fares.",
        tools=[HotelTool(), TransportTool()],
    )
