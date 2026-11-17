# ANSWER: javaai/w5-t1 The tutor cites the wrong lessons

## Approach

Eval history first: recall@3 was 0.90 after the model bump on 2026-11-11 and fell to 0.05 only
after the content merge on 2026-11-12. Sample citations have the right heading with the wrong lesson
id. Compared stored ids with front matter, then ran the eval with and without 00-welcome.md.

## Root cause

ingest() assigns lesson ids by enumerate over the sorted file names, ignoring front matter. The new
00-welcome.md sorts first, so welcome became l1 and every real lesson moved up one (vaccines l2 -> l3,
antibiotics l3 -> l4). Without the file: recall@3 0.900; with it: 0.050. Citations point one lesson
off and l4 404s. Not the embedding model: same model, 0.90 the day before.

## Fix

Ids from front matter; missing or duplicate ids raise. recall@3 back to 0.90 over 20 questions
(the two new welcome questions included); renaming files changes nothing; 9/9 tests.

## Trade-offs / what I would do in production

Make the eval blocking in Cloud Build, add a citation link check, build the index as a new version
and swap, validate front matter in the content repo CI. Keep model 005.
