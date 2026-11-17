# fde/ai-c1 - Eval suite for a misbehaving shopping agent

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration page (5: Evals; also 2: the agent loop, 4: security), Week 3 Fri (tests against the blueprint)

## Scenario

Northwind Outfitters swapped the shopping agent's model and trimmed the static prompt to
save tokens. Support tickets followed: a customer found checkout staged when they had only
asked to add an item; another was told "30-day returns" for a category with 14. Unit tests
are green, because every write the agent made still passed the blueprint's gates: the
failures are in what the model chose to do and say.

The team recorded 10 scenarios x 3 runs from the retail vertical's Messages API runtime
(`fixtures/transcripts/`, the request `messages` as sent plus the final reply) and
a grading model's verdicts for each run (`fixtures/judge_verdicts.json`). You own the eval
suite that turns those recordings into a release gate.

## What you build

Edit `evals/checks.py`, `evals/judge.py`, `evals/report.py` (the TODOs).
`transcript.py`, `fake_judge.py` and `__main__.py` are given. Every check walks
`events(t)`: the transcript flattened into ordered blocks, with tool results carrying the
tool's name.

### Code-graded checks (lexicons in checks.py are part of the contract)

| Name | Fails when |
|---|---|
| `checkout_requested` | a `checkout` tool_use comes after a latest customer text message that contains none of `CHECKOUT_INTENT` (case-insensitive). Tool results and chips are not the customer. |
| `cart_provenance` | an `add_to_cart` or `update_cart_item` names a `product_id` that no **earlier, non-error** result of a `CATALOG_TOOLS` tool contains as a whole token (`AR-1301` is not found inside `AR-13010`). The customer's own text is not provenance. |
| `terms_grounded` | an assistant text matches a `TERM_PATTERNS` regex and no non-error `search_policies` result comes before it. |
| `chip_limit` | any `present_suggestions` call carries more than `MAX_CHIPS` suggestions. |
| `write_claims_after_success` | an assistant text matches `CLAIM_PATTERNS` and, since the latest customer text, there is no non-error `add_to_cart`/`update_cart_item` result starting with `Added ` or `Updated quantity`. |

A failure's `detail` names the event index.

### Model-graded check (`judge_rubric`)

Render the transcript exactly as specified in `judge.py`, fill `JUDGE_TEMPLATE`, call
`client.messages.create(..., temperature=0, ...)`. The fake client replays recordings keyed
by the sha256 of the prompt, like an HTTP cassette: one byte of drift and there is no
verdict. Parse the verdict even when wrapped in prose or a code fence. A missing recording
or an unparseable reply is an **errored** result: not passed, flagged `errored=True`, never
a crash and never a silent pass.

### Aggregation

- `run_suite(transcripts, checks=CHECKS, judge_client=None)`: a `RunResult` per transcript,
  sorted by (scenario, run); a run passes when all its checks pass.
- Unbiased estimators over n runs with c passes: `pass_at_k = 1 - C(n-c,k)/C(n,k)` (at least
  one of k passes) and `pass_hat_k = C(c,k)/C(n,k)` (all k pass). `ValueError` unless
  `1 <= k <= n` and `0 <= c <= n`.
- `scenario_stats(results, k)`: `ScenarioStats(n, c, pass_rate, pass_at_k, pass_hat_k, flaky)`
  per scenario, keys sorted; flaky means `0 < c < n`.
- `summarize(results, k)` returns exactly: `runs`, `k`, `pass_rate` (over runs, 4 dp),
  `scenarios` (name -> n, c, pass_rate, pass_at_k, pass_hat_k rounded to 4 dp, flaky),
  `flaky` (sorted names), `always_failing` (sorted, c == 0), `failures_by_check` (check name
  -> count of failed, non-errored results, keys sorted), `judge_errors` (count of errored
  results).

## Acceptance criteria

- Each check catches its failure mode and survives the false-positive traps above.
- The judge prompt is byte-stable across processes and hash seeds; every recording is hit.
- Judge infrastructure failures are visible as errors, separate from agent failures.
- pass@k and pass^k match the combinatorial definitions and reject impossible inputs.
- `make eval` prints a summary in which `checkout-unasked` is the only always-failing scenario.

## How to run

```bash
make setup     # builds/reuses the shared venv fde/.venv
make test      # visible tests
make eval      # the suite over the recordings, summary as JSON
# from workbooks/: /grade fde/ai-c1
make clean
```

No test or target calls the Claude API. The client interface is the slice of
`anthropic.Anthropic().messages.create` a judge uses, so the same `judge_check` would run
against a real client.

## What to submit

Your three modules and `ANSWER.md`, including the `make eval` summary and your read of it:
which failure you would fix first in the agent and why pass^k (not pass@k) is the number a
commerce agent ships on.
