# Rubric: connect/w8-c2 Java 11 to Java 21 and AWS SDK for Java 2.x
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | SDK 2.x migration correctness | 15 | Full: BOM-managed SDK 2.x, builders and fromS/bool used correctly, SdkException (or narrower) caught, the SDK 2.x "missing item is an empty auto-construct map" semantics handled with hasItem()/isEmpty(), no 1.x artifacts left (including transitive via other deps). Partial: tests pass but the not-found check is accidental or exceptions are caught as Exception/Throwable. |
| 3 | Lambda/Connect fitness | 10 | Full: client built once outside the handler path, timeouts inside the 3 s flow budget with a stated rationale (Connect retries within its 8 s sync limit, dead air), lightweight HTTP client (url-connection or CRT) with Apache/Netty excluded, flat string map preserved. Partial: some of these without reasoning. |
| 4 | Code and test quality | 5 | Idiomatic Java 21 where it helps (Map.of, records/var where sensible), JUnit 5 tests readable, no dead code. |
| 5 | ANSWER.md upgrade thinking | 20 | Full: names the breaking changes (packages, builders, exception hierarchy, empty-map semantics, JUnit 5 annotations/assertions), SnapStart caveats (unique ids/randomness after restore, re-established network connections, credentials, runtime hooks for priming, published versions only, compatible only with certain features), rollout plan (publish version, alias shift with CodeDeploy canary, alarms on Errors/Duration and Connect ContactFlowErrors), runtime deprecation dates (java11/java17 AL2 to 2027-06-30). Partial: generic "upgraded deps". |
Total: 100
