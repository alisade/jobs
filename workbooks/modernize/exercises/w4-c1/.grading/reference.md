# Reference: modernize/w4-c1

Solution files: `.grading/solution/pom.xml` (tomcat-embed-core 10.1.34), `ClaimServlet.java`,
`RequestIdFilter.java`, `ErrorServlet.java` with `jakarta.servlet` imports.

Two traps:
1. Over-migration: `JdbcSupport` imports `javax.sql.DataSource` and `javax.naming.InitialContext`. They are
   Java SE packages and were never part of Java EE's namespace move; renaming them breaks the build. Other
   Java SE javax packages: javax.crypto, javax.net.ssl, javax.xml.parsers, javax.security.auth.
2. Under-migration: `ErrorServlet` reads `"javax.servlet.error.status_code"` (and message, exception) as
   string literals. Servlet 5+ containers set `jakarta.servlet.error.*`, so the reads return null, every error
   becomes 500 "error", and four golden flows fail. Use `RequestDispatcher.ERROR_STATUS_CODE`,
   `ERROR_MESSAGE`, `ERROR_EXCEPTION`. OpenRewrite's recipe handles imports and types; check its output for
   string literals, reflection, config files and descriptors.

EAP 8 follow-ups: descriptor namespaces (jakarta.ee schemas), Elytron instead of PicketBox security domains,
library upgrades or Eclipse Transformer for javax-only jars, and the golden flows as the deployment smoke test.
