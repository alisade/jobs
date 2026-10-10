package com.larkspur.helpdesk;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.services.dynamodbv2.AbstractAmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.GetItemRequest;
import com.amazonaws.services.dynamodbv2.model.GetItemResult;
import com.amazonaws.services.lambda.runtime.events.ConnectEvent;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;

public class EmployeeLookupHandlerTest {

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

    static class FakeDynamo extends AbstractAmazonDynamoDB {
        final Map<String, Map<String, AttributeValue>> rows = new HashMap<>();
        RuntimeException fail;

        @Override
        public GetItemResult getItem(GetItemRequest request) {
            if (fail != null) {
                throw fail;
            }
            return new GetItemResult().withItem(rows.get(request.getKey().get("phone").getS()));
        }
    }

    @Test
    public void foundEmployeeIsReturnedAsFlatStrings() {
        FakeDynamo db = new FakeDynamo();
        Map<String, AttributeValue> row = new HashMap<>();
        row.put("employeeId", new AttributeValue().withS("E10442"));
        row.put("department", new AttributeValue().withS("Finance"));
        row.put("tier", new AttributeValue().withS("gold"));
        row.put("vip", new AttributeValue().withBOOL(true));
        db.rows.put("+16175550142", row);
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("true", out.get("found"));
        assertEquals("E10442", out.get("employeeId"));
        assertEquals("true", out.get("vip"));
    }

    @Test
    public void unknownNumberIsNotFound() {
        Map<String, String> out = new EmployeeLookupHandler(new FakeDynamo(), "t").handleRequest(call("+16175550199"), null);
        assertEquals("false", out.get("found"));
        assertEquals("false", out.get("vip"));
    }

    @Test
    public void dynamoErrorDegradesToNotFound() {
        FakeDynamo db = new FakeDynamo();
        db.fail = new AmazonServiceException("ProvisionedThroughputExceededException");
        Map<String, String> out = new EmployeeLookupHandler(db, "t").handleRequest(call("+16175550142"), null);
        assertEquals("false", out.get("found"));
        assertEquals("true", out.get("lookupError"));
    }
}
