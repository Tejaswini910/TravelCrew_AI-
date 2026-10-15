"""Deterministic sample transport estimates; no carrier inventory is queried."""

from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TransportInput(BaseModel):
    origin: str = Field(description="Starting location")
    destination: str = Field(description="Destination")
    duration_days: int = Field(ge=1, le=30)
    travelers: int = Field(ge=1, le=20)


class TransportTool(BaseTool):
    name: str = "mock_transport_options"
    description: str = "Return mock round-trip and local transport estimates in USD, clearly marked as estimates rather than live fares."
    args_schema: Type[BaseModel] = TransportInput

    def _run(self, origin: str, destination: str, duration_days: int, travelers: int) -> str:
        same_region = origin.strip().casefold() == destination.strip().casefold()
        fares = (("Coach (sample)", 35), ("Rail (sample)", 110), ("Air (sample)", 280))
        if same_region:
            fares = (("Public transit (sample)", 12), ("Regional rail (sample)", 35), ("Taxi / rideshare allowance (sample)", 75))
        local_per_day_person = 12.0
        options = []
        for name, fare_per_person in fares:
            outbound_return = fare_per_person * travelers
            local_total = local_per_day_person * duration_days * travelers
            options.append(
                {
                    "name": name,
                    "round_trip_per_person_usd": fare_per_person,
                    "round_trip_total_usd": round(outbound_return, 2),
                    "local_transport_total_usd": round(local_total, 2),
                    "estimated_total_usd": round(outbound_return + local_total, 2),
                    "source": "local mock data; not a live schedule or fare",
                }
            )
        return json.dumps(
            {"origin": origin, "destination": destination, "options": options, "notice": "Check real routes, schedules, baggage, and fares before booking."}
        )
