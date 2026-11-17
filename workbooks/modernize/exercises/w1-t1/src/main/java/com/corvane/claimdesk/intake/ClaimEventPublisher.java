package com.corvane.claimdesk.intake;

import java.util.LinkedHashMap;
import java.util.Map;

import com.fasterxml.jackson.core.JsonProcessingException;

/** Builds the claim.opened v3 event that goes to the downstream queue (reserving, fraud, reinsurance). */
public final class ClaimEventPublisher {

    private ClaimEventPublisher() {
    }

    public static String claimOpened(FnolRecord r) throws JsonProcessingException {
        Map<String, Object> event = new LinkedHashMap<>();
        event.put("type", "claim.opened");
        event.put("schemaVersion", 3);
        event.put("claimId", r.claimId());
        event.put("policyNumber", r.policyNumber());
        event.put("lossDate", r.lossDate());
        event.put("lossCause", r.lossCause());
        return Json.MAPPER.writeValueAsString(event);
    }
}
