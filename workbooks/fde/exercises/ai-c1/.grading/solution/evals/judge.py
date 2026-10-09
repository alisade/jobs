"""Model-graded rubric check through a judge client. Reference solution."""

from __future__ import annotations

import json
import re
from typing import Any

from .fake_judge import MissingRecording, judge_key
from .transcript import CheckResult, Transcript, events

JUDGE_MODEL = "claude-judge-recorded"
RESULT_MAX_CHARS = 300

RUBRIC = (
    "The assistant recommends only items that fit the customer's stated budget and needs, "
    "names at least one trade-off, and does not pressure the customer to buy."
)

JUDGE_TEMPLATE = """You are grading one conversation between a customer and a store's shopping assistant.

Rubric:
{rubric}

Conversation:
<transcript>
{transcript}
</transcript>

Answer with one JSON object and nothing else: {{"verdict": "pass" or "fail", "reason": "<one sentence>"}}"""


def _one_line(text: str) -> str:
    return " ".join(text.split())


def render_transcript(t: Transcript) -> str:
    lines = []
    for e in events(t):
        if e.kind == "user_text":
            lines.append(f"USER: {_one_line(e.text)}")
        elif e.kind == "assistant_text":
            lines.append(f"ASSISTANT: {_one_line(e.text)}")
        elif e.kind == "tool_use":
            args = json.dumps(e.input, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            lines.append(f"TOOL_CALL {e.name} {args}")
        else:
            status = "error" if e.is_error else "ok"
            lines.append(f"TOOL_RESULT {e.name} {status}: {_one_line(e.text)[:RESULT_MAX_CHARS]}")
    return "\n".join(lines)


def judge_prompt(t: Transcript, rubric: str = RUBRIC) -> str:
    return JUDGE_TEMPLATE.format(rubric=rubric, transcript=render_transcript(t))


def parse_verdict(text: str) -> dict[str, Any] | None:
    """The verdict object from a judge reply that may wrap it in prose or a code fence."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("verdict") in ("pass", "fail"):
            return obj
    return None


def judge_check(t: Transcript, client: Any, *, rubric: str = RUBRIC, model: str = JUDGE_MODEL) -> CheckResult:
    prompt = judge_prompt(t, rubric)
    try:
        reply = client.messages.create(
            model=model,
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
    except MissingRecording:
        return CheckResult("judge_rubric", False, f"no recorded verdict for prompt {judge_key(prompt)}", errored=True)
    text = "".join(getattr(b, "text", "") for b in reply.content if getattr(b, "type", "") == "text")
    verdict = parse_verdict(text)
    if verdict is None:
        return CheckResult("judge_rubric", False, "judge reply had no parseable verdict", errored=True)
    return CheckResult("judge_rubric", verdict["verdict"] == "pass", str(verdict.get("reason", ""))[:200])
