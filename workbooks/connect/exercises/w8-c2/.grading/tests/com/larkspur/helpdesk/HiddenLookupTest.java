package com.larkspur.helpdesk;

import com.amazonaws.services.lambda.runtime.events.ConnectEvent;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.core.exception.SdkClientException;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.GetItemRequest;
import software.amazon.awssdk.services.dynamodb.model.GetItemResponse;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Hidden tests for connect/w8-c2 (copied into src/test/java by the grader). */
class HiddenLookupTest {

    static ConnectEvent call(String from) {
        return ConnectEvent.builder()
                .withName("ContactFlowEvent")
                .withDetails(ConnectEvent.Details.builder()
                        .withContactData(ConnectEvent.ContactData.builder()
                                .withContactId("0b9f6c2e-4f1a-4c55-9d1e-7a3b2c1d0e9f")
                                .withChannel("VOICE")
                                .withCustomerEndpoint(ConnectEvent.CustomerEndpoint.builder().withAddress(from).withType("TELEPHONE_NUMBER").build())
                                .build())
                        .withParameters(new HashMap<>())
                        .build())
                .build();
    }

    static class Recorder implements DynamoDbClient {
        final List<GetItemRequest> requests = new ArrayList<>();
        GetItemResponse response = GetItemResponse.builder().build();
        RuntimeException fail;

        @Override
        public GetItemResponse getItem(GetItemRequest request) {
            requests.add(request);
            if (fail != null) {
                throw fail;
            }
            return response;
        }

        @Override
        public String serviceName() {
            return "dynamodb";
        }

        @Override
        public void close() {
        }
    }

    static Map<String, AttributeValue> row(boolean vip) {
        return Map.of("employeeId", AttributeValue.fromS("E20871"), "department", AttributeValue.fromS("Treasury"),
                "tier", AttributeValue.fromS("platinum"), "vip", AttributeValue.fromBool(vip));
    }

    @Test
    void sdkV2NotFoundIsAnEmptyItemNotNull() {
        Recorder db = new Recorder(); // GetItemResponse with no item: item() is an empty map in SDK v2
        Map<String, String> out = new EmployeeLookupHandler(db, "lfg-employee-directory").handleRequest(call("+16175550199"), null);
        assertEquals("false", out.get("found"));
        assertEquals("false", out.get("lookupError"));
    }

    @Test
    void formattedNumberIsNormalizedAndTheConfiguredTableIsQueried() {
        Recorder db = new Recorder();
        db.response = GetItemResponse.builder().item(row(false)).build();
        Map<String, String> out = new EmployeeLookupHandler(db, "lfg-employee-directory-prod").handleRequest(call("+1 (617) 555-0142"), null);
        assertEquals(1, db.requests.size());
        assertEquals("lfg-employee-directory-prod", db.requests.get(0).tableName());
        assertEquals("+16175550142", db.requests.get(0).key().get("phone").s());
        assertEquals("true", out.get("found"));
        assertEquals("E20871", out.get("employeeId"));
        assertEquals("Treasury", out.get("department"));
        assertEquals("platinum", out.get("tier"));
    }

    @Test
    void vipFlagComesFromTheBooleanAttribute() {
        Recorder db = new Recorder();
        db.response = GetItemResponse.builder().item(row(true)).build();
        assertEquals("true", new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null).get("vip"));
        db.response = GetItemResponse.builder().item(Map.of("employeeId", AttributeValue.fromS("E1"))).build();
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("false", out.get("vip"));
        assertEquals("", out.get("department"));
    }

    @Test
    void clientSideTimeoutDegradesToLookupError() {
        Recorder db = new Recorder();
        db.fail = SdkClientException.create("Client execution did not complete before the specified timeout configuration: 1800 millis");
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("false", out.get("found"));
        assertEquals("true", out.get("lookupError"));
    }

    @Test
    void withheldCallerIsNotLookedUp() {
        Recorder db = new Recorder();
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("anonymous"), null);
        assertEquals("false", out.get("found"));
        assertEquals(0, db.requests.size());
    }

    @Test
    void responseIsAFlatStringMapWithEveryKey() {
        Recorder db = new Recorder();
        for (Map<String, String> out : List.of(
                new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550199"), null),
                new EmployeeLookupHandler(new Recorder() {{ response = GetItemResponse.builder().item(row(true)).build(); }}, "t").handleRequest(call("+16175550142"), null))) {
            for (String k : List.of("found", "employeeId", "vip", "department", "tier", "lookupError")) {
                assertNotNull(out.get(k), "missing key " + k);
            }
        }
    }

    @Test
    void sdkTimeoutsFitInsideTheFlowsThreeSecondBudget() {
        ClientOverrideConfiguration c = EmployeeLookupHandler.overrideConfig();
        Duration call = c.apiCallTimeout().orElseThrow();
        Duration attempt = c.apiCallAttemptTimeout().orElseThrow();
        assertTrue(call.toMillis() <= 2000, "apiCallTimeout " + call);
        assertTrue(attempt.toMillis() <= 1000, "apiCallAttemptTimeout " + attempt);
    }

    @Test
    void compiledForJava21() throws Exception {
        try (InputStream in = EmployeeLookupHandler.class.getResourceAsStream("EmployeeLookupHandler.class")) {
            byte[] b = in.readNBytes(8);
            int major = ((b[6] & 0xff) << 8) | (b[7] & 0xff);
            assertEquals(65, major, "class file major version (65 = Java 21)");
        }
    }

    @Test
    void pomIsOnSdkV2AndJUnit5Only() throws Exception {
        String pom = Files.readString(Path.of("pom.xml"));
        assertFalse(pom.matches("(?s).*<artifactId>aws-java-sdk[a-z0-9-]*</artifactId>.*"), "AWS SDK for Java 1.x is still a dependency");
        assertFalse(pom.matches("(?s).*<groupId>junit</groupId>.*"), "JUnit 4 is still a dependency");
        assertTrue(pom.contains("software.amazon.awssdk"), "AWS SDK for Java 2.x missing");
        assertTrue(pom.matches("(?s).*(<maven.compiler.release>21</maven.compiler.release>|<release>21</release>).*"), "compile with release 21");
    }

    @Test
    void functionRunsOnJava21WithSnapStart() throws Exception {
        String yaml = Files.readString(Path.of("infra/function.yaml"));
        assertTrue(yaml.matches("(?s).*Runtime:\\s*java21.*"), "Runtime java21");
        assertTrue(yaml.matches("(?s).*SnapStart:\\s*\\n\\s*ApplyOn:\\s*PublishedVersions.*"), "SnapStart ApplyOn PublishedVersions");
        assertTrue(yaml.contains("AutoPublishAlias"), "SnapStart only applies to published versions: keep the alias");
    }
}
