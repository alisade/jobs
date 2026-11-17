"""Visible tests: metrics on a stub model, one decision, the first promotion."""

import numpy as np
import pytest

from gate import gate as G


class Fixed:
    def __init__(self, pred):
        self.pred = np.asarray(pred)

    def predict(self, X):
        return self.pred[: len(X)] if len(X) == len(self.pred) else np.zeros(len(X), dtype=int)


def test_evaluate_recall_and_false_alarms():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    m = G.evaluate(Fixed([1, 1, 1, 0, 1, 0, 0, 0, 0, 0]), np.zeros((10, 3)), y)
    assert m.recall == pytest.approx(0.75)
    assert m.false_alarm_rate == pytest.approx(1 / 6)
    assert (m.positives, m.negatives) == (4, 6)


def test_better_challenger_is_promoted():
    champ = G.Metrics(0.64, 0.025, 1.0, 300, 2700)
    chal = G.Metrics(0.70, 0.021, 1.0, 300, 2700)
    assert G.decide(champ, chal).promote


def test_first_model_promoted(env):
    code = G.promote(env["reg"], "pump-anomaly", 1, env["holdout"], env["sha"])
    assert code == G.PROMOTED
    assert env["reg"].get_alias("pump-anomaly", "champion") == 1
