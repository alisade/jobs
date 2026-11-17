# Rubric: backend/ai-t1 The assistant showed another business unit's pipeline
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: authorization derived from a model-controlled `tenant_id` argument (confused deputy) while the session was correctly scoped; the prompt injection in act-1002 is the trigger, not the cause. Partial: "prompt injection" as the cause with a vague fix. Zero: blames the model or the token. |
| 3 | Evidence | 15 | Quotes the session-open line (tenant=bu-amer, verified), the tools/call line with tenant_id=bu-emea, the injected note and transcript turn 3, the code line using args.get("tenant_id"), and the thin audit rows. |
| 4 | Assessment of the proposed fix | 10 | Explains why system prompt, temperature and keyword stripping are not controls; enforcement must be server-side. |
| 5 | Fix quality | 10 | Identity only from the session, closed schemas, not-found for foreign ids, untrusted marking, bounded limit, complete audit including denials. |
| 6 | Production follow-up | 5 | RLS under the tools, injection evals, cross-BU access as a token role, incident communication. |
Total: 100
