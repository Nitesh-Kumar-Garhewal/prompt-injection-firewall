from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..models import ScanRecord
from ..schemas import HistoryItem, ScanRequest, ScanResponse, TestSuiteResponse
from ..services.content_extractor import ExtractionError, content_stats, extract_text
from ..services.detectors import list_attack_catalog
from ..services.firewall import merge_findings, run_firewall

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/attacks")
async def attacks() -> list[dict[str, str]]:
    return list_attack_catalog()


@router.post("/scan", response_model=ScanResponse)
async def scan_text(request: ScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    if len(request.content) > settings.max_input_chars:
        raise HTTPException(status_code=413, detail=f"Content exceeds {settings.max_input_chars} characters.")
    state = await run_firewall(content=request.content, source_type=request.source_type, source_name=request.source_name)
    findings = merge_findings(state)
    record = ScanRecord(
        source_type=request.source_type,
        source_name=request.source_name,
        content_preview=state.normalized_content[:4_000],
        decision=state.decision,
        risk_score=state.risk_score,
        attack_types=[f["attack_type"] for f in findings],
        findings=findings,
        sanitized_content=state.sanitized_content[:settings.max_input_chars],
        agent_trace=state.trace,
        llm_used=state.llm_used,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _response(record, findings, state)


@router.post("/scan/file", response_model=ScanResponse)
async def scan_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ScanResponse:
    data = await file.read()
    try:
        content, detected_type = extract_text(file.filename or "upload.txt", data)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if len(content) > settings.max_input_chars:
        raise HTTPException(status_code=413, detail=f"Extracted content exceeds {settings.max_input_chars} characters.")
    state = await run_firewall(content=content, source_type=detected_type, source_name=file.filename)
    findings = merge_findings(state)
    record = ScanRecord(
        source_type=detected_type,
        source_name=file.filename,
        content_preview=state.normalized_content[:4_000],
        decision=state.decision,
        risk_score=state.risk_score,
        attack_types=[f["attack_type"] for f in findings],
        findings=findings,
        sanitized_content=state.sanitized_content[:settings.max_input_chars],
        agent_trace=state.trace,
        llm_used=state.llm_used,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _response(record, findings, state)


@router.get("/history", response_model=list[HistoryItem])
async def history(limit: int = 20, db: Session = Depends(get_db)) -> list[HistoryItem]:
    limit = max(1, min(limit, 100))
    rows = db.execute(select(ScanRecord).order_by(desc(ScanRecord.created_at)).limit(limit)).scalars().all()
    return [HistoryItem(
        id=row.id,
        source_type=row.source_type,
        source_name=row.source_name,
        decision=row.decision,
        risk_score=row.risk_score,
        attack_types=row.attack_types or [],
        llm_used=row.llm_used,
        created_at=row.created_at,
    ) for row in rows]


@router.get("/stats")
async def stats(db: Session = Depends(get_db)) -> dict[str, object]:
    total = db.scalar(select(func.count()).select_from(ScanRecord)) or 0
    blocked = db.scalar(select(func.count()).select_from(ScanRecord).where(ScanRecord.decision == "BLOCK")) or 0
    escalated = db.scalar(select(func.count()).select_from(ScanRecord).where(ScanRecord.decision == "ESCALATE")) or 0
    sanitized = db.scalar(select(func.count()).select_from(ScanRecord).where(ScanRecord.decision == "ALLOW_WITH_SANITIZATION")) or 0
    allowed = db.scalar(select(func.count()).select_from(ScanRecord).where(ScanRecord.decision == "ALLOW")) or 0
    return {"total": total, "blocked": blocked, "escalated": escalated, "sanitized": sanitized, "allowed": allowed}


@router.post("/test-suite/run", response_model=TestSuiteResponse)
async def run_test_suite() -> TestSuiteResponse:
    sample_path = Path(__file__).resolve().parents[3] / "sample_data" / "attack_test_cases.json"
    import json

    cases = json.loads(sample_path.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        state = await run_firewall(content=case["content"], source_type=case.get("source_type", "text"))
        detected = set(f.attack_type for f in state.findings)
        expected = set(case.get("expected_attacks", []))
        passed = expected.issubset(detected) and state.risk_score >= case.get("min_risk", 0)
        results.append({
            "id": case["id"],
            "name": case["name"],
            "passed": passed,
            "expected": sorted(expected),
            "detected": sorted(detected),
            "decision": state.decision,
            "risk_score": state.risk_score,
        })
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    return TestSuiteResponse(total=total, passed=passed, failed=total - passed, pass_rate=round((passed / total) * 100, 2) if total else 0, results=results)


def _response(record: ScanRecord, findings: list[dict], state) -> ScanResponse:
    return ScanResponse(
        id=record.id,
        decision=record.decision,
        risk_score=record.risk_score,
        attack_types=[f["attack_type"] for f in findings],
        findings=findings,
        sanitized_content=state.sanitized_content,
        agent_trace=state.trace,
        llm_used=state.llm_used,
        content_stats=content_stats(state.normalized_content),
    )
