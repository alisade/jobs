"""Static checks of a trust policy YAML. Reference solution."""

from __future__ import annotations

from typing import Any

import yaml

from .models import PolicyFinding, PolicyReport

MAX_YAML_CHARS = 16_384


class PolicyInputError(ValueError):
    """The input cannot be checked at all (too large, not YAML, not a mapping)."""


_HOOK_KEYS = {"timeout_ms", "on_failure"}
_BREAKER_KEYS = {"failures", "reset_s"}
_TOP_KEYS = {"cart", "checkout", "breaker"}
_BUDGET_WARN = {"cart": 300, "checkout": 1500}


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def lint_policy(yaml_text: str) -> PolicyReport:
    if len(yaml_text) > MAX_YAML_CHARS:
        raise PolicyInputError(f"policy YAML is larger than {MAX_YAML_CHARS} characters")
    try:
        doc = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}" if mark is not None else ""
        raise PolicyInputError(f"invalid YAML{where}") from None
    if not isinstance(doc, dict):
        raise PolicyInputError("policy must be a YAML mapping with cart / checkout sections")

    findings: list[PolicyFinding] = []

    def add(severity: str, path: str, code: str, message: str) -> None:
        findings.append(PolicyFinding(severity=severity, path=path, code=code, message=message))

    for key in doc:
        if key not in _TOP_KEYS:
            add("error", str(key), "unknown_key", f"unknown section {key!r}; expected one of cart, checkout, breaker")

    for hook in ("cart", "checkout"):
        section = doc.get(hook)
        if section is None:
            add("warning", hook, "missing_section", f"no {hook} section; the code defaults apply")
            continue
        if not isinstance(section, dict):
            add("error", hook, "invalid_value", f"{hook} must be a mapping")
            continue
        for key in section:
            if key not in _HOOK_KEYS:
                add("error", f"{hook}.{key}", "unknown_key", f"unknown key {key!r} in {hook}")
        if "on_failure" in section:
            value = section["on_failure"]
            path = f"{hook}.on_failure"
            if isinstance(value, bool):
                add("error", path, "yaml_boolean",
                    f"on_failure parsed as the boolean {value}; YAML 1.1 reads yes/no/on/off as "
                    "booleans. Write \"open\" or \"closed\" (quoted).")
            elif value not in ("open", "closed"):
                add("error", path, "invalid_value", "on_failure must be \"open\" or \"closed\"")
            elif hook == "checkout" and value == "open":
                add("error", path, "checkout_fail_open",
                    "checkout fails open: a risk-API outage lets orders through with no decision")
        if "timeout_ms" in section:
            value = section["timeout_ms"]
            path = f"{hook}.timeout_ms"
            if not _is_number(value) or not 0 < value <= 5000:
                add("error", path, "invalid_value", "timeout_ms must be a number in (0, 5000]")
            elif value > _BUDGET_WARN[hook]:
                add("warning", path, "budget_high",
                    f"{value} ms is above the {_BUDGET_WARN[hook]} ms latency budget for {hook}")

    breaker = doc.get("breaker")
    if breaker is not None:
        if not isinstance(breaker, dict):
            add("error", "breaker", "invalid_value", "breaker must be a mapping")
        else:
            for key in breaker:
                if key not in _BREAKER_KEYS:
                    add("error", f"breaker.{key}", "unknown_key", f"unknown key {key!r} in breaker")
            failures = breaker.get("failures")
            if failures is not None and (not isinstance(failures, int) or isinstance(failures, bool) or failures < 1):
                add("error", "breaker.failures", "invalid_value", "failures must be an integer >= 1")
            reset = breaker.get("reset_s")
            if reset is not None and (not _is_number(reset) or reset <= 0):
                add("error", "breaker.reset_s", "invalid_value", "reset_s must be a positive number")

    return PolicyReport(valid=not any(f.severity == "error" for f in findings), findings=findings)
