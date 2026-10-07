from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SourceType = Literal["text", "markdown", "html", "pdf", "docx", "json", "csv", "email", "image", "url", "code"]
Decision = Literal["ALLOW", "ALLOW_WITH_SANITIZATION", "ESCALATE", "BLOCK"]


class ScanRequest(BaseModel):
    content: str = Field(min_length=1)
    source_type: SourceType = "text"
    source_name: str | None = None


class Finding(BaseModel):
    attack_type: str
    confidence: float = Field(ge=0, le=1)
    severity: Literal["low", "medium", "high", "critical"]
    evidence: str
    rationale: str
    source: str
    matched_terms: list[str] = Field(default_factory=list)


class ScanResponse(BaseModel):
    id: int | None = None
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    attack_types: list[str]
    findings: list[Finding]
    sanitized_content: str
    agent_trace: list[dict[str, Any]]
    llm_used: bool
    content_stats: dict[str, Any]


class HistoryItem(BaseModel):
    id: int
    source_type: str
    source_name: str | None
    decision: str
    risk_score: int
    attack_types: list[str]
    llm_used: bool
    created_at: datetime


class TestSuiteResponse(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[dict[str, Any]]
