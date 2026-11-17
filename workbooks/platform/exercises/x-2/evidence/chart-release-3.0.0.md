# riq-api 3.0.0 (2026-11-10)

BREAKING
- `db.url` is renamed to `database.dsn`. Update every `values-<env>.yaml` before upgrading.
  values-dev.yaml and values-stg.yaml are updated in this release PR; values-prod.yaml is updated in
  the stable bump PR after the canary soak (PLAT-1219).

Changes
- Postgres 16 driver, connection pool metrics, readiness waits for the DB.
