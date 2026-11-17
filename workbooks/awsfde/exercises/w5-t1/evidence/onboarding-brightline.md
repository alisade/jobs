# Onboarding runbook: Brightline Health graph (executed 2026-11-11)

1. Brightline ERP extract received (data/source/brightline-health.json). OK
2. Nightly export job generated brightline-health-nodes.csv / -edges.csv in the openCypher load
   format (export_job/export.py, unchanged since the Acme onboarding in August). OK
3. Pre-load validation: ASK-377 (validator) not implemented yet; skipped. OK
4. Bulk load into the shared graph g-tw0graph01 (same graph as Acme). Load status LOAD_COMPLETED,
   no errors. OK
5. Smoke test: "suppliers of Exam room kit" for brightline-health returns Northwind Medical Gloves
   and Clearview Syringe Co. OK

Known issues
- CS-5480 (2026-10-20): suppliers sometimes listed twice in answers (Acme). Fix scheduled for the
  next tool release: add DISTINCT to the tool query.
