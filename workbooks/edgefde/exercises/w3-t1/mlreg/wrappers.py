"""Model wrapper pickled into every artifact (do not edit).

A model is trained on named feature columns. predict() takes a table (a mapping of
column name -> 1-D array, like a dataframe or an npz file) and builds the matrix in
the model's own column order, so a renamed or missing column raises KeyError.
"""

from __future__ import annotations

import numpy as np


class ColumnModel:
    def __init__(self, columns: list[str], model, threshold: float):
        self.columns, self.model, self.threshold = list(columns), model, threshold

    def matrix(self, table) -> np.ndarray:
        return np.column_stack([np.asarray(table[c], dtype=np.float32) for c in self.columns])

    def predict(self, table) -> np.ndarray:
        return (self.model.predict_proba(self.matrix(table))[:, 1] >= self.threshold).astype(int)
