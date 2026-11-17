# ANSWER: modernize/w4-c1 javax.servlet to jakarta.servlet

## Approach

Ran `make test` first: 8/8 green on Tomcat 9. Bumped the pom to tomcat-embed-core 10.1.34 and changed
the Servlet imports (what the OpenRewrite recipe would do). Compile was clean, but 4 flows failed:
02, 04, 07 and 08 all returned `{"status":500,"error":"error"}`. `grep -rn 'javax' src/main` showed
the error attribute names as string literals in ErrorServlet.

## Fix

- pom: Tomcat 10.1 (Servlet 6.0, same API level as EAP 8).
- ClaimServlet, ErrorServlet, RequestIdFilter: `jakarta.servlet` imports.
- ErrorServlet reads `RequestDispatcher.ERROR_STATUS_CODE`, `ERROR_MESSAGE` and `ERROR_EXCEPTION`
  instead of `"javax.servlet.error.*"` literals; Servlet 5+ uses `jakarta.servlet.error.*`.
- Not changed: JdbcSupport's `javax.sql.DataSource` and `javax.naming.InitialContext` are Java SE.
  This is why the sed attempt failed to compile.
- Golden files untouched; 8/8 green again.

## Trade-offs / what I would do in production

On EAP 8 there is more: web.xml and jboss-web.xml move to the Jakarta schemas, the PicketBox
security domain becomes an Elytron application-security-domain, and javax-only libraries need
upgrades or Eclipse Transformer. Review OpenRewrite output for literals, reflection and config.
Roll out with the golden flows as the post-deploy smoke test, and keep the javax build deployable
as the rollback until a full release cycle has passed.
