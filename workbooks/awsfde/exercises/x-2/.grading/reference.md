# Reference: awsfde/x-2

See `.grading/solution/DESIGN.md` for a model answer. What separates a strong answer:

- It names the shared cause (tenant scope optional in app code, no second layer, local fixes), not
  three separate bugs.
- Every component states a guarantee, and the defense-in-depth table shows at least two layers per bug.
- The IAM details are right: ForAllValues with dynamodb:LeadingKeys on a session tag, no Scan (an
  empty set of leading keys satisfies ForAllValues).
- The adoption plan respects the constraints (a day per service, three platform engineers, AppSec)
  and turns the review into checks that run in CI.
- It says what not to generalize and treats the kit itself as a risk to be managed.
- The FDE story ends with a measured result.
