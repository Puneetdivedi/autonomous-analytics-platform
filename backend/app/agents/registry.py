"""Agent registry.

Maps each agent's ``name`` to its class and provides :func:`get_agent` to
instantiate one by name. Node functions in :mod:`app.graphs` resolve agents
through this registry so wiring stays declarative and consistent.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.business_insight_agent import BusinessInsightAgent
from app.agents.chart_generator_agent import ChartGeneratorAgent
from app.agents.intent_agent import IntentAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.python_analyst_agent import PythonAnalystAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.sql_generator_agent import SQLGeneratorAgent
from app.agents.sql_validator_agent import SQLValidatorAgent
from app.agents.supervisor_agent import SupervisorAgent

#: Registry of every agent keyed by its ``name`` attribute.
AGENTS: dict[str, type[BaseAgent]] = {
    IntentAgent.name: IntentAgent,
    PlannerAgent.name: PlannerAgent,
    MetadataAgent.name: MetadataAgent,
    SQLGeneratorAgent.name: SQLGeneratorAgent,
    SQLValidatorAgent.name: SQLValidatorAgent,
    PythonAnalystAgent.name: PythonAnalystAgent,
    ChartGeneratorAgent.name: ChartGeneratorAgent,
    BusinessInsightAgent.name: BusinessInsightAgent,
    RecommendationAgent.name: RecommendationAgent,
    ReflectionAgent.name: ReflectionAgent,
    SupervisorAgent.name: SupervisorAgent,
}


def get_agent(name: str) -> BaseAgent:
    """Instantiate and return the agent registered under ``name``.

    Raises:
        KeyError: if no agent is registered with that name.
    """
    try:
        agent_cls = AGENTS[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown agent '{name}'. Registered: {sorted(AGENTS)}"
        ) from exc
    return agent_cls()
