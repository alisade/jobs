# labelgate 2.7.0

- feat(router): decision cache (bounded FIFO, 50k entries) so repeated series skip rule
  evaluation. Expected hit rate in prod: high for stable series.
- feat(router): per-tenant routing rules (`tenant` field); rules are now evaluated per
  tenant and patterns may be overridden per tenant in a later release.
- refactor(router): pattern validation moved into `New` so a bad rules file fails the
  rollout instead of returning 500s.
- chore: Go 1.26.3, distroless base image bump.
