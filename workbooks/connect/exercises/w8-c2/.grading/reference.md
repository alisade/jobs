# Reference: connect/w8-c2

Reference files: `.grading/solution/pom.xml`, `.grading/solution/src/...`, `.grading/solution/infra/function.yaml`.

Breaking changes in the 1.x -> 2.x move that matter here:
- Packages `com.amazonaws.services.dynamodbv2.*` -> `software.amazon.awssdk.services.dynamodb.*`;
  `AmazonDynamoDBClientBuilder` -> `DynamoDbClient.builder()`; mutable `withX` requests ->
  immutable builders; `getS()/getBOOL()` -> `s()/bool()`; `AttributeValue.fromS(...)`.
- Exceptions: `AmazonClientException`/`AmazonServiceException` -> `SdkException`
  (`SdkClientException` for client-side failures such as timeouts, `AwsServiceException` /
  `DynamoDbException` for service errors).
- Semantics: in 2.x, collection getters never return null. A missing item gives an empty
  auto-construct map; `hasItem()` tells you whether the field was present. A literal port of
  `if (result.getItem() == null)` to `if (response.item() == null)` silently returns
  `found=true` with empty fields.
- Timeouts: `ClientConfiguration.withRequestTimeout/withClientExecutionTimeout` ->
  `ClientOverrideConfiguration.apiCallAttemptTimeout/apiCallTimeout`.
- HTTP client: 2.x ships Apache and Netty by default; for Lambda, exclude them and use
  `url-connection-client` (or the CRT client) for a smaller package and faster init.
- JUnit 4 -> 5: `org.junit.Test` -> `org.junit.jupiter.api.Test`, `Assert` -> `Assertions`,
  package-private test classes, surefire 3.x picks up the platform provider.

SnapStart (java21): snapshot taken when a version is published (not $LATEST), no extra cost on
Java runtimes; restore can reuse state, so regenerate uniqueness (random seeds, ids) after
restore, expect network connections to be re-established, and use runtime hooks (CRaC
`beforeCheckpoint`/`afterRestore`) to prime the client (e.g. a cheap call or class loading) so the
first real invoke is fast. Roll out by publishing a version and shifting the `live` alias with a
CodeDeploy canary while watching Lambda Errors/Duration and Connect `ContactFlowErrors`.
