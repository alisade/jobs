# ANSWER: javaai/w1-c1 Catalog API validation, problem details and schema

## Approach

<!-- What you changed first and why; how you decided where each rule lives (record, validator,
controller, database). -->

## Fix

<!-- What you changed (records, handler, controller, migration) and how you verified it. -->

## Trade-offs / what I would do in production

<!-- Short. Rolling V2 out against a table that may hold duplicates (find and merge them first,
expand-and-contract, CREATE INDEX CONCURRENTLY on PostgreSQL), API versioning of the learner view,
problem type URIs as a contract, page caps vs keyset pagination. -->
