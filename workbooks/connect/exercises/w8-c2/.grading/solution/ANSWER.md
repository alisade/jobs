# ANSWER: connect/w8-c2 Java 11 to Java 21 and AWS SDK for Java 2.x

## Approach

Ported the tests to JUnit 5 and the SDK 2.x API first (fake DynamoDbClient implementing the
interface), then changed the handler until they passed, then the pom and infra.

## Fix

pom: release 21, SDK BOM 2.x, dynamodb with Apache/Netty excluded plus url-connection-client,
aws-lambda-java-events 3.16.1, junit-bom 5.11 + jupiter; no 1.x, no junit 4. Handler: builders,
AttributeValue.fromS/s()/bool(), catches SdkException, and treats a missing item as
`!hasItem() || item().isEmpty()` because 2.x returns an empty auto-construct map instead of null.
overrideConfig(): attempt 800 ms, call 1.8 s, inside the 3 s flow limit. infra: java21 + SnapStart
ApplyOn PublishedVersions with the live alias. make test and the grader pass.

## Trade-offs / what I would do in production

SnapStart: publish versions only, prime the client in a CRaC afterRestore hook, regenerate any
randomness after restore, expect reconnects. Canary the alias with CodeDeploy and alarm on Lambda
Errors/Duration and Connect ContactFlowErrors. Provisioned concurrency only if SnapStart restore
time is still too slow for the IVR.
