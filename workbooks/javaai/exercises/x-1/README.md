# javaai/x-1 - Bounded contexts, write ownership and the schema for twelve universities

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 7 add-on (Mon-Tue: DDD and service architecture, Spring Modulith; Wed: schema and partitioning)

## Scenario

Kestrel Learning grows from one pilot university to twelve. The Spring Boot catalog API has become
a shared tangle, every feature asks for a new microservice, generated quiz drafts once leaked to
learners, quiz attempts grow 6M rows a month on the primary, tutoring transcripts are not stored at
all, and three universities require logically isolated data. The head of engineering wants a design
document to review with the architects before two more teams are hired. Read `inputs/brief.md` and
`inputs/constraints.md`.

## Deliverable

`DESIGN.md` (sections are pre-filled with guidance comments) and `ANSWER.md`:

- ubiquitous language, bounded contexts and a context map;
- aggregates and invariants, including how drafts can never reach learners;
- write ownership and integration (sync vs events, outbox, failure behaviour);
- deployment boundaries: modular monolith with Spring Modulith vs separate services, with reasons;
- relational schema for the core contexts with keys, constraints and indexes tied to named queries;
- quiz attempts at scale (partitioning, BigQuery, read replica, retention);
- tenancy, privacy and retention (deletion, 180-day transcripts);
- a migration path without a rewrite.

## How it is graded

Review-only: `make test` prints a completeness report (empty sections, word counts, diagram found)
and `GRADE_TESTS 0/0`; the rubric carries all 100 points. A senior reviewer looks for decisions with
reasons tied to the constraints, not a catalogue of patterns.

## How to run

```bash
make setup     # nothing to install
make test      # completeness report
# from workbooks/: /grade javaai/x-1
```
