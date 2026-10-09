# Rubric: fde/w2-t1 MCP gateway intermittently 401s after a JWKS rotation
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: `JWKS_MIN_REFRESH_INTERVAL=86400` in `gateway.env` (set to the cache TTL) means `KeyCache.get` (`gateway/jwks_cache.py`, the `now - last_fetch >= min_refresh_interval` branch) never refreshes on an unknown kid within a day of the startup fetch, so new-kid tokens 401 until a restart or the 24 h TTL; explains why it is intermittent (staged rollover: only new-kid tokens fail; existing sessions hold old-kid tokens). Partial (10): "stale JWKS cache" without the setting and code path. Zero: clock skew, IdP fault, or "restart fixes it". |
| 3 | Evidence | 20 | Full: shows the IdP JWKS containing both kids vs `/debug/jwks` showing one kid with a large `last_fetch_age_s`; `make probe` split by kid (all 401s on `k-2026-10`); log lines `401 invalid_token kid=k-2026-10 reason=signing key not found`; the DEBUG "refresh skipped" path or the config line; and the red herring ruled out (2 s skew is inside the 30 s leeway, those requests got 200). Partial: some of these. Zero: assertions without evidence. |
| 4 | Fix quality | 15 | Full: interval set to a value that satisfies SEC-114 (>= 10 s) and bounds rotation latency (<= a few minutes), TTL reduced to something reasonable or justified, startup validation with an actionable message, verification not loosened; verified live without a restart. Partial: config-only fix, no guard. Zero: verification weakened or refresh rate limit removed. |
| 5 | Trade-offs and prevention | 10 | Full: at least two of: cooldown should be measured from the last forced refresh not any fetch; alert on 401 rate by kid; IdP publishes new keys a day before signing with them; synthetic probe after rollovers; negative caching. Partial: generic. |
Total: 100
