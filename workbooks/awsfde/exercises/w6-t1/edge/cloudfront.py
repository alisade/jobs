"""A small CloudFront cache simulator driven by config/distribution.json.

Modelled behaviour (from the CloudFront developer guide, cache policies and expiration):
- The first matching CacheBehaviors PathPattern wins, else DefaultCacheBehavior.
- Cache key = path + (query string if the policy includes it) + the listed headers.
- TTL: Cache-Control max-age / s-maxage clamped to [MinTTL, MaxTTL]; no Cache-Control -> DefaultTTL.
- no-store / no-cache / private are honoured only when MinTTL is 0; with MinTTL > 0 the object is
  cached for MinTTL anyway.
- MaxTTL 0 (CachingDisabled) never caches.
- Viewer request headers are forwarded to the origin (origin request policy AllViewerExceptHostHeader).
"""

from __future__ import annotations

import fnmatch
import json
import pathlib
import re
from typing import Callable


class Distribution:
    def __init__(self, config_path: pathlib.Path) -> None:
        self.cfg = json.loads(config_path.read_text())
        self.cache: dict[str, tuple[float, dict]] = {}

    def behavior(self, path: str) -> dict:
        for b in self.cfg.get("CacheBehaviors", []):
            if fnmatch.fnmatchcase(path, b["PathPattern"]):
                return b
        return self.cfg["DefaultCacheBehavior"]

    def policy(self, b: dict) -> dict:
        return self.cfg["CachePolicies"][b["CachePolicyId"]]

    @staticmethod
    def _ttl(policy: dict, headers: dict) -> float:
        cc = {k.lower(): v for k, v in headers.items()}.get("cache-control", "")
        if policy["MaxTTL"] == 0:
            return 0
        if re.search(r"\b(no-store|no-cache|private)\b", cc) and policy["MinTTL"] == 0:
            return 0
        m = re.search(r"s-maxage=(\d+)", cc) or re.search(r"max-age=(\d+)", cc)
        ttl = int(m.group(1)) if m else policy["DefaultTTL"]
        return max(policy["MinTTL"], min(policy["MaxTTL"], ttl))

    def get(self, now: float, path: str, query: str, headers: dict,
            origin: Callable[[str, str, dict], dict]) -> tuple[dict, str, dict]:
        """Returns (response, x-edge-result-type, behavior)."""
        b = self.behavior(path)
        p = self.policy(b)
        key = path + ("?" + query if p["QueryStringsInCacheKey"] != "none" and query else "")
        for h in p["HeadersInCacheKey"]:
            key += f"|{h.lower()}={headers.get(h, '')}"
        hit = self.cache.get(key)
        if hit and hit[0] > now:
            return hit[1], "Hit", b
        resp = origin(path, query, headers)
        ttl = self._ttl(p, resp.get("headers", {}))
        if ttl > 0 and resp.get("statusCode") == 200:
            self.cache[key] = (now + ttl, resp)
        return resp, "Miss" if ttl > 0 else "Miss-NotCached", b
