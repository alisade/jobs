# Constraints

- Notes contain PHI. Anything that sees real notes must be a BAA-covered service in the PHI project,
  inside the VPC Service Controls perimeter, with Data Access audit logs on.
- Training data must be synthetic or de-identified (Healthcare API de-identify), and the training set is
  kept as an auditable artifact.
- The ICD-10-CM code set updates every October 1; new and deleted codes must be handled within two weeks.
- Suggestions are reviewed by nurses; a missed rare diagnosis (for example an oncology code) is worse than
  a noisy suggestion because it can route a case to the wrong policy.
- The platform team supports at most one new always-on GPU endpoint this year.
