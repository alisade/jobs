import json
from datetime import datetime, timedelta

from migrate_agent.fake_api import _blocks
from migrate_agent.prompt import build_request, load_skills
from migrate_agent.session import REPO, replay

T0 = datetime(2026, 11, 12, 2, 0, 0)
SKILLS = load_skills()


def prefix(req):
    blocks = _blocks(req)
    marks = [i for i, b in enumerate(blocks) if "cache_control" in b]
    assert marks, "no cache_control breakpoint"
    return json.dumps(blocks[: marks[-1] + 1], sort_keys=True)


def test_prefix_stable_across_time():
    a = build_request("t", REPO, SKILLS, T0, [])
    b = build_request("t", REPO, SKILLS, T0 + timedelta(minutes=3, seconds=17), [])
    assert prefix(a) == prefix(b)


def test_prefix_stable_across_listing_order():
    a = build_request("t", REPO, SKILLS, T0, [])
    b = build_request("t", list(reversed(REPO)), SKILLS, T0, [])
    c = build_request("t", set(REPO), SKILLS, T0, [])
    assert prefix(a) == prefix(b) == prefix(c)


def test_prefix_stable_across_skill_order():
    rev = dict(reversed(list(SKILLS.items())))
    assert prefix(build_request("t", REPO, SKILLS, T0, [])) == prefix(build_request("t", REPO, rev, T0, []))


def test_time_still_reaches_the_model_after_the_breakpoint():
    req = build_request("t", REPO, SKILLS, T0, [])
    whole = json.dumps(req)
    assert "2026-11-12T02:00:00" in whole, "the change log still needs the time"
    assert "2026-11-12" not in prefix(req), "time must not be inside the cached prefix"


def test_instructions_skills_and_listing_are_inside_the_cached_prefix():
    p = prefix(build_request("t", REPO, SKILLS, T0, []))
    assert "Never edit tests or golden files" in p
    assert "Skill: dependency-upgrade" in p and "Skill: reverse-engineer" in p
    assert "RatingExporter.java" in p


def test_different_modules_do_not_share_a_prefix():
    other = [f.replace("rating", "intake") for f in REPO]
    assert prefix(build_request("t", REPO, SKILLS, T0, [])) != prefix(build_request("t", other, SKILLS, T0, []))


def test_replay_reads_cache_after_turn_one():
    rows = replay(seed=7)
    assert rows[0]["cache_creation_input_tokens"] > 0
    for r in rows[1:]:
        assert r["cache_read_input_tokens"] > 0 and r["cache_creation_input_tokens"] == 0, r


def test_replay_cost_drops():
    total = sum(r["cost_usd"] for r in replay(seed=3))
    assert total < 0.40, f"8-turn replay costs {total:.4f} USD; with caching working it should be far below the 1.03 baseline"
