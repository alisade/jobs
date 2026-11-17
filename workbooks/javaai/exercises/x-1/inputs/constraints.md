# Constraints and facts

- Team: 3 teams of 4-6 after hiring (Learning, Authoring + AI, Platform). One product lead.
- Cloud SQL for PostgreSQL 16, db-custom-8-32768 primary, one read replica available. BigQuery is
  approved for analytics. Pub/Sub is approved for events.
- Peak: 12 universities x ~8,000 active learners, 09:00 cohort spikes; ~200 quiz attempts per second
  at peak; tutor turns ~60 per second at peak.
- Data protection: learner deletion requests within 30 days; tutor transcripts retained at most 180 days;
  quiz attempts kept 4 years for academic records.
- Contracts: 3 universities require "logically isolated" data (no shared rows with other tenants
  visible to their admins; per-tenant export on request). None require separate databases.
- Spring Boot 3.5 / Java 21, Spring Modulith available. The tutor agent stays Python (ADK features).
- Authors must review every generated quiz item before learners see it.
