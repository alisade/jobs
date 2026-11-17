package com.corvane.claimdesk.intake;

import java.time.LocalDate;

/** First notice of loss, as the agent portal drops it into the intake inbox. */
public record FnolRecord(String claimId, String policyNumber, LocalDate lossDate, String lossCause,
                         String description, String reportedBy) {
}
