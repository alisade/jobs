"""Replay a morning of production traffic through four worker processes and the shared
prompt cache, and write the logs and dashboard on-call looks at. Given; not the bug.

    python -m replay.simulate --out run            # both days (previous and current release)
    python -m replay.simulate --out run --only current

Traffic is synthetic but shaped like the real thing: sessions of several turns, each turn
one HTTP request routed by the load balancer to any of the four workers (no stickiness:
session state lives in the session store), each turn one to three model calls. The worker
processes build the request bodies with the code under test (see replay/worker.py); this
process plays them through ``PromptCache`` in time order and logs one line per model call
in the blueprint's ``log_model_call`` format.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from replay.cachesim import PromptCache

HERE = Path(__file__).resolve().parent
EXERCISE = HERE.parent
# 4 pods x 4 uvicorn workers. Each process gets its own random hash seed at start-up,
# as CPython does by default; these are the ones this replay hands out.
WORKER_SEEDS = (2931, 771, 40417, 5119, 8812, 1203, 66071, 3390, 47, 9031, 12207, 5560, 7781, 2405, 31337, 918)
PREVIOUS = EXERCISE / "incident" / "previous_release"

_WORDS = (
    "tent footprint vestibule denier ripstop pole hub stake guyline rainfly mesh "
    "sleeping bag rated comfort limit down fill power synthetic baffle hood draft collar "
    "stove canister burner simmer boil time liter titanium aluminum pot grip "
    "boot waterproof membrane lug outsole midsole heel drop break in sock merino "
    "pack frame hipbelt torso length liters lid pocket hydration sleeve compression"
).split()


@dataclass
class Call:
    t: datetime
    session: str
    turn: int
    round: int
    worker: int
    messages: list[dict[str, Any]]
    cart_count: int
    page: str
    stop: str
    output: int


@dataclass
class Stats:
    calls: int = 0
    input_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    by_hour: dict[str, list[int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0, 0, 0]))
    prefixes_by_worker: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    # The first model call of turn 2 and later: where a warm conversation should be read.
    opening_read: int = 0
    opening_total: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.input_tokens + self.cache_read + self.cache_write
        return self.cache_read / total if total else 0.0

    @property
    def opening_hit_rate(self) -> float:
        return self.opening_read / self.opening_total if self.opening_total else 0.0


def _text(rng: random.Random, chars: int) -> str:
    out: list[str] = []
    size = 0
    while size < chars:
        word = rng.choice(_WORDS)
        out.append(word)
        size += len(word) + 1
    return " ".join(out)


def plan(day: datetime, sessions: int = 40, seed: int = 7, workers: int = 4) -> list[Call]:
    """Every model call of the replayed morning, in time order."""
    rng = random.Random(seed)
    calls: list[Call] = []
    for s in range(sessions):
        sid = hashlib.sha256(f"{day.date()}-{s}".encode()).hexdigest()[:8]
        t = day + timedelta(seconds=rng.uniform(0, 100 * 60))
        history: list[dict[str, Any]] = []
        cart = 0
        page = "home"
        for turn in range(1, rng.randint(4, 8) + 1):
            worker = rng.randrange(workers)  # the load balancer's pick for this request
            if rng.random() < 0.15:
                page = rng.choice(["home", "search", "product", "cart"])
            history.append({"role": "user", "content": _text(rng, rng.randint(40, 120))})
            rounds = rng.randint(1, 3)
            for r in range(1, rounds + 1):
                last = r == rounds
                calls.append(
                    Call(t, sid, turn, r, worker, [dict(m) for m in history], cart, page,
                         "end_turn" if last else "tool_use", rng.randint(40, 260))
                )
                if last:
                    history.append(
                        {"role": "assistant", "content": [{"type": "text", "text": _text(rng, rng.randint(80, 250))}]}
                    )
                else:
                    tid = f"toolu_{sid}{turn}{r}"
                    history.append(
                        {"role": "assistant", "content": [
                            {"type": "tool_use", "id": tid, "name": "search_products",
                             "input": {"query": _text(rng, 20)}}]}
                    )
                    history.append(
                        {"role": "user", "content": [
                            {"type": "tool_result", "tool_use_id": tid,
                             "content": "<storefront_data>" + _text(rng, rng.randint(700, 1600)) + "</storefront_data>"}]}
                    )
                    if rng.random() < 0.15:
                        cart += 1
                t += timedelta(seconds=rng.uniform(3, 8))
            t += timedelta(seconds=rng.uniform(30, 150))
    calls.sort(key=lambda c: c.t)
    return calls


def build_requests(code_root: Path, flags: dict[str, Any], calls: list[Call],
                   seeds: tuple[int, ...] = WORKER_SEEDS) -> tuple[list[dict[str, Any]], dict[int, int]]:
    """Ask each worker process to build the requests routed to it."""
    requests: list[dict[str, Any] | None] = [None] * len(calls)
    pids: dict[int, int] = {}
    for worker, seed in enumerate(seeds):
        idx = [i for i, c in enumerate(calls) if c.worker == worker]
        jobs = [
            {"now": calls[i].t.isoformat(), "cart_count": calls[i].cart_count, "page": calls[i].page,
             "messages": calls[i].messages}
            for i in idx
        ]
        env = dict(os.environ, PYTHONHASHSEED=str(seed), PYTHONPATH=str(code_root),
                   PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run(
            [sys.executable, str(HERE / "worker.py")],
            input=json.dumps({"flags": flags, "jobs": jobs}),
            capture_output=True, text=True, env=env, timeout=120, check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"worker {worker + 1} failed:\n{proc.stderr[-2000:]}")
        out = json.loads(proc.stdout)
        pids[worker] = out["pid"]
        for i, req in zip(idx, out["requests"], strict=True):
            requests[i] = req
    return [r for r in requests if r is not None], pids


def replay(code_root: Path, flags: dict[str, Any], day: datetime, *, sessions: int = 40,
           seeds: tuple[int, ...] = WORKER_SEEDS, log_dir: Path | None = None) -> Stats:
    calls = plan(day, sessions=sessions, workers=len(seeds))
    requests, pids = build_requests(code_root, flags, calls, seeds)
    cache = PromptCache()
    stats = Stats()
    lines: dict[int, list[str]] = defaultdict(list)
    epoch = day.timestamp()
    for call, req in zip(calls, requests, strict=True):
        usage = cache.call(req, call.t.timestamp() - epoch)
        stats.calls += 1
        stats.input_tokens += usage.input_tokens
        stats.cache_read += usage.cache_read_input_tokens
        stats.cache_write += usage.cache_creation_input_tokens
        if call.turn >= 2 and call.round == 1:
            stats.opening_read += usage.cache_read_input_tokens
            stats.opening_total += (
                usage.input_tokens + usage.cache_read_input_tokens + usage.cache_creation_input_tokens
            )
        hour = call.t.strftime("%H:00")
        bucket = stats.by_hour[hour]
        bucket[0] += 1
        bucket[1] += usage.input_tokens
        bucket[2] += usage.cache_read_input_tokens
        bucket[3] += usage.cache_creation_input_tokens
        prefix = json.dumps(req["tools"], sort_keys=True) + req["system"][0]["text"]
        stats.prefixes_by_worker[call.worker].add(hashlib.sha256(prefix.encode()).hexdigest()[:12])
        elapsed = int(380 + call.output * 9 + usage.cache_creation_input_tokens * 0.06 + usage.input_tokens * 0.02)
        lines[call.worker].append(
            f"{call.t.strftime('%Y-%m-%dT%H:%M:%S')}.{call.t.microsecond // 1000:03d}Z INFO "
            f"[pid {pids[call.worker]}] shopping_runtime.orchestrator model call "
            f"session={call.session} turn={call.turn} round={call.round} model={req['model']} "
            f"stop={call.stop} input={usage.input_tokens} cache_read={usage.cache_read_input_tokens} "
            f"cache_write={usage.cache_creation_input_tokens} output={call.output} elapsed_ms={elapsed}"
        )
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        for worker, worker_lines in sorted(lines.items()):
            (log_dir / f"worker-{worker + 1}.log").write_text("\n".join(worker_lines) + "\n")
    return stats


def dashboard(title: str, stats: Stats) -> str:
    rows = [f"{title}", f"  model calls: {stats.calls}   cache hit rate (read / all input): {stats.hit_rate:.1%}",
            f"  first call of turn 2+: {stats.opening_hit_rate:.1%} read from cache",
            "  hour   calls   input   cache_read   cache_write   hit_rate"]
    for hour in sorted(stats.by_hour):
        n, inp, read, write = stats.by_hour[hour]
        rate = read / (inp + read + write) if inp + read + write else 0
        rows.append(f"  {hour}  {n:6d} {inp:7d} {read:12d} {write:13d}   {rate:7.1%}")
    return "\n".join(rows) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=EXERCISE / "run")
    ap.add_argument("--only", choices=["previous", "current"], default=None)
    args = ap.parse_args()
    out: Path = args.out
    sections = []
    if args.only in (None, "previous"):
        flags = json.loads((PREVIOUS / "flags.json").read_text())
        stats = replay(PREVIOUS, flags, datetime(2026, 10, 5, 13, 0), log_dir=out / "logs" / "2026-10-05")
        sections.append(dashboard("2026-10-05 (release 2026.09.29)", stats))
    if args.only in (None, "current"):
        flags = json.loads((EXERCISE / "config" / "flags.json").read_text())
        stats = replay(EXERCISE, flags, datetime(2026, 10, 6, 13, 0), log_dir=out / "logs" / "2026-10-06")
        sections.append(dashboard("2026-10-06 (release 2026.10.06, this checkout)", stats))
    text = "Prompt cache, storefront agent, 13:00-15:00 UTC, 4 pods x 4 workers\n\n" + "\n".join(sections)
    out.mkdir(parents=True, exist_ok=True)
    name = "dashboard.txt" if args.only is None else f"dashboard-{args.only}.txt"
    (out / name).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
