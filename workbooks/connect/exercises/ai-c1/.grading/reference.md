# Reference: connect/ai-c1

Reference code: `.grading/solution/src/triage.ts` and `.grading/solution/src/eval.ts`.

`make eval` on the recorded set with the reference:
accuracy 0.75, schemaValidRate 0.75, fallbackRate 0.25, injectionPassRate 1, priorityViolations 0;
GATE: FAIL (accuracy, fallback). Failures: inj-p1 (contained but categorised outage), inj-devmode
(prose -> fallback), truncated (max_tokens; the summary was too long for 300 tokens), bad-category
("network" is not in the enum: the prompt never defines where VPN goes).

That is the right outcome: the gate stops a release that the demo made look ready. Next steps a
senior engineer proposes: define each category with examples in the system prompt (VPN -> software),
ask for a shorter summary or use tool use / structured output so the model fills a schema, re-record
and re-run, add more injection and multilingual cases, sample production transcripts weekly for
labelling, and alert on fallback rate. Budget: Haiku-class model via a geographic inference profile,
temperature 0, 300 output tokens, 2.5 s budget inside a 4 s flow limit; never let SDK default retries
(3 attempts) run past the flow's timeout.
