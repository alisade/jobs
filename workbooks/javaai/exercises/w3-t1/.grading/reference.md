# Reference: javaai/w3-t1

## Root cause

Release 2.3 (PLAT-3317, "one safety profile for all products") replaced the adult profile
(HARASSMENT, HATE_SPEECH, SEXUALLY_EXPLICIT at BLOCK_MEDIUM_AND_ABOVE, DANGEROUS_CONTENT at
BLOCK_ONLY_HIGH) with the kids profile: everything BLOCK_LOW_AND_ABOVE. University biology,
history, literature and psychology answers routinely get a LOW probability rating (pathogens,
propaganda, war poetry, substance use). Under the new thresholds Gemini returns either:

- a candidate with `finishReason: SAFETY`, `safetyRatings` with `blocked: true`, and no `content`, or
- for a prompt rated LOW (hist-220-l3, chem-101-l7): `promptFeedback.blockReason: SAFETY` and no `candidates`.

`service.generate_quiz` does `resp["candidates"][0]["content"]["parts"][0]["text"]`, raising
`KeyError: 'content'` or `KeyError: 'candidates'`; FastAPI turns it into a 500.

The Sunday errors are all chem-330-l2, rated HIGH: blocked under the old profile too, and already
a 500 because of the same handling bug. The release turned a latent bug into an incident.

## Red herring

429s: 11 on Sunday, 13 on Monday, each followed by a successful retry; no 500 follows a 429. Quota
peak was 31% of the limit. More retries would add latency and cost.

## Fix (`.grading/solution/`)

- `config/safety.yaml`: the adult profile restored; the kids profile belongs to its own service config.
- `service.py`: check `promptFeedback.blockReason`, empty `candidates`, and blocking finish reasons;
  return `{"status": "blocked", "source", "reason", "category", "message"}`; log a warning with the category.
- `app.py`: blocked results return 422.

## Follow-ups

Per-audience profiles with an owner and review; a metric of blocked responses per category with an
alert on change; a CI eval set of lessons that must not be blocked (and some that must); Model Armor
for prompt-injection and sensitive-data screening as a separate layer.
