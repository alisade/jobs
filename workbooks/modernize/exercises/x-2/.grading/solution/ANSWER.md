# ANSWER: modernize/x-2 Blast radius and rollback for corvane-commons 3.0

## Approach

Listed every way each consumer touches the library (compile-time API, runtime container, version range,
HTTP contract, SQL, JMS, shared Flyway history), then mapped each to the calendar.

## Fix

Key decisions: split API, JDK baseline and DDL; dual publish javax 2.15 and jakarta 3.0 with a support end date;
fix the open version range first; take commons-schema migrations away from consumers; make the DDL additive and
run it once in a DBA window; consumers move on their own calendars; contract tests for the .NET consumer; NOT NULL
only at the contract step.

## Trade-offs / what I would do in production

Dual publishing costs the platform team a build matrix for six months; cheaper than forcing three consumers. First I
would prove the 3.0 artifact on PolicyHub, which wants it and runs EAP 8 already. Pushback on ARCH-212: do not drop
2.x, do not ship DDL inside a library, do not let every consumer migrate a shared schema at startup.
