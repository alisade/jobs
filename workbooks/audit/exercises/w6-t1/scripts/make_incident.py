"""make setup: write the incident bundle (incident/) the way the reviewer and the team handed it over."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INC = ROOT / "incident"

FILES = {
"reviewer-memo.md": """# QA review memo: CM-03 Q3 2026 sample, ControlPilot results

From: S. Lindqvist, IT audit senior (reviewer)
To: Internal audit engineering
Date: 2026-11-10

I re-performed 30 of 30 Q3 sample items by hand before sign-off. ControlPilot reported 3 exceptions.
I found 7. The four the agent marked "pass":

| Sample | Change | What I found |
|---|---|---|
| Q3-03 | CHG-105239 | approver jdoyle@meridianfreight.example is the author jdoyle (self-approval via e-mail alias) |
| Q3-11 | CHG-105343 | approver and author are the same person under two aliases |
| Q3-19 | CHG-105447 | same pattern as Q3-03, emergency change approved by its author |
| Q3-26 | CHG-105538 | deployed under pipeline run deploy-93112, which belongs to a different ticket |

The eval dashboard shown at the October steering committee said 96.7% accuracy and 100% exception
recall. Those numbers do not match what I see. Until this is explained I cannot rely on ControlPilot
for the year-end cycle.

Separately, please do not change the labels in labels/human_v1/: Raj and I signed those off in July.
""",
"dashboard-2026Q3.txt": """ControlPilot eval dashboard - CM-03            snapshot 2026-11-02 09:00 CT (posted to #audit-eng)
  golden set     labels/golden.jsonl (30 rows)
  runs           runs/2026Q3/production.jsonl (30 scored)
  accuracy       96.7%
  exc. recall    100.0% of 3
  missed         none
  cost/100       $84.0116
""",
"changelog.txt": """eval repo history (newest first)

2026-11-02  m.adeyemi   docs: post Q3 dashboard snapshot
2026-10-30  t.brandt    chore: refresh golden set for schema v2 (control_id)   [labels/golden.jsonl: 30 rows changed]
                        ran `make refresh-golden` after the loader started requiring control_id
2026-10-30  t.brandt    feat(loader): require control_id on golden rows (schema v2)
2026-10-30  ops-bot     replay: CM-03 Q3 sample with prompt v3.2 -> runs/replay-2026-10-30.jsonl
2026-10-15  m.adeyemi   prompt v3.2: tighten SoD instruction wording
2026-10-02  m.adeyemi   feat(dashboard): cost per 100 samples
2026-09-30  ops-bot     production run: CM-03 Q3 sample -> runs/2026Q3/production.jsonl
2026-07-28  s.lindqvist labels: CM-03 golden v1 signed off (labels/human_v1/cm03-golden-v1.jsonl)
2026-07-21  r.okafor    labels: first pass of CM-03 golden v1
""",
"refresh-golden.log": """$ make refresh-golden
python scripts/refresh_golden.py
refresh-golden: wrote 30 rows to labels/golden.jsonl from runs/replay-2026-10-30.jsonl
$ make dashboard
...
  accuracy       96.7%
  exc. recall    100.0% of 3
""",
"finance-note.txt": """From: finance business partner, internal audit
Re: ControlPilot run costs

The dashboard says $84 per 100 samples. Our Gemini invoice for October is $3.12 for all of
ControlPilot. Is the dashboard wrong, or are we about to get a large bill? We would like an answer
before the budget meeting, but this is not urgent for the audit sign-off.
""",
}


def main() -> None:
    INC.mkdir(exist_ok=True)
    for name, text in FILES.items():
        (INC / name).write_text(text)
    print(f"incident bundle written to {INC.relative_to(ROOT)}/ ({len(FILES)} files)")


if __name__ == "__main__":
    main()
