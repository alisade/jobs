# ANSWER: javaai/w1-c1 Catalog API validation, problem details and schema

## Approach

Listed every rule from the README and placed each one where it belongs: field rules as Bean
Validation on the request records, cross-field rules (answer index in range, distinct options) in a
class-level constraint that reports the exact property, existence and uniqueness checks in the
controller, and every invariant again in the database through a new V2 migration.

## Fix

- `Dtos.java`: `@NotBlank`, `@Size`, `@Pattern`, `@Min`, `@NotNull`; separate `QuizItemLearnerView`
  with id, stem and options only.
- `ValidQuizItem.java`: class-level constraint with `addPropertyNode`.
- `ApiErrors.java`: RFC 9457 problem details, `errors` array, 404/409/400, integrity violation to 409.
- `CatalogController.java`: `@Valid`, page cap 50, negative page 400, chosen index range check.
- `V2__catalog_constraints.sql`: unique slug, unique (course_id, position), FKs, CHECKs, learner index.

Verified with `make test` and the full grader run (17/17).

## Trade-offs / what I would do in production

Clean duplicates before adding the unique constraint, and on PostgreSQL use CREATE INDEX
CONCURRENTLY plus NOT VALID / VALIDATE CONSTRAINT to avoid long locks. Keyset pagination for deep
lists. Version the learner view contract because the Angular app and the agent both consume it.
