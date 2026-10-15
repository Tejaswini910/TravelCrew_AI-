"""Streamlit interface for the local Ollama travel planner."""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

# Streamlit does not consistently add the project parent to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from travel_planner.logging_config import configure_logging
from travel_planner.models import TripRequest
from travel_planner.services.planner import OllamaUnavailableError, plan_trip

configure_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="TravelCrew | Smart Trip Planner", page_icon="✦", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --ink: #1d2939;
        --navy: #254c78;
        --navy-deep: #172b45;
        --blue: #6f93b8;
        --copper: #c96f50;
        --paper: #f1f4f7;
        --line: #d5dde6;
    }
    .stApp {
        color: var(--ink);
        background-color: var(--paper);
        background-image:
            linear-gradient(90deg, rgba(37,76,120,.03) 1px, transparent 1px),
            linear-gradient(rgba(37,76,120,.03) 1px, transparent 1px),
            linear-gradient(130deg, #f5f7fa 0%, #eaf0f6 62%, #f5eeea 100%);
        background-size: 34px 34px, 34px 34px, cover;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 1.3rem; }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.65rem 1.8rem 1.55rem;
        margin-bottom: 1.35rem;
        color: #f8fafc;
        border-radius: 8px;
        background: linear-gradient(108deg, var(--navy-deep) 0%, #254c78 100%);
        box-shadow: 0 12px 28px rgba(23,43,69,.14);
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 9px;
        inset: 0 auto 0 0;
        background: var(--coral);
    }
    .hero h1 {
        color: #f8fafc;
        font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
        font-size: 2.65rem;
        line-height: 1.08;
        margin: 0;
        letter-spacing: 0;
    }
    .hero p { color: #d7e2ee; font-size: 1.04rem; margin: .55rem 0 0; }
    div[data-testid="stForm"] {
        background: rgba(255,255,255,.94);
        border: 1px solid var(--line);
        border-top: 4px solid var(--copper);
        padding: 1.25rem;
        border-radius: 8px;
        box-shadow: 0 9px 24px rgba(29,41,57,.07);
    }
    div[data-testid="stForm"] h3, h2, h3 { color: var(--ink); letter-spacing: 0; }
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        border-color: #c8d3df;
        border-radius: 5px;
        background: #ffffff;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 2px rgba(111,147,184,.28) !important;
    }
    div.stButton > button, div[data-testid="stFormSubmitButton"] button {
        background: var(--navy);
        color: #ffffff;
        border: 0;
        border-radius: 5px;
        min-height: 2.8rem;
        font-weight: 650;
        transition: background-color .18s ease, transform .18s ease;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        background: var(--navy-deep);
        color: white;
        transform: translateY(-1px);
    }
    [data-testid="stSidebar"] { background: var(--navy-deep); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #f8fafc; }
    [data-testid="stSidebar"] p { color: #d4dfeb; }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,.92);
        border: 1px solid var(--line);
        border-top: 3px solid var(--blue);
        padding: .8rem;
        border-radius: 6px;
        box-shadow: 0 6px 16px rgba(29,41,57,.05);
    }
    [data-baseweb="tab-list"] { gap: .35rem; }
    button[data-baseweb="tab"] { color: #60758e; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--navy-deep);
        border-bottom-color: var(--copper);
    }
    @media (max-width: 640px) {
        .hero { padding: 1.35rem 1.2rem; }
        .hero h1 { font-size: 2.15rem; }
        div[data-testid="stForm"] { padding: .9rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>TravelCrew</h1><p>Thoughtful itineraries, locally powered by Ollama.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Planning notes")
    st.caption("Hotel and transport prices are prototype estimates, not live inventory. No booking is made.")
    st.caption("Offline attraction research covers the bundled city catalog. Optional web search can be enabled in .env.")
    st.caption("Budgets are in USD. Ollama must be reachable by this app.")

with st.form("trip_request"):
    st.subheader("Your trip")
    location_col, origin_col = st.columns(2)
    destination = location_col.text_input("Destination", placeholder="Lisbon")
    origin = origin_col.text_input("Starting location", placeholder="Boston, MA")
    date_col, duration_col, travelers_col = st.columns(3)
    start_date = date_col.date_input("Start date", value=date.today(), min_value=date.today())
    duration_days = duration_col.number_input("Duration (days)", min_value=1, max_value=30, value=3, step=1)
    travelers = travelers_col.number_input("Travelers", min_value=1, max_value=20, value=1, step=1)
    budget_col, interests_col = st.columns([1, 2])
    budget = budget_col.number_input("Total budget (USD)", min_value=1.0, value=2500.0, step=100.0)
    interests = interests_col.multiselect(
        "Interests",
        ["Sightseeing", "Museums", "Food", "Shopping", "Adventure", "Relaxation", "Local culture", "Nature"],
        default=["Sightseeing", "Food"],
    )
    submitted = st.form_submit_button("Build my travel plan", use_container_width=True)

if submitted:
    st.session_state.pop("travel_plan", None)
    if not destination.strip():
        st.error("Enter a destination before building your plan.")
    elif not origin.strip():
        st.error("Enter a starting location before building your plan.")
    else:
        try:
            request = TripRequest(
                destination=destination,
                origin=origin,
                start_date=start_date,
                duration_days=int(duration_days),
                budget_usd=budget,
                travelers=int(travelers),
                interests=interests,
            )
        except ValidationError as exc:
            for error in exc.errors():
                st.error(error["msg"].removeprefix("Value error, "))
        except ValueError as exc:
            st.error(str(exc))
        else:
            with st.spinner("Local llama3.2 is coordinating your plan; generation may take a few minutes on this machine…"):
                try:
                    st.session_state["travel_plan"] = plan_trip(request)
                except OllamaUnavailableError as exc:
                    st.error(str(exc))
                    st.info("Local setup: install Ollama, run `ollama pull llama3.2`, then start the Ollama service.")
                except Exception as exc:
                    logger.exception("Travel planning failed")
                    st.error("The plan could not be completed. Check that Ollama is available and try again.")
                    if st.query_params.get("debug") == "1":
                        st.exception(exc)

result = st.session_state.get("travel_plan")
if result:
    request = result.request
    budget_data = result.budget
    st.divider()
    st.subheader(f"{request.destination} · {request.duration_days} days")
    st.caption(f"{request.start_date:%A, %B %d, %Y} – {request.end_date:%A, %B %d, %Y} · From {request.origin}")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total budget", f"${request.budget_usd:,.2f}")
    metric_cols[1].metric("Estimated trip cost", f"${float(budget_data['grand_total_usd']):,.2f}")
    metric_cols[2].metric(
        "Budget remaining",
        f"${float(budget_data['remaining_budget_usd']):,.2f}" if budget_data["within_budget"] else "Over budget",
    )
    metric_cols[3].metric(
        "Budget status",
        "Within budget" if budget_data["within_budget"] else f"Over by ${float(budget_data['budget_exceeded_usd']):,.2f}",
    )

    if not result.search.get("results"):
        st.warning("No verified offline attractions were found for this destination. Enable optional web search or verify local attractions before relying on a sightseeing plan.")
    if not budget_data["within_budget"]:
        st.error(f"Even the lowest-cost mock combination exceeds budget by ${float(budget_data['budget_exceeded_usd']):,.2f}.")
    elif result.alternatives:
        st.info("Budget adjustments applied: " + " ".join(result.alternatives))

    plan_tab, costs_tab, sources_tab = st.tabs(["Travel plan", "Expenses & options", "Research sources"])
    with plan_tab:
        st.markdown(result.report)
    with costs_tab:
        st.subheader("Expense breakdown")
        expense_rows = {
            "Hotel": budget_data["hotel_cost_usd"],
            "Transport": budget_data["transport_cost_usd"],
            "Food allowance": budget_data["food_cost_usd"],
            "Attractions": budget_data["attraction_cost_usd"],
            "Grand total": budget_data["grand_total_usd"],
        }
        st.dataframe(
            [{"Category": name, "Estimated cost (USD)": f"${float(amount):,.2f}"} for name, amount in expense_rows.items()],
            hide_index=True,
            use_container_width=True,
        )
        st.subheader("Selected mock options")
        st.write(f"**Accommodation:** {result.selected_hotel['name']} · ${float(result.selected_hotel['estimated_total_usd']):,.2f}")
        st.write(f"**Transport:** {result.selected_transport['name']} · ${float(result.selected_transport['estimated_total_usd']):,.2f}")
        st.caption("Mock options are planning estimates only; they do not reflect actual availability, taxes, or current fares.")
    with sources_tab:
        st.write(f"**Research mode:** {result.search.get('source', 'unknown')}")
        for attraction in result.attractions:
            name = attraction.get("name", "Research result")
            url = attraction.get("url")
            if url:
                st.markdown(f"- [{name}]({url})")
            else:
                st.write(f"- {name}: {attraction.get('summary', '')}")
        st.write(f"**Weather:** {result.weather.get('source', 'unknown')} · {result.weather.get('summary', '')}")
        st.caption("Check official venue information and current conditions before traveling.")
