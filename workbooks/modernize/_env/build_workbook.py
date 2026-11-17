#!/usr/bin/env python3
"""Build modernize/workbook.html from exercises/*/card.json and _env/quiz/*.json.

The page is a single self-contained file (SPEC.md "workbook.html"): CSS from workbook.css,
behaviour from workbook.js, data embedded as window.MODERNIZE_DATA. Re-run after changing a card or
a question bank:  python3 modernize/_env/build_workbook.py   (or: make workbook)
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

ENV = pathlib.Path(__file__).resolve().parent
TRACK = ENV.parent
GUIDE = "../../lead-ai-modernization-study-plan.html"

AREAS = [
    ("java", "Enterprise Java modernization"),
    ("maven", "Dependency and build remediation"),
    ("reveng", "Reverse engineering and specs"),
    ("identity", "LDAP to OIDC/JWT"),
    ("safechange", "Characterization tests and blast radius"),
    ("appserver", "App servers: JBoss EAP/WildFly"),
    ("dotnet", ".NET modernization"),
    ("supply", "Supply chain and vulnerability remediation"),
    ("pods", "Leading AI-assisted pods"),
    ("agents", "Agent skills, tools and evals"),
    ("security", "LLM and application security"),
]

# (tab id, plan anchor, tab title, theme, lede)
WEEKS = [
    ("w1", "week1", "Week 1", "JDK 8 to 21 and Jakarta mechanics", "What JDK 9-21 removed and encapsulated, jdeps and jdeprscan, Maven mediation, BOMs and enforcer rules."),
    ("w2", "week2", "Week 2", "Agentic reverse engineering into specs", "Discovery checklists, subagent fan-out, evidence that resolves to file:line, and agent tools that never truncate silently."),
    ("w3", "week3", "Week 3", "LDAP to OIDC/JWT", "Where legacy authorization hides, mapping groups to token claims with identical decisions, and token pitfalls: algorithm, audience, skew, key rotation."),
    ("w4", "week4", "Week 4", "Safe change on monoliths", "Characterization tests, javax to jakarta, parallel runs, blast radius and the JDK changes that only show up in output files."),
    ("w5", "week5", "Week 5", ".NET Framework to modern .NET and supply-chain remediation", "SDK-style projects, BinaryFormatter, ICU string comparison, configuration; SBOMs, scanners and remediation reports you can trust."),
    ("w6", "week6", "Week 6", "Leading pods", "Skills with approval gates, a pod playbook, and reviewing agent PRs for the ways they game CI."),
    ("w7", "week7", "Week 7 (add-on)", "Optional drills", "Optional: JBoss EAP 8 security migration and a shared-library blast-radius plan."),
    ("ai", "ai", "AI Integration", "AI integration fundamentals", "The shared AI Integration page applied to migration agents: tool scoping and approval gates, and prompt caching in a headless CI agent."),
]


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load_cards() -> list[dict]:
    cards = []
    for p in sorted((TRACK / "exercises").glob("*/card.json")):
        try:
            c = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"skipping {p}: {e}", file=sys.stderr)
            continue
        c["_dir"] = p.parent.name
        cards.append(c)
    return cards


def week_key(c: dict) -> str:
    w = c.get("week")
    if w == "ai" or c["_dir"].startswith("ai-"):
        return "ai"
    if c["_dir"].startswith("x-"):
        return "w7"
    return f"w{int(w)}"


def sort_key(c: dict):
    ex = c["_dir"]
    kind = {"c": 0, "t": 1}.get(ex.split("-")[1][0], 2) if "-" in ex else 2
    return (ex.split("-")[0], kind, ex)


def practice_href(h: str) -> str:
    h = str(h)
    if h == "ai" or h.startswith("week") or h in ("interview", "resources", "overview"):
        return h
    return "week" + h


def card_html(c: dict) -> str:
    ex = c["_dir"]
    typ = c["type"]
    tag_cls = {"coding": "coding", "troubleshooting": "troubleshooting", "design": "design"}.get(typ, "coding")
    optional = c.get("optional") or ex.startswith("x-")
    opt = '<span class="tag opt">optional</span>' if optional else ""
    tasks = "".join(f"<li>{esc(t)}</li>" for t in c.get("task", []))
    acc = "".join(f"<li>{esc(t)}</li>" for t in c.get("acceptance", []))
    prac = "".join(
        f'<li><a href="{GUIDE}#{esc(practice_href(p["href"]))}">{esc(p["label"])}</a></li>'
        for p in c.get("practices", [])
    )
    if typ == "design":
        cmds = f"""cd modernize/exercises/{ex}
make setup      # nothing to install; read inputs/
# write the documents the README names, and ANSWER.md
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code:
/grade modernize/{ex}
make clean"""
    else:
        setup_note = "toolchain + evidence bundle" if typ == "troubleshooting" else "toolchain (Maven/NuGet/venv, once)"
        cmds = f"""cd modernize/exercises/{ex}
make setup      # {setup_note}
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code:
/grade modernize/{ex}
make clean"""
    return f"""
  <div class="card ex" data-ex="modernize/{esc(ex)}" id="ex-{esc(ex)}">
    <div class="exhead">
      <h3>{esc(c['title'])}</h3>
      <span class="tag {tag_cls}">{esc(typ)}</span>{opt}
      <span class="est">{esc(c['estimate'])}</span>
      <span class="badge" data-badge="modernize/{esc(ex)}"></span>
    </div>
    <p class="meta"><code>modernize/{esc(ex)}</code> &middot; {esc(c.get('area', ''))}</p>
    <p><b>Scenario.</b> {esc(c['scenario'])}</p>
    <div class="cols">
      <div><h4>Task</h4><ul class="plain">{tasks}</ul></div>
      <div><h4>Acceptance criteria</h4><ul class="plain">{acc}</ul></div>
    </div>
    <div class="cols">
      <div><h4>Run it</h4>
<pre>{esc(cmds)}</pre>
        <p class="small">Folder: <code>modernize/exercises/{esc(ex)}/</code> &middot; <a href="exercises/{esc(ex)}/README.md">README</a> &middot; <a href="exercises/{esc(ex)}/ANSWER.md">ANSWER.md</a>{' &middot; <a href="exercises/' + esc(ex) + '/DESIGN.md">DESIGN.md</a>' if typ == 'design' and (TRACK / 'exercises' / ex / 'DESIGN.md').exists() else ''}</p>
      </div>
      <div><h4>Practices (study plan)</h4><ul class="links">{prac}</ul></div>
    </div>
  </div>"""


def load_questions() -> list[dict]:
    weekly: list[dict] = []
    for p in sorted((ENV / "quiz").glob("weekly-*.json")):
        weekly.extend(json.loads(p.read_text())["questions"])
    return weekly


def check_questions(weekly: list[dict]) -> list[str]:
    errs = []
    keys = {k for k, _ in AREAS}
    weeks = {"1", "2", "3", "4", "5", "6", "7", "ai"}
    seen = set()
    for q in weekly:
        qid = q.get("id")
        if qid in seen:
            errs.append(f"duplicate id {qid}")
        seen.add(qid)
        if q.get("area") not in keys:
            errs.append(f"{qid}: unknown area {q.get('area')}")
        if str(q.get("week")) not in weeks:
            errs.append(f"{qid}: unknown week {q.get('week')}")
        n = len(q.get("options", []))
        if not q.get("answer") or any(not (0 <= a < n) for a in q["answer"]):
            errs.append(f"{qid}: answer out of range")
        if q.get("type") not in ("single", "multi"):
            errs.append(f"{qid}: bad type")
        if q.get("type") == "single" and len(q["answer"]) != 1:
            errs.append(f"{qid}: single with {len(q['answer'])} answers")
        if q.get("type") == "multi" and len(q["answer"]) < 2:
            errs.append(f"{qid}: multi with fewer than 2 answers")
        if not q.get("explanation"):
            errs.append(f"{qid}: no explanation")
    return errs


def main() -> int:
    cards = sorted(load_cards(), key=sort_key)
    weekly = load_questions()
    errs = check_questions(weekly)
    if errs:
        print("question bank problems:\n  " + "\n  ".join(errs[:40]), file=sys.stderr)
        return 1
    by_week: dict[str, list[dict]] = {}
    for c in cards:
        by_week.setdefault(week_key(c), []).append(c)

    css = (ENV / "workbook.css").read_text()
    js = (ENV / "workbook.js").read_text()

    counts: dict[str, int] = {}
    for q in weekly:
        counts[str(q["week"])] = counts.get(str(q["week"]), 0) + 1
    count_txt = ", ".join(
        (f"week {w}: {counts[w]}" if w != "ai" else f"AI page: {counts[w]}")
        for w in sorted(counts, key=lambda x: (x == "ai", int(x) if x != "ai" else 0))
    )
    rows = []
    for wk in WEEKS:
        for c in by_week.get(wk[0], []):
            optional = c.get("optional") or c["_dir"].startswith("x-")
            rows.append(
                f'<tr><td><a href="#ex-{esc(c["_dir"])}">modernize/{esc(c["_dir"])}</a></td><td>{esc(c["title"])}</td><td>{esc(c["type"])}{" (optional)" if optional else ""}</td>'
                f'<td>{esc(wk[2])}</td><td>{esc(c["estimate"])}</td><td><span class="badge" data-badge="modernize/{esc(c["_dir"])}"></span></td></tr>'
            )
    n_code = sum(1 for c in cards if c["type"] == "coding")
    n_ts = sum(1 for c in cards if c["type"] == "troubleshooting")
    n_des = sum(1 for c in cards if c["type"] == "design")

    sections = []
    for key, anchor, title, theme, lede in WEEKS:
        ex_cards = by_week.get(key, [])
        if not ex_cards:
            continue
        sections.append(f"""
<section class="page" id="{key}" data-title="{esc(title)}">
  <h2>{esc(title)} - {esc(theme)}</h2>
  <p class="lede">{esc(lede)} Study plan: <a href="{GUIDE}#{anchor}">{esc(title)}</a>.</p>
  <div class="progress"><div id="bar-{key}"></div></div>
  {''.join(card_html(c) for c in ex_cards)}
</section>""")

    data = {"areas": [{"key": k, "name": n} for k, n in AREAS], "weekly": weekly, "mocks": {}}
    data_js = json.dumps(data, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")
    title = "Modernization workbook - Lead AI Engineer, application modernization"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<script src="../grades/grades.js"></script>
{css.replace("</style>", "  .tag.design {{ color: var(--done); background: var(--done-soft); }}\n</style>")}
</head>
<body>
<header>
  <button class="themebtn" id="themebtn" type="button">light / dark</button>
  <h1>{esc(title)}</h1>
  <p>Exercises and self-exams for the <a href="{GUIDE}">Lead AI Engineer (application modernization) study plan</a>. Scores update after /grade; reload the page.</p>
</header>
<nav><div class="inner" id="tabs"></div></nav>
<main>

<section class="page" id="overview" data-title="Overview">
  <h2>Modernization workbook</h2>
  <p class="lede">Hands-on coding, troubleshooting and design exercises set in ClaimDesk, the Java monolith of
  Corvane Mutual Insurance (fictional), and its .NET agent portal: JDK and Jakarta upgrades, dependency remediation,
  reverse engineering into specs, LDAP to OIDC, characterization tests, supply chain, pod leadership and guarded
  migration agents. One tab per study week, plus weekly self-exams. Everything grades locally and offline.</p>
  <div class="progress"><div id="bar-all"></div></div>
  <p class="note"><b>Scores update after /grade; reload the page.</b> Grades come from <code>../grades/grades.js</code>, written by
  <code>tools/update_grades.py</code> when you run <code>/grade modernize/&lt;id&gt;</code> in Claude Code from the <code>workbooks/</code> folder.
  Quiz answers save in this browser (localStorage key <code>wb-modernize-v1</code>).</p>
  <div class="grid2">
    <div class="card"><h3>How to work an exercise</h3><ol>
      <li><code>tools/doctor.sh modernize</code> once: JDK 21 + Maven, the dotnet SDK, python3 + uv, jq. <code>make deps</code> in <code>modernize/</code> fills the caches.</li>
      <li>Open the week tab, read the card, then the folder README.</li>
      <li><code>cd modernize/exercises/&lt;id&gt; &amp;&amp; make setup</code> (downloads Maven, NuGet or Python packages once, so grading runs offline), solve it, <code>make test</code>, fill in <code>ANSWER.md</code>.</li>
      <li>From <code>workbooks/</code>: <code>/grade modernize/&lt;id&gt;</code>. Reload this page.</li>
      <li><code>make clean</code>. Retry as often as you like; every attempt is kept.</li>
    </ol><p class="small">Do not open <code>.grading/</code> before you submit. Pass mark 70/100. Troubleshooting is graded mostly on root cause and evidence; design exercises are graded by rubric only (the grader reports 0/0 tests and the automated row does not apply).</p></div>
    <div class="card"><h3>How the local stand-ins work</h3><ul class="plain">
      <li>Java exercises build with JDK 21 and Maven, run JUnit 5, and grade offline (<code>mvn -o</code>) from the <code>~/.m2</code> cache that <code>make setup</code> fills.</li>
      <li>Identity: an embedded UnboundID LDAP server loaded from an LDIF snapshot, and a local token issuer with its own RSA keys and JWKS in place of Okta. No tenant, no network.</li>
      <li>Servlet migration runs on embedded Tomcat (9 for javax, 10.1 for jakarta), driven by HTTP characterization tests.</li>
      <li>.NET runs on the dotnet 10 SDK with xunit, restoring offline from the NuGet cache.</li>
      <li>Python exercises (spec checkers, scanners, CI guards, agents) run pytest in <code>modernize/.venv</code>.</li>
      <li>Agents use scripted model clients that replay Messages-API-shaped responses, and a fake prompt-cache API that does the cache accounting. No API key.</li>
      <li>Troubleshooting exercises ship or generate evidence bundles: logs, transcripts, SBOMs, scanner output, mainframe reports.</li>
    </ul></div>
  </div>
  <h3>Self-exam</h3>
  <ul class="plain"><li>Weekly sets ({len(weekly)} questions): {esc(count_txt)}.</li></ul>
  <h3>All exercises ({len(cards)}: {n_code} coding, {n_ts} troubleshooting, {n_des} design)</h3>
  <table><tr><th>Id</th><th>Title</th><th>Type</th><th>Week</th><th>Estimate</th><th>Grade</th></tr>{''.join(rows)}</table>
</section>
{''.join(sections)}
<section class="page" id="selfexam" data-title="Self-exam">
  <h2>Self-exam</h2>
  <p class="lede">Scenario questions per study week. Check each answer to see the explanation and a link to learn more.</p>
  <div class="subnav" id="se-nav"></div>
  <div id="se-root"></div>
</section>

<section class="page" id="scoreboard" data-title="Scoreboard">
  <h2>Scoreboard</h2>
  <p class="lede">Exercise scores come from <code>../grades/grades.js</code> (reload after <code>/grade</code>); quiz scores from this browser.</p>
  <p class="card" id="sb-overall"></p>
  <h3>Exercises</h3>
  <table><thead><tr><th>Exercise</th><th>Title</th><th>Type</th><th>Latest</th><th>Best</th><th>Status</th><th>Attempts</th><th>Feedback</th></tr></thead><tbody id="sb-ex"></tbody></table>
  <h3>Weekly quizzes</h3>
  <table><thead><tr><th>Set</th><th>Correct / checked</th><th>Checked / total</th><th>%</th></tr></thead><tbody id="sb-quiz"></tbody></table>
</section>
</main>
<script>window.MODERNIZE_DATA = {data_js};</script>
<script>
{js}</script>
</body>
</html>
"""
    out = TRACK / "workbook.html"
    out.write_text(page)
    bad = [i for i, ch in enumerate(page) if ord(ch) > 127]
    missing = [e for e in ("ai-t1", "x-1") if not (TRACK / "exercises" / e / "card.json").exists()]
    print(f"wrote {out} ({len(page)} bytes): {len(cards)} exercises, {len(weekly)} weekly questions"
          + (f"; cards not yet present: {', '.join(missing)}" if missing else "")
          + (f"; NON-ASCII at {bad[:5]}" if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
