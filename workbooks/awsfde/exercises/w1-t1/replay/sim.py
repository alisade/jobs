"""Discrete-event replay of one Monday peak through a release of the answer service.

What is modeled (the environment):
- API Gateway HTTP API in front of the Lambda: the caller gives up after api_gateway_timeout_s (504),
  the Lambda keeps running until it finishes or hits lambda_timeout_s.
- Lambda reserved concurrency: arrivals beyond it are rejected (429, TooManyRequestsException).
- Bedrock on-demand quota as a token bucket (replay/quota.py); throttled attempts return fast.
- The SDK retry layer, emulated from the release's real botocore client config
  (client.meta.config.retries): standard-mode delay rand(0,1) * min(2 ** (n - 1), 20) seconds.
- The release's application retry layer, from its resilience.APP_POLICY (if the release has one):
  should_retry(code, attempt) and delay(attempt, rng).
- The release's status mapping, from service.outcome_for_error(code).
"""

from __future__ import annotations

import heapq
import importlib
import importlib.util
import json
import pathlib
import random
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace

from .quota import TokenBucket
from .traffic import WINDOW_S, clock, trace

WINDOW_END = WINDOW_S

SDK_RETRYABLE = {
    "ThrottlingException", "Throttling", "TooManyRequestsException", "ServiceUnavailableException",
    "InternalServerException", "ModelNotReadyException", "RequestTimeout",
}


class _NoAppRetry:
    max_attempts = 1

    def should_retry(self, code: str, attempt: int) -> bool:
        return False

    def delay(self, attempt: int, rng) -> float:
        return 0.0


def load_release(root: pathlib.Path, alias: str) -> SimpleNamespace:
    """Import <root>/answer_svc as package `alias` (so two releases can be loaded side by side)."""
    root = pathlib.Path(root).resolve()
    for k in [k for k in sys.modules if k == alias or k.startswith(alias + ".")]:
        del sys.modules[k]
    pkg_dir = root / "answer_svc"
    spec = importlib.util.spec_from_file_location(alias, pkg_dir / "__init__.py",
                                                  submodule_search_locations=[str(pkg_dir)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    service = importlib.import_module(alias + ".service")
    bedrock_client = importlib.import_module(alias + ".bedrock_client")
    try:
        resilience = importlib.import_module(alias + ".resilience")
    except ModuleNotFoundError:
        resilience = None
    config = json.loads((root / "config" / "release.json").read_text())
    return SimpleNamespace(service=service, bedrock_client=bedrock_client, resilience=resilience,
                           config=config, root=root)


def sdk_total_attempts(release: SimpleNamespace) -> tuple[int, str]:
    retries = dict(release.bedrock_client.make_client().meta.config.retries or {})
    mode = retries.get("mode", "standard")
    if "total_max_attempts" in retries:
        total = int(retries["total_max_attempts"])
    elif "max_attempts" in retries:
        total = int(retries["max_attempts"]) + 1
    else:
        total = 3 if mode in ("standard", "adaptive") else 5
    return max(1, total), mode


@dataclass
class Req:
    rid: str
    arrival: float
    invalid: bool
    latency: float
    rng: random.Random
    start: float = 0.0
    app_attempt: int = 1
    sdk_attempt: int = 1
    model_calls: int = 0
    attempts: list = field(default_factory=list)
    done: bool = False
    client_retry: bool = False


def run(release: SimpleNamespace, day: str, *, concurrency: int | None = None,
        bucket: TokenBucket | None = None, always_throttle: bool = False) -> dict:
    cfg = release.config
    limit = int(concurrency if concurrency is not None else cfg["lambda_reserved_concurrency"])
    lambda_timeout = float(cfg["lambda_timeout_s"])
    apigw_timeout = float(cfg["api_gateway_timeout_s"])
    sdk_total, sdk_mode = sdk_total_attempts(release)
    app = getattr(release.resilience, "APP_POLICY", None) if release.resilience else None
    app = app or _NoAppRetry()
    outcome = release.service.outcome_for_error
    bucket = bucket or TokenBucket()

    events: list = []
    seq = 0

    def push(t: float, kind: str, req: Req, arg=None) -> None:
        nonlocal seq
        seq += 1
        heapq.heappush(events, (t, seq, kind, req, arg))

    reqs = [Req(r["request_id"], r["arrival"], r["invalid"], r["latency"], random.Random(r["jitter_seed"]))
            for r in trace(day)]
    for r in reqs:
        push(r.arrival, "arrive", r)

    active = 0
    max_active = 0
    results: list[dict] = []
    minute: dict[int, dict] = {}

    def m(t: float) -> dict:
        k = int(t // 60)
        return minute.setdefault(k, {"requests": 0, "s200": 0, "s400": 0, "s429": 0, "s500": 0, "s503": 0,
                                     "s504": 0, "bedrock_invocations": 0, "throttles": 0,
                                     "latencies": [], "max_concurrency": 0})

    def finish(t: float, r: Req, status: int, code: str | None) -> None:
        nonlocal active
        if r.done:
            return
        r.done = True
        active -= 1
        client_latency = t - r.arrival
        client_status = status
        if client_latency > apigw_timeout:
            client_status, client_latency = 504, apigw_timeout
        results.append({"request_id": r.rid, "arrival": clock(r.arrival), "portal_retry": r.client_retry, "status": client_status,
                        "lambda_status": status, "error": code, "latency_ms": int(client_latency * 1000),
                        "lambda_duration_ms": int((t - r.start) * 1000), "model_calls": r.model_calls,
                        "attempts": r.attempts})
        mm = m(r.arrival)
        mm["s%d" % client_status] = mm.get("s%d" % client_status, 0) + 1
        mm["latencies"].append(client_latency)
        # The portal (unchanged for months) retries once, 1 s after a 5xx/429 response, unless the
        # response is 503 with Retry-After (then it shows "busy, try again shortly").
        if not r.client_retry and client_status in (429, 500, 502, 504) and t < WINDOW_END:
            again = Req(r.rid + "-r1", r.arrival + client_latency + 1.0, r.invalid, r.latency,
                        random.Random(r.rng.random()), client_retry=True)
            push(again.arrival, "arrive", again)

    def schedule_attempt(t: float, r: Req) -> None:
        if t - r.start > lambda_timeout:
            push(r.start + lambda_timeout, "timeout", r)
        else:
            push(t, "attempt", r)

    while events:
        t, _, kind, r, arg = heapq.heappop(events)
        if r.done:
            continue
        if kind == "arrive":
            m(t)["requests"] += 1
            if active >= limit:
                active += 1  # finish() decrements
                r.start = t
                finish(t, r, 429, "TooManyRequestsException")
                continue
            active += 1
            max_active = max(max_active, active)
            mm = m(t)
            mm["max_concurrency"] = max(mm["max_concurrency"], active)
            r.start = t
            schedule_attempt(t, r)
        elif kind == "attempt":
            r.model_calls += 1
            mm = m(t)
            mm["bedrock_invocations"] += 1
            if r.invalid:
                code, dt = "ValidationException", 0.1
            elif not always_throttle and bucket.take(t):
                code, dt = None, r.latency
            else:
                code, dt = "ThrottlingException", 0.08
                mm["throttles"] += 1
            r.attempts.append([round(t - r.arrival, 2), r.app_attempt, r.sdk_attempt, code or "ok"])
            if t + dt - r.start > lambda_timeout:
                push(r.start + lambda_timeout, "timeout", r)
            else:
                push(t + dt, "result", r, code)
        elif kind == "result":
            code = arg
            if code is None:
                finish(t, r, 200, None)
                continue
            if code in SDK_RETRYABLE and r.sdk_attempt < sdk_total:
                delay = r.rng.random() * min(2 ** (r.sdk_attempt - 1), 20)
                r.sdk_attempt += 1
                schedule_attempt(t + delay, r)
                continue
            if app.should_retry(code, r.app_attempt):
                delay = float(app.delay(r.app_attempt, r.rng.random))
                r.app_attempt += 1
                r.sdk_attempt = 1
                schedule_attempt(t + delay, r)
                continue
            finish(t, r, int(outcome(code)), code)
        elif kind == "timeout":
            finish(t, r, 504, "Task timed out")

    for mm in minute.values():
        lat = sorted(mm.pop("latencies"))
        mm["p95_ms"] = int(lat[int(0.95 * (len(lat) - 1))] * 1000) if lat else 0
    n = len(results)
    statuses: dict[int, int] = {}
    for x in results:
        statuses[x["status"]] = statuses.get(x["status"], 0) + 1
    lat = sorted(x["latency_ms"] for x in results)
    calls = sum(x["model_calls"] for x in results)
    valid = [x for x in results if x["error"] != "ValidationException"]
    errors = sum(1 for x in valid if x["status"] != 200)
    summary = {
        "day": day,
        "release": cfg.get("release"),
        "requests": n,
        "statuses": dict(sorted(statuses.items())),
        "error_rate": round(errors / max(1, len(valid)), 4),
        "answered_rate": round(statuses.get(200, 0) / max(1, n), 4),
        "p50_ms": lat[n // 2] if n else 0,
        "p95_ms": lat[int(0.95 * (n - 1))] if n else 0,
        "model_calls": calls,
        "amplification": round(calls / max(1, n), 3),
        "max_attempts_per_request": max((x["model_calls"] for x in results), default=0),
        "throttles": sum(v["throttles"] for v in minute.values()),
        "max_concurrency": max_active,
        "sdk_total_attempts": sdk_total,
        "sdk_mode": sdk_mode,
        "app_max_attempts": int(getattr(app, "max_attempts", 1)),
    }
    return {"summary": summary, "minutes": dict(sorted(minute.items())), "requests": results}
