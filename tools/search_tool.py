"""Local destination search with an optional, keyless DuckDuckGo fallback."""

from __future__ import annotations

import json
import logging
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from travel_planner.config.settings import get_settings

logger = logging.getLogger(__name__)

_ATTRACTIONS: dict[str, list[dict[str, object]]] = {
    "paris": [
        {"name": "Louvre Museum", "category": "museum", "admission_usd": 25, "url": "https://www.louvre.fr/en"},
        {"name": "Eiffel Tower", "category": "sightseeing", "admission_usd": 30, "url": "https://www.toureiffel.paris/en"},
        {"name": "Musée d'Orsay", "category": "museum", "admission_usd": 18, "url": "https://www.musee-orsay.fr/en"},
        {"name": "Montmartre neighborhood walk", "category": "local experience", "admission_usd": 0, "url": "https://parisjetaime.com/eng/"},
        {"name": "Luxembourg Gardens", "category": "relaxation", "admission_usd": 0, "url": "https://parisjetaime.com/eng/"},
    ],
    "tokyo": [
        {"name": "Sensō-ji Temple", "category": "sightseeing", "admission_usd": 0, "url": "https://www.senso-ji.jp/english/"},
        {"name": "Tokyo National Museum", "category": "museum", "admission_usd": 7, "url": "https://www.tnm.jp/?lang=en"},
        {"name": "Shinjuku Gyoen National Garden", "category": "relaxation", "admission_usd": 3, "url": "https://www.env.go.jp/garden/shinjukugyoen/english/"},
        {"name": "Tsukiji Outer Market", "category": "food and local experience", "admission_usd": 0, "url": "https://www.tsukiji.or.jp/english/"},
        {"name": "Meiji Jingu Shrine", "category": "sightseeing", "admission_usd": 0, "url": "https://www.meijijingu.or.jp/en/"},
    ],
    "rome": [
        {"name": "Colosseum Archaeological Park", "category": "sightseeing", "admission_usd": 20, "url": "https://colosseo.it/en/"},
        {"name": "Vatican Museums", "category": "museum", "admission_usd": 22, "url": "https://www.museivaticani.va/content/museivaticani/en.html"},
        {"name": "Pantheon", "category": "sightseeing", "admission_usd": 5, "url": "https://direzionemuseiroma.cultura.gov.it/pantheon/"},
        {"name": "Villa Borghese gardens", "category": "relaxation", "admission_usd": 0, "url": "https://www.turismoroma.it/en"},
        {"name": "Trastevere neighborhood walk", "category": "local experience", "admission_usd": 0, "url": "https://www.turismoroma.it/en"},
    ],
    "london": [
        {"name": "British Museum", "category": "museum", "admission_usd": 0, "url": "https://www.britishmuseum.org/"},
        {"name": "Natural History Museum", "category": "museum", "admission_usd": 0, "url": "https://www.nhm.ac.uk/"},
        {"name": "Tower of London", "category": "sightseeing", "admission_usd": 38, "url": "https://www.hrp.org.uk/tower-of-london/"},
        {"name": "Hyde Park", "category": "relaxation", "admission_usd": 0, "url": "https://www.royalparks.org.uk/visit/parks/hyde-park"},
        {"name": "Borough Market", "category": "food and local experience", "admission_usd": 0, "url": "https://boroughmarket.org.uk/"},
    ],
    "new york": [
        {"name": "Central Park", "category": "relaxation", "admission_usd": 0, "url": "https://www.centralparknyc.org/"},
        {"name": "The Metropolitan Museum of Art", "category": "museum", "admission_usd": 30, "url": "https://www.metmuseum.org/"},
        {"name": "American Museum of Natural History", "category": "museum", "admission_usd": 30, "url": "https://www.amnh.org/"},
        {"name": "Staten Island Ferry", "category": "local experience", "admission_usd": 0, "url": "https://www.nyc.gov/html/dot/html/ferrybus/staten-island-ferry.shtml"},
        {"name": "High Line", "category": "sightseeing", "admission_usd": 0, "url": "https://www.thehighline.org/"},
    ],
    "lisbon": [
        {"name": "Jerónimos Monastery", "category": "sightseeing", "admission_usd": 12, "url": "https://www.museusemonumentos.pt/en/museus-e-monumentos/mosteiro-dos-jeronimos"},
        {"name": "Belém Tower", "category": "sightseeing", "admission_usd": 9, "url": "https://www.museusemonumentos.pt/en/museus-e-monumentos/torre-de-belem"},
        {"name": "Alfama neighborhood walk", "category": "local experience", "admission_usd": 0, "url": "https://www.visitlisboa.com/en"},
        {"name": "Time Out Market Lisboa", "category": "food and local experience", "admission_usd": 0, "url": "https://www.timeoutmarket.com/lisboa/en/"},
        {"name": "Miradouro da Senhora do Monte", "category": "sightseeing", "admission_usd": 0, "url": "https://www.visitlisboa.com/en"},
    ],
}


class SearchInput(BaseModel):
    destination: str = Field(description="City or region to research")
    query: str = Field(default="attractions and local experiences", description="Research topic")


class SearchTool(BaseTool):
    name: str = "destination_search"
    description: str = "Search curated local destination facts; optionally use keyless web search when enabled. Returns JSON with source URLs."
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, destination: str, query: str = "attractions and local experiences") -> str:
        normalized = destination.strip().lower()
        local = next((items for city, items in _ATTRACTIONS.items() if city in normalized or normalized in city), [])
        results: list[dict[str, object]] = list(local)
        source = "bundled_offline_catalog"
        if get_settings().enable_web_search:
            try:
                from ddgs import DDGS

                web_results = list(DDGS().text(f"{destination} {query}", max_results=5))
                if web_results:
                    results = [
                        {"name": item.get("title", "Search result"), "summary": item.get("body", ""), "url": item.get("href", "")}
                        for item in web_results
                    ]
                    source = "DuckDuckGo search; verify details with the linked publisher"
            except Exception as exc:  # Optional search must not prevent offline planning.
                logger.warning("Optional destination search failed: %s", exc)

        return json.dumps(
            {
                "destination": destination,
                "source": source if results else "no_verified_offline_results",
                "results": results,
                "notice": "Bundled prices are illustrative USD estimates; verify current prices and opening hours with each venue.",
            },
            ensure_ascii=False,
        )
