package com.corvane.claimdesk.recon;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.StringWriter;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.Locale;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class HiddenExtractTest {

    static final String[] COPYBOOK_MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};

    @Test
    void everyMonthUsesTheCopybookAbbreviation() {
        for (int m = 1; m <= 12; m++) {
            String r = ExtractWriter.record(new PaidLoss("CLM-2025-100001", LocalDate.of(2025, m, 5), new BigDecimal("10.00"), "PAID"));
            assertEquals("05-" + COPYBOOK_MONTHS[m - 1] + "-25", r.substring(15, 24), "month " + m);
            assertEquals(45, r.length(), "month " + m);
        }
    }

    @Test
    void independentOfTheDefaultLocale() {
        Locale saved = Locale.getDefault();
        try {
            for (Locale l : new Locale[] {Locale.GERMANY, Locale.forLanguageTag("en-AU"), Locale.FRANCE}) {
                Locale.setDefault(l);
                String r = ExtractWriter.record(new PaidLoss("CLM-2025-100001", LocalDate.of(2025, 6, 30), new BigDecimal("1234567.5"), "PAID"));
                assertEquals("CLM-2025-10000130-Jun-25   1234567.50PAID    ", r, l.toString());
            }
        } finally {
            Locale.setDefault(saved);
        }
    }

    @ParameterizedTest
    @ValueSource(strings = {"2025-08", "2025-09", "2025-10"})
    void parallelRunMatchesJdk8Production(String month) throws Exception {
        StringWriter w = new StringWriter();
        ExtractWriter.write(ExtractJob.read(Paths.get("data/paid-losses-" + month + ".csv")), w);
        assertEquals(Files.readString(Paths.get("evidence/CLMRECON." + month + ".jdk8-prod.dat")), w.toString());
    }

    @Test
    void overflowingFieldsFailFast() {
        assertThrows(IllegalArgumentException.class, () -> ExtractWriter.record(
                new PaidLoss("CLM-2025-1000012", LocalDate.of(2025, 1, 1), BigDecimal.ONE, "PAID")));
        assertThrows(IllegalArgumentException.class, () -> ExtractWriter.record(
                new PaidLoss("CLM-2025-100001", LocalDate.of(2025, 1, 1), new BigDecimal("12345678901.00"), "PAID")));
        assertThrows(IllegalArgumentException.class, () -> ExtractWriter.record(
                new PaidLoss("CLM-2025-100001", LocalDate.of(2025, 1, 1), BigDecimal.ONE, "WRITTENOFF")));
    }

    @Test
    void jobWritesAsciiFile(@TempDir Path dir) throws Exception {
        Path out = dir.resolve("CLMRECON.dat");
        ExtractJob.main(new String[] {"data/paid-losses-2025-09.csv", out.toString()});
        byte[] bytes = Files.readAllBytes(out);
        assertEquals(24 * 46, bytes.length);
        assertEquals(Files.readString(Paths.get("evidence/CLMRECON.2025-09.jdk8-prod.dat")), new String(bytes, StandardCharsets.US_ASCII));
    }
}
