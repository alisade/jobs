"""CM-03 batch run: one Gemini call per sample for the facts, attributes decided in code."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from google.genai import types
from pydantic import ValidationError

from . import prompt
from .contract import ChangeFacts

MODEL = "gemini-3.8-flash"
TEMPERATURE = 0.0  # extraction, not prose: no reason for sampling noise


@dataclass
class SampleResult:
    sample_id: str
    change_id: str
    result: str  # pass | exception | needs_review
    failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=prompt.SYSTEM,
        temperature=TEMPERATURE,
        response_mime_type="application/json",
        response_schema=ChangeFacts,
    )


def _resolve(identity: str | None, directory: dict) -> str | None:
    if not identity:
        return None
    return {k.casefold(): v for k, v in directory.items()}.get(identity.strip().casefold())


def _instant(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def attributes(f: ChangeFacts, deploy: dict, directory: dict) -> tuple[list[str], list[str]]:
    """Return (failed attributes, not-evaluable attributes)."""
    failed, unknown = [], []
    deployed = _instant(deploy["deployed_at"])
    if f.approver is None or f.approval_at is None or f.approval_at.astimezone(timezone.utc) >= deployed:
        failed.append("approval_before_deploy")
    if f.approver is None:
        failed.append("independent_approver")
    else:
        a, b = _resolve(f.author, directory), _resolve(f.approver, directory)
        if a is None or b is None:
            unknown.append("independent_approver")
        elif a == b:
            failed.append("independent_approver")
    if deploy["change_id"] != f.change_id or deploy["pr_number"] != f.pr_number:
        failed.append("linked_change")
    if f.tests_passed is False:
        failed.append("tests_passed")
    elif f.tests_passed is None:
        unknown.append("tests_passed")
    return failed, unknown


def test_sample(client: Any, sample: dict, deploy: dict, directory: dict) -> SampleResult:
    resp = client.models.generate_content(model=MODEL, contents=prompt.render(sample), config=build_config())
    try:
        f = ChangeFacts.model_validate_json(resp.text or "")
    except ValidationError as e:
        return SampleResult(sample["sample_id"], sample["change_id"], "needs_review", errors=[str(e)])
    if f.change_id != sample["change_id"]:
        return SampleResult(sample["sample_id"], sample["change_id"], "needs_review", errors=["change_id mismatch"])
    failed, unknown = attributes(f, deploy, directory)
    result = "exception" if failed else ("needs_review" if unknown else "pass")
    return SampleResult(sample["sample_id"], sample["change_id"], result, failed=failed, errors=unknown)


def run(client: Any, samples: dict, deploys: dict, directory: dict) -> list[SampleResult]:
    return [test_sample(client, s, deploys[s["change_id"]], directory) for _, s in sorted(samples.items())]


def report(results: list[SampleResult]) -> str:
    lines = [f"ControlPilot CM-03 run  prompt={prompt.PROMPT_VERSION}  model={MODEL}  samples={len(results)}"]
    for r in results:
        extra = (" failed=" + ",".join(r.failed)) if r.failed else ""
        lines.append(f"  {r.sample_id} {r.change_id} {r.result}{extra}")
    counts = {k: sum(1 for r in results if r.result == k) for k in ("pass", "exception", "needs_review")}
    lines.append(f"pass={counts['pass']} exception={counts['exception']} needs_review={counts['needs_review']}")
    return "\n".join(lines)
