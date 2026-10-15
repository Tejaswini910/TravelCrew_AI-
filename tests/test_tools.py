import json
from datetime import date, timedelta

from travel_planner.tools.calculator_tool import BudgetCalculatorTool
from travel_planner.tools.date_tool import DateUtilityTool
from travel_planner.tools.hotel_tool import HotelTool
from travel_planner.tools.search_tool import SearchTool
from travel_planner.tools.transport_tool import TransportTool


def test_calculator_reports_exact_totals_and_budget_status() -> None:
    result = json.loads(
        BudgetCalculatorTool().run(
            hotel_cost_usd=200,
            transport_cost_usd=100,
            food_per_person_per_day_usd=20,
            attraction_cost_per_person_usd=15,
            travelers=2,
            duration_days=3,
            budget_usd=500,
        )
    )
    assert result["grand_total_usd"] == 450
    assert result["within_budget"] is True
    assert result["remaining_budget_usd"] == 50


def test_offline_search_returns_catalog_sources() -> None:
    result = json.loads(SearchTool().run(destination="Paris", query="museums"))
    assert result["source"] == "bundled_offline_catalog"
    assert any(item["name"] == "Louvre Museum" for item in result["results"])


def test_mock_options_are_labeled_and_have_totals() -> None:
    hotels = json.loads(HotelTool().run(destination="Rome", nights=2, travelers=2))
    transport = json.loads(TransportTool().run(origin="Boston", destination="Rome", duration_days=3, travelers=2))
    assert hotels["offers"][0]["estimated_total_usd"] > 0
    assert "mock" in hotels["offers"][0]["source"]
    assert transport["options"][0]["estimated_total_usd"] > 0


def test_date_tool_returns_one_entry_per_day() -> None:
    start = date.today() + timedelta(days=4)
    result = json.loads(DateUtilityTool().run(start_date=start.isoformat(), duration_days=3))
    assert len(result["days"]) == 3
    assert result["days"][0]["date"] == start.isoformat()
    assert result["end_date"] == (start + timedelta(days=2)).isoformat()