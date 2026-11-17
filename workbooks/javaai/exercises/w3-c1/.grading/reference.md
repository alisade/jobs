# Reference: javaai/w3-c1

Files in `.grading/solution/src/main/java/com/kestrel/quizgen/`: `QuizSchema.java`, `QuizValidator.java`, `QuizGenerator.java`.

## Design

- Schema for shape, validator for meaning. Controlled generation guarantees parseable JSON of the
  right shape when the response completes; it does not guarantee that `answerIndex` points at the
  right option, that the cited section exists, or that the stem does not give the answer away. A
  `MAX_TOKENS` finish also returns truncated JSON regardless of the schema.
- One loop, two budgets: `validityAttempts` (answered calls) and `rateLimitRetries` (429s). The
  deadline is checked before each sleep so the endpoint answers within its SLO.
- Full jitter: `jitter * min(cap, base * 2^n)`, with the server's Retry-After as a floor. Jitter
  matters because 09:00 is when every cohort's batch starts at once.
- The corrective prompt repeats the original and lists numbered problems; it costs another full
  input, which is why validity attempts are capped at 3.

## Blocked vs Failed

Blocked is a content decision: show the author "this lesson triggered a safety filter, try a
narrower section" and count it per category; do not retry. Failed is operational: 503 with
Retry-After, alert on rate.

## Interview angles

- "If the schema is enforced, why validate?" (meaning vs shape, truncation, model drift.)
- "What does a retry cost?" (input tokens again; with 5 sections of context that is most of the cost.)
- Spring AI `ChatClient` with `.entity(QuizEnvelope.class)` gives structured output plus a retry
  advisor; the Gen AI SDK gives direct control of `responseSchema`, thinking config and safety settings.
