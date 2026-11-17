"""Visible tests: one guard and the cache hit rate in a single process. Run: make test"""

from __future__ import annotations

from promptkit.fake_gemini import CachingFakeClient
from promptkit.prompt import build_request
from promptkit.runner import run_batch, summarize


def test_all_four_tools_are_declared(samples):
    _, config = build_request(samples[0], run_id="R", started_at="2026-10-07T02:00:00Z")
    names = sorted(d.name for t in config.tools for d in t.function_declarations)
    assert names == ["get_deploy_record", "get_directory_entry", "get_pr_checks", "get_ticket_approvals"]


def test_batch_hits_the_implicit_cache(samples):
    rows = run_batch(CachingFakeClient(), samples, run_id="CM03-2026Q3-R2", started_at="2026-10-07T02:00:00Z")
    s = summarize(rows)
    assert s["cache_hit_ratio"] >= 0.85, s
