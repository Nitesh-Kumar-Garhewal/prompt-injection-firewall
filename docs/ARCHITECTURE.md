# Structural Architecture for Submission

## End-to-end flow

1. **Input boundary**
   - Text request or uploaded file enters FastAPI.
   - File content is extracted into text; the original file is never executed.

2. **IngestionAgent**
   - Removes null bytes and normalizes line endings.
   - Creates basic content statistics.

3. **RuleAnalysisAgent**
   - Runs deterministic detectors for all nine attack classes.
   - Adds base64 payload inspection as a second encoded-instruction signal.

4. **LLMAnalysisAgent**
   - Optional semantic classifier receives content as untrusted data.
   - System prompt explicitly says not to follow the supplied content.
   - Timeout/error causes a safe fallback to deterministic analysis.

5. **RiskScoringAgent**
   - Combines category severity, confidence, number of distinct categories and optional LLM confirmation.
   - Caps the score at 100.

6. **PolicyAgent**
   - Critical signal or high score -> BLOCK.
   - High but noncritical -> ESCALATE.
   - Medium -> ALLOW_WITH_SANITIZATION.
   - Low -> ALLOW.

7. **SanitizationAgent**
   - BLOCK: quarantine marker.
   - Other suspicious content: explicit untrusted-content boundary.
   - Safe content: preserved.

8. **Audit / observability**
   - Decision, score, attack categories, evidence, sanitized content and agent trace are stored in SQLAlchemy.

## Control boundary

The firewall intentionally does **not** execute tools from scanned content. Tool execution would sit downstream of this firewall and require a separate authorization layer. This is an important responsible-AI property for the judge demo.

## Failure handling

- Unsupported file -> HTTP 400
- Oversized input -> HTTP 413
- PDF/DOCX/OCR extraction failure -> explicit error
- LLM timeout/API failure -> deterministic fallback
- Unknown LLM attack category -> ignored by whitelist
- Database history persists every completed scan

## Evidence for evaluation

### Significance
The firewall protects downstream AI agents from direct and indirect instructions embedded in external content.

### Innovation
Hybrid deterministic + semantic detection, risk-based policy, quarantine boundary, traceable agent path, and adversarial regression tests.

### Effective AI
The optional LLM semantic agent handles context-sensitive signals that simple pattern rules may not catch.

### Technical complexity
Multi-agent orchestration, document extraction, confidence/risk aggregation, persistence, frontend observability, and test suite.

### Agentic capability
Multiple specialized agents transform, analyze, evaluate, decide, sanitize and recover from LLM failure.

### Business impact
Reduces probability of unauthorized tool use, secret disclosure and poisoned-context behavior in AI workflows.

### Prototype quality
Live dashboard + Swagger API + uploads + scan history + test suite.

### Scalability / responsible AI
Deterministic final policy, input-size limits, LLM fallback, category whitelist, quarantine, audit trail, and explicit human-oversight path.
