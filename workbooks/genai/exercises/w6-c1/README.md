# genai/w6-c1 - Catalog enrichment with validated structured output

**Type:** coding | **Estimate:** 2-2.5 hours | **Study plan:** Week 6 (retail GenAI use cases: catalog
enrichment); shared core (tool calling and structured outputs, Pydantic as the contract, evals)

## Scenario

Kestrel Outfitters onboards about 4,000 new supplier products before each season. Supplier feeds arrive as
messy free text, and merchandisers spend weeks turning them into titles, categories and attributes. The
merchandising lead wants a nightly batch that asks a model for structured attributes, publishes the ones
that check out and sends everything else to a human review queue. Last season a pilot ran with another
vendor. It published "eco-friendly" on a PVC tarp and gave a cooler 45 L when the supplier said 45 qt.
Legal now requires that every published attribute be traceable to the supplier text.

## What you have

| Path | What it is |
|---|---|
| `enrich/pipeline.py` | the batch (prototype: publishes whatever the model returns) |
| `enrich/models.py` | the output model (fields only, no constraints yet) and the category taxonomy |
| `enrich/checks.py` | deterministic grounding checks (empty) |
| `enrich/llm.py` | model client interface and the scripted fake, with token prices (complete) |
| `enrich/store.py` | per-item outcome store for idempotent re-runs (complete) |
| `data/feed.jsonl`, `data/recorded-answers.json` | a sample feed and recorded model answers for `make run` |
| `tests/` | visible tests and the fixtures they use |

## Output contract

`EnrichedAttributes`: `title` 1-80 chars; `category` one of `TAXONOMY`; `material`, `color`, `care`
optional strings; `weight_kg`, `capacity_l` optional and > 0; `description` 1-400 chars; `confidence`
0-1. Unknown fields are invalid.

## Your task

1. **Validate.** Enforce the contract in `models.py`. When the model's answer is not valid JSON or fails
   validation, retry once with the validation error in the prompt (`build_prompt(item, feedback)`).
   After two failed attempts the item goes to review with reason `invalid_output`.
2. **Check grounding** in `checks.py` (`review_reasons`), returning reason strings:
   - `unsupported:material`, `unsupported:color` when the value does not appear in the supplier text;
   - `unsupported:weight_kg`, `unsupported:capacity_l` when no quantity in the text matches within
     2 percent after unit conversion (kg, g, lb, oz; L, ml, qt, gal);
   - `banned_claim:<term>` for any `BANNED_CLAIMS` term in title, description or care, always;
   - `unsupported_claim:waterproof` when the output says waterproof and the supplier text does not;
   - `low_confidence` below `MIN_CONFIDENCE`.
   Any reason sends the item to review with all its reasons; otherwise it is published.
3. **Idempotency.** Key each item by supplier SKU plus `source_hash(description)` in the store. An
   unchanged item is never sent to the model again, whether it was published or sent to review. A
   changed description is processed again.
4. **Cost cap.** Before each model call, stop if the batch has already spent `cost_cap_usd`. Set
   `budget_exhausted`, and list the item being processed and every remaining item in `skipped`, in order.
5. `write_jsonl` keeps input order. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Retry carries the validation error; at most two model calls per item.
- Invented materials, colors, weights and capacities are caught; correct unit conversions pass.
- Banned and unsupported claims, and low confidence, go to review with the right reasons.
- A re-run of an unchanged feed makes zero model calls and gives the same result.
- The cost cap stops the batch and reports skipped items.

## How to run

```bash
make setup     # shared Python venv
make run       # sample feed with recorded answers (run it twice: the second run should be free)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w6-c1
make clean
```
