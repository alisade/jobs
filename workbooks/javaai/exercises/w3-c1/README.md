# javaai/w3-c1 - Quiz generation with Gemini structured output: validate, retry, back off

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Mon: structured output; Tue: quotas and 429s; Wed: safety; Thu: cost); shared core section 3 (tool calling and structured outputs)

## Scenario

Kestrel Learning's Spring Boot API has a `/quiz/generate` endpoint that asks Gemini on Vertex AI
(Gemini Enterprise Agent Platform) for multiple-choice items about one lesson. The hackathon
version (`QuizGenerator`) calls the model once with plain text mode, trusts whatever comes back,
and lets a 429 escape as a 500. In the pilot it produced items with 3 options, an `answerIndex` of 4,
explanations citing sections that do not exist, stems that contained the answer, and an outage
when Standard PayGo capacity was tight at 09:00.

You turn it into the production version. The Gemini client is behind an interface (in production
the Google Gen AI Java SDK; in tests a scripted fake), and time is injected so backoff is testable.

## What you have

| Path | What it is |
|---|---|
| `src/main/java/com/kestrel/quizgen/Model.java` | request/response types, `GeminiClient`, `Sleeper`, `RateLimitedException` (do not change) |
| `QuizSchema.java` | the response schema (TODO) |
| `QuizValidator.java` | business validation (TODO) |
| `QuizGenerator.java` | the generation loop (TODO) |
| `QuizGenConfig.java`, `Prompts.java`, `GenerationResult.java`, `QuizItem.java` | config, prompts, result types |
| `src/test/java/.../FakeGemini.java`, `Fixtures.java` | scripted fake model, fake clock/sleeper, sample lesson |

## Requirements

1. **Request** - `responseMimeType` `application/json`, `responseSchema` = `QuizSchema.schema()`, the
   configured (pinned) model, `temperature` and `maxOutputTokens` from `QuizGenConfig`.
2. **Schema** - `{"items": [ {stem, options, answerIndex, explanation, sectionId} ]}` with every
   field required, `options` an array of exactly 4 strings (`minItems`/`maxItems` 4), `answerIndex`
   an integer. Types in Gemini's schema style (`OBJECT`, `ARRAY`, `STRING`, `INTEGER`).
3. **Validation rules** (`QuizValidator`, specific messages; never throw):
   exactly `expectedCount` items; 4 options, none blank, distinct after trim/ignore case ("duplicate");
   `answerIndex` in range ("answerIndex"); stem and explanation not blank; `sectionId` is a section of the
   lesson ("sectionId"); no two stems the same ignoring case ("duplicate"); the stem must not contain the
   correct option's text (a giveaway).
4. **Corrective retry** - invalid JSON, validation problems or `MAX_TOKENS`: call again with the
   original prompt plus the list of problems. At most `maxValidityAttempts` (3) answered calls, then
   `Failed` with the last problems.
5. **Safety** - finish reason `SAFETY` or `RECITATION`: `Blocked`, no retry.
6. **429** - retry up to `maxRateLimitRetries` (4) with full-jitter exponential backoff:
   `delay = jitter() * min(maxBackoff, baseBackoff * 2^n)` for retry n = 0, 1, ...; a `retryAfter` from
   the server is a floor. Rate-limited calls do not use up validity attempts. Out of retries: `Failed`
   mentioning the rate limit.
7. **Deadline** - never sleep past `deadline` (20 s) from the start: return `Failed` mentioning the deadline.
8. **Usage** - sum input and output tokens of every answered call; cost = tokens x price / 1M.
   `modelCalls` counts every call, 429s included. No exceptions escape `generate`.

## Acceptance criteria (what the grader checks)

- Hidden JUnit tests for each requirement: request fields, schema shape, every validation rule,
  corrective retry content, MAX_TOKENS, give-up after 3, SAFETY not retried, exact backoff sleeps,
  Retry-After floor, deadline, summed usage and cost.
- `ANSWER.md`: why you still validate when the schema is enforced, what you would put in the
  endpoint's response for `Blocked` vs `Failed`, and the retry budget's effect on cost and p95.

## How to run

```bash
make setup     # JDK 21 + Maven, downloads Jackson and JUnit once
make test
# fill in ANSWER.md, then from workbooks/: /grade javaai/w3-c1
make clean
```

No network, no Google Cloud credentials: the model is a scripted fake.
