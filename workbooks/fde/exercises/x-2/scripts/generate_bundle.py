"""Replay a slice of yesterday's traffic through the trust layer as deployed, writing
run/decisions.log and run/dlp-report.txt (what the SIEM saw)."""

from __future__ import annotations

import contextlib
import io
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from dlp_scan import scan  # noqa: E402

from trustlog.core import log_started  # noqa: E402
from trustlog.decisions import DecisionEvent, log_decision  # noqa: E402
from trustlog.logging_setup import configure  # noqa: E402
from trustlog.risk_client import log_risk_failure  # noqa: E402

CUSTOMERS = ["maria.lopez@example.com", "j.chen@example.org", "sam.okafor@example.net"]
BINS = ["411111", "552233", "37828200"]


def main() -> None:
    run = ROOT / "run"
    run.mkdir(exist_ok=True)
    log_path = run / "decisions.log"
    log_path.unlink(missing_ok=True)
    configure(path=str(log_path))
    rng = random.Random(412)
    log_started("northwind-prod-use1", "oncall.trust@northwind.example")
    for n in range(24):
        i = rng.randrange(3)
        log_decision(
            DecisionEvent(
                decision_id=f"dec-{9000 + n}",
                hook=rng.choice(["add_to_cart", "update_cart_item", "checkout"]),
                outcome=rng.choice(["allow", "allow", "allow", "review", "deny"]),
                reason_codes=rng.choice([[], ["velocity_high"], ["device_mismatch"]]),
                amount=round(rng.uniform(12, 480), 2),
                card_bin=BINS[i],
                customer_email=CUSTOMERS[i],
            )
        )
        if n % 9 == 4:
            log_risk_failure(CUSTOMERS[i], "4111 1111 1111 1111", "ReadTimeout after 150 ms")
    report = io.StringIO()
    with contextlib.redirect_stdout(report):
        scan(str(log_path.relative_to(ROOT)) if Path.cwd() == ROOT else str(log_path))
    (run / "dlp-report.txt").write_text(report.getvalue())
    print(report.getvalue(), end="")


if __name__ == "__main__":
    main()
