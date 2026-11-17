# Tidewater Ask release 2026.11.10

- ASK-398 Knowledge Base: switch the data source to hierarchical chunking (parent 1500 / child 300
  tokens) and re-ingest all tenants. Sync job completed, see evidence/ingestion-job-2026-11-10.json.
- ASK-412 Answer quality: fewer "I could not find that" answers for tenants with small document
  sets. Product asked for this after the Delta Outfitters onboarding call (they have very few
  documents loaded so far). Change in ask_service/retrieval.py. Reviewed by: platform-oncall.
- ASK-415 Bump boto3 to 1.44.2.
