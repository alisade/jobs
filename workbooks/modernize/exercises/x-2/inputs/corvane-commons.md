# corvane-commons (shared library) - 3.0 proposal

Owner: platform team (2 developers). Repo: corvane/corvane-commons. Current: 2.14.3 (javax).
Proposal (ARCH-212): release 3.0.0 on Jakarta EE 10 (`jakarta.*`), JDK 17 baseline, and drop 2.x.

What it contains and what is javax in its public API:

| Package | What | javax/jakarta exposure |
|---|---|---|
| com.corvane.commons.web | RequestIdFilter, CorsFilter, ErrorJsonWriter | `javax.servlet.Filter`, `HttpServletRequest` in signatures |
| com.corvane.commons.audit | AuditLogger (writes AUDIT_EVENT), AuditInterceptor | `javax.interceptor`, `javax.persistence.EntityManager` |
| com.corvane.commons.json | Mapper factory (Jackson) | none; pins jackson-bom 2.15.4 |
| com.corvane.commons.rest | `/commons/v1/reference/*` REST resources (JAX-RS) served by each WAR | `javax.ws.rs` |
| com.corvane.commons.db | Flyway migrations for AUDIT_EVENT, REF_CODE, REF_CODE_I18N | none (SQL) |
| com.corvane.commons.jms | AuditPublisher to queue AUDIT.EVENTS | `javax.jms` |

Database objects owned by the library (schema COMMONS, Oracle): AUDIT_EVENT (append-only, 410 M rows,
partitioned by month), REF_CODE, REF_CODE_I18N, and the Flyway history table. Every consumer runs the
Flyway migrations at startup against the shared schema (`commons.flyway.enabled=true` by default).
3.0 adds migration V3_0__audit_event_tenant.sql: `ALTER TABLE AUDIT_EVENT ADD TENANT_ID NUMBER NOT NULL DEFAULT 1`.
