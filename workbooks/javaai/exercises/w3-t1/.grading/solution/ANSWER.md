# ANSWER: javaai/w3-t1 Generate quiz fails for some lessons

## Approach

Compared Sunday and Monday logs: Monday's 500s are all KeyError tracebacks in service.py line 58,
grouped by subject (bio-210, hist-220, lit-210, psych-101, chem). Read the 2.3 diff, then replayed
bio-210-l4 locally and printed the raw response.

## Root cause

Release 2.3 set every safety category to BLOCK_LOW_AND_ABOVE (kids profile). LOW-rated answers on
ordinary university topics are now blocked: the candidate has finishReason SAFETY,
safetyRatings [{HARM_CATEGORY_DANGEROUS_CONTENT, LOW, blocked: true}] and no content; for blocked
prompts there are no candidates, only promptFeedback.blockReason SAFETY. The code indexes
candidates[0].content.parts[0].text, raises KeyError ('content' / 'candidates'), and FastAPI
returns 500. Sunday's 6 errors are all chem-330-l2 (HIGH), blocked under the old profile as well:
the handling bug was already there.
Not the quota: 429s on both days (11 vs 13), each retried successfully, usage peaked at 31%.

## Fix

Restored the adult thresholds (MEDIUM_AND_ABOVE, DANGEROUS_CONTENT ONLY_HIGH). service.py returns
a typed blocked result (source, reason, category, message) for promptFeedback blocks, empty
candidates and blocking finish reasons; app.py maps it to 422. Verified: all lessons 200 or 422,
the six ordinary lessons 200, chem-330-l2 422; 26/26 tests.

## Trade-offs / what I would do in production

Separate safety profiles per product with an owner; blocked-rate metric per category; a CI eval
of must-not-block lessons; Model Armor as a separate screening layer; safety config changes through review.
