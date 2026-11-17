# ANSWER: modernize/w2-c1 Reverse-engineer claimdesk-web

## Approach

Checklist by area: build files and descriptors first (pom, web.xml, jboss-web.xml, persistence.xml,
orm.xml), then entry points, then every DAO and resource file for SQL, then clients, then ops files.
With an agent I would run one subagent per area, each returning items with evidence, and a verifier
(`make check`) that resolves every reference before I read the result.

## Fix

The inventory and SPEC.md. Hardest finds: PAYMENT only in orm.xml, SQL in queries.properties, the
archive table name built at runtime plus a cron script outside the WAR, the fraud URL living in a JNDI
binding from the jboss-cli script, and five different authorization mechanisms.

## Trade-offs / what I would do in production

Static reading cannot prove prod JNDI bindings, DB grants or traffic. I would compare against the live
server config, SchemaSpy over CLMPRD, and access logs. Skill failure modes to encode: grep only *.java,
trusting JNDI names as endpoints, listing dead code, skipping ops files.
