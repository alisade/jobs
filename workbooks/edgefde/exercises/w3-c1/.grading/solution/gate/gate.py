"""Champion/challenger promotion gate, run by CI after a training job registers a version.

    python -m gate.gate promote --registry data/registry --model pump-anomaly --challenger 2 \
        --holdout data/holdout.npz --expected-holdout-sha <sha256> --comment run/comment.md
    python -m gate.gate rollback --registry data/registry --model pump-anomaly

Exit codes: 0 promoted (or rolled back), 3 rejected, 2 error. Every error fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import pickle
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from mlreg.registry import FileRegistry, RegistryError

PROMOTED, REJECTED, ERROR = 0, 3, 2


@dataclass(frozen=True)
class Metrics:
    recall: float
    false_alarm_rate: float
    p95_latency_ms: float
    positives: int
    negatives: int

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Rules:
    min_recall: float = 0.60
    max_false_alarm_rate: float = 0.03
    max_p95_latency_ms: float = 50.0


@dataclass
class Decision:
    promote: bool
    reasons: list[str] = field(default_factory=list)


class GateError(RuntimeError):
    pass


def holdout_sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_holdout(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    d = np.load(path)
    return d["X"], d["y"]


def evaluate(model, X: np.ndarray, y: np.ndarray, latency_samples: int = 200) -> Metrics:
    pred = np.asarray(model.predict(X)).astype(int)
    pos, neg = y == 1, y == 0
    if pos.sum() == 0 or neg.sum() == 0:
        raise GateError("holdout must contain both classes")
    recall = float((pred[pos] == 1).mean())
    far = float((pred[neg] == 1).mean())
    n = min(latency_samples, len(X))
    for i in range(min(10, n)):
        model.predict(X[i:i + 1])
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        model.predict(X[i:i + 1])
        times.append((time.perf_counter() - t0) * 1000)
    return Metrics(recall, far, float(np.percentile(times, 95)), int(pos.sum()), int(neg.sum()))


def decide(champion: Metrics | None, challenger: Metrics, rules: Rules = Rules()) -> Decision:
    reasons = []
    if challenger.recall < rules.min_recall:
        reasons.append(f"recall {challenger.recall:.4f} below floor {rules.min_recall:.2f}")
    if challenger.false_alarm_rate > rules.max_false_alarm_rate:
        reasons.append(f"false-alarm rate {challenger.false_alarm_rate:.4f} above ceiling {rules.max_false_alarm_rate:.2f}")
    if challenger.p95_latency_ms > rules.max_p95_latency_ms:
        reasons.append(f"p95 latency {challenger.p95_latency_ms:.2f} ms above budget {rules.max_p95_latency_ms} ms")
    if champion is not None:
        if challenger.recall < champion.recall:
            reasons.append(f"recall worse than champion ({challenger.recall:.4f} < {champion.recall:.4f})")
        if challenger.false_alarm_rate > champion.false_alarm_rate:
            reasons.append(f"false-alarm rate worse than champion ({challenger.false_alarm_rate:.4f} > {champion.false_alarm_rate:.4f})")
        if challenger.recall == champion.recall and challenger.false_alarm_rate == champion.false_alarm_rate:
            reasons.append("no improvement over champion (tie)")
    return Decision(not reasons, reasons or ["beats champion on the same holdout" if champion else "first model, meets floors"])


def _load(registry: FileRegistry, name: str, version: int):
    rec = registry.get_version(name, version)
    try:
        return pickle.loads(Path(rec["artifact"]).read_bytes())
    except Exception as exc:  # unreadable artifact: fail closed
        raise GateError(f"cannot load {name} v{version} artifact {rec['artifact']}: {exc}") from None


def comment(name: str, champ_v: int | None, champ: Metrics | None, chal_v: int, chal: Metrics,
            sha: str, dec: Decision) -> str:
    rows = [("recall", "recall", "{:.4f}"), ("false-alarm rate", "false_alarm_rate", "{:.4f}"),
            ("p95 latency (ms)", "p95_latency_ms", "{:.2f}")]
    head = f"| metric | champion {'v' + str(champ_v) if champ_v else '(none)'} | challenger v{chal_v} |"
    lines = [f"### Model gate: {name} v{chal_v}", "", f"Holdout sha256 `{sha[:12]}`, "
             f"{chal.positives} fault windows, {chal.negatives} healthy windows.", "", head, "|---|---|---|"]
    for label, key, fmt in rows:
        c = fmt.format(getattr(champ, key)) if champ else "-"
        lines.append(f"| {label} | {c} | {fmt.format(getattr(chal, key))} |")
    lines += ["", f"Decision: {'PROMOTE' if dec.promote else 'REJECT'}", ""] + [f"- {r}" for r in dec.reasons]
    return "\n".join(lines) + "\n"


def promote(registry: FileRegistry, name: str, challenger: int, holdout: str | Path, expected_sha: str,
            rules: Rules = Rules(), comment_path: str | Path | None = None) -> int:
    sha = holdout_sha(holdout)
    if sha != expected_sha:
        raise GateError(f"holdout sha256 {sha[:12]} does not match the pinned {expected_sha[:12]}")
    X, y = load_holdout(holdout)
    champ_v = registry.get_alias(name, "champion")
    if champ_v == challenger:
        raise GateError(f"v{challenger} is already the champion")
    chal_model = _load(registry, name, challenger)
    chal = evaluate(chal_model, X, y)
    registry.log_metrics(name, challenger, sha, chal.as_dict())
    champ = None
    if champ_v is not None:
        champ = evaluate(_load(registry, name, champ_v), X, y)
        registry.log_metrics(name, champ_v, sha, champ.as_dict())
    dec = decide(champ, chal, rules)
    if comment_path:
        Path(comment_path).parent.mkdir(parents=True, exist_ok=True)
        Path(comment_path).write_text(comment(name, champ_v, champ, challenger, chal, sha, dec))
    if not dec.promote:
        return REJECTED
    if champ_v is not None:
        registry.set_alias(name, "previous-champion", champ_v)
    registry.set_alias(name, "champion", challenger)
    return PROMOTED


def rollback(registry: FileRegistry, name: str) -> int:
    prev = registry.get_alias(name, "previous-champion")
    if prev is None:
        raise GateError("no previous-champion alias to roll back to")
    registry.set_alias(name, "champion", prev)
    registry.delete_alias(name, "previous-champion")
    return PROMOTED


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gate.gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("promote")
    p.add_argument("--registry", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--challenger", required=True, type=int)
    p.add_argument("--holdout", required=True)
    p.add_argument("--expected-holdout-sha", required=True)
    p.add_argument("--comment")
    r = sub.add_parser("rollback")
    r.add_argument("--registry", required=True)
    r.add_argument("--model", required=True)
    args = ap.parse_args(argv)
    reg = FileRegistry(args.registry)
    try:
        if args.cmd == "promote":
            code = promote(reg, args.model, args.challenger, args.holdout, args.expected_holdout_sha,
                           comment_path=args.comment)
        else:
            code = rollback(reg, args.model)
    except (GateError, RegistryError, OSError, KeyError, ValueError) as exc:
        print(f"GATE ERROR (fail closed): {exc}", file=sys.stderr)
        return ERROR
    print({PROMOTED: "PROMOTED", REJECTED: "REJECTED"}[code])
    return code


if __name__ == "__main__":
    sys.exit(main())
