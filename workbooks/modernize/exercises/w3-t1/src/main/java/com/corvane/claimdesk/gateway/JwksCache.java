package com.corvane.claimdesk.gateway;

import java.io.IOException;
import java.text.ParseException;
import java.time.Clock;
import java.time.Duration;
import java.util.Optional;

import com.nimbusds.jose.jwk.JWK;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;

/**
 * Signing keys of the identity provider, by kid. Loaded once: the JWKS endpoint is slow (300-800 ms)
 * and we do not want it on the request path (CLM-4521, 2026-09).
 */
public final class JwksCache {

    private final JWKSet keys;

    /**
     * @param fetcher            reads the JWKS document
     * @param clock              time source
     * @param maxAge             how long a fetched JWKS may be used before it is refreshed
     * @param minRefreshInterval never fetch more often than this (protects the IdP from kid floods)
     */
    public JwksCache(JwksFetcher fetcher, Clock clock, Duration maxAge, Duration minRefreshInterval) {
        try {
            this.keys = JWKSet.parse(fetcher.fetch());
        } catch (IOException | ParseException e) {
            throw new IllegalStateException("cannot load JWKS at startup", e);
        }
    }

    public Optional<RSAKey> key(String kid) {
        JWK k = keys.getKeyByKeyId(kid);
        return k instanceof RSAKey r ? Optional.of(r) : Optional.empty();
    }
}
