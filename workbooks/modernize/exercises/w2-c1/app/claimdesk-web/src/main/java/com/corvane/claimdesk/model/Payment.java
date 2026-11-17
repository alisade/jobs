package com.corvane.claimdesk.model;

import java.math.BigDecimal;

/** Mapped in META-INF/orm.xml (the 2012 team preferred XML mappings). */
public class Payment {
    private long id;
    private String claimNumber;
    private BigDecimal amount;
    private String approvedBy;

    protected Payment() {
    }

    public Payment(String claimNumber, BigDecimal amount, String approvedBy) {
        this.claimNumber = claimNumber;
        this.amount = amount;
        this.approvedBy = approvedBy;
    }

    public long getId() { return id; }
    public String getClaimNumber() { return claimNumber; }
    public BigDecimal getAmount() { return amount; }
    public String getApprovedBy() { return approvedBy; }
}
