package com.corvane.claimdesk.recon;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;
import java.time.LocalDate;

import org.junit.jupiter.api.Test;

class ExtractWriterTest {

    @Test
    void augustRecordMatchesProduction() {
        PaidLoss p = new PaidLoss("CLM-2025-114433", LocalDate.of(2025, 8, 14), new BigDecimal("1250.5"), "PAID");
        assertEquals("CLM-2025-11443314-Aug-25      1250.50PAID    ", ExtractWriter.record(p));
    }

    @Test
    void recordIsFortyFiveBytes() {
        PaidLoss p = new PaidLoss("CLM-2025-100001", LocalDate.of(2025, 10, 2), new BigDecimal("99.99"), "PARTIAL");
        assertEquals(ExtractWriter.RECORD_LENGTH, ExtractWriter.record(p).length());
    }
}
