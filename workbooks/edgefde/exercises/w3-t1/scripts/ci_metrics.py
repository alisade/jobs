"""The metric formula used by the CI evaluate step (do not edit)."""

import numpy as np


def metrics(model, table) -> dict[str, float]:
    y = np.asarray(table["y"])
    p = model.predict(table)
    return {"recall": float((p[y == 1] == 1).mean()), "false_alarm_rate": float((p[y == 0] == 1).mean())}
