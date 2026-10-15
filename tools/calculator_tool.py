"""Deterministic budget calculations exposed as a CrewAI tool."""

from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    hotel_cost_usd: float = Field(ge=0)
    transport_cost_usd: float = Field(ge=0)
    food_per_person_per_day_usd: float = Field(ge=0)
    attraction_cost_per_person_usd: float = Field(ge=0)
    travelers: int = Field(ge=1)
    duration_days: int = Field(ge=1)
    budget_usd: float = Field(gt=0)


class BudgetCalculatorTool(BaseTool):
    name: str = "trip_budget_calculator"
    description: str = "Calculate itemized trip costs and compare the exact total with the customer budget. Do not estimate or alter supplied amounts."
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(
        self,
        hotel_cost_usd: float,
        transport_cost_usd: float,
        food_per_person_per_day_usd: float,
        attraction_cost_per_person_usd: float,
        travelers: int,
        duration_days: int,
        budget_usd: float,
    ) -> str:
        food = food_per_person_per_day_usd * travelers * duration_days
        attractions = attraction_cost_per_person_usd * travelers
        grand_total = round(hotel_cost_usd + transport_cost_usd + food + attractions, 2)
        remaining = round(budget_usd - grand_total, 2)
        return json.dumps(
            {
                "hotel_cost_usd": round(hotel_cost_usd, 2),
                "transport_cost_usd": round(transport_cost_usd, 2),
                "food_cost_usd": round(food, 2),
                "attraction_cost_usd": round(attractions, 2),
                "grand_total_usd": grand_total,
                "budget_usd": round(budget_usd, 2),
                "within_budget": remaining >= 0,
                "remaining_budget_usd": max(remaining, 0),
                "budget_exceeded_usd": max(-remaining, 0),
            }
        )
