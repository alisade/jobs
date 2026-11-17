# Rubric: awsfde/ai-t1 A weekly summary email went to an outside address
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: indirect prompt injection in corvid-rivermark-q4 (uploaded through the partner portal by Rivermark Freight on 2026-11-07) instructs the assistant to send the summary to ops-archive@example.net; the model follows it; share_report accepts any recipient the model chooses and the loop auto-executes write tools, so private data + untrusted content + an exfiltration channel all hold. Partial (10-15): "prompt injection" without the tool/loop side or without the document. Zero: blames the guardrail, the model or the job definition. |
| 3 | Evidence | 20 | Full: agent.log retrieval line for weekly-2026-11-10 with corvid-rivermark-q4 (absent on 10-27 and 11-03), the share_report args with the extra address, the audit CSV row, and the replay with GV=3 still leaking (and the guardrail action NONE). Partial: one source. |
| 4 | Red herring | 5 | Guardrail v4 ruled out: the 11-03 run also used no injected doc and was clean, the 11-10 leak reproduces with version 3, guardrails filter content categories, they do not authorize tool calls. |
| 5 | Fix quality | 10 | Full: recipients decided server-side: intersection of recipients approved outside the model (job definition or user confirmation) and verified tenant domains, exact domain match; refusal logged; retrieved text wrapped as untrusted data and explained as defense in depth only. Partial: domain allowlist only, or only prompt wording. Zero: a prompt instruction or a regex on the document as the fix. |
| 6 | Exposure and prevention | 10 | Full: exposure: one weekly summary (Corvid's carrier metrics: on-time by carrier, damage claims, detention, late lanes) sent to ops-archive@example.net on 2026-11-10 07:00; ask Corvid to treat it as a disclosure, find who controls example.net, remove or quarantine the document, review other partner uploads. Prevention: partner-uploaded content labelled and quarantined or separated from instructions, write tools behind confirmation, egress allowlist on the relay, alarm on refused recipients, injection cases in the eval suite (ai-c1). Partial: generic. |
Total: 100
