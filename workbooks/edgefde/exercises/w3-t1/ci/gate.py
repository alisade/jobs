"""CI step 4/4: promote the challenger if it is at least as good as the champion.

    python -m ci.gate --data data --model pump-anomaly --challenger 7
Exit 0 promoted, 3 rejected.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mlreg.registry import FileRegistry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci.gate")
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--challenger", required=True, type=int)
    args = ap.parse_args(argv)
    data = Path(args.data)
    reg = FileRegistry(data / "registry")
    pinned = (data / "pinned_holdout_sha.txt").read_text().strip()

    champ_v = reg.get_alias(args.model, "champion")
    champ = reg.metrics_for(args.model, champ_v, pinned)
    latest = reg.latest_metrics(args.model)  # the evaluate step just logged the challenger's metrics
    chal = latest["values"]
    print(f"gate: challenger v{args.challenger} recall={chal['recall']:.4f} far={chal['false_alarm_rate']:.4f} "
          f"vs champion v{champ_v} recall={champ['recall']:.4f} far={champ['false_alarm_rate']:.4f}")
    if chal["recall"] >= champ["recall"] and chal["false_alarm_rate"] <= champ["false_alarm_rate"]:
        reg.set_alias(args.model, "previous-champion", champ_v)
        reg.set_alias(args.model, "champion", args.challenger)
        print(f"gate: PROMOTE v{args.challenger} -> champion")
        return 0
    print(f"gate: REJECT v{args.challenger}")
    return 3


if __name__ == "__main__":
    sys.exit(main())
