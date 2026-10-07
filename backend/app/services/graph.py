from __future__ import annotations

from typing import Any

from .agents import (
    FirewallState,
    IngestionAgent,
    LLMAnalysisAgent,
    PolicyAgent,
    RiskScoringAgent,
    RuleAnalysisAgent,
    SanitizationAgent,
)

try:
    from langgraph.graph import END, StateGraph
    from typing_extensions import TypedDict
    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only on minimal installs
    END = None
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


if LANGGRAPH_AVAILABLE:
    class GraphState(TypedDict, total=False):
        state: FirewallState
else:
    GraphState = dict


async def _ingest(data: GraphState) -> GraphState:
    data["state"] = IngestionAgent().run(data["state"])
    return data


async def _rules(data: GraphState) -> GraphState:
    data["state"] = RuleAnalysisAgent().run(data["state"])
    return data


async def _llm(data: GraphState) -> GraphState:
    data["state"] = await LLMAnalysisAgent().run(data["state"])
    return data


async def _score(data: GraphState) -> GraphState:
    data["state"] = RiskScoringAgent().run(data["state"])
    return data


async def _policy(data: GraphState) -> GraphState:
    data["state"] = PolicyAgent().run(data["state"])
    return data


async def _sanitize(data: GraphState) -> GraphState:
    data["state"] = SanitizationAgent().run(data["state"])
    return data


_graph = None


def build_graph():
    global _graph
    if _graph is not None:
        return _graph
    if not LANGGRAPH_AVAILABLE:
        return None

    builder = StateGraph(GraphState)
    builder.add_node("ingestion_agent", _ingest)
    builder.add_node("rule_analysis_agent", _rules)
    builder.add_node("llm_analysis_agent", _llm)
    builder.add_node("risk_scoring_agent", _score)
    builder.add_node("policy_agent", _policy)
    builder.add_node("sanitization_agent", _sanitize)
    builder.set_entry_point("ingestion_agent")
    builder.add_edge("ingestion_agent", "rule_analysis_agent")
    builder.add_edge("rule_analysis_agent", "llm_analysis_agent")
    builder.add_edge("llm_analysis_agent", "risk_scoring_agent")
    builder.add_edge("risk_scoring_agent", "policy_agent")
    builder.add_edge("policy_agent", "sanitization_agent")
    builder.add_edge("sanitization_agent", END)
    _graph = builder.compile()
    return _graph


async def run_firewall_graph(*, content: str, source_type: str, source_name: str | None = None) -> FirewallState:
    initial = FirewallState(source_type=source_type, source_name=source_name, content=content)
    graph = build_graph()
    if graph is None:
        data: GraphState = {"state": initial}
        for node in (_ingest, _rules, _llm, _score, _policy, _sanitize):
            data = await node(data)
        return data["state"]

    result: dict[str, Any] = await graph.ainvoke({"state": initial})
    return result["state"]
