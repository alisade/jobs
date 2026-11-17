package com.corvane.claimdesk.rating;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

/** Characterization tests: the feed bytes must not change across the JDK upgrade. */
class RatingExporterTest {

    @Test
    void cessionAboveRetention() {
        RatingResult r = Golden.harborPoint();
        assertEquals(new BigDecimal("1135000.00"), r.getCededLoss());
    }

    @Test
    void xmlHasTheFeedNamespace() {
        String xml = RatingExporter.toXml(Golden.harborPoint());
        assertTrue(xml.contains("urn:corvane:claims:rating:1"), xml);
        assertTrue(xml.contains("<ns2:policyNumber>CMP-0042117</ns2:policyNumber>") || xml.contains("policyNumber>CMP-0042117<"), xml);
    }

    @Test
    void envelopeMatchesProductionGoldenMaster() throws Exception {
        assertEquals(Golden.read("RT-2026-000184.env"), RatingExporter.envelope(Golden.harborPoint()));
    }
}
