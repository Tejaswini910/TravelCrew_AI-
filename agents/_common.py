"""Shared Ollama-backed CrewAI agent construction."""

import logging

from crewai import Agent, LLM

from travel_planner.config.settings import get_settings

logger = logging.getLogger(__name__)


def local_llm() -> LLM:
    settings = get_settings()
    logger.info(
        "Temporary Ollama config: provider=%s model=%s endpoint=%s api_key_loaded=%s",
        settings.provider,
        settings.model,
        settings.safe_endpoint,
        bool(settings.ollama_api_key),
    )
    return LLM(
        model=settings.crewai_model,
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key if not settings.is_local_endpoint else None,
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
