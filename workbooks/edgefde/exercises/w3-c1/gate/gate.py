"""Champion/challenger promotion gate, run by CI after a training job registers a version.

    python -m gate.gate promote --registry data/registry --model pump-anomaly --challenger 2 \
        --holdout data/holdout.npz --expected-holdout-sha <sha256> --comment run/comment.md
    python -m gate.gate rollback --registry data/registry --model pump-anomaly

Exit codes: 0 promoted (or rolled back), 3 rejected, 2 error. Every error fails closed.

TODO: implement everything marked TODO to the contract in README.md.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from mlreg.registry import FileRegistry

PROMOTED, REJECTED, ERROR = 0, 3, 2


@dataclass(frozen=True)
class Metrics:
    recall: float
    false_alarm_rate: float
    p95_latency_ms: float
    positives: int
    negatives: int

    def as_dict(self) -> dict:
        raise NotImplementedError("TODO")


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
    raise NotImplementedError("TODO")


def load_holdout(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    d = np.load(path)
    return d["X"], d["y"]


def evaluate(model, X: np.ndarray, y: np.ndarray, latency_samples: int = 200) -> Metrics:
    raise NotImplementedError("TODO")


def decide(champion: Metrics | None, challenger: Metrics, rules: Rules = Rules()) -> Decision:
    raise NotImplementedError("TODO")


def promote(registry: FileRegistry, name: str, challenger: int, holdout: str | Path, expected_sha: str,
            rules: Rules = Rules(), comment_path: str | Path | None = None) -> int:
    raise NotImplementedError("TODO")


def rollback(registry: FileRegistry, name: str) -> int:
    raise NotImplementedError("TODO")


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    sys.exit(main())
