package com.corvane.claimdesk.gateway;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.jwk.JWK;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.gen.RSAKeyGenerator;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

/** Local stand-in for the Okta authorization server: rotating signing keys and a JWKS endpoint. */
final class FakeIdp implements JwksFetcher {

    static final String ISSUER = "https://corvane.okta.example/oauth2/aus1claimdesk";
    static final String AUDIENCE = "api://claimdesk";

    final List<RSAKey> published = new ArrayList<>();
    RSAKey active;
    final AtomicInteger fetches = new AtomicInteger();
    volatile boolean down;
    final MutableClock clock = new MutableClock(Instant.parse("2026-11-10T13:00:00Z"));

    FakeIdp() throws Exception {
        active = newKey("k-2026-10");
        published.add(active);
    }

    static RSAKey newKey(String kid) throws Exception {
        return new RSAKeyGenerator(2048).keyID(kid).generate();
    }

    /** Okta-style rotation: publish the new key and sign with it; the old key stays published for now. */
    void rotate(String kid) throws Exception {
        active = newKey(kid);
        published.add(active);
    }

    void retire(String kid) {
        published.removeIf(k -> k.getKeyID().equals(kid));
    }

    @Override
    public String fetch() throws IOException {
        fetches.incrementAndGet();
        if (down) {
            throw new IOException("connect timed out: corvane.okta.example:443");
        }
        List<JWK> pub = new ArrayList<>();
        published.forEach(k -> pub.add(k.toPublicJWK()));
        return new JWKSet(pub).toString();
    }

    String token(String sub) throws Exception {
        Instant now = clock.instant();
        JWTClaimsSet c = new JWTClaimsSet.Builder().issuer(ISSUER).audience(AUDIENCE).subject(sub)
                .issueTime(Date.from(now)).expirationTime(Date.from(now.plus(Duration.ofHours(1)))).build();
        SignedJWT jwt = new SignedJWT(new JWSHeader.Builder(JWSAlgorithm.RS256).keyID(active.getKeyID()).build(), c);
        jwt.sign(new RSASSASigner(active));
        return jwt.serialize();
    }

    static final class MutableClock extends Clock {
        private Instant now;

        MutableClock(Instant start) {
            now = start;
        }

        void advance(Duration d) {
            now = now.plus(d);
        }

        @Override
        public Instant instant() {
            return now;
        }

        @Override
        public java.time.ZoneId getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(java.time.ZoneId zone) {
            return this;
        }
    }
}
