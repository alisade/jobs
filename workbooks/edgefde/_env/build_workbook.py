#!/usr/bin/env python3
"""Build edgefde/workbook.html from exercises/*/card.json and _env/quiz/*.json.

The page is a single self-contained file (SPEC.md "workbook.html"): CSS from workbook.css,
behaviour from workbook.js, data embedded as window.EDGEFDE_DATA. Re-run after changing a card or
a question bank:  python3 edgefde/_env/build_workbook.py
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

ENV = pathlib.Path(__file__).resolve().parent
TRACK = ENV.parent
GUIDE = "../../fde-edge-ai-study-plan.html"

AREAS = [
    ("pipelines", "Production Python and data pipelines"),
    ("signals", "Signal processing and sensor data"),
    ("mlops", "MLOps: registry, gates, monitoring"),
    ("edgeai", "Edge AI: ONNX, quantization, runtimes"),
    ("fleet", "Edge fleet operations"),
    ("llm", "LLMs and agents at the edge"),
    ("network", "Locked-down networks and on-site debugging"),
    ("integrations", "API integrations"),
    ("fde", "FDE practice: framing, outcomes, handoff"),
]

WEEKS = [
    ("w1", "1", "Week 1", "Production Python and data pipelines", "Packaging, typing and tests; Kafka as a client author; at-least-once plus idempotent writes; backfills and data quality."),
    ("w2", "2", "Week 2", "Signal processing and sensor data", "Sampling, Nyquist and aliasing, FFT and windowing, Welch PSD, filters, envelopes and bearing defect frequencies."),
    ("w3", "3", "Week 3", "MLOps", "Registry, champion/challenger, eval gates in CI that fail closed, drift and monitoring."),
    ("w4", "4", "Week 4", "Edge AI runtimes", "ONNX export, ONNX Runtime, static INT8 quantization with calibration, honest benchmarks."),
    ("w5", "5", "Week 5", "Edge fleet operations", "OTA canary and rollback, offline buffering and idempotent replay, air-gapped installs."),
    ("w6", "6", "Week 6", "LLMs at the edge and FDE practice", "Engagement framing and handoff, locked-down networks, proxies and CA bundles."),
    ("ai", "ai", "AI Integration", "AI integration fundamentals", "The shared AI Integration page applied to an edge operator assistant: read-only tools, validated answers, hybrid routing, and an injection that reached a write tool."),
    ("w7", "7", "Week 7 (add-on)", "Integrations and field drills", "Optional: a CMMS work-order client with retries and idempotency keys, and a streaming filter drill."),
]

MOCKS = {
    "screen": {
        "title": "FDE technical screen (edge AI)",
        "short": "FDE technical screen",
        "minutes": 45,
        "scale": "percent",
        "pass": 70,
        "unit": "%",
        "intro": "A forward deployed engineering screen across pipelines, signal processing, MLOps, edge AI, fleet operations, LLMs at the edge, locked-down networks and FDE practice. No answers are shown until you submit or time runs out. Scored as percent correct with 70% to pass.",
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
        cmds = f"""cd edgefde/exercises/{ex}
make setup      # nothing to install; read inputs/
# write BRIEF.md and ANSWER.md
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code:
/grade edgefde/{ex}
make clean"""
    else:
        setup_note = "deps + incident bundle" if typ == "troubleshooting" else "deps"
        cmds = f"""cd edgefde/exercises/{ex}
make setup      # {setup_note}
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code:
/grade edgefde/{ex}
make clean"""
    return f"""
  <div class="card ex" data-ex="edgefde/{esc(ex)}" id="ex-{esc(ex)}">
    <div class="exhead">
      <h3>{esc(c['title'])}</h3>
      <span class="tag {tag_cls}">{esc(typ)}</span>{opt}
      <span class="est">{esc(c['estimate'])}</span>
      <span class="badge" data-badge="edgefde/{esc(ex)}"></span>
    </div>
    <p class="meta"><code>edgefde/{esc(ex)}</code> &middot; {esc(c.get('area', ''))}</p>
    <p><b>Scenario.</b> {esc(c['scenario'])}</p>
    <div class="cols">
      <div><h4>Task</h4><ul class="plain">{tasks}</ul></div>
      <div><h4>Acceptance criteria</h4><ul class="plain">{acc}</ul></div>
    </div>
    <div class="cols">
      <div><h4>Run it</h4>
<pre>{esc(cmds)}</pre>
        <p class="small">Folder: <code>edgefde/exercises/{esc(ex)}/</code> &middot; <a href="exercises/{esc(ex)}/README.md">README</a> &middot; <a href="exercises/{esc(ex)}/ANSWER.md">ANSWER.md</a>{' &middot; <a href="exercises/' + esc(ex) + '/BRIEF.md">BRIEF.md</a>' if typ == 'design' else ''}</p>
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
                f'<tr><td><a href="#ex-{esc(c["_dir"])}">edgefde/{esc(c["_dir"])}</a></td><td>{esc(c["title"])}</td><td>{esc(c["type"])}{" (optional)" if c.get("optional") else ""}</td>'
                f'<td>{esc(wk[2])}</td><td>{esc(c["estimate"])}</td><td><span class="badge" data-badge="edgefde/{esc(c["_dir"])}"></span></td></tr>'
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
<title>Forward Deployed Engineer (Edge AI) workbook</title>
<script src="../grades/grades.js"></script>
{css.replace("</style>", "  .tag.design {{ color: var(--done); background: var(--done-soft); }}\n</style>")}
</head>
<body>
<header>
  <button class="themebtn" id="themebtn" type="button">light / dark</button>
  <h1>Forward Deployed Engineer (Edge AI) workbook</h1>
  <p>Exercises, self-exams and a timed screen for the <a href="{GUIDE}">FDE Edge AI study plan</a>. Scores update after /grade; reload the page.</p>
</header>
<nav><div class="inner" id="tabs"></div></nav>
<main>

<section class="page" id="overview" data-title="Overview">
  <h2>FDE (Edge AI) workbook</h2>
  <p class="lede">Hands-on coding, troubleshooting and design exercises set at Corvane Industrial's Dunmore pump plant
  (fictional), where you are embedded as a Tessellate Edge (fictional) forward deployed engineer: pipelines, signals, MLOps,
  edge AI, fleet operations, LLMs at the edge and locked-down networks. One tab per study week, weekly self-exams and one
  timed screen. Everything grades locally and offline: Python in a shared venv, in-process fakes for Kafka, the registry,
  the fleet and the CMMS, and a stub LLM that replays recorded turns.</p>
  <div class="progress"><div id="bar-all"></div></div>
  <p class="note"><b>Scores update after /grade; reload the page.</b> Grades come from <code>../grades/grades.js</code>, written by
  <code>tools/update_grades.py</code> when you run <code>/grade edgefde/&lt;id&gt;</code> in Claude Code from the <code>workbooks/</code> folder.
  Quiz answers and mock results save in this browser (localStorage key <code>wb-edgefde-v1</code>).</p>
  <div class="grid2">
    <div class="card"><h3>How to work an exercise</h3><ol>
      <li><code>tools/doctor.sh edgefde</code> once: python3, uv, jq.</li>
      <li>Open the week tab, read the card, then the folder README.</li>
      <li><code>cd edgefde/exercises/&lt;id&gt; &amp;&amp; make setup</code> (the first run builds <code>edgefde/.venv</code>: numpy, scipy, scikit-learn, onnx, onnxruntime, skl2onnx, pydantic, pytest), solve it, <code>make test</code>, fill in <code>ANSWER.md</code>.</li>
      <li>From <code>workbooks/</code>: <code>/grade edgefde/&lt;id&gt;</code>. Reload this page.</li>
      <li><code>make clean</code>. Retry as often as you like; every attempt is kept.</li>
    </ol><p class="small">Do not open <code>.grading/</code> before you submit. Pass mark 70/100. Troubleshooting is graded mostly on root cause and evidence; the design exercise is graded by rubric only (the grader reports 0/0 tests).</p></div>
    <div class="card"><h3>How the local stand-ins work</h3><ul class="plain">
      <li>Kafka: an in-process broker with partitions, consumer groups, committed offsets and auto-commit.</li>
      <li>Signals: synthetic accelerometer captures with known tones, gear mesh and bearing impacts, so every feature has a known answer.</li>
      <li>MLOps and edge AI: a file-based registry fake; scikit-learn models exported with skl2onnx and quantized with ONNX Runtime on CPU.</li>
      <li>Fleet and offline: simulated gateways with a fake clock, a SQLite buffer and a lossy uplink.</li>
      <li>LLM: a stub client replaying recorded OpenAI-compatible turns (the shape Ollama and llama.cpp serve). No API keys.</li>
      <li>Locked-down network: an evidence bundle (pip/uv logs, s_client captures) and real config files you fix.</li>
    </ul></div>
  </div>
  <h3>Self-exam</h3>
  <ul class="plain"><li>Weekly sets ({len(weekly)} questions): {esc(count_txt)}.</li><li>Timed: {esc(mock_txt)}.</li></ul>
  <h3>All exercises ({len(cards)}: {n_code} coding, {n_ts} troubleshooting, {n_des} design)</h3>
  <table><tr><th>Id</th><th>Title</th><th>Type</th><th>Week</th><th>Estimate</th><th>Grade</th></tr>{''.join(rows)}</table>
</section>
{''.join(sections)}
<section class="page" id="selfexam" data-title="Self-exam">
  <h2>Self-exam</h2>
  <p class="lede">Scenario questions per study week (check each answer to see the explanation), and a timed screen scored by area
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
<script>window.EDGEFDE_DATA = {data_js};</script>
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
