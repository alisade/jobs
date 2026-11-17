package com.corvane.claimdesk.gateway;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.Optional;

import org.junit.jupiter.api.Test;

class TokenVerifierTest {

    static TokenVerifier verifier(FakeIdp idp) {
        JwksCache cache = new JwksCache(idp, idp.clock, Duration.ofHours(1), Duration.ofSeconds(30));
        return new TokenVerifier(cache, FakeIdp.ISSUER, FakeIdp.AUDIENCE, idp.clock);
    }

    @Test
    void verifiesTokenSignedWithPublishedKey() throws Exception {
        FakeIdp idp = new FakeIdp();
        assertEquals(Optional.of("ana@corvane.example"), verifier(idp).verify(idp.token("ana@corvane.example")));
    }

    @Test
    void rejectsGarbage() throws Exception {
        assertTrue(verifier(new FakeIdp()).verify("abc.def.ghi").isEmpty());
    }

    @Test
    void acceptsTokensAfterKeyRotation() throws Exception {
        FakeIdp idp = new FakeIdp();
        TokenVerifier v = verifier(idp);
        idp.clock.advance(Duration.ofHours(20));
        idp.rotate("k-2026-11");
        assertEquals(Optional.of("ben@corvane.example"), v.verify(idp.token("ben@corvane.example")));
    }
}
