package com.corvane.claimdesk.gateway;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

class HiddenRotationTest {

    static JwksCache cache(FakeIdp idp) {
        return new JwksCache(idp, idp.clock, Duration.ofHours(1), Duration.ofSeconds(30));
    }

    @Test
    void unknownKidTriggersOneRefetch() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        int before = idp.fetches.get();
        idp.rotate("k-2026-11");
        assertTrue(c.key("k-2026-11").isPresent());
        assertEquals(before + 1, idp.fetches.get());
    }

    @Test
    void knownKidDoesNotFetch() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        int before = idp.fetches.get();
        for (int i = 0; i < 50; i++) {
            assertTrue(c.key("k-2026-10").isPresent());
        }
        assertEquals(before, idp.fetches.get());
    }

    @Test
    void unknownKidFloodIsRateLimited() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        int before = idp.fetches.get();
        for (int i = 0; i < 100; i++) {
            assertTrue(c.key("attacker-" + i).isEmpty());
            idp.clock.advance(Duration.ofMillis(100));
        }
        assertTrue(idp.fetches.get() - before <= 1, "at most one fetch per minRefreshInterval, got " + (idp.fetches.get() - before));
    }

    @Test
    void refetchAllowedAgainAfterInterval() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        assertTrue(c.key("nope").isEmpty());
        idp.clock.advance(Duration.ofSeconds(31));
        idp.rotate("k-2026-11");
        assertTrue(c.key("k-2026-11").isPresent());
    }

    @Test
    void maxAgeRefreshDropsRetiredKeys() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        idp.rotate("k-2026-11");
        idp.retire("k-2026-10");
        idp.clock.advance(Duration.ofMinutes(61));
        assertTrue(c.key("k-2026-10").isEmpty(), "a key the IdP stopped publishing must stop verifying after maxAge");
        assertTrue(c.key("k-2026-11").isPresent());
    }

    @Test
    void idpOutageKeepsServingCachedKeys() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        idp.down = true;
        idp.clock.advance(Duration.ofMinutes(90));
        assertTrue(c.key("k-2026-10").isPresent(), "a failed refresh must not wipe the keys");
        assertTrue(c.key("k-unknown").isEmpty());
    }

    @Test
    void endToEndRotationOnLongRunningNode() throws Exception {
        FakeIdp idp = new FakeIdp();
        TokenVerifier v = new TokenVerifier(cache(idp), FakeIdp.ISSUER, FakeIdp.AUDIENCE, idp.clock);
        String old = idp.token("cara@corvane.example");
        idp.clock.advance(Duration.ofMinutes(5));
        idp.rotate("k-2026-11");
        assertEquals(Optional.of("cara@corvane.example"), v.verify(old), "tokens signed with the previous key still work");
        assertEquals(Optional.of("dev@corvane.example"), v.verify(idp.token("dev@corvane.example")));
    }

    @Test
    void concurrentLookupsAfterRotationFetchOnce() throws Exception {
        FakeIdp idp = new FakeIdp();
        JwksCache c = cache(idp);
        idp.rotate("k-2026-11");
        int before = idp.fetches.get();
        ExecutorService pool = Executors.newFixedThreadPool(8);
        try {
            List<Future<Boolean>> fs = new ArrayList<>();
            for (int i = 0; i < 64; i++) {
                fs.add(pool.submit(() -> c.key("k-2026-11").isPresent()));
            }
            for (Future<Boolean> f : fs) {
                assertTrue(f.get(10, TimeUnit.SECONDS));
            }
        } finally {
            pool.shutdownNow();
        }
        assertTrue(idp.fetches.get() - before <= 1, "concurrent misses should share one refresh, got " + (idp.fetches.get() - before));
    }
}
