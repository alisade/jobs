"""Replay recorded production turns through the CURRENT turn loop and write the incident
bundle. Given; do not change. ``make setup`` runs it; run it again after a fix.

    python -m agentloop.replay --fixtures fixtures/recorded_turns.jsonl --out run

Time is compressed for replay: tool timeout 0.2 s (2 s in production), retry base 10 ms.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import anthropic

from . import loop
from .fake_api import FakeAnthropic
from .tools import ReplayToolBox

REPLAY_TOOL_TIMEOUT_S = 0.2
REPLAY_RETRY_BASE_S = 0.01
START = datetime(2026, 10, 8, 13, 41, 7, tzinfo=UTC)


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@dataclass
class TurnOutcome:
    record: dict[str, Any]
    text: str | None = None
    error: Exception | None = None
    attempts: int = 0
    last_request: dict[str, Any] | None = None
    rate_limited: int = 0


@dataclass
class Report:
    outcomes: list[TurnOutcome] = field(default_factory=list)

    @property
    def bad_requests(self) -> list[TurnOutcome]:
        return [o for o in self.outcomes if isinstance(o.error, anthropic.BadRequestError)]


async def replay_turn(record: dict[str, Any]) -> TurnOutcome:
    client = FakeAnthropic(copy.deepcopy(record["script"]), set(record.get("rate_limit_calls", [])))
    toolbox = ReplayToolBox(record["tools"])
    messages = copy.deepcopy(record["history"])
    outcome = TurnOutcome(record=record)
    try:
        result = await loop.run_turn(
            client,
            toolbox,
            messages,
            turn_id=record["turn_id"],
            tool_timeout_s=REPLAY_TOOL_TIMEOUT_S,
            retry_base_s=REPLAY_RETRY_BASE_S,
        )
        outcome.text = result.text
    except Exception as exc:  # recorded as an incident event
        outcome.error = exc
    outcome.attempts = client.messages.attempts
    outcome.rate_limited = len(record.get("rate_limit_calls", []))
    outcome.last_request = client.messages.requests[-1] if client.messages.requests else None
    return outcome


async def replay_all(records: list[dict[str, Any]]) -> Report:
    report = Report()
    for record in records:
        report.outcomes.append(await replay_turn(record))
    return report


class _JsonLines(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.lines: list[dict[str, Any]] = []
        self.clock = START

    def emit(self, record: logging.LogRecord) -> None:
        self.clock += timedelta(milliseconds=180 + (len(self.lines) * 37) % 900)
        try:
            body = json.loads(record.getMessage())
        except ValueError:
            body = {"message": record.getMessage()}
        self.lines.append(
            {"ts": self.clock.isoformat().replace("+00:00", "Z"), "level": record.levelname,
             "logger": record.name, "service": "lumen-agent", "release": "2.14.0", **body}
        )


def write_bundle(report: Report, out: Path, handler: _JsonLines) -> None:
    (out / "logs").mkdir(parents=True, exist_ok=True)
    (out / "sentry").mkdir(parents=True, exist_ok=True)
    with (out / "logs" / "agent.jsonl").open("w") as fh:
        for line in handler.lines:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
    events = []
    for o in report.outcomes:
        if o.error is None:
            continue
        turn = o.record["turn_id"]
        crumbs = [ln for ln in handler.lines if ln.get("turn_id") == turn][-6:]
        status = getattr(o.error, "status_code", None)
        events.append(
            {
                "event_id": uuid.uuid5(uuid.NAMESPACE_URL, turn).hex,
                "timestamp": crumbs[-1]["ts"] if crumbs else START.isoformat(),
                "level": "error",
                "release": "lumen-agent@2.14.0",
                "issue": "LUMEN-AGENT-4F2" if status == 400 else "LUMEN-AGENT-OTHER",
                "exception": {"type": type(o.error).__name__, "module": type(o.error).__module__,
                              "value": str(o.error)},
                "tags": {"conversation_id": o.record["conversation_id"], "turn_id": turn,
                         "http.status_code": status, "model": loop.MODEL},
                "extra": {"request_message_count": len((o.last_request or {}).get("messages", [])),
                          "api_attempts": o.attempts},
                "breadcrumbs": crumbs,
            }
        )
    with (out / "sentry" / "events.jsonl").open("w") as fh:
        for e in events:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    first = next((o for o in report.outcomes if isinstance(o.error, anthropic.BadRequestError)), None)
    failing = out / "failing_request.json"
    if first is not None and first.last_request is not None:
        failing.write_text(json.dumps({"turn_id": first.record["turn_id"], "request": first.last_request}, indent=2) + "\n")
    elif failing.exists():
        failing.unlink()
    total = len(report.outcomes)
    bad = len(report.bad_requests)
    retried = sum(1 for o in report.outcomes if o.rate_limited)
    other = sum(1 for o in report.outcomes if o.error is not None) - bad
    (out / "metrics.txt").write_text(
        "lumen-agent turn metrics, replay of 2026-10-08 13:41-14:12 UTC (release 2.14.0)\n"
        f"turns                 {total}\n"
        f"turns_ok              {total - bad - other}\n"
        f"http_400_turns        {bad}\n"
        f"other_failed_turns    {other}\n"
        f"turns_with_429_retry  {retried}\n"
        f"turn_error_rate       {100.0 * (bad + other) / max(total, 1):.1f}%\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path, default=Path("fixtures/recorded_turns.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("run"))
    args = ap.parse_args()
    handler = _JsonLines()
    agent_log = logging.getLogger("lumen.agent")
    agent_log.setLevel(logging.INFO)
    agent_log.addHandler(handler)
    agent_log.propagate = False
    report = asyncio.run(replay_all(load(args.fixtures)))
    write_bundle(report, args.out, handler)
    bad = len(report.bad_requests)
    print(f"replayed {len(report.outcomes)} turns: {bad} failed with HTTP 400; bundle in {args.out}/")


if __name__ == "__main__":
    main()
