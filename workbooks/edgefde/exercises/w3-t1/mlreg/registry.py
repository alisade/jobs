"""File-based model registry with an MLflow-like shape (complete: do not edit).

Layout under root/:
  models/<name>/versions/<v>.json   version record: run_id, artifact (path), train_data_sha,
                                     params, created, metrics (list of {holdout_sha, values, ts})
  models/<name>/aliases.json        {"aliases": {alias: version}, "history": [{ts, alias, from, to}]}

Like MLflow, an alias is a mutable pointer to a version ("champion", "challenger");
moving an alias is the promotion. Metrics are append-only and each entry says which
holdout set (by sha256) it was computed on.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class RegistryError(RuntimeError):
    pass


class FileRegistry:
    def __init__(self, root: str | Path, clock=time.time) -> None:
        self.root = Path(root)
        self.clock = clock

    # ---- paths
    def _mdir(self, name: str) -> Path:
        return self.root / "models" / name

    def _vpath(self, name: str, version: int) -> Path:
        return self._mdir(name) / "versions" / f"{version}.json"

    def _apath(self, name: str) -> Path:
        return self._mdir(name) / "aliases.json"

    @staticmethod
    def _write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
        tmp.replace(path)

    # ---- versions
    def list_versions(self, name: str) -> list[int]:
        d = self._mdir(name) / "versions"
        return sorted(int(p.stem) for p in d.glob("*.json")) if d.is_dir() else []

    def register(self, name: str, artifact: str | Path, run_id: str, train_data_sha: str,
                 params: dict | None = None) -> int:
        version = (self.list_versions(name) or [0])[-1] + 1
        self._write(self._vpath(name, version), {
            "name": name, "version": version, "run_id": run_id, "artifact": str(artifact),
            "train_data_sha": train_data_sha, "params": params or {}, "created": self.clock(), "metrics": [],
        })
        return version

    def get_version(self, name: str, version: int) -> dict:
        p = self._vpath(name, version)
        if not p.exists():
            raise RegistryError(f"{name} v{version} not registered")
        return json.loads(p.read_text())

    def log_metrics(self, name: str, version: int, holdout_sha: str, values: dict[str, float]) -> None:
        rec = self.get_version(name, version)
        rec["metrics"].append({"holdout_sha": holdout_sha, "values": dict(values), "ts": self.clock()})
        self._write(self._vpath(name, version), rec)

    def metrics_for(self, name: str, version: int, holdout_sha: str) -> dict[str, float] | None:
        """Latest metrics logged for exactly this version on exactly this holdout, or None."""
        hits = [m for m in self.get_version(name, version)["metrics"] if m["holdout_sha"] == holdout_sha]
        return hits[-1]["values"] if hits else None

    def latest_metrics(self, name: str) -> dict | None:
        """Most recently logged metrics across ALL versions of the model (for the dashboard tile).

        Returns {"version", "holdout_sha", "values", "ts"} or None.
        """
        best = None
        for v in self.list_versions(name):
            for m in self.get_version(name, v)["metrics"]:
                if best is None or m["ts"] >= best["ts"]:
                    best = {"version": v, **m}
        return best

    # ---- aliases
    def _aliases(self, name: str) -> dict:
        p = self._apath(name)
        return json.loads(p.read_text()) if p.exists() else {"aliases": {}, "history": []}

    def get_alias(self, name: str, alias: str) -> int | None:
        return self._aliases(name)["aliases"].get(alias)

    def set_alias(self, name: str, alias: str, version: int) -> None:
        self.get_version(name, version)  # must exist
        a = self._aliases(name)
        a["history"].append({"ts": self.clock(), "alias": alias, "from": a["aliases"].get(alias), "to": version})
        a["aliases"][alias] = version
        self._write(self._apath(name), a)

    def delete_alias(self, name: str, alias: str) -> None:
        a = self._aliases(name)
        if alias in a["aliases"]:
            a["history"].append({"ts": self.clock(), "alias": alias, "from": a["aliases"][alias], "to": None})
            del a["aliases"][alias]
            self._write(self._apath(name), a)

    def alias_history(self, name: str) -> list[dict]:
        return self._aliases(name)["history"]
