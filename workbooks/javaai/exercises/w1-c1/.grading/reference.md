# Reference: javaai/w1-c1

Reference files are in `.grading/solution/`:

- `api/Dtos.java` - Bean Validation on every request record; `QuizItemLearnerView` without key and explanation.
- `api/ValidQuizItem.java` - class-level constraint; `addPropertyNode("answerIndex")` / `("options")` so the
  problem detail names the field the author must fix.
- `api/ApiErrors.java` - `@RestControllerAdvice` extending `ResponseEntityExceptionHandler`: overrides
  `handleMethodArgumentNotValid` to add an `errors` array; typed NotFound / Conflict / BadRequest; maps
  `DataIntegrityViolationException` to 409 as the backstop for races.
- `api/CatalogController.java` - `@Valid` on bodies, pre-check for duplicate slug, page cap 50, 404s.
- `db/migration/V2__catalog_constraints.sql` - unique, FK, CHECK constraints and
  `ix_attempt_learner_item (learner_id, quiz_item_id, created_at)`.

## Why both layers

The API gives authors a precise, friendly error. The database protects the invariant against every
other writer (batch imports, the quiz generator, a second service, a manual fix) and against races
that a "select then insert" check cannot see. Uniqueness checked only in Java is a bug waiting for
two concurrent requests.

## Rolling V2 out against live data

1. Find violations first (`select slug, count(*) from course group by slug having count(*) > 1`),
   decide the survivor, re-point lessons, delete the losers in a reviewed data migration.
2. On PostgreSQL: `CREATE UNIQUE INDEX CONCURRENTLY` in its own non-transactional migration, then
   `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX`; foreign keys and checks with `NOT VALID`
   and a later `VALIDATE CONSTRAINT` so the long scan does not hold a blocking lock.
3. Deploy the application change (validation, 409 mapping) before or with the constraint.

## Interview angles

- Why problem details (stable `type` URIs clients can switch on) instead of ad hoc error JSON.
- Why the learner DTO is a separate type rather than `@JsonIgnore` on a shared one: it makes the
  leak impossible to reintroduce by adding a field.
- Offset paging breaks at depth; keyset pagination on `(title, id)` for large catalogs.
