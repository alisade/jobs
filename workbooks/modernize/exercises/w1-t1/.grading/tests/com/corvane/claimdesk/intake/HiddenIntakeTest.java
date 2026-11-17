package com.corvane.claimdesk.intake;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class HiddenIntakeTest {

    @Test
    void jacksonArtifactsConverge() {
        String core = com.fasterxml.jackson.core.json.PackageVersion.VERSION.toString();
        String databind = com.fasterxml.jackson.databind.cfg.PackageVersion.VERSION.toString();
        String jsr310 = com.fasterxml.jackson.datatype.jsr310.PackageVersion.VERSION.toString();
        assertEquals(databind, core, "jackson-core on the classpath must match jackson-databind");
        assertEquals(databind, jsr310, "jackson-datatype-jsr310 must match jackson-databind");
    }

    @Test
    void jacksonCoreStillMeetsTheSecurityFloor() {
        com.fasterxml.jackson.core.Version v = com.fasterxml.jackson.core.json.PackageVersion.VERSION;
        assertTrue(v.getMajorVersion() == 2 && v.getMinorVersion() >= 17, "SEC-2291 floor and databind 2.17 both satisfied, got " + v);
    }

    @Test
    void claimOpenedEventV3() throws Exception {
        FnolRecord r = IntakeParser.parse(Paths.get("inbox/FNOL-20261112-0001.json"));
        assertEquals("{\"type\":\"claim.opened\",\"schemaVersion\":3,\"claimId\":\"CLM-2026-118204\",\"policyNumber\":\"HO-3318820\","
                + "\"lossDate\":\"2026-11-11\",\"lossCause\":\"WATER\"}", ClaimEventPublisher.claimOpened(r));
    }

    @Test
    void auditFingerprintIsStable() throws Exception {
        assertEquals("ef12034f334d1cca96e075e26364ef554742205a281328ae22aba34f56b953e3",
                AuditTrail.fingerprint(Files.readAllBytes(Paths.get("inbox/FNOL-20261112-0001.json"))));
    }

    @Test
    void auditFingerprintIgnoresKeyOrderAndWhitespace() throws Exception {
        byte[] a = "{\"b\":1,\"a\":{\"y\":2,\"x\":3}}".getBytes(StandardCharsets.UTF_8);
        byte[] b = "{ \"a\" : {\"x\":3, \"y\":2},\n \"b\":1 }".getBytes(StandardCharsets.UTF_8);
        byte[] c = "{\"a\":{\"x\":3,\"y\":2},\"b\":2}".getBytes(StandardCharsets.UTF_8);
        assertEquals(AuditTrail.fingerprint(a), AuditTrail.fingerprint(b));
        assertNotEquals(AuditTrail.fingerprint(a), AuditTrail.fingerprint(c));
    }

    @Test
    void nightlyBatchProcessesTheWholeInbox(@TempDir Path out) throws Exception {
        assertEquals(3, IntakeBatch.run(Paths.get("inbox"), out));
        List<String> events = Files.readAllLines(out.resolve("events.jsonl"));
        assertEquals(3, events.size());
        assertTrue(events.get(2).contains("\"claimId\":\"CLM-2026-118206\""));
        assertEquals(4, Files.readAllLines(out.resolve("audit.csv")).size());
    }

    @Test
    void buildGuardsAgainstDowngrades() throws Exception {
        String pom = Files.readString(Paths.get("pom.xml"));
        assertTrue(pom.contains("requireUpperBoundDeps") || pom.contains("dependencyConvergence"),
                "add a Maven enforcer rule that fails the build on this class of conflict");
        assertFalse(pom.contains("<version>2.13.5</version>"), "the stale jackson-core pin is still in pom.xml");
    }
}
