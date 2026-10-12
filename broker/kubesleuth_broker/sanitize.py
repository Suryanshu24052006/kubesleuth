"""Output hygiene for everything that leaves the broker.

Cluster data is attacker-influenced: anyone who can make a pod log a line, set an
annotation or name a resource can put text in front of the model. We therefore:

1. redact credential-shaped strings (defence against leaking secrets the agent
   should never see, even though RBAC already denies Secret reads);
2. strip terminal control sequences;
3. *flag* (never silently delete) instruction-like text, so the agent can treat it
   as evidence of tampering rather than as an instruction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

MAX_STRING = 2000

_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_REDACTIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED:private-key]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "[REDACTED:jwt]"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,}"), r"\1 [REDACTED]"),
    (re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"), "[REDACTED:aws-key]"),
    (re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_-]{20,}\b"), "[REDACTED:api-key]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), "[REDACTED:github-token]"),
    (re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^\s:/@]+):([^\s@/]+)@"), r"\1:[REDACTED]@"),
    (re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret)"
                r"(\"?\s*[:=]\s*\"?)([^\s\"',;&]{3,})"), r"\1\2[REDACTED]"),
]

SENSITIVE_KEY = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private|credential|cert|dsn)")

# Instruction-like text that has no business appearing in telemetry.
_INJECTION: list[tuple[str, re.Pattern]] = [
    ("override-instructions", re.compile(
        r"(?i)\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|your|system)\b"
        r".{0,30}\b(instructions?|prompts?|rules|guidelines|directives)")),
    ("role-hijack", re.compile(r"(?i)\b(you are now|act as|pretend to be|new instructions|system prompt|developer mode)\b")),
    ("chat-markup", re.compile(r"(?i)(<\|im_start\|>|<\|im_end\|>|</?system>|\[/?INST\]|^\s*(assistant|system)\s*:)", re.M)),
    ("command-request", re.compile(
        r"(?i)\b(run|execute|exec|invoke|call)\b.{0,30}\b(command|kubectl|shell|bash|script|tool|function)\b")),
    ("mutating-kubectl", re.compile(r"(?i)\bkubectl\s+(delete|apply|patch|edit|scale|exec|drain|cordon|create|replace|rollout)\b")),
    ("exfiltration", re.compile(r"(?i)(curl|wget)\s+[^|]{0,120}\|\s*(sh|bash)|\b(send|post|upload|exfiltrate)\b.{0,40}\b(secrets?|tokens?|credentials?|kubeconfig)\b")),
    ("tool-steering", re.compile(r"(?i)\b(root cause is|conclude that|mark (this|the) (incident|investigation)|report that)\b")),
]


@dataclass
class Findings:
    redactions: int = 0
    suspicious: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"redactions": self.redactions, "suspicious_instructions": self.suspicious[:20]}


def redact(text: str, f: Findings) -> str:
    for rx, repl in _REDACTIONS:
        text, n = rx.subn(repl, text)
        f.redactions += n
    return text


def scan_injection(text: str, path: str, f: Findings) -> None:
    for name, rx in _INJECTION:
        m = rx.search(text)
        if m:
            start = max(0, m.start() - 60)
            f.suspicious.append({"path": path, "pattern": name, "excerpt": text[start:m.end() + 60]})
            return  # one flag per string is enough


def clean_string(text: str, path: str, f: Findings, scan: bool = True) -> str:
    text = _ANSI.sub("", text)
    if len(text) > MAX_STRING:
        text = text[:MAX_STRING] + f"…[truncated {len(text) - MAX_STRING} chars]"
    text = redact(text, f)
    if scan:
        scan_injection(text, path, f)
    return text


def sanitize(obj: Any, f: Findings, path: str = "$") -> Any:
    """Recursively clean every string in a JSON-like structure."""
    if isinstance(obj, str):
        return clean_string(obj, path, f)
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = str(k)
            if isinstance(v, str) and SENSITIVE_KEY.search(key) and not key.endswith(("_count", "Count")):
                if v and not v.startswith("[REDACTED") and not v.startswith("<from "):
                    f.redactions += 1
                    v = "[REDACTED:sensitive-key]"
            out[key] = sanitize(v, f, f"{path}.{key}")
        return out
    if isinstance(obj, (list, tuple)):
        return [sanitize(v, f, f"{path}[{i}]") for i, v in enumerate(obj)]
    return obj
