"""Generate the incident bundle for fde/w3-t1 into run/incident/ (deterministic).

What production looked like: decision logs from two risk-API brownouts (one before the
1.4.0 release, one after), the risk API's latency/breaker metrics, fraud-ops' chargeback
export, and the page that started the investigation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "run/incident")
SALT = "northwind-trust-v1"


def digest(value: str) -> str:
    return hashlib.sha256(f"{SALT}:{value}".encode()).hexdigest()[:16]


def ts(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def decision_log(
    rng: random.Random,
    day: datetime,
    version: str,
    pod_prefix: str,
    brown_start: datetime,
    brown_end: datetime,
    breaker_failures: int,
    checkout_on_failure: str,
    with_policy_field: bool,
) -> tuple[list[dict], list[dict]]:
    """Two hours of decisions; returns (records, fail_open_checkouts)."""
    records: list[dict] = []
    fail_open_checkouts: list[dict] = []
    t = day.replace(hour=13, minute=0, second=0)
    end = day.replace(hour=15, minute=0, second=0)
    seq = 0
    consecutive = 0
    breaker_until: datetime | None = None
    pods = [f"{pod_prefix}-{s}" for s in ("7f9c4", "7f9c4-b", "2kq8x")]
    while t < end:
        t += timedelta(milliseconds=rng.randint(700, 2600))
        seq += 1
        hook = rng.choices(["add_to_cart", "update_cart_item", "checkout"], [62, 14, 24])[0]
        session = digest(f"sess-{day:%m%d}-{rng.randint(1, 900)}")
        in_brownout = brown_start <= t < brown_end
        rec: dict = {
            "ts": ts(t),
            "level": "INFO",
            "logger": "northwind_trust.decisions",
            "service": "storefront-host",
            "pod": rng.choice(pods),
            "version": version,
            "hook": hook,
            "session_digest": session,
        }
        budget = 150 if hook != "checkout" else 400
        on_failure = "open" if hook != "checkout" else checkout_on_failure
        if breaker_until is not None and t < breaker_until:
            rec.update(outcome=f"fail_{on_failure}", latency_ms=0, decision_id=None,
                       reason_codes=[], error="BreakerOpen")
        elif in_brownout and rng.random() < 0.78:
            rec.update(outcome=f"fail_{on_failure}", latency_ms=budget + rng.randint(0, 4),
                       decision_id=None, reason_codes=[], error="TimeoutError")
            consecutive += 1
            if consecutive >= breaker_failures:
                breaker_until = t + timedelta(seconds=30)
                consecutive = 0
        else:
            consecutive = 0
            breaker_until = None
            dec = rng.choices(["allow", "deny", "review"], [93, 4, 3])[0]
            codes = {"allow": ["ok"], "deny": [rng.choice(["velocity_high", "device_mismatch",
                     "card_testing_pattern"])], "review": ["new_device_high_value"]}[dec]
            rec.update(outcome=dec, latency_ms=rng.randint(31, 95) if not in_brownout
                       else rng.randint(120, budget - 1),
                       decision_id=f"hx-{t:%m%d}-{seq:06d}", reason_codes=codes, error=None)
        if with_policy_field:
            rec["policy"] = on_failure
        records.append(rec)
        if hook == "checkout" and rec["outcome"] == "fail_open":
            fail_open_checkouts.append(rec)
    return records, fail_open_checkouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(4120)

    # 2026-09-28: a short brownout under 1.3.2 (breaker at 10, checkout from code default).
    d1 = datetime(2026, 9, 28, tzinfo=UTC)
    recs1, open1 = decision_log(
        rng, d1, "1.3.2", "storefront-host-6d8b5", d1.replace(hour=14, minute=5),
        d1.replace(hour=14, minute=22), 10, "closed", with_policy_field=False,
    )
    # 2026-10-06: the incident, under 1.4.0.
    d2 = datetime(2026, 10, 6, tzinfo=UTC)
    recs2, open2 = decision_log(
        rng, d2, "1.4.0", "storefront-host-58c7d", d2.replace(hour=13, minute=38),
        d2.replace(hour=14, minute=21), 5, "open", with_policy_field=True,
    )
    for name, recs in (("decisions-2026-09-28.jsonl", recs1), ("decisions-2026-10-06.jsonl", recs2)):
        with (OUT / name).open("w") as fh:
            for r in recs:
                fh.write(json.dumps(r, separators=(",", ":")) + "\n")

    # Risk API metrics, per minute, 13:00-15:00 on 2026-10-06.
    with (OUT / "halyard-risk-latency-2026-10-06.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["minute_utc", "requests", "p50_ms", "p99_ms", "error_rate", "client_breaker_state"])
        for m in range(120):
            t = d2.replace(hour=13) + timedelta(minutes=m)
            brown = d2.replace(hour=13, minute=38) <= t < d2.replace(hour=14, minute=21)
            p50 = rng.randint(380, 900) if brown else rng.randint(38, 55)
            p99 = rng.randint(2400, 9000) if brown else rng.randint(120, 190)
            err = round(rng.uniform(0.18, 0.41), 3) if brown else round(rng.uniform(0, 0.004), 3)
            state = rng.choice(["open", "open", "half_open", "closed"]) if brown else "closed"
            w.writerow([t.strftime("%Y-%m-%dT%H:%MZ"), rng.randint(140, 260), p50, p99, err, state])

    # Fraud ops: chargebacks on agent-originated orders (a sample of the fail-open checkouts).
    with (OUT / "fraud-ops-chargebacks-2026-10.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["order_ref", "placed_at_utc", "channel", "amount_usd", "chargeback_reason",
                    "session_digest", "risk_decision_id"])
        picks = rng.sample(open2, min(37, len(open2)))
        for i, r in enumerate(sorted(picks, key=lambda x: x["ts"])):
            w.writerow([f"NW-{88310 + i * 7}", r["ts"][:19] + "Z", "shopping-agent",
                        f"{rng.uniform(180, 1450):.2f}", rng.choice(["10.4 fraud card-absent",
                        "10.4 fraud card-absent", "13.1 merchandise not received"]),
                        r["session_digest"], ""])
        # A few ordinary chargebacks on the web channel, with decisions, for contrast.
        for i in range(6):
            w.writerow([f"NW-{87100 + i * 13}", f"2026-10-0{1 + i}T1{i}:2{i}:0{i}Z", "web",
                        f"{rng.uniform(40, 300):.2f}", "13.3 not as described",
                        digest(f"web-{i}"), f"hx-100{i}-00{i}417"])

    (OUT / "PAGE.txt").write_text(
        "PagerDuty  P2  #inc-2231  triggered 2026-10-07 09:14 UTC  service: storefront-host\n"
        "\n"
        "From: fraud-ops (Dana Whitfield)\n"
        "Chargeback spike on shopping-agent orders placed Mon 2026-10-06 between ~13:40 and\n"
        "~14:20 UTC. 37 chargebacks so far (10.4 card-absent fraud mostly), ~$24k. Every one of\n"
        "them has an EMPTY risk_decision_id in our export. Web-channel orders in the same window\n"
        "look normal.\n"
        "\n"
        "Halyard (risk vendor) status page: 'Elevated latency and errors on /v2/assess,\n"
        "13:38-14:21 UTC, resolved'. Their TAM says clients should fail safe during brownouts.\n"
        "\n"
        "Trust-platform on-call (first response): 'Checkout fails closed, it is in trust.env.\n"
        "The breaker change in 1.4.0 (10 -> 5) made it open faster, maybe the breaker lets\n"
        "requests through when it trips? Or the httpx bump changed timeout behaviour?'\n"
        "\n"
        "Ask: why were these checkouts allowed with no risk decision, is it still possible\n"
        "right now, and what is the fix? Brownouts happen monthly; the last one (2026-09-28)\n"
        "produced no chargebacks.\n"
        "\n"
        "Attached: decision logs for both brownouts, Halyard latency export, fraud-ops export.\n"
        "Deployed config and the 1.4.0 release diff are in deploy/.\n"
    )
    print(f"incident bundle written to {OUT}/ ({len(recs1) + len(recs2)} decision records)")


if __name__ == "__main__":
    main()
