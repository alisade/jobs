package com.corvane.claimdesk.model;

public class Claim {
    private final long id;
    private final String claimNumber;
    private final String policyNumber;
    private final String status;
    private final long adjusterId;

    public Claim(long id, String claimNumber, String policyNumber, String status, long adjusterId) {
        this.id = id;
        this.claimNumber = claimNumber;
        this.policyNumber = policyNumber;
        this.status = status;
        this.adjusterId = adjusterId;
    }

    public long getId() { return id; }
    public String getClaimNumber() { return claimNumber; }
    public String getPolicyNumber() { return policyNumber; }
    public String getStatus() { return status; }
    public long getAdjusterId() { return adjusterId; }
}
