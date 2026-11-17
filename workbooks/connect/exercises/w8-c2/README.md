# connect/w8-c2 - lfg-identify-caller: Java 11 to Java 21 and AWS SDK for Java 2.x

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 8 (Fri: Java Lambda for Connect: runtimes, SnapStart, cold starts, SDK and JDK upgrades)

## Scenario

`lfg-identify-caller` is the Java Lambda that the Larkspur help desk inbound flow invokes
synchronously (time limit 3 s) to look the caller's number up in the `lfg-employee-directory`
DynamoDB table. It was written in 2023 on the `java11` runtime with the AWS SDK for Java 1.x
and JUnit 4. Security has flagged it: the AWS SDK for Java 1.x reached end of support on
2025-12-31, and the `java11` (Amazon Linux 2) runtime is deprecated on 2027-06-30. The
architecture board also wants SnapStart on it, because cold starts after every deploy put
1.8 s of dead air on the first calls (see `connect/w8-t1`).

The upgrade is not a version bump: SDK 2.x changes packages, builders, exceptions and some
semantics. One of those semantic changes bit the team that upgraded the HR bot last quarter.

## What you have

| Path | What it is |
|---|---|
| `pom.xml` | Java 11, `aws-java-sdk-dynamodb` 1.12.x, `aws-lambda-java-events` 3.11.6, JUnit 4 |
| `src/main/java/.../EmployeeLookupHandler.java` | the handler (`RequestHandler<ConnectEvent, Map<String,String>>`) |
| `src/main/java/.../PhoneNumbers.java` | E.164 normalization (fine as is) |
| `src/test/java/.../EmployeeLookupHandlerTest.java` | JUnit 4 tests with a fake SDK 1.x client |
| `infra/function.yaml` | the SAM/CloudFormation excerpt that deploys the function |
| `events/connect-event.json` | a sample Connect Lambda event |

## Requirements

1. Compile with `maven.compiler.release` 21; run on the `java21` Lambda runtime.
2. Replace the AWS SDK for Java 1.x with 2.x (use the SDK BOM). Keep constructor injection:
   `new EmployeeLookupHandler(DynamoDbClient client, String tableName)`; the no-arg
   constructor builds the real client once (static-init friendly for SnapStart).
3. Behavior is unchanged: flat string map with keys `found`, `employeeId`, `vip`,
   `department`, `tier`, `lookupError`; a number with no directory row is `found=false`; any
   SDK error degrades to `found=false, lookupError=true` (never throw to Connect); withheld or
   anonymous callers are not looked up.
4. Expose `public static ClientOverrideConfiguration overrideConfig()` and use it on the real
   client: the whole call must finish inside the flow's 3 s budget with room for Connect's own
   overhead (API call timeout <= 2 s, per-attempt timeout <= 1 s).
5. Move the tests to JUnit 5 (Jupiter); remove JUnit 4 and every SDK 1.x artifact.
6. `infra/function.yaml`: `java21`, SnapStart on published versions (keep the alias).
7. Prefer a lightweight HTTP client for cold start (and say why in ANSWER.md).

## Acceptance criteria (what the grader checks)

- Hidden JUnit 5 tests against the SDK 2.x API: found, not found (as SDK 2.x actually
  reports it), formatted numbers normalized, configured table name used, vip from the
  boolean attribute, client-side timeout degrades, withheld caller not looked up, every key
  present.
- `overrideConfig()` timeouts within budget; classes compiled for Java 21 (class file 65).
- `pom.xml` has no SDK 1.x or JUnit 4; `infra/function.yaml` is java21 with SnapStart.
- `ANSWER.md`: the breaking changes you hit, SnapStart caveats (uniqueness, network
  connections, priming, published versions only), and how you would roll it out.

## How to run

```bash
make setup      # checks JDK 21 + Maven, downloads Maven artifacts once to ~/.m2 (a minute on first run)
make test       # mvn test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w8-c2
make clean
```

Toolchain: JDK 21 and Maven (`brew install openjdk@21 maven`); `connect/_env/java-env.sh`
finds Homebrew's openjdk@21 or honours `JAVA_HOME`. Grading needs no network once `make
setup` has run.
