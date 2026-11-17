package com.corvane.claimdesk.rating;

import java.math.BigDecimal;
import java.math.RoundingMode;

/** Excess-of-loss cession: everything above the retention is ceded, capped at the layer limit. */
public final class RatingEngine {

    private final BigDecimal retention;
    private final BigDecimal layerLimit;

    public RatingEngine(BigDecimal retention, BigDecimal layerLimit) {
        this.retention = retention;
        this.layerLimit = layerLimit;
    }

    public RatingResult rate(String id, String policyNumber, String insuredName, String lossCause, BigDecimal grossLoss) {
        BigDecimal excess = grossLoss.subtract(retention).max(BigDecimal.ZERO);
        BigDecimal ceded = excess.min(layerLimit).setScale(2, RoundingMode.HALF_UP);
        return new RatingResult(id, policyNumber, insuredName, lossCause,
                grossLoss.setScale(2, RoundingMode.HALF_UP), retention.setScale(2, RoundingMode.HALF_UP), ceded);
    }
}
