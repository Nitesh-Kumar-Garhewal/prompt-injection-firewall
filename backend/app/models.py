from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .core.db import Base


class ScanRecord(Base):
    __tablename__ = "scan_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_preview: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(40), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)
    attack_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    sanitized_content: Mapped[str] = mapped_column(Text)
    agent_trace: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    llm_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
