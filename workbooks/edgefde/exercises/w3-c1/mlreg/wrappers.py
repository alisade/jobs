"""Model wrapper pickled into every artifact (complete: do not edit)."""

from __future__ import annotations

import numpy as np


class Thresholded:
    """A probabilistic model plus the fixed alert threshold the gateway applies."""

    def __init__(self, model, threshold: float):
        self.model, self.threshold = model, threshold

    def predict(self, X) -> np.ndarray:
        return (self.model.predict_proba(X)[:, 1] >= self.threshold).astype(int)
