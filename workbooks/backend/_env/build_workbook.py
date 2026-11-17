#!/usr/bin/env python3
"""Build backend/workbook.html from exercises/*/card.json and _env/quiz/*.json.

The page is a single self-contained file (SPEC.md "workbook.html"): CSS from workbook.css,
behaviour from workbook.js, data embedded as window.BACKEND_DATA. Re-run after changing a card or
a question bank:  python3 backend/_env/build_workbook.py   (or: make workbook)
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

ENV = pathlib.Path(__file__).resolve().parent
TRACK = ENV.parent
GUIDE = "../../ai-backend-data-platform-study-plan.html"

AREAS = [
    ("design", "System design and platform architecture"),
    ("postgres", "PostgreSQL: modeling, indexing, RLS, migrations"),
    ("python", "Python services: FastAPI, SQLAlchemy 2, asyncio"),
    ("typescript", "TypeScript services: Node, Fastify, Kysely"),
    ("api", "API design: REST, GraphQL, idempotency, pagination"),
    ("events", "Events and messaging: outbox, Kafka, consumers"),
    ("go", "Go"),
    ("workflow", "Workflow engines and durable execution"),
    ("crm", "CRM data models and migration"),
    ("agents", "Agentic apps on the platform: MCP, scopes, audit"),
    ("delivery", "Delivery and reliability"),
]

WEEKS = [
    ("w1", "1", "Week 1", "System design and the CRM domain", "Whiteboard method, service boundaries, multi-tenancy, the Salesforce object model and what a migration has to preserve."),
    ("w2", "2", "Week 2", "PostgreSQL in depth", "Schema and constraints, indexes, reading plans, row-level security for tenancy, MVCC and locking."),
    ("w3", "3", "Week 3", "Python services and API design", "FastAPI with async SQLAlchemy 2, idempotency keys, cursor pagination, RFC 9457 errors."),
    ("w4", "4", "Week 4", "TypeScript services and a GraphQL read layer", "Fastify, Kysely and Zod, transactions with row locks, an outbox row per change, DataLoader done right."),
    ("w5", "5", "Week 5", "Events, the outbox and Go", "Transactional outbox, relays, at-least-once delivery, idempotent consumers, Go for platform glue."),
    ("w6", "6", "Week 6", "Workflow automation and durable execution", "Temporal workflows, activities, signals and timers for approvals, versioning running workflows."),
    ("ai", "ai", "AI Integration", "Agents on the platform", "The shared AI Integration page applied to this role: tenant-scoped MCP tools, an audit log, and why tool scoping, not the prompt, is the control."),
    ("w7", "7", "Week 7 (add-on)", "Migrations at scale and mock whiteboards", "Optional: a zero-downtime migration incident and a timed system design session."),
]

MOCKS = {
    "screen": {
        "title": "Senior backend / platform technical screen",
        "short": "Backend platform screen",
        "minutes": 45,
        "scale": "percent",
        "pass": 70,
        "unit": "%",
        "intro": "A timed screen across the posting's required bullets: system design trade-offs, PostgreSQL, Python and TypeScript services, API design, events, Go, workflows, CRM migration and agent tooling. No answers are shown until you submit or time runs out. Scored as percent correct with 70% to pass.",
        "file": "mock-screen.json",
    },
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load_cards() -> list[dict]:
    cards = []
    for p in sorted((TRACK / "exercises").glob("*/card.json")):
        c = json.loads(p.read_text())
        c["_dir"] = p.parent.name
        cards.append(c)
    return cards


def week_key(c: dict) -> str:
    w = c.get("week")
    if w == "ai":
        return "ai"
    return f"w{int(w)}"


def sort_key(c: dict):
    ex = c["_dir"]
    kind = {"c": 0, "t": 1}.get(ex.split("-")[1][0], 2) if "-" in ex else 2
    return (ex.split("-")[0], kind, ex)


def card_html(c: dict) -> str:
    ex = c["_dir"]
    typ = c["type"]
    tag_cls = {"coding": "coding", "troubleshooting": "troubleshooting", "design": "design"}.get(typ, "coding")
    opt = '<span class="tag opt">optional</span>' if c.get("optional") else ""
    tasks = "".join(f"<li>{esc(t)}</li>" for t in c.get("task", []))
    acc = "".join(f"<li>{esc(t)}</li>" for t in c.get("acceptance", []))
    prac = "".join(
        f'<li><a href="{GUIDE}#{esc(p["href"] if p["href"] in ("ai",) or p["href"].startswith("week") else "week" + str(p["href"]))}">{esc(p["label"])}</a></li>'
        for p in c.get("practices", [])
    )
    if typ == "design":
        cmds = f"""cd backend/exercises/{ex}
make setup      # nothing to install; read inputs/
# write DESIGN.md and ANSWER.md
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code:
/grade backend/{ex}
make clean"""
    else:
        setup_note = "deps + incident bundle" if typ == "troubleshooting" else "deps"
        cmds = f"""cd backend/exercises/{ex}
make setup      # {setup_note}
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code:
/grade backend/{ex}
make clean"""
    return f"""
  <div class="card ex" data-ex="backend/{esc(ex)}" id="ex-{esc(ex)}">
    <div class="exhead">
      <h3>{esc(c['title'])}</h3>
      <span class="tag {tag_cls}">{esc(typ)}</span>{opt}
      <span class="est">{esc(c['estimate'])}</span>
      <span class="badge" data-badge="backend/{esc(ex)}"></span>
    </div>
    <p class="meta"><code>backend/{esc(ex)}</code> &middot; {esc(c.get('area', ''))}</p>
    <p><b>Scenario.</b> {esc(c['scenario'])}</p>
    <div class="cols">
      <div><h4>Task</h4><ul class="plain">{tasks}</ul></div>
      <div><h4>Acceptance criteria</h4><ul class="plain">{acc}</ul></div>
    </div>
    <div class="cols">
      <div><h4>Run it</h4>
<pre>{esc(cmds)}</pre>
        <p class="small">Folder: <code>backend/exercises/{esc(ex)}/</code> &middot; <a href="exercises/{esc(ex)}/README.md">README</a> &middot; <a href="exercises/{esc(ex)}/ANSWER.md">ANSWER.md</a>{' &middot; <a href="exercises/' + esc(ex) + '/DESIGN.md">DESIGN.md</a>' if typ == 'design' else ''}</p>
      </div>
      <div><h4>Practices (study guide)</h4><ul class="links">{prac}</ul></div>
    </div>
  </div>"""


def load_questions() -> tuple[list[dict], dict]:
    weekly: list[dict] = []
    mocks: dict = {}
    qdir = ENV / "quiz"
    for p in sorted(qdir.glob("weekly-*.json")):
        weekly.extend(json.loads(p.read_text())["questions"])
    for key, meta in MOCKS.items():
        p = qdir / meta["file"]
        if p.exists():
            m = {k: v for k, v in meta.items() if k != "file"}
            m["questions"] = json.loads(p.read_text())["questions"]
            mocks[key] = m
    return weekly, mocks


def check_questions(weekly: list[dict], mocks: dict) -> list[str]:
    errs = []
    keys = {k for k, _ in AREAS}
    seen = set()
    allq = weekly + [q for m in mocks.values() for q in m["questions"]]
    for q in allq:
        qid = q.get("id")
        if qid in seen:
            errs.append(f"duplicate id {qid}")
        seen.add(qid)
        if q.get("area") not in keys:
            errs.append(f"{qid}: unknown area {q.get('area')}")
        n = len(q.get("options", []))
        if not q.get("answer") or any(not (0 <= a < n) for a in q["answer"]):
            errs.append(f"{qid}: answer out of range")
        if q.get("type") not in ("single", "multi", "order"):
            errs.append(f"{qid}: bad type")
        if q.get("type") == "single" and len(q["answer"]) != 1:
            errs.append(f"{qid}: single with {len(q['answer'])} answers")
    return errs


def main() -> int:
    cards = sorted(load_cards(), key=sort_key)
    weekly, mocks = load_questions()
    errs = check_questions(weekly, mocks)
    if errs:
        print("question bank problems:\n  " + "\n  ".join(errs[:40]), file=sys.stderr)
        return 1
    by_week: dict[str, list[dict]] = {}
    for c in cards:
        by_week.setdefault(week_key(c), []).append(c)

    css = (ENV / "workbook.css").read_text()
    js = (ENV / "workbook.js").read_text()

    # overview
    counts = {}
    for q in weekly:
        counts[str(q["week"])] = counts.get(str(q["week"]), 0) + 1
    count_txt = ", ".join(
        (f"week {w}: {counts[w]}" if w != "ai" else f"AI page: {counts[w]}")
        for w in sorted(counts, key=lambda x: (x == "ai", int(x) if x != "ai" else 0))
    )
    mock_txt = "; ".join(f"{m['title']}: {len(m['questions'])} questions, {m['minutes']} minutes" for m in mocks.values())
    rows = []
    for wk in WEEKS:
        for c in by_week.get(wk[0], []):
            rows.append(
                f'<tr><td><a href="#ex-{esc(c["_dir"])}">backend/{esc(c["_dir"])}</a></td><td>{esc(c["title"])}</td><td>{esc(c["type"])}{" (optional)" if c.get("optional") else ""}</td>'
                f'<td>{esc(wk[2])}</td><td>{esc(c["estimate"])}</td><td><span class="badge" data-badge="backend/{esc(c["_dir"])}"></span></td></tr>'
            )
    n_code = sum(1 for c in cards if c["type"] == "coding")
    n_ts = sum(1 for c in cards if c["type"] == "troubleshooting")
    n_des = sum(1 for c in cards if c["type"] == "design")

    sections = []
    for key, num, title, theme, lede in WEEKS:
        ex_cards = by_week.get(key, [])
        if not ex_cards:
            continue
        anchor = "ai" if key == "ai" else f"week{num}"
        sections.append(f"""
<section class="page" id="{key}" data-title="{esc(title)}">
  <h2>{esc(title)} - {esc(theme)}</h2>
  <p class="lede">{esc(lede)} Study guide: <a href="{GUIDE}#{anchor}">{esc(title)}</a>.</p>
  <div class="progress"><div id="bar-{key}"></div></div>
  {''.join(card_html(c) for c in ex_cards)}
</section>""")

    data = {
        "areas": [{"key": k, "name": n} for k, n in AREAS],
        "weekly": weekly,
        "mocks": mocks,
    }
    data_js = json.dumps(data, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Backend data platform workbook - system design, PostgreSQL, services, events, workflows, agents</title>
<script src="../grades/grades.js"></script>
{css.replace("</style>", "  .tag.design { color: var(--done); background: var(--done-soft); }\n</style>")}
</head>
<body>
<header>
  <button class="themebtn" id="themebtn" type="button">light / dark</button>
  <h1>Backend data platform workbook - system design, PostgreSQL, services, events, workflows, agents</h1>
  <p>Exercises, self-exams and a timed mock for the <a href="{GUIDE}">AI backend data platform study plan</a>. Scores update after /grade; reload the page.</p>
</header>
<nav><div class="inner" id="tabs"></div></nav>
<main>

<section class="page" id="overview" data-title="Overview">
  <h2>Backend data platform workbook</h2>
  <p class="lede">Hands-on coding, troubleshooting and design exercises for Keystone, the platform layer that
  Lumenfold (a fictional enterprise data and AI company) is building to move its internal apps off a third-party CRM.
  One tab per study week, weekly self-exams and a timed technical screen. Everything grades locally and offline:
  no cloud accounts, no API keys, no Docker.</p>
  <div class="progress"><div id="bar-all"></div></div>
  <p class="note"><b>Scores update after /grade; reload the page.</b> Grades come from <code>../grades/grades.js</code>, written by
  <code>tools/update_grades.py</code> when you run <code>/grade backend/&lt;id&gt;</code> in Claude Code from the <code>workbooks/</code> folder.
  Quiz answers and mock results save in this browser (localStorage key <code>wb-backend-v1</code>).</p>
  <div class="grid2">
    <div class="card"><h3>How to work an exercise</h3><ol>
      <li><code>tools/doctor.sh backend</code> once: python3, uv, node 22, go, jq. <code>make deps</code> in <code>backend/</code> installs the shared toolchain in one go (about 30 s).</li>
      <li>Open the week tab, read the card, then the folder README.</li>
      <li><code>cd backend/exercises/&lt;id&gt; &amp;&amp; make setup</code> (first run installs the shared toolchain into <code>backend/_env</code>), solve it, <code>make test</code>, fill in <code>ANSWER.md</code>.</li>
      <li>From <code>workbooks/</code>: <code>/grade backend/&lt;id&gt;</code>. Reload this page.</li>
      <li><code>make clean</code>. Retry as often as you like; every attempt is kept.</li>
    </ol><p class="small">Do not open <code>.grading/</code> before you submit. Pass mark 70/100. Troubleshooting is graded mostly on root cause and evidence; design exercises are graded by rubric only (the grader reports 0/0 tests and the automated row does not apply).</p></div>
    <div class="card"><h3>How the local stand-ins work</h3><ul class="plain">
      <li>PostgreSQL: <a href="https://pglite.dev/">PGlite</a>, real PostgreSQL 18 compiled to WebAssembly and installed with npm. The planner, RLS, constraints and <code>EXPLAIN</code> are the real thing; it is a single session, so lock waits are studied from captured <code>pg_locks</code> evidence instead.</li>
      <li>Python services: FastAPI and SQLAlchemy 2 async on SQLite (aiosqlite) where the exercise is about the service, not Postgres; pytest with httpx against the ASGI app.</li>
      <li>TypeScript services: Fastify, Kysely (PGlite dialect), Zod, graphql-js and DataLoader, tested with jest.</li>
      <li>Kafka: an in-process partitioned log with offsets, consumer groups and redelivery. Temporal: the real Python SDK with its time-skipping test server (downloaded once by <code>make deps</code>) and the offline <code>Replayer</code>.</li>
      <li>MCP: the official Python SDK, called in process; the "model" is a scripted client, so no API key is needed. Go: standard library only.</li>
    </ul></div>
  </div>
  <h3>Self-exam</h3>
  <ul class="plain"><li>Weekly sets ({len(weekly)} questions): {esc(count_txt)}.</li><li>Timed mocks: {esc(mock_txt)}.</li></ul>
  <h3>All exercises ({len(cards)}: {n_code} coding, {n_ts} troubleshooting, {n_des} design)</h3>
  <table><tr><th>Id</th><th>Title</th><th>Type</th><th>Week</th><th>Estimate</th><th>Grade</th></tr>{''.join(rows)}</table>
</section>
{''.join(sections)}
<section class="page" id="selfexam" data-title="Self-exam">
  <h2>Self-exam</h2>
  <p class="lede">Scenario questions per study week (check each answer to see the explanation), and a timed technical screen scored by area
  with a full review and docs links after you submit.</p>
  <div class="subnav" id="se-nav"></div>
  <div id="se-root"></div>
</section>

<section class="page" id="scoreboard" data-title="Scoreboard">
  <h2>Scoreboard</h2>
  <p class="lede">Exercise scores come from <code>../grades/grades.js</code> (reload after <code>/grade</code>); quiz and mock scores from this browser.</p>
  <p class="card" id="sb-overall"></p>
  <h3>Exercises</h3>
  <table><thead><tr><th>Exercise</th><th>Title</th><th>Type</th><th>Latest</th><th>Best</th><th>Status</th><th>Attempts</th><th>Feedback</th></tr></thead><tbody id="sb-ex"></tbody></table>
  <h3>Weekly quizzes</h3>
  <table><thead><tr><th>Set</th><th>Correct / checked</th><th>Checked / total</th><th>%</th></tr></thead><tbody id="sb-quiz"></tbody></table>
  <h3>Mock exams</h3>
  <table><thead><tr><th>Exam</th><th>Latest</th><th>Best</th><th>Status</th><th>Attempts</th><th>Weakest areas (latest)</th></tr></thead><tbody id="sb-mock"></tbody></table>
</section>
</main>
<script>window.BACKEND_DATA = {data_js};</script>
<script>
{js}</script>
</body>
</html>
"""
    out = TRACK / "workbook.html"
    out.write_text(page)
    bad = [i for i, ch in enumerate(page) if ord(ch) > 127]
    print(f"wrote {out} ({len(page)} bytes): {len(cards)} exercises, {len(weekly)} weekly questions, mocks: "
          + ", ".join(f"{k}={len(m['questions'])}" for k, m in mocks.items())
          + (f"; NON-ASCII at {bad[:5]}" if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
