# Constraints for the CI/CD design

- Source control is GitHub Enterprise Cloud (org `larkspur-fin`); GitHub Actions is the approved CI.
  Octopus Deploy is used by the .NET teams and may be proposed if justified.
- Deployments to AWS must use OIDC federation (no long-lived keys). One deploy role per account.
- Prod changes need CAB approval for "normal" changes; "standard" (pre-approved) changes may ship
  in business hours if the pipeline enforces automated tests and a rollback path.
- Release cadence target: weekly to prod; hotfix within 2 hours.
- Offshore (Pune, IST) and nearshore (Monterrey, CST) engineers must be able to ship to dev and
  test without Boston, and to prepare (not approve) prod releases.
- Change freeze: last two weeks of each quarter (financial close), except hotfixes.
- DR (us-west-2) must never lag prod by more than one release.
- Budget: no new paid tooling beyond what exists (GitHub, AWS, Octopus).
- Audit: every prod change traceable to a PR, an approver and a pipeline run (SOX-adjacent).
