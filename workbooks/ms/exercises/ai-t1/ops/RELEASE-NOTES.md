# Litware Policy Assistant - release notes

## 2026.12.1 (deployed 2026-12-07 02:10 UTC, change CHG-40871)

Index pipeline:
- Re-indexed the HR policy corpus with the improved tokenizer embedder `hash-bow-v2`
  (stemming, stop-word removal, bigrams). Same 1024 dimensions, so no schema change.
- Smaller chunks for tighter citations: `chunk_size` 200 -> 120 words, overlap 20.
- Nightly index build moved from the old VM to the pipeline runner.

App:
- Teams card layout: citations now show the chunk id.
- Bumped pyyaml.

Rollback plan: redeploy the 2026.11.4 index artifact (`hash-bow-v1`, chunk 200).

## 2026.11.4 (deployed 2026-11-24)

- Added benefits-enrollment and security-badges documents.
- Retrieval eval hit rate 1.0 (12/12).
