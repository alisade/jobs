package com.corvane.claimdesk.rating;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class HiddenUpgradeTest {

    private static final String UMLAUT_NAME = "M\u00fcller-L\u00fcdenscheid Fr\u00e8res GmbH";

    @Test
    void xmlMatchesGoldenMaster() throws Exception {
        assertEquals(Golden.read("RT-2026-000184.xml"), RatingExporter.toXml(Golden.harborPoint()));
    }

    @Test
    void belowRetentionEnvelope() throws Exception {
        RatingResult r = Golden.ENGINE.rate("RT-2026-000185", "CMP-0039950", "Lindqvist Cold Storage AB", "FIRE", new BigDecimal("212500.50"));
        assertEquals(Golden.read("RT-2026-000185.env"), RatingExporter.envelope(r));
    }

    @Test
    void layerCappedEnvelope() throws Exception {
        RatingResult r = Golden.ENGINE.rate("RT-2026-000186", "CMP-0044802", "Okonkwo Logistics Ltd", "FLOOD", new BigDecimal("6120000"));
        assertEquals(new BigDecimal("4750000.00"), r.getCededLoss());
        assertEquals(Golden.read("RT-2026-000186.env"), RatingExporter.envelope(r));
    }

    @Test
    void accentedNamesStayUtf8() throws Exception {
        RatingResult r = Golden.ENGINE.rate("RT-2026-000190", "CMP-0045001", UMLAUT_NAME, "THEFT", new BigDecimal("990000"));
        assertEquals(Golden.read("RT-2026-000190.env"), RatingExporter.envelope(r));
    }

    @Test
    void partnerLineFormat() {
        String env = RatingExporter.envelope(Golden.harborPoint());
        assertFalse(env.contains("\r"), "partner parser rejects CR");
        List<String> body = Stream.of(env.split("\n")).skip(3).collect(Collectors.toList());
        body = body.subList(0, body.size() - 1);
        for (int i = 0; i < body.size() - 1; i++) {
            assertEquals(76, body.get(i).length(), "base64 line " + i + " must be 76 chars");
        }
        assertTrue(env.endsWith("\nEND CORVANE-RATING\n"));
    }

    @Test
    void feedCharsetIsUtf8WithoutReflection() {
        assertEquals(StandardCharsets.UTF_8, Encodings.feedCharset());
        Encodings.forceUtf8();
        assertEquals(StandardCharsets.UTF_8, Encodings.feedCharset());
    }

    @Test
    void classesCompiledForJava21() throws IOException {
        try (InputStream in = RatingExporter.class.getResourceAsStream("RatingExporter.class");
             DataInputStream d = new DataInputStream(in)) {
            assertEquals(0xCAFEBABE, d.readInt());
            d.readUnsignedShort();
            assertEquals(65, d.readUnsignedShort(), "class file major version (65 = Java 21)");
        }
    }

    @Test
    void noInternalApisOrAddOpens() throws IOException {
        String pom = new String(Files.readAllBytes(Paths.get("pom.xml")), StandardCharsets.UTF_8);
        assertFalse(pom.contains("add-opens"), "no --add-opens: fix the code, do not open java.base");
        assertFalse(pom.contains("add-exports"), "no --add-exports");
        assertFalse(pom.contains("<groupId>javax.xml.bind</groupId>"), "use Jakarta XML Binding, not the retired javax artifact");
        try (Stream<Path> files = Files.walk(Paths.get("src/main/java"))) {
            for (Path p : files.filter(f -> f.toString().endsWith(".java")).collect(Collectors.toList())) {
                String src = new String(Files.readAllBytes(p), StandardCharsets.UTF_8);
                assertFalse(src.contains("sun.misc"), p + " still uses sun.misc");
                assertFalse(src.contains("setAccessible"), p + " still uses reflective access");
                assertFalse(src.contains("javax.xml.bind"), p + " still imports javax.xml.bind");
            }
        }
    }

    @Test
    void nightlyBatchRunsEndToEnd(@TempDir Path out) throws Exception {
        Main.main(new String[] {"data/claims-2026-11-12.csv", out.toString()});
        assertEquals(Golden.read("RT-2026-000184.env"),
                new String(Files.readAllBytes(out.resolve("RT-2026-000184.env")), StandardCharsets.US_ASCII));
        try (Stream<Path> s = Files.list(out)) {
            assertEquals(3, s.count());
        }
    }
}
