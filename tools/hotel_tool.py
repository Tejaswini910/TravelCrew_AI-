"""Deterministic sample hotel offers; these are not booking inventory."""

from __future__ import annotations

import json
from math import ceil
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class HotelInput(BaseModel):
    destination: str = Field(description="Destination city")
    nights: int = Field(ge=0, le=29)
    travelers: int = Field(ge=1, le=20)


class HotelTool(BaseTool):
    name: str = "mock_hotel_options"
    description: str = "Return clearly labeled mock accommodation estimates in USD. These are not live availability or booking quotes."
    args_schema: Type[BaseModel] = HotelInput

    def _run(self, destination: str, nights: int, travelers: int) -> str:
        rooms = ceil(travelers / 2)
        location_factor = 1.25 if destination.strip().lower() in {"paris", "london", "new york", "tokyo"} else 1.0
        offers = []
        for name, base_rate, category in (
            ("Budget guesthouse (sample)", 55, "budget"),
            ("Standard hotel (sample)", 115, "standard"),
            ("Comfort hotel (sample)", 190, "comfort"),
        ):
            rate = round(base_rate * location_factor, 2)
            offers.append(
                {
                    "name": name,
                    "category": category,
                    "estimated_rate_per_room_night_usd": rate,
                    "rooms": rooms,
                    "nights": nights,
                    "estimated_total_usd": round(rate * rooms * nights, 2),
                    "source": "local mock data; not a real property or quote",
                }
            )
        return json.dumps({"destination": destination, "offers": offers, "notice": "Confirm availability, taxes, and fees before booking."})
