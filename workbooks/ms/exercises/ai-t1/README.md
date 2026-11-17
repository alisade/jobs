# ms/ai-t1: Policy assistant cites the wrong documents after the re-index

Type: troubleshooting. Estimate: 1.5-2 h. Exam: AI integration (shared page) - area 6 RAG and grounding, area 5 Evals. AB-100 relevant (Deploy: monitor, analyze and tune; testing).

## Scenario

Litware's HR policy assistant answers employee questions in Teams, grounded on the HR policy
corpus and citing the policy it used. Release 2026.12.1 went out on Monday 2026-12-07 at 02:10
UTC. By Tuesday:

> **Pager (Sev2, Azure Monitor):** policy-assistant-retrieval-quality. Nightly retrieval eval
> hit rate 0.417, threshold 0.80, previous run 1.0.
>
> **Helpdesk:** "The assistant answered my PTO carryover question by citing the benefits
> enrollment policy." "Parental leave answer quotes the remote work policy." "It used to be
> really good."

Nobody touched the corpus. The release notes are in `ops/RELEASE-NOTES.md`. The retrieval
pipeline is local and deterministic (no network, no model): `policy_rag/` has a versioned hashing
embedder, a chunker, a file-based vector index with a manifest, a retriever and an eval.

How this maps to Azure: in Azure AI Search with integrated vectorization, an embedding skill
vectorizes chunks at indexing time and a **vectorizer** (attached to the vector field through a
vector profile) vectorizes the query text at query time. Microsoft's guidance is that both must use
the same embedding model. A wrong dimension count fails loudly; a different model with the SAME
dimensions fails silently, which is the case here. Copilot Studio knowledge from Azure AI Search
inherits whatever the index does.

## Your task

1. `make setup`: builds `index/` from `config/index.yaml` (as the release did) and generates the
   evidence bundle in `incident/`: eval reports before and after, query logs with top-k scores,
   the index manifest, the deployed app config, and the alert.
2. Find the root cause. Prove it with evidence (commands and output). Rule out the other changes
   in the release notes with evidence, not by assertion.
3. Fix the configuration, and make the failure impossible to ship silently again: the query path
   must refuse to start (`IndexMismatchError`, already declared in `policy_rag/retriever.py`)
   when it cannot safely use the index it is pointed at.
4. Fill in `ANSWER.md`.

## Acceptance criteria

- The retrieval eval (`make eval`, or `make test`) reaches hit rate >= 0.8 with the shipped
  configs: `config/index.yaml` builds the index, `config/app.yaml` drives the query path.
- `Retriever(index_dir, query_embedder, ...)` raises `IndexMismatchError` when the index manifest
  says it was built with a different embedder than the query path uses, or when the manifest's
  dimensions do not match the query embedder. The message names both sides. A matching pair must
  still work (no false positives).
- `ANSWER.md` has the root cause with evidence, why the chunk-size change is not the cause, the
  fix and how you verified it, and what you would change in the deployment process.

## How to run

```
make setup    # build index/ and generate incident/
make eval     # run the retrieval eval with config/app.yaml -> report.json
make test     # visible tests
make clean    # removes .venv, index/, incident/, report.json
```

Tip: `uv run python -m policy_rag.build --config <file> --out /tmp/idx` lets you build
alternative indexes to test hypotheses.

## What to submit

Your changes under `config/` and `policy_rag/`, and `ANSWER.md`. Then `/grade ms/ai-t1`.

## Study guide links

- [AI integration fundamentals page (6 RAG, 5 Evals)](../../../../microsoft-adf-powerapps-study-plan.html#ai)
- [Azure AI Search: configure a vectorizer](https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-configure-vectorizer)
- [Azure AI Search: RAG overview](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview)
- [Week 10 - Monitor, analyze, tune](../../../../microsoft-adf-powerapps-study-plan.html#week10)
- [Contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) / [Embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings)
