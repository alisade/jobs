package com.larkspur.helpdesk;

import com.amazonaws.services.lambda.runtime.events.ConnectEvent;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.DynamoDbException;
import software.amazon.awssdk.services.dynamodb.model.GetItemRequest;
import software.amazon.awssdk.services.dynamodb.model.GetItemResponse;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class EmployeeLookupHandlerTest {

    static ConnectEvent call(String from) {
        return ConnectEvent.builder()
                .withName("ContactFlowEvent")
                .withDetails(ConnectEvent.Details.builder()
                        .withContactData(ConnectEvent.ContactData.builder()
                                .withContactId("6ca32fbd-8f92-46af-92a5-6b0f970f0efe")
                                .withChannel("VOICE")
                                .withCustomerEndpoint(ConnectEvent.CustomerEndpoint.builder().withAddress(from).withType("TELEPHONE_NUMBER").build())
                                .build())
                        .withParameters(new HashMap<>())
                        .build())
                .build();
    }

    static class FakeDynamo implements DynamoDbClient {
        final Map<String, Map<String, AttributeValue>> rows = new HashMap<>();
        RuntimeException fail;

        @Override
        public GetItemResponse getItem(GetItemRequest request) {
            if (fail != null) {
                throw fail;
            }
            Map<String, AttributeValue> row = rows.get(request.key().get("phone").s());
            return row == null ? GetItemResponse.builder().build() : GetItemResponse.builder().item(row).build();
        }

        @Override
        public String serviceName() {
            return "dynamodb";
        }

        @Override
        public void close() {
        }
    }

    @Test
    void foundEmployeeIsReturnedAsFlatStrings() {
        FakeDynamo db = new FakeDynamo();
        db.rows.put("+16175550142", Map.of(
                "employeeId", AttributeValue.fromS("E10442"),
                "department", AttributeValue.fromS("Finance"),
                "tier", AttributeValue.fromS("gold"),
                "vip", AttributeValue.fromBool(true)));
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("true", out.get("found"));
        assertEquals("E10442", out.get("employeeId"));
        assertEquals("true", out.get("vip"));
    }

    @Test
    void unknownNumberIsNotFound() {
        Map<String, String> out = new EmployeeLookupHandler(new FakeDynamo(), "t").handleRequest(call("+16175550199"), null);
        assertEquals("false", out.get("found"));
        assertEquals("false", out.get("vip"));
    }

    @Test
    void dynamoErrorDegradesToNotFound() {
        FakeDynamo db = new FakeDynamo();
        db.fail = DynamoDbException.builder().message("ProvisionedThroughputExceededException").build();
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("false", out.get("found"));
        assertEquals("true", out.get("lookupError"));
    }
}
