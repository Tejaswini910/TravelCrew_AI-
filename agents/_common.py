"""Shared Ollama-backed CrewAI agent construction."""

from crewai import Agent, LLM

from travel_planner.config.settings import get_settings


def local_llm() -> LLM:
    settings = get_settings()
    return LLM(
        model=settings.crewai_model,
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
        temperature=0.2,
        timeout=settings.ollama_timeout_seconds,
    )


def build_agent(role: str, goal: str, backstory: str, tools: list[object] | None = None) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=local_llm(),
        tools=tools or [],
        verbose=False,
        allow_delegation=False,
        max_iter=2,
    )
