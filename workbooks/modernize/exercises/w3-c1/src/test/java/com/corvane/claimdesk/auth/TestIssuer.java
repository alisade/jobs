package com.corvane.claimdesk.auth;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.Map;

import com.nimbusds.jose.JOSEObjectType;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.gen.RSAKeyGenerator;
import com.nimbusds.jose.util.JSONObjectUtils;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

/** A local stand-in for the Okta authorization server: signs access tokens, publishes a JWKS. */
final class TestIssuer {

    static final String ISSUER = "https://corvane.okta.example/oauth2/aus1claimdesk";
    static final String AUDIENCE = "api://claimdesk";

    final RSAKey key;

    TestIssuer(String kid) throws Exception {
        key = new RSAKeyGenerator(2048).keyID(kid).generate();
    }

    JWKSet publicJwks() {
        return new JWKSet(key.toPublicJWK());
    }

    JWTClaimsSet.Builder claims(String uid, Object groups) {
        long now = System.currentTimeMillis();
        JWTClaimsSet.Builder b = new JWTClaimsSet.Builder()
                .issuer(ISSUER).audience(AUDIENCE).subject(uid + "@corvane.example")
                .claim("uid", uid).claim("scp", List.of("claims.read", "claims.write"))
                .issueTime(new Date(now)).notBeforeTime(new Date(now)).expirationTime(new Date(now + 3600_000));
        if (groups != null) {
            b.claim("groups", groups);
        }
        return b;
    }

    String sign(JWTClaimsSet claims) throws Exception {
        SignedJWT jwt = new SignedJWT(new JWSHeader.Builder(JWSAlgorithm.RS256).keyID(key.getKeyID()).type(JOSEObjectType.JWT).build(), claims);
        jwt.sign(new RSASSASigner(key));
        return jwt.serialize();
    }

    String tokenFor(String uid) throws Exception {
        return sign(claims(uid, oktaGroups().get(uid)).build());
    }

    @SuppressWarnings("unchecked")
    static Map<String, Object> oktaGroups() throws Exception {
        try (InputStream in = TestIssuer.class.getResourceAsStream("/okta-users.json")) {
            return (Map<String, Object>) (Map<?, ?>) JSONObjectUtils.parse(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }
}
