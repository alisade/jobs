package com.larkspur.helpdesk;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.ConnectEvent;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.core.exception.SdkException;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.GetItemRequest;
import software.amazon.awssdk.services.dynamodb.model.GetItemResponse;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * lfg-identify-caller: invoked synchronously by the "LFG Help Desk Inbound" flow (time limit 3 s).
 * Looks the caller's number up in the employee directory table and returns a flat string map
 * (Connect ResponseValidation STRING_MAP): found, employeeId, vip, department, tier, lookupError.
 *
 * Java 21 + AWS SDK for Java 2.x. The client is created once per execution environment (static
 * init), which is also what SnapStart snapshots.
 */
public class EmployeeLookupHandler implements RequestHandler<ConnectEvent, Map<String, String>> {

    private final DynamoDbClient dynamo;
    private final String tableName;

    /** SDK v2 timeouts inside the flow's 3 s budget: one attempt <= 800 ms, whole call <= 1.8 s. */
    public static ClientOverrideConfiguration overrideConfig() {
        return ClientOverrideConfiguration.builder()
                .apiCallAttemptTimeout(Duration.ofMillis(800))
                .apiCallTimeout(Duration.ofMillis(1800))
                .build();
    }

    static DynamoDbClient defaultClient() {
        String region = System.getenv().getOrDefault("AWS_REGION", "us-east-1");
        return DynamoDbClient.builder()
                .region(Region.of(region))
                .httpClient(UrlConnectionHttpClient.builder().connectionTimeout(Duration.ofMillis(500)).build())
                .overrideConfiguration(overrideConfig())
                .build();
    }

    /** Used by the Lambda runtime. */
    public EmployeeLookupHandler() {
        this(defaultClient(), System.getenv().getOrDefault("TABLE_NAME", "lfg-employee-directory"));
    }

    public EmployeeLookupHandler(DynamoDbClient dynamo, String tableName) {
        this.dynamo = dynamo;
        this.tableName = tableName;
    }

    @Override
    public Map<String, String> handleRequest(ConnectEvent event, Context context) {
        String phone = PhoneNumbers.normalize(event.getDetails().getContactData().getCustomerEndpoint().getAddress());
        if (phone == null) {
            return notFound(false);
        }
        GetItemResponse response;
        try {
            response = dynamo.getItem(GetItemRequest.builder()
                    .tableName(tableName)
                    .key(Map.of("phone", AttributeValue.fromS(phone)))
                    .consistentRead(false)
                    .build());
        } catch (SdkException e) {
            return notFound(true);
        }
        // SDK v2: item() is never null; a missing item is an EMPTY auto-construct map.
        if (!response.hasItem() || response.item().isEmpty()) {
            return notFound(false);
        }
        Map<String, AttributeValue> item = response.item();
        Map<String, String> out = new HashMap<>();
        out.put("found", "true");
        out.put("employeeId", str(item.get("employeeId")));
        out.put("department", str(item.get("department")));
        out.put("tier", str(item.get("tier")));
        AttributeValue vip = item.get("vip");
        out.put("vip", vip != null && Boolean.TRUE.equals(vip.bool()) ? "true" : "false");
        out.put("lookupError", "false");
        return out;
    }

    private static String str(AttributeValue v) {
        return v == null || v.s() == null ? "" : v.s();
    }

    private static Map<String, String> notFound(boolean error) {
        Map<String, String> out = new HashMap<>();
        out.put("found", "false");
        out.put("employeeId", "");
        out.put("department", "");
        out.put("tier", "");
        out.put("vip", "false");
        out.put("lookupError", error ? "true" : "false");
        return out;
    }
}
