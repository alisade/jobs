# ANSWER: healthai/w5-t1 The chunker splits a criteria table mid-row

## Approach

<!-- What you ran and looked at first, and how you separated the two release changes. -->

## Root cause

<!-- The mechanism, with evidence: a chunk that starts mid-row, missed query ids, before/after numbers. -->

## Fix

<!-- Your chunking rules and how you verified them (eval numbers, tests). -->

## Trade-offs / what I would do in production

<!-- Shipping two retrieval changes in one release, eval gates per change, Document AI layout parser,
parent-child chunks, re-embedding cost, the embedding upgrade on its own merits. -->
