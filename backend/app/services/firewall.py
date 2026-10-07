from __future__ import annotations

from typing import Any

from .agents import FirewallState
from .graph import run_firewall_graph


async def run_firewall(*, content: str, source_type: str, source_name: str | None = None) -> FirewallState:
    return await run_firewall_graph(content=content, source_type=source_type, source_name=source_name)


def merge_findings(state: FirewallState) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for finding in state.findings:
        merged[finding.attack_type] = {
            "attack_type": finding.attack_type,
            "confidence": round(finding.confidence, 3),
            "severity": finding.severity,
            "evidence": finding.evidence,
            "rationale": finding.rationale,
            "source": finding.source,
            "matched_terms": finding.matched_terms,
        }

    allowed_types = {
        "Instruction Override", "Role Change", "Secret Extraction", "Tool Abuse",
        "Credential Theft", "Context Poisoning", "Multi-Step Jailbreaks",
        "Encoded Instructions", "Indirect Prompt Injection",
    }
    for item in state.llm_findings:
        attack = item.get("attack_type")
        if not attack or attack not in allowed_types:
            continue
        existing = merged.get(attack)
        try:
            llm_confidence = max(0.0, min(1.0, float(item.get("confidence", 0))))
        except (TypeError, ValueError):
            llm_confidence = 0.0
        llm_severity = str(item.get("severity", "medium")).lower()
        if llm_severity not in {"low", "medium", "high", "critical"}:
            llm_severity = "medium"
        if existing:
            existing["confidence"] = round(max(float(existing["confidence"]), llm_confidence), 3)
            existing["source"] = "rules+llm"
        else:
            merged[attack] = {
                "attack_type": attack,
                "confidence": round(llm_confidence, 3),
                "severity": llm_severity,
                "evidence": item.get("evidence", "LLM semantic signal"),
                "rationale": item.get("rationale", "Semantic analysis signal."),
                "source": "llm",
                "matched_terms": [],
            }
    return sorted(merged.values(), key=lambda item: item["confidence"], reverse=True)
