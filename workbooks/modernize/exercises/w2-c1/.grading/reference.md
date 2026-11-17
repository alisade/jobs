# Reference: modernize/w2-c1

Model inventory: `.grading/solution/spec/inventory.json`. The touchpoints that separate a careful read
from a grep for "SELECT":

- `PAYMENT` exists only in `META-INF/orm.xml` (the entity class has no annotations).
- `USER_ROLE` and `ADJUSTER` live in `queries.properties`; `ADJUSTER` is used by the batch export.
- `CLMARCH.CLAIM_ARCHIVE_<YYYY>` is built by string concatenation and is deleted from by a cron script
  outside the WAR (`ops/crontab`, `ops/purge-archive.sh`), on one host only.
- `PKG_RESERVE.RECALC` is a PL/SQL call: business logic in the database.
- The fraud URL is not in the code or the properties file: it is a JNDI simple binding created by the
  2019 jboss-cli script. The scorer fails open.
- Authorization lives in five mechanisms: container constraints (CLAIMS_USER, CLAIMS_ADMIN), code
  (CLAIMS_SUPERVISOR above 25000), a servlet filter doing a direct-membership LDAP search
  (claims-payments, nested groups ignored), a JSP (AUDITOR) and a database table (REASSIGN_CLAIMS).
- `LegacyFaxGateway` is unreferenced dead code.
- Runtime: America/New_York, ISO-8859-1 default charset, Oracle dialect, EAP 7.4 with PicketBox,
  Java 8, local outbox directory.

Interview angle: how you would make an agent produce this reliably (checklist per area, subagent per
area with its own evidence, a verifier that resolves every ref, a final human read of the risky claims).
