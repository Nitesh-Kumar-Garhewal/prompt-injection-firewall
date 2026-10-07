# Judge Demo Script

Start backend and frontend first.

## 0:00–0:10 — Problem
"An agent can receive instructions from documents, web pages and API responses. The firewall must decide whether that content is data or an attempt to control the agent."

## 0:10–0:25 — Clean input
Click **safe** → **Run firewall scan**.

Say: "Legitimate content passes with minimal disruption."

## 0:25–0:45 — Direct attack
Click **direct** → scan.

Point to:
- BLOCK decision
- risk score
- Instruction Override
- Secret Extraction
- evidence

Say: "The security gate is deterministic; the LLM is supporting evidence, not authority."

## 0:45–1:00 — Indirect attack
Click **indirect** → scan.

Say: "The malicious instruction is embedded in otherwise normal business content. This is the key indirect-injection problem."

## 1:00–1:15 — Encoded attack
Click **encoded** → scan.

Say: "We detect encoded payloads and do not blindly decode-and-follow them."

## 1:15–1:30 — Agent trace
Scroll to Agent trace.

Say: "Every stage is observable: ingest, detection, semantic analysis, risk, policy, and sanitization."

## 1:30–1:45 — Reliability
Click **Run 9-case suite**.

Say: "The prototype ships with an adversarial regression suite. Our current deterministic path passes 9 out of 9 bundled cases."

## 1:45–2:00 — Close
"This makes the firewall usable as a pre-execution security boundary for any downstream LLM agent or tool-using workflow."
