"""Budget analyst agent."""

from crewai import Agent

from travel_planner.agents._common import build_agent
from travel_planner.tools.calculator_tool import BudgetCalculatorTool


def create_budget_analyst() -> Agent:
    return build_agent(
        role="Budget Analyst Agent",
        goal="Use the calculator tool to verify hotel, transport, food, and attraction costs against the customer budget, then explain practical savings.",
        backstory="You are a meticulous cost analyst. Arithmetic comes from the calculator tool, not mental estimates; every assumption and shortfall is explicit.",
        tools=[BudgetCalculatorTool()],
    )
