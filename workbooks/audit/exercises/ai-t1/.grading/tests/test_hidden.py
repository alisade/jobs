"""Hidden tests for audit/ai-t1: byte-stable prefix across samples, runs and processes."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from promptkit.fake_gemini import CachingFakeClient, serialize_request, serialize_tools
from promptkit.prompt import build_request
from promptkit.runner import run_batch, summarize

PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from promptkit.prompt import build_request
from promptkit.fake_gemini import serialize_request
samples = list(json.load(open(sys.argv[1] + "/fixtures/samples.json")).values())
out = []
for i, s in enumerate(samples[:3]):
    c, cfg = build_request(s, run_id="RUN-" + sys.argv[2], started_at="2026-10-0%sT02:00:00Z" % (i + 1))
    out.append(serialize_request(c, cfg))
print(json.dumps(out))
"""


def _system(cfg):
    return str(cfg.system_instruction)


def test_system_instruction_is_static(samples):
    _, a = build_request(samples[0], run_id="R1", started_at="2026-10-07T02:00:00Z")
    _, b = build_request(samples[7], run_id="R9", started_at="2026-11-01T03:15:00Z")
    assert _system(a) == _system(b)


def test_no_per_request_values_in_system_or_tools(samples):
    s = samples[3]
    _, cfg = build_request(s, run_id="CM03-2026Q3-R2", started_at="2026-10-07T02:00:00Z")
    static = _system(cfg) + serialize_tools(cfg)
    for v in ("CM03-2026Q3-R2", "2026-10-07T02:00:00Z", s["change_id"], str(s["pr_number"])):
        assert v not in static, f"{v} is in the cached prefix"


def test_sample_data_is_in_the_last_user_content(samples):
    s = samples[5]
    contents, _ = build_request(s, run_id="R", started_at="2026-10-07T02:00:00Z")
    last = contents[-1]
    assert last.role == "user"
    text = " ".join(p.text or "" for p in last.parts)
    assert s["change_id"] in text and str(s["pr_number"]) in text and s["title"] in text


def test_request_contract_unchanged(samples):
    _, cfg = build_request(samples[0], run_id="R", started_at="2026-10-07T02:00:00Z")
    assert cfg.temperature == 0 and cfg.response_mime_type == "application/json"
    assert cfg.automatic_function_calling.disable is True
    assert "Evidence policy" in _system(cfg)


def _probe(root, seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    p = subprocess.run([sys.executable, "-c", PROBE, str(root), str(seed)], env=env,
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def test_static_prefix_identical_across_processes(root):
    prefixes = set()
    for seed in (0, 1, 7, 11, 29, 123):
        for text in _probe(root, seed):
            prefixes.add(text.split("\n[CONTENTS]")[0])
    assert len(prefixes) == 1, f"{len(prefixes)} different tools+system prefixes across hash seeds"


def test_two_instances_share_the_cache(root, samples, tmp_path):
    store = tmp_path / "cache.json"
    rows = []
    for n, seed in enumerate(("11", "29")):
        code = (
            "import json,sys; sys.path.insert(0, sys.argv[1]);"
            "from promptkit.fake_gemini import CachingFakeClient; from promptkit.runner import run_batch;"
            "s=list(json.load(open(sys.argv[1]+'/fixtures/samples.json')).values());"
            "part=s[:13] if sys.argv[3]=='0' else s[13:];"
            "print(json.dumps(run_batch(CachingFakeClient(store=sys.argv[2]), part, run_id='R2', started_at='2026-10-07T02:00:00Z')))"
        )
        p = subprocess.run([sys.executable, "-c", code, str(root), str(store), str(n)],
                           env=dict(os.environ, PYTHONHASHSEED=seed), capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr
        rows += json.loads(p.stdout)
    misses = [r for r in rows if r["cached_tokens"] == 0]
    assert len(misses) <= 1, f"{len(misses)} cache misses across two instances"
    assert summarize(rows)["cache_hit_ratio"] >= 0.9


def test_cost_per_100_samples_back_to_baseline(samples):
    rows = run_batch(CachingFakeClient(), samples, run_id="R2", started_at="2026-10-07T02:00:00Z")
    s = summarize(rows)
    assert s["cost_per_100_samples_usd"] <= 0.085, s
    assert s["p50_latency_ms"] <= 250, s


def test_new_run_reuses_cache_from_previous_run(samples):
    client = CachingFakeClient()
    run_batch(client, samples[:3], run_id="R1", started_at="2026-10-06T02:00:00Z")
    rows = run_batch(client, samples[3:6], run_id="R2", started_at="2026-10-07T02:00:00Z")
    assert all(r["cached_tokens"] > 4000 for r in rows)


def test_model_change_costs_one_miss_only(samples):
    client = CachingFakeClient()
    a = run_batch(client, samples[:5], run_id="R1", started_at="x", model="gemini-3.8-flash-001")
    b = run_batch(client, samples[5:10], run_id="R1", started_at="x", model="gemini-3.8-flash-002")
    assert a[0]["cached_tokens"] == 0 and b[0]["cached_tokens"] == 0
    assert all(r["cached_tokens"] > 4000 for r in a[1:] + b[1:])


def test_serialization_guard():
    # the simulator itself: identical requests are fully cached
    from google.genai import types
    cfg = types.GenerateContentConfig(system_instruction="x" * 8000)
    c = CachingFakeClient()
    r1 = c.models.generate_content(model="m", contents=["hello"], config=cfg)
    r2 = c.models.generate_content(model="m", contents=["hello"], config=cfg)
    assert r1.usage_metadata.cached_content_token_count == 0
    assert r2.usage_metadata.cached_content_token_count == len(serialize_request(["hello"], cfg)) // 4
