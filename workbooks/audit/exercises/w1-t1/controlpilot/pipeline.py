"""CM-03 batch run: one Gemini call per sample, then the run report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google.genai import types
from pydantic import ValidationError

from . import prompt
from .contract import ChangeAssessment

MODEL = "gemini-3.8-flash"
TEMPERATURE = 0.4  # 2026.10.2: raised from 0.0 so summaries read less robotic (DEV-2291)


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
    )


def test_sample(client: Any, sample: dict, deploy: dict, directory: dict) -> SampleResult:
    resp = client.models.generate_content(model=MODEL, contents=prompt.render(sample), config=build_config())
    try:
        a = ChangeAssessment.model_validate_json(resp.text or "")
    except ValidationError as e:
        return SampleResult(sample["sample_id"], sample["change_id"], "needs_review", errors=[str(e)])
    failed = [name for name, ok in (("approval_before_deploy", a.approved_before_deploy),
                                    ("independent_approver", a.independent_approver),
                                    ("tests_passed", a.tests_passed)) if not ok]
    return SampleResult(sample["sample_id"], sample["change_id"], "exception" if failed else "pass", failed=failed)


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
