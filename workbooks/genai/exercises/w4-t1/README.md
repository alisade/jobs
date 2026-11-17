# genai/w4-t1 - The assistant offers a 20 percent promo code that does not exist

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (guardrails, grounding
checks, indirect prompt injection, the "lethal trifecta"); Week 3 (grounding product answers on tool
results)

## Symptom

Customers say Kestrel Outfitters' website assistant told them code SPRING20 takes 20 percent off the
Ridgeline 2P tent. Checkout rejects it, stores are honoring the price, and legal is asking questions. The
output grounding check that should block invented promotions logged `grounded=True`. The product team
wants to roll back the model upgrade. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the escalation and the thread |
| `evidence/transcripts.jsonl` | the conversations, with model snapshot and timestamps |
| `evidence/tool-calls.log` | the search_products results the model saw |
| `evidence/grounding.log` | the grounding check's verdict per conversation |
| `evidence/moderation-export.csv` | review moderation decisions |
| `evidence/release-notes.md` | the last three assistant releases |
| `assistant/catalog.py` | catalog, promotions and reviews (local stand-in: do not edit) |
| `assistant/prompting.py` | how tool results are written into the model's context |
| `assistant/grounding.py` | the output grounding check |
| `assistant/pipeline.py` | one assistant turn; `RecordedModel` replays the production model outputs |
| `data/recorded_outputs.json` | the model outputs recorded in production for each question |

`make demo` replays every recorded question through the pipeline and shows what the customer sees.
The model outputs are fixed recordings, so your fix has to work on what the model actually said.

## Your task

1. Find the root cause and prove it with the evidence. Say where the code came from, why the grounding
   check passed it, why other answers were wrongly blocked or wrongly shown, and whether the model upgrade
   had anything to do with it.
2. Fix it in `assistant/grounding.py` and `assistant/prompting.py`. Keep the function names and
   signatures.
   - Grounding sources are trusted structured data only. Every dollar amount must equal the `price_cents`
     of a product the answer cites as `[SKU]`, or that price after an active promotion that applies to
     it. Every promo code and every percent off must be an active promotion that applies to a cited
     product. A price with no cited product is not grounded. Review text is never evidence.
   - In the prompt, keep trusted fields as data and put review text only inside
     `<untrusted_reviews sku="...">...</untrusted_reviews>` blocks that a review cannot close. The
     system prompt must tell the model how to treat that block.
   - Do not special-case SPRING20 or FREESHIP50: the next review will say something else.
3. Verify with `make demo` and `make test`.
4. Write `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- The SPRING20, FREESHIP50 and "$289.00 from a review" answers are blocked; the legitimate WINTER15
  discounted price and the HOLIDAY10 comparison are shown.
- Prices must belong to the cited product; promos must apply to the cited product; a new injection
  wording is also blocked.
- No review text outside the untrusted fence in the prompt, even when a review tries to close the fence.
- `ANSWER.md` names the mechanism with evidence and rules out the red herring.

## How to run

```bash
make setup     # shared Python venv
make demo      # what customers see for each recorded question
make prompt    # also print the prompt the model saw
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w4-t1
make clean
```
