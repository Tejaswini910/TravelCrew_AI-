"""Validated request and result models shared by the UI and planner."""

from __future__ import annotations

from datetime import date, timedelta
from math import isfinite

from pydantic import BaseModel, Field, field_validator


class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    origin: str = Field(min_length=2, max_length=100)
    start_date: date
    duration_days: int = Field(ge=1, le=30)
    budget_usd: float = Field(gt=0, le=5_000_000)
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(min_length=1, max_length=10)

    @field_validator("destination", "origin", mode="before")
    @classmethod
    def normalize_location(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("A destination and starting location are required")
        return value.strip()

    @field_validator("start_date")
    @classmethod
    def require_future_start_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Travel start date must be today or later")
        return value

    @field_validator("budget_usd")
    @classmethod
    def require_finite_budget(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("Budget must be a finite number")
        return round(value, 2)

    @field_validator("interests")
    @classmethod
    def normalize_interests(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if not normalized:
            raise ValueError("Select at least one interest")
        return list(dict.fromkeys(normalized))

    @property
    def end_date(self) -> date:
        return self.start_date + timedelta(days=self.duration_days - 1)


class PlanningResult(BaseModel):
    request: TripRequest
    report: str
    budget: dict[str, float | bool | str]
    selected_hotel: dict[str, object]
    selected_transport: dict[str, object]
    attractions: list[dict[str, object]]
    weather: dict[str, object]
    search: dict[str, object]
    alternatives: list[str]
