# ANSWER: javaai/w3-c1 Quiz generation with structured output

## Approach

Schema for shape (OBJECT with an items ARRAY, 4 options, INTEGER answerIndex, all fields required),
validator for meaning (count, distinct options, index range, grounding in a real section, no
giveaway, unique stems), and one bounded loop with separate budgets for answered calls and 429s.
Tested backoff with the fake sleeper and clock.

## Fix

QuizSchema, QuizValidator and QuizGenerator implemented; corrective retries append numbered problems
to the original prompt; SAFETY/RECITATION return Blocked; full-jitter backoff with Retry-After as a
floor; deadline checked before every sleep; usage and cost summed. 17/17 tests pass.

## Trade-offs / what I would do in production

The schema does not express grounding or giveaways and does not survive truncation, so validation
stays. Blocked maps to a 422 with an author-facing message and a per-category metric; Failed maps
to 503 with Retry-After. Each retry pays the full input again, so 3 attempts is the cap. For the
09:00 peak consider Provisioned Throughput, pin the model version, and log tokens and cost per request.
