from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass


@dataclass
class Rule:
    attack_type: str
    severity: str
    weight: int
    patterns: tuple[str, ...]
    rationale: str


RULES = [
    Rule(
        "Instruction Override", "high", 28,
        (
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"ignore\s+(the\s+)?system\s+prompt",
            r"disregard\s+(all\s+)?prior\s+rules",
            r"ignore\s+previous\s+rules",
            r"override\s+(the\s+)?developer\s+message",
            r"from\s+now\s+on\s*,?\s*you\s+must",
        ),
        "Attempts to replace higher-priority instructions with attacker-controlled instructions.",
    ),
    Rule(
        "Role Change", "high", 20,
        (
            r"you\s+are\s+now\s+(?:(?:a|an)\s+)?(system|developer|admin|root|unrestricted)",
            r"act\s+as\s+(a|an)\s+(admin|developer|system|root)",
            r"switch\s+to\s+developer\s+mode",
            r"pretend\s+you\s+are\s+the\s+system",
        ),
        "Attempts to alter the agent's role, authority, or trust boundary.",
    ),
    Rule(
        "Secret Extraction", "critical", 32,
        (
            r"reveal\s+(the\s+)?system\s+prompt",
            r"show\s+(me\s+)?(your|the)\s+hidden\s+instructions",
            r"print\s+(the\s+)?environment\s+variables",
            r"dump\s+(all\s+)?secrets",
            r"give\s+me\s+the\s+api\s+key",
            r"expose\s+internal\s+configuration",
        ),
        "Targets protected prompts, environment data, keys, or internal configuration.",
    ),
    Rule(
        "Tool Abuse", "critical", 30,
        (
            r"run\s+(this\s+)?shell\s+command",
            r"execute\s+(this\s+)?command",
            r"call\s+the\s+.+\s+tool",
            r"invoke\s+.+\s+function",
            r"send\s+an\s+email\s+to",
            r"delete\s+(all\s+)?files",
            r"make\s+the\s+api\s+request",
        ),
        "Attempts to induce tool execution or external side effects without trusted authorization.",
    ),
    Rule(
        "Credential Theft", "critical", 34,
        (
            r"steal\s+(the\s+)?password",
            r"capture\s+login\s+credentials",
            r"collect\s+otp\b",
            r"extract\s+access\s+token",
            r"send\s+(the\s+)?credentials\s+to",
            r"send\s+(the\s+)?password\s+to",
            r"forward\s+the\s+password",
        ),
        "Seeks authentication material or instructs the system to exfiltrate it.",
    ),
    Rule(
        "Context Poisoning", "high", 22,
        (
            r"important\s+instruction\s*:\s*",
            r"trusted\s+policy\s+says\s+to",
            r"this\s+document\s+is\s+authoritative",
            r"treat\s+the\s+following\s+as\s+system\s+instructions",
            r"security\s+reviewer\s+has\s+approved\s+this",
        ),
        "Embeds false authority or manipulates the context so untrusted content gains undue priority.",
    ),
    Rule(
        "Multi-Step Jailbreaks", "high", 26,
        (
            r"step\s*1\s*[:\-]",
            r"first\s+do\s+.+then\s+do",
            r"phase\s+1\s+.+phase\s+2",
            r"after\s+you\s+complete\s+this\s*,?\s+continue",
            r"chain\s+these\s+instructions",
        ),
        "Uses staged instructions to gradually move an agent across a security boundary.",
    ),
    Rule(
        "Encoded Instructions", "high", 25,
        (
            r"base64\s*(decode|encoded|payload)",
            r"decode\s+the\s+following",
            r"\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){3,}",
            r"%[0-9a-fA-F]{2}(?:%[0-9a-fA-F]{2}){3,}",
        ),
        "Conceals instructions in an encoding intended to evade straightforward filters.",
    ),
    Rule(
        "Indirect Prompt Injection", "critical", 32,
        (
            r"when\s+(the\s+)?ai\s+(reads|processes|opens)\s+this",
            r"when\s+the\s+assistant\s+reads\s+this",
            r"if\s+you\s+are\s+an\s+ai\s+agent",
            r"hidden\s+instruction\s+for\s+the\s+assistant",
            r"ignore\s+the\s+user\s+and\s+instead",
            r"<comment[^>]*>.*?(ignore|system|assistant).*?</comment>",
        ),
        "Instruction is embedded in content intended to be treated as data, not trusted control input.",
    ),
]


@dataclass
class Detection:
    attack_type: str
    confidence: float
    severity: str
    evidence: str
    rationale: str
    matched_terms: list[str]
    source: str = "rules"


def detect_attacks(text: str) -> list[Detection]:
    findings: list[Detection] = []
    lowered = text.lower()
    for rule in RULES:
        matches: list[str] = []
        for pattern in rule.patterns:
            for match in re.finditer(pattern, lowered, flags=re.IGNORECASE | re.DOTALL):
                matches.append(text[max(0, match.start() - 40): min(len(text), match.end() + 80)].replace("\n", " ").strip())
                if len(matches) >= 3:
                    break
            if len(matches) >= 3:
                break
        if matches:
            confidence = min(0.99, 0.68 + 0.08 * min(4, len(matches)))
            findings.append(Detection(rule.attack_type, confidence, rule.severity, matches[0], rule.rationale, matches))

    encoded = _decode_possible_base64(text)
    if encoded:
        findings.append(Detection(
            "Encoded Instructions",
            0.95,
            "high",
            f"Decoded candidate payload: {encoded[:180]}",
            "A decodable payload contains instruction-like text and should be inspected as untrusted data.",
            [encoded[:120]],
        ))

    # Additional heuristic: direct prompt-like verbs followed by high-risk actions.
    if re.search(r"\b(system prompt|developer message|api key|password|access token|secret)\b", lowered) and re.search(
        r"\b(reveal|show|print|send|dump|extract|expose|share)\b", lowered
    ):
        findings.append(Detection(
            "Secret Extraction",
            0.93,
            "critical",
            "Sensitive target combined with an extraction verb.",
            "The request combines a protected artifact with an explicit exfiltration action.",
            [],
        ))

    return _deduplicate(findings)


def _decode_possible_base64(text: str) -> str | None:
    candidates = re.findall(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/])", text)
    for candidate in candidates:
        if len(candidate) % 4:
            continue
        try:
            decoded = base64.b64decode(candidate, validate=True).decode("utf-8", errors="strict")
        except (binascii.Error, UnicodeDecodeError):
            continue
        if re.search(r"\b(ignore|system prompt|developer|password|token|execute|send|secret)\b", decoded, re.I):
            return decoded
    return None


def _deduplicate(findings: list[Detection]) -> list[Detection]:
    best: dict[str, Detection] = {}
    for item in findings:
        current = best.get(item.attack_type)
        if current is None or item.confidence > current.confidence:
            best[item.attack_type] = item
    return sorted(best.values(), key=lambda item: item.confidence, reverse=True)


def list_attack_catalog() -> list[dict[str, str]]:
    return [
        {"name": r.attack_type, "severity": r.severity, "weight": str(r.weight), "rationale": r.rationale}
        for r in RULES
    ]
