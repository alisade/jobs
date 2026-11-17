# ANSWER: audit/ai-t1 Gemini cost up after the prompt refactor

## Approach

<!-- How you investigated: which numbers in the usage logs, how you compared requests. -->

## Root cause

<!-- The actual cause, with evidence (usage excerpts, the first bytes where two requests differ,
two processes compared). Is the model bump involved? -->

## Fix

<!-- What you changed in prompt.py and how you verified it (make replay dashboard, tests). -->

## Trade-offs / what I would do in production

<!-- Implicit vs explicit context caching, where the run metadata goes instead, a regression test or
alarm on cached_content_token_count, cost per control in the eval report. -->
