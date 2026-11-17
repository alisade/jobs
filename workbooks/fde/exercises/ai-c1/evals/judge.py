"""Model-graded rubric check through a judge client.

YOUR WORK GOES HERE. The recorded verdicts in fixtures/judge_verdicts.json are keyed by
``judge_key(prompt)``: your prompt must be byte-identical to the one the recordings were
made with, so follow the rendering spec exactly.

render_transcript(t): one line per event of ``events(t)``, joined with "\n", no trailing
newline. Collapse every run of whitespace in a text to one space (" ".join(s.split())).

    user_text        USER: <text>
    assistant_text   ASSISTANT: <text>
    tool_use         TOOL_CALL <name> <json.dumps(input, sort_keys=True, separators=(",", ":"), ensure_ascii=True)>
    tool_result      TOOL_RESULT <name> ok|error: <collapsed text, first RESULT_MAX_CHARS chars>

judge_prompt(t, rubric): JUDGE_TEMPLATE.format(rubric=rubric, transcript=render_transcript(t)).

judge_check(t, client): call ``client.messages.create(model=..., max_tokens=200,
temperature=0, messages=[{"role": "user", "content": prompt}])``, read the text blocks,
and find the verdict object even when the judge wraps it in prose or a ```json fence.
A reply with no {"verdict": "pass"|"fail"} object, or a MissingRecording, is an
*errored* result (passed False, errored True), never a silent pass or a crash.
"""

from __future__ import annotations

import json  # noqa: F401
import re  # noqa: F401
from typing import Any

from .fake_judge import MissingRecording, judge_key  # noqa: F401
from .transcript import CheckResult, Transcript, events  # noqa: F401

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


def render_transcript(t: Transcript) -> str:
    raise NotImplementedError("render_transcript")


def judge_prompt(t: Transcript, rubric: str = RUBRIC) -> str:
    raise NotImplementedError("judge_prompt")


def parse_verdict(text: str) -> dict[str, Any] | None:
    """The verdict object from a judge reply, or None."""
    raise NotImplementedError("parse_verdict")


def judge_check(t: Transcript, client: Any, *, rubric: str = RUBRIC, model: str = JUDGE_MODEL) -> CheckResult:
    """name: judge_rubric"""
    raise NotImplementedError("judge_check")
