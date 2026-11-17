# Rubric: connect/w5-c1 Lex V2 code hook for the help desk bot
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Lex contract correctness | 15 | Full: response builders per dialogAction type (required fields), intent echoed with updated slots, ElicitSlot clears the bad value, Delegate only when Lex should continue, dialog hook never fulfills. Partial: correct but ad hoc object literals everywhere, or relies on Lex defaults it cannot see. Zero: can return a response Lex rejects. |
| 3 | Handoff design | 15 | Full: one handoff builder, stable reason codes, queue names the flow can branch on, compact summary written for the analyst, slots as JSON string, incoming attributes preserved; ANSWER.md says how the flow reads $.Lex.SessionAttributes.* and copies them into contact attributes for the screen pop. Partial: contract present but inconsistent reasons or summary. |
| 4 | Robustness and security | 10 | try/catch around backends with BACKEND_ERROR handoff, no full employee ID read back, no PII beyond what the analyst needs, tolerant parsing (missing slots, null values). |
| 5 | ANSWER.md trade-offs | 10 | Full: at least three concrete items: slot obfuscation for EmployeeId in conversation logs, runtime hints / Assisted slot resolution for SystemName, keeping code hook latency low on voice, per-alias versions and Test Workbench regression sets, confidence threshold and Intent Disambiguation vs the code-hook disambiguation. Partial: generic. |
Total: 100
