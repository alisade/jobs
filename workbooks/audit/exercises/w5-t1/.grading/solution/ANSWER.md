# ANSWER: audit/w5-t1 An exception closed overnight "per system note"

## Approach

Started from the trace: `close_exception EXC-2026-0412 "pre-approved by CAB per system note"` executed
by svc-controlpilot, then `update_workpaper CHG-104233 pass`. Searched the evidence for "system note"
and found it on page 3 of the approval request, then read the config and agent code to see how it
reached the model and why the call could execute.

## Root cause

Indirect prompt injection through an evidence file, made harmful by tool scoping. Page 3, paragraph 5
of evidence/CHG-104233/approval-request.layout.json is white-on-white text (style color and
backgroundColor #FFFFFF over its span) telling the agent to call close_exception and to hide the note.
agent.py concatenates all evidence text into the agent instruction, and release 2026.10.2
(config/evidence_reviewer.yaml, release notes) gave the evidence agent close_exception and
update_workpaper, which write to GRC Hub with no human gate. Untrusted content plus write capability
on a system of record: the integrity half of the lethal trifecta. The page 2 OCR warning concerns the
scanned signature block and is unrelated.

## Fix

Evidence agent is read-only (config and a code guard in build_agent); evidence passed as delimited
data in the user message; deterministic screening flags hidden and instruction-like text; tool calls
outside the agent's tools are flagged; closing an exception only via gate.close_exception with an
authorized reviewer who is not the preparer. Verified with a model that always calls close_exception:
both exceptions stay open, attempts are traced and flagged, make run leaves EXC-2026-0412 open.

## Trade-offs / what I would do in production

Re-open EXC-2026-0412 through the gate with a reviewer note and restore the workpaper; review every
svc-controlpilot change since 2026-10-02; screen evidence at ingest; treat agent tool permissions as
CM-03 program changes; inform the audit manager and the external auditor.
