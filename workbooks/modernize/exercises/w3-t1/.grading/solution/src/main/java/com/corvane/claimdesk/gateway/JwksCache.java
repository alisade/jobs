package com.corvane.claimdesk.gateway;

import java.io.IOException;
import java.text.ParseException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.logging.Logger;

import com.nimbusds.jose.jwk.JWK;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;

/**
 * Signing keys of the identity provider, by kid. Off the request path in the common case, but never
 * stale for long: refreshed after maxAge, and on an unknown kid (key rotation) at most once per
 * minRefreshInterval. A failed refresh keeps the keys we have.
 */
public final class JwksCache {

    private static final Logger LOG = Logger.getLogger(JwksCache.class.getName());

    private final JwksFetcher fetcher;
    private final Clock clock;
    private final Duration maxAge;
    private final Duration minRefreshInterval;

    private volatile JWKSet keys;
    private volatile Instant fetchedAt;
    private Instant lastMissRefresh = Instant.MIN;
    private Instant lastAgeAttempt = Instant.MIN;

    public JwksCache(JwksFetcher fetcher, Clock clock, Duration maxAge, Duration minRefreshInterval) {
        this.fetcher = fetcher;
        this.clock = clock;
        this.maxAge = maxAge;
        this.minRefreshInterval = minRefreshInterval;
        if (!fetch()) {
            throw new IllegalStateException("cannot load JWKS at startup");
        }
    }

    public Optional<RSAKey> key(String kid) {
        refreshIfOld();
        Optional<RSAKey> k = find(keys, kid);
        if (k.isEmpty()) {
            JWKSet seen = keys;
            synchronized (this) {
                if (keys == seen) {
                    refreshOnMiss(); // unknown kid: maybe the IdP rotated; rate-limited
                }
            }
            k = find(keys, kid);
        }
        return k;
    }

    private static Optional<RSAKey> find(JWKSet set, String kid) {
        JWK k = kid == null ? null : set.getKeyByKeyId(kid);
        return k instanceof RSAKey r ? Optional.of(r) : Optional.empty();
    }

    private synchronized void refreshIfOld() {
        Instant now = clock.instant();
        // after maxAge; if the IdP is down, retry no more than once per minRefreshInterval
        if (now.isAfter(fetchedAt.plus(maxAge)) && !now.isBefore(lastAgeAttempt.plus(minRefreshInterval))) {
            lastAgeAttempt = now;
            fetch();
        }
    }

    private synchronized void refreshOnMiss() {
        Instant now = clock.instant();
        if (now.isBefore(lastMissRefresh.plus(minRefreshInterval))) {
            return;
        }
        lastMissRefresh = now;
        fetch();
    }

    private synchronized boolean fetch() {
        try {
            keys = JWKSet.parse(fetcher.fetch());
            fetchedAt = clock.instant();
            return true;
        } catch (IOException | ParseException e) {
            LOG.warning("JWKS refresh failed, keeping " + (keys == null ? 0 : keys.size()) + " cached keys: " + e.getMessage());
            return false;
        }
    }
}
