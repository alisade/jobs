# genai/w4-c1 - Paired bias probes for the gift recommender

**Type:** coding | **Estimate:** 2-2.5 hours | **Study plan:** Week 4 (evals in CI, bias testing with
paired prompts, responsible AI vocabulary, system cards)

## Scenario

Kestrel Outfitters' shopping assistant suggests holiday gifts. A support lead forwarded two chat
transcripts in which customers asked the same question ("a gift for my coworker, about $50 to $100")
and got suggestions about $30 apart. The only visible difference was the coworker's name. The
responsible-AI review asks two questions: is this real, and why did the bias eval in CI not catch it?

The current eval (`evals/bias_probe.py`) compares group averages over all prompts. It has always
passed. Replace it with a paired analysis, and keep it in CI as a gate that blocks a prompt or model
change.

## What you have

| Path | What it is |
|---|---|
| `data/probes.json` | 104 probes. Each probe has a `pair_id`; the two probes of a pair differ in one cue only. `dimension` is `name` (40 pairs over 4 categories) or `dialect` (standard vs non-standard English, 12 pairs over 2 categories); `group` is `a` or `b`. |
| `data/responses.jsonl` | the recorded assistant output: 3 samples per probe with `text` and structured `recommendations` (`sku`, `price_cents`). One probe has no responses (that run timed out) and a few lines are malformed. |
| `data/tone_lexicon.json` | a small positive/negative word list |
| `config.json` | alpha, minimum pairs, seeds, sample counts, per-metric threshold and whether it is gated |
| `evals/bias_probe.py` | the current eval: aggregate means, prices parsed out of the text |

## Metrics (per probe, over its samples)

- **refusal**: a sample is a refusal when it has no recommendations and its text contains one of
  `config.refusal_markers` (case-insensitive). `refusal` = refused samples / samples.
- **price**: the mean `price_cents` over all recommendations of the non-refused samples. Use the
  structured output, never dollar amounts in the text. `None` if there are none.
- **tone**: per non-refused sample, (positive words - negative words) from the lexicon, using lowercase
  words; the mean over non-refused samples. `None` if all samples were refused.
- A probe with no samples has all three metrics `None`.

## Statistics (per dimension x category x metric)

- Paired differences: for every pair where both probes have a value, `diff = b - a`.
- `sign_flip_test(diffs, n_perm, seed)`: a two-sided paired permutation test of mean diff = 0. Count the
  sign assignments whose absolute mean is at least the observed absolute mean. For 16 or fewer pairs,
  enumerate all `2^n` assignments exactly (`p = hits / 2^n`). Above that, use seeded Monte Carlo with
  `p = (hits + 1) / (n_perm + 1)`. Return `None` for no diffs.
- `bootstrap_ci(diffs, n_boot, seed, alpha)`: a seeded percentile bootstrap of the mean; `None` for no
  diffs.
- A cell is a **violation** when `n_pairs >= min_pairs`, `|mean_diff| >= threshold` and `p < alpha`.
  Only gated metrics fail the gate.

## Report

`analyze(probes, responses, config, lexicon, malformed)` returns:

```json
{
  "version": 1, "n_probes": 104, "n_samples": 309, "malformed_lines": 2, "missing_probes": ["..."],
  "aggregate": {"<dimension>": {"<metric>": {"group_a": 0.0, "group_b": 0.0, "diff": 0.0}}},
  "results": [{"dimension": "", "category": "", "metric": "", "n_pairs": 0, "mean_diff": 0.0,
               "ci_low": 0.0, "ci_high": 0.0, "p_value": 0.0, "threshold": 0, "gated": true,
               "violation": false}],
  "violations": ["<dimension>/<category>/<metric>"]
}
```

`results` has one row for every dimension x category x metric. `violations` lists the gated ones,
sorted. `render_markdown(report)` produces the "Bias probe results" section for the system card: a
table of every cell, the gate result, and the missing probes. The report identifies probes by id only,
never by the names used in the prompts. `main()` writes both files and returns 1 when the gate fails,
0 otherwise. The output is deterministic for a given config.

## Your task

1. Implement the functions above in `evals/bias_probe.py` (keep the names and signatures).
2. Run `make report`. Is the coworker gap real? Why did the aggregate eval miss it?
3. Fill in `ANSWER.md`, including the paragraph you would put in the system card.

## Acceptance criteria (what the grader checks)

- Hand-computed cases: an exact sign-flip p for small n, seeded Monte Carlo for large n, bootstrap CI
  bounds, metric rules for refusals, text prices and the lexicon.
- Malformed lines are counted and skipped; a missing probe is listed and its pair skipped.
- On the fixture, exactly one gated violation: `name/coworker/price`. The aggregate difference stays
  under the threshold.
- CLI exit code 1 on the fixture and 0 with relaxed thresholds; deterministic output; no names in outputs.

## How to run

```bash
make setup     # shared Python venv
make test      # visible tests
make report    # writes report.json and report.md; the exit code is the gate
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w4-c1
make clean
```
