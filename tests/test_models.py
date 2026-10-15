from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from travel_planner.models import TripRequest


def make_request(**changes: object) -> TripRequest:
    values: dict[str, object] = {
        "destination": " Lisbon ",
        "origin": "Boston",
        "start_date": date.today() + timedelta(days=2),
        "duration_days": 3,
        "budget_usd": 1500,
        "travelers": 2,
        "interests": [" Food ", "Sightseeing", "Food"],
    }
    values.update(changes)
    return TripRequest(**values)


def test_request_normalizes_values_and_calculates_end_date() -> None:
    request = make_request()
    assert request.destination == "Lisbon"
    assert request.interests == ["Food", "Sightseeing"]
    assert request.end_date == request.start_date + timedelta(days=2)


@pytest.mark.parametrize("budget", [0, -1, float("inf"), float("nan")])
def test_request_rejects_invalid_budget(budget: float) -> None:
    with pytest.raises(ValidationError):
        make_request(budget_usd=budget)


def test_request_rejects_past_dates() -> None:
    with pytest.raises(ValidationError):
        make_request(start_date=date.today() - timedelta(days=1))
