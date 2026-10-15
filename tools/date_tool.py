"""Date validation and day-by-day schedule utilities."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DateInput(BaseModel):
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    duration_days: int = Field(ge=1, le=30)


class DateUtilityTool(BaseTool):
    name: str = "trip_date_schedule"
    description: str = "Validate a trip start date and return the exact date and weekday for each itinerary day."
    args_schema: Type[BaseModel] = DateInput

    def _run(self, start_date: str, duration_days: int) -> str:
        start = date.fromisoformat(start_date)
        days = [
            {
                "day": index + 1,
                "date": (start + timedelta(days=index)).isoformat(),
                "weekday": (start + timedelta(days=index)).strftime("%A"),
            }
            for index in range(duration_days)
        ]
        return json.dumps({"days": days, "end_date": days[-1]["date"]})
