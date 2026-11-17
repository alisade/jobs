package com.corvane.claimdesk.gateway;

import java.text.ParseException;
import java.time.Clock;
import java.util.Date;
import java.util.Optional;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.crypto.RSASSAVerifier;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

/** Verifies Okta access tokens at the ClaimDesk API edge. Returns the subject, or empty (the caller sends 401). */
public final class TokenVerifier {

    static final long SKEW_SECONDS = 60;

    private final JwksCache keys;
    private final String issuer;
    private final String audience;
    private final Clock clock;

    public TokenVerifier(JwksCache keys, String issuer, String audience, Clock clock) {
        this.keys = keys;
        this.issuer = issuer;
        this.audience = audience;
        this.clock = clock;
    }

    public Optional<String> verify(String token) {
        try {
            SignedJWT jwt = SignedJWT.parse(token);
            if (!JWSAlgorithm.RS256.equals(jwt.getHeader().getAlgorithm())) {
                return Optional.empty();
            }
            Optional<RSAKey> key = keys.key(jwt.getHeader().getKeyID());
            if (key.isEmpty() || !jwt.verify(new RSASSAVerifier(key.get()))) {
                return Optional.empty();
            }
            JWTClaimsSet c = jwt.getJWTClaimsSet();
            Date now = Date.from(clock.instant());
            if (!issuer.equals(c.getIssuer()) || c.getAudience() == null || !c.getAudience().contains(audience)
                    || c.getExpirationTime() == null
                    || c.getExpirationTime().getTime() + SKEW_SECONDS * 1000 < now.getTime()) {
                return Optional.empty();
            }
            return Optional.ofNullable(c.getSubject());
        } catch (ParseException | JOSEException e) {
            return Optional.empty();
        }
    }
}
