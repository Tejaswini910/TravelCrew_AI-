"""Optional Open-Meteo forecast with an offline seasonal fallback."""

from __future__ import annotations

import json
import logging
import time
from datetime import date, timedelta
from typing import Type
from urllib.parse import urlencode
from urllib.request import urlopen

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from travel_planner.config.settings import get_settings

logger = logging.getLogger(__name__)


class WeatherInput(BaseModel):
    destination: str = Field(description="City or region")
    start_date: str = Field(description="Trip start date in YYYY-MM-DD format")
    duration_days: int = Field(ge=1, le=30)


class WeatherTool(BaseTool):
    name: str = "destination_weather"
    description: str = "Get an optional Open-Meteo forecast or an explicitly labeled seasonal planning estimate. No API key is required."
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, destination: str, start_date: str, duration_days: int) -> str:
        trip_date = date.fromisoformat(start_date)
        if get_settings().enable_web_search and date.today() <= trip_date <= date.today() + timedelta(days=15):
            live = self._forecast(destination, trip_date, duration_days)
            if live:
                return json.dumps(live, ensure_ascii=False)
        season = self._season(trip_date.month)
        return json.dumps(
            {
                "source": "offline seasonal planning estimate",
                "destination": destination,
                "period": trip_date.isoformat(),
                "summary": f"Typical {season} conditions vary by destination; check a current forecast closer to departure.",
                "is_live_forecast": False,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _season(month: int) -> str:
        if month in (12, 1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        return "autumn"

    @staticmethod
    def _get_json(url: str) -> dict[str, object]:
        for attempt in range(2):
            try:
                with urlopen(url, timeout=5) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception:
                if attempt == 1:
                    raise
                time.sleep(0.25)
        raise RuntimeError("Weather request failed")

    def _forecast(self, destination: str, trip_date: date, duration_days: int) -> dict[str, object] | None:
        try:
            query = urlencode({"name": destination, "count": 1, "language": "en", "format": "json"})
            place = self._get_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
            places = place.get("results", [])
            if not places:
                return None
            location = places[0]
            forecast_query = urlencode(
                {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "start_date": trip_date.isoformat(),
                    "end_date": (trip_date + timedelta(days=min(duration_days - 1, 14))).isoformat(),
                    "timezone": "auto",
                }
            )
            forecast = self._get_json(f"https://api.open-meteo.com/v1/forecast?{forecast_query}")
            return {
                "source": "Open-Meteo forecast",
                "destination": destination,
                "summary": "Forecast for the requested dates; conditions can change.",
                "daily": forecast.get("daily", {}),
                "is_live_forecast": True,
            }
        except Exception as exc:  # Weather is optional; preserve offline planning on outages.
            logger.info("Optional weather lookup unavailable: %s", exc)
            return None
