# connect/w5-c3 - Tune the help desk AI agent against an eval set

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 5 (Fri: prompt engineering and tuning AI agents - eval sets, accuracy, containment, latency, hallucination)

## Scenario

LFG's help desk AI agent (an orchestrator-style agent in Connect; its intent triage and KB
answer settings are kept in `tuning/agent.yaml`, rendered into the AI prompt at deploy time)
missed its go-live gate. The pilot config was written in an afternoon: one-word intent
descriptions, no examples, a 0.9 confidence threshold "to be safe", `topK: 1` retrieval and no
citation requirement. In UAT almost everything fell back to an analyst, and when the team
lowered the threshold the bot started answering from the wrong articles.

You get the recorded eval set the QA team labeled from UAT transcripts (`eval/eval-set.jsonl`:
53 utterances with gold intents, and for how-to questions the recorded knowledge base ranking
with scores and the correct article). Tune the config until it clears the gates. A hidden
holdout set from a later UAT week checks you did not overfit.

### The simulator (read this)

Grading must be offline and deterministic, so the model is replaced by `lfg-sim-1`
(`src/sim.ts`): **a simulator, not an LLM**. It reproduces the levers you tune on a real agent:

- each intent understands the vocabulary of its description and examples; words shared by many
  intents carry less weight; only the first 30 description tokens and first 6 examples (20
  tokens each) are read - a context budget, so keyword stuffing stops working;
- confidence = how clearly the top intent beats the runner-up; below `confidenceThreshold` the
  agent hands off (Fallback);
- how-to answers use the recorded KB ranking: `topK` chunks with `score >= minScore` reach the
  model; if the right article is among them the answer is contained; if not, the agent either
  hallucinates (`requireCitations: false`) or declines and hands off (`requireCitations: true`);
- latency = 250 ms + 1 ms per prompt token + 80 ms per retrieved chunk + 400 ms for an answer.

Treat `src/sim.ts` as the environment: the grader scores with a pristine copy.

## Your task

1. `make eval` to see the baseline and the failing cases (`SHOW=all make eval` for everything).
2. Tune `tuning/agent.yaml`: descriptions, examples, threshold, retrieval and answer settings,
   model parameters. Keep the same seven intents.
3. Keep an iteration log in `ANSWER.md`: each change, the metric it moved, and what you traded.

## Acceptance criteria (what the grader checks)

- Visible set: intent accuracy >= 0.85 (and at least +0.5 over the baseline), containment >= 0.45,
  no hallucinations, misroutes <= 5%, p95 latency <= 1800 ms.
- Hidden holdout: accuracy >= 0.80, containment >= 0.35, misroutes <= 5%, no hallucinations, and
  visible-minus-holdout accuracy gap <= 0.10.
- Config hygiene: temperature 0, maxTokens <= 300, citations required, threshold in 0.3-0.8, no eval
  utterance pasted verbatim as a description or example.
- `ANSWER.md` iteration log with metrics, and how you would run the same loop on the real agent.

## How to run

```bash
make setup     # links the shared toolchain
make eval      # metrics + wrong cases
make test      # visible gates
# from workbooks/ in Claude Code: /grade connect/w5-c3
make clean
```
