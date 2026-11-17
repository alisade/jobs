# javaai/w6-c1 - Tune or prompt? Build the tuning set and pick a model with numbers

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Mon: when to tune; Tue: supervised tuning data; Wed: evaluating candidates)

## Scenario

Kestrel's quiz generator runs on Gemini 2.5 Flash with a long prompt. Course Ops wrote 309 quiz
items in the house style and asked "can we tune a cheaper model on these?" A teammate ran three
candidates on a 50-item held-out set and recorded the outputs, tokens and latency:

- `prompt-flash`: Flash, instructions only
- `fewshot-flash`: Flash with 5 examples in the prompt
- `tuned-flashlite`: Flash-Lite after supervised tuning on an earlier draft of the data

You build the tuning dataset properly (format, duplicates, leakage, a deterministic split) and the
comparison that decides what ships. No cloud calls: everything is recorded.

## What you have

| Path | What it is |
|---|---|
| `data/authored.jsonl` | 309 authored records (lesson, section text, item) |
| `data/heldout.jsonl` | 50 held-out records with the expected `answer` text and `sectionId` |
| `data/candidates/*.jsonl` | raw outputs per candidate with tokens and latency; `models.json` maps candidate to base model |
| `data/prices.json` | illustrative USD per 1M tokens |
| `tuneval/tuning.py` | `to_example`, `build_dataset` (TODO) |
| `tuneval/evaluate.py` | `parse_item`, `percentile`, `score`, `pick` (TODO); `make run` prints the comparison |

## Requirements

The docstrings carry the exact rules. In short:

1. `to_example`: Gemini supervised tuning JSONL format (systemInstruction, user turn with the
   prompt, model turn with the item as compact JSON).
2. `build_dataset`: drop duplicate stems (normalized), drop anything that leaks held-out content,
   split by a hash of the id (10% validation), return a report of counts.
3. `parse_item`: strict schema check (4 non-empty options, integer answerIndex 0-3, not a bool, all fields).
4. `score`: format validity, correctness against the key text, grounding (cited section), cost per
   1,000 items (invalid outputs cost too), p50/p95 latency by nearest rank.
5. `pick`: the cheapest candidate meeting `min_valid` and `min_correct`, else None.

## Acceptance criteria (what the grader checks)

- Tuning example format; dataset counts (duplicates, leakage, train, validation); order-independent split.
- `parse_item` rejects nine kinds of bad output; percentile on hand cases.
- `score` matches the reference numbers for all three candidates; `pick` for three threshold settings.
- `ANSWER.md`: which candidate you would ship and why, what the numbers cannot tell you (50 items,
  the tuned model saw an earlier data draft), and when tuning is the wrong tool (fresh knowledge: use RAG).

## How to run

```bash
make setup
make test
make run       # comparison table and pick
# fill in ANSWER.md, then from workbooks/: /grade javaai/w6-c1
make clean
```
