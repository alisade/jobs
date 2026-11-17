# edgefde/w6-c1 - Engagement brief, decision record and handoff plan

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 6 (Mon: framing and measurable outcomes; Thu: customer-owned assets and handoff)

## Scenario

Tessellate Edge (fictional) has sold Corvane Industrial (fictional) an 8-week pilot. The plant
manager's ask is "AI on the pumps"; the reliability lead wants fewer surprise bearing failures; the
controls engineer was burned by a vendor box that alarmed twenty times a week; security will not let
raw data leave the site; the planner wants work orders to go through the queue. You have the kickoff
notes, an email thread and the site constraints. Before any code, you write the one-page-plus brief
that everyone signs: what problem, what it costs today, what "working" means as a number, what is out
of scope, the first thin slice, the architecture decision, and what the client owns at the end.

## What you have

| Path | What it is |
|---|---|
| `inputs/kickoff-notes.md` | who said what, the numbers they gave |
| `inputs/email-thread.md` | conflicting expectations after the call |
| `inputs/site-constraints.md` | network, data, change control, support |
| `BRIEF.md` | the template you fill in |
| `ANSWER.md` | short summary of your key decisions |

## Your task

Fill in every section of `BRIEF.md`, using the numbers in `inputs/` (show the arithmetic for the
baseline cost), and write `ANSWER.md`.

## Acceptance criteria (graded by rubric, no automated tests)

- The problem is framed as unplanned bearing failures on named pumps with a cost, not as "AI".
- Baseline and target metrics are numbers with a measurement method and an owner; false alarms are a
  first-class metric.
- Scope is cut with reasons (seals, motors, energy, chatbot, all ten pumps by January).
- The design honours every constraint (raw data on site, no PLC writes, change windows, proxy).
- A thin slice that is end to end and measured by week 2; an ADR with real options and trade-offs.
- Handoff assets have client-side owners; the stakeholders' conflicting asks are addressed directly.

## How to run

```bash
make test      # completeness report: which sections are still empty
# then from workbooks/ in Claude Code: /grade edgefde/w6-c1
```

## What to submit

`BRIEF.md` and `ANSWER.md`.
