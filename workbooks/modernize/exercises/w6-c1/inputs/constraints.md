# Constraints

- Change windows: production deploys Tuesday and Thursday 20:00-23:00 ET, never in the last 5
  business days of a month (actuarial close) or the first 3 (reinsurance bordereau).
- CAB approval for every production change; standard changes need a rollback plan and a
  validated test evidence link.
- Partner contracts: Halberd Re bordereau and rating envelopes are byte-compared by the partner
  (golden files under claimdesk-rating/src/test/resources/golden). Any change needs a partner
  test file and written sign-off.
- AppSec: dependency floors (for example SEC-2291 jackson-core >= 2.13.5) must hold; SBOM per
  release.
- Rollback: the previous WAR must stay deployable on the old hosts until each increment has
  been in production for 10 business days.
