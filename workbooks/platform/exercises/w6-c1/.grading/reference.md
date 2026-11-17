# Reference: platform/w6-c1

Reference code: `.grading/solution/gate/*.go`.

- `Classify` switches on the joined action list; both replace orders map to replace, everything
  else is an error. `Validate` checks `format_version` major 1 and classifies every change, so a
  state file (`{"version":4,...}`) or a future format fails with exit 2 instead of "0 changes, PASS".
- `Summarize` counts imports from `change.importing`, so an import with a labels update counts as
  1 import and 1 change, matching terraform's own summary line. Replacements count in add and destroy.
- `ChangedAttributes` compares top-level keys with `reflect.DeepEqual`; a sensitive marker that is
  `true` anywhere below an attribute masks the whole attribute (safer than masking leaves).
- `Evaluate`: protected types apply in every mode; imports-only adds the action and attribute rules.
- `Run` returns 2 for every input problem before building a report. `Build` keeps violations as an
  empty slice so the JSON is `[]`, never `null` (downstream jq checks break on null).

Talking points: the plan is the contract because provider defaults and ForceNew attributes are only
visible there (the VPC replace came from a missing `auto_create_subnetworks = false`, invisible in an
HCL diff that only shows a deleted line); gate the same saved plan file the apply job consumes;
the gate complements `gcloud beta terraform vet` / OPA (organization rules) with change-shape rules.
