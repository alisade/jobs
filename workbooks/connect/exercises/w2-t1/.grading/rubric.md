# Rubric: connect/w2-t1 Password-reset service level collapsed after a "copy" routing change
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several are guards that pass on the starter) |
| 2 | Root cause identified | 25 | Full: in rp-service-desk, PasswordReset carries Delay 20 copied from rp-general, where it was an overflow queue. Delay in a routing profile means agents with that profile only receive a contact after it has waited 20 s; tier 1 used to take PasswordReset at delay 0, so after the consolidation nobody can answer a password-reset call in its first 20 s. Partial (10-15): "the delay" without explaining profile delay semantics or why the copy was wrong. Zero: blames staffing, volume, priority alone, or the IVR. |
| 3 | Evidence | 20 | Full: at least two independent pieces, quoted: queue-time distribution of answered PasswordReset contacts with nothing under 20 s after the change (vs many under 10 s before), the real-time snapshot (callers waiting < 20 s while rp-service-desk agents sit Available), metrics before/after with ASA. Explains why the smoke test (one call, answered after 20 s) passed. Partial: one piece or numbers without commands. |
| 4 | Red herring handled | 10 | Rules out the Wednesday training absence: Monday, Tuesday and Friday are also below target at full staffing, the previous week at the same headcount was ~86%, and the training day still recovers to ~74% with the fix. |
| 5 | Fix quality | 5 | Delay 0 on PasswordReset in rp-service-desk; consolidation kept; no unrelated changes (priorities juggled without reason, users moved back). |
| 6 | Prevention / production | 10 | Concrete: routing changes reviewed as data (diff of priority and delay per queue per profile with intent), simulated against last week's demand before CAB, canary by moving a few agents first, alarm on SL and on "agents available while contacts in queue", post-implementation review. Partial: generic. |
Total: 100
