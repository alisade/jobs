"""The GRC Hub exception register and workpaper, as a JSON file (state/grc.json). Complete."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class GrcStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text())

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")

    @property
    def reviewers(self) -> list[str]:
        return list(self.data.get("reviewers", []))

    def exception(self, exception_id: str) -> dict:
        if exception_id not in self.data["exceptions"]:
            raise KeyError(f"unknown exception {exception_id}")
        return self.data["exceptions"][exception_id]

    def exceptions_for(self, change_id: str) -> dict[str, dict]:
        return {k: v for k, v in self.data["exceptions"].items() if v["change_id"] == change_id}

    def set_status(self, exception_id: str, status: str, by: str, comment: str, **extra) -> None:
        exc = self.exception(exception_id)
        exc["status"] = status
        exc["history"].append(dict({"at": now(), "by": by, "status": status, "comment": comment}, **extra))
        self.save()

    def set_workpaper(self, change_id: str, result: str, by: str) -> None:
        self.data["workpaper"][change_id] = result
        self.data.setdefault("workpaper_history", []).append({"at": now(), "by": by, "change_id": change_id, "result": result})
        self.save()
