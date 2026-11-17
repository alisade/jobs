package com.larkspur.helpdesk;

import com.amazonaws.AmazonClientException;
import com.amazonaws.ClientConfiguration;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.GetItemRequest;
import com.amazonaws.services.dynamodbv2.model.GetItemResult;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.ConnectEvent;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * lfg-identify-caller: invoked synchronously by the "LFG Help Desk Inbound" flow (time limit 3 s).
 * Looks the caller's number up in the employee directory table and returns a flat string map
 * (Connect ResponseValidation STRING_MAP): found, employeeId, vip, department, tier, lookupError.
 */
public class EmployeeLookupHandler implements RequestHandler<ConnectEvent, Map<String, String>> {

    private final AmazonDynamoDB dynamo;
    private final String tableName;

    /** Used by the Lambda runtime. */
    public EmployeeLookupHandler() {
        this(AmazonDynamoDBClientBuilder.standard()
                        .withClientConfiguration(new ClientConfiguration()
                                .withRequestTimeout(1000)
                                .withClientExecutionTimeout(2000)
                                .withMaxErrorRetry(1))
                        .build(),
                envOr("TABLE_NAME", "lfg-employee-directory"));
    }

    public EmployeeLookupHandler(AmazonDynamoDB dynamo, String tableName) {
        this.dynamo = dynamo;
        this.tableName = tableName;
    }

    @Override
    public Map<String, String> handleRequest(ConnectEvent event, Context context) {
        String phone = PhoneNumbers.normalize(event.getDetails().getContactData().getCustomerEndpoint().getAddress());
        if (phone == null) {
            return notFound(false);
        }
        GetItemResult result;
        try {
            result = dynamo.getItem(new GetItemRequest()
                    .withTableName(tableName)
                    .withKey(Collections.singletonMap("phone", new AttributeValue().withS(phone)))
                    .withConsistentRead(false));
        } catch (AmazonClientException e) {
            return notFound(true);
        }
        Map<String, AttributeValue> item = result.getItem();
        if (item == null) {
            return notFound(false);
        }
        Map<String, String> out = new HashMap<>();
        out.put("found", "true");
        out.put("employeeId", str(item.get("employeeId")));
        out.put("department", str(item.get("department")));
        out.put("tier", str(item.get("tier")));
        AttributeValue vip = item.get("vip");
        out.put("vip", vip != null && Boolean.TRUE.equals(vip.getBOOL()) ? "true" : "false");
        out.put("lookupError", "false");
        return out;
    }

    private static String str(AttributeValue v) {
        return v == null || v.getS() == null ? "" : v.getS();
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

    private static String envOr(String name, String fallback) {
        String v = System.getenv(name);
        return v == null || v.isEmpty() ? fallback : v;
    }
}
