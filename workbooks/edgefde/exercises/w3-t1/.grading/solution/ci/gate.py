"""CI step 4/4: promote the challenger only if it beats the champion on the pinned holdout.

    python -m ci.gate --data data --model pump-anomaly --challenger 7
Exit 0 promoted, 3 rejected, 2 error (fail closed: missing metrics, no champion metrics, bad input).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mlreg.registry import FileRegistry, RegistryError

PROMOTED, REJECTED, ERROR = 0, 3, 2


def gate(reg: FileRegistry, name: str, challenger: int, pinned: str) -> int:
    champ_v = reg.get_alias(name, "champion")
    if champ_v == challenger:
        print(f"gate: ERROR v{challenger} is already champion", file=sys.stderr)
        return ERROR
    # Metrics must belong to exactly this version AND exactly the pinned holdout.
    chal = reg.metrics_for(name, challenger, pinned)
    if chal is None:
        print(f"gate: ERROR no metrics for v{challenger} on pinned holdout {pinned[:12]}: refusing to promote",
              file=sys.stderr)
        return ERROR
    champ = reg.metrics_for(name, champ_v, pinned) if champ_v is not None else None
    if champ_v is not None and champ is None:
        print(f"gate: ERROR champion v{champ_v} has no metrics on pinned holdout {pinned[:12]}", file=sys.stderr)
        return ERROR
    if champ is None:
        print(f"gate: first model v{challenger}: PROMOTE")
        reg.set_alias(name, "champion", challenger)
        return PROMOTED
    print(f"gate: challenger v{challenger} recall={chal['recall']:.4f} far={chal['false_alarm_rate']:.4f} "
          f"vs champion v{champ_v} recall={champ['recall']:.4f} far={champ['false_alarm_rate']:.4f}")
    not_worse = chal["recall"] >= champ["recall"] and chal["false_alarm_rate"] <= champ["false_alarm_rate"]
    better = chal["recall"] > champ["recall"] or chal["false_alarm_rate"] < champ["false_alarm_rate"]
    if not_worse and better:
        reg.set_alias(name, "previous-champion", champ_v)
        reg.set_alias(name, "champion", challenger)
        print(f"gate: PROMOTE v{challenger} -> champion")
        return PROMOTED
    print(f"gate: REJECT v{challenger} ({'tie' if not_worse else 'worse on at least one metric'})")
    return REJECTED


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci.gate")
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--challenger", required=True, type=int)
    args = ap.parse_args(argv)
    data = Path(args.data)
    try:
        pinned = (data / "pinned_holdout_sha.txt").read_text().strip()
        return gate(FileRegistry(data / "registry"), args.model, args.challenger, pinned)
    except (RegistryError, OSError, KeyError) as exc:
        print(f"gate: ERROR {exc}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    sys.exit(main())
