package com.corvane.claimdesk.auth;

import java.util.Set;

import com.nimbusds.jose.jwk.JWKSet;

/**
 * Tomorrow's resolver: roles from the groups claim of an Okta access token (JWT).
 * See README.md for the contract and the Okta group mapping.
 */
public final class JwtRoleResolver implements RoleResolver {

    public static final long MAX_CLOCK_SKEW_SECONDS = 60;

    private final JWKSet keys;
    private final String issuer;
    private final String audience;

    public JwtRoleResolver(JWKSet keys, String issuer, String audience) {
        this.keys = keys;
        this.issuer = issuer;
        this.audience = audience;
    }

    @Override
    public Set<Role> rolesFor(String bearerToken) {
        // TODO: validate the token (RS256 only, signature against keys by kid, iss, aud, exp/nbf with
        // MAX_CLOCK_SKEW_SECONDS) and map the groups claim to roles so ClaimPolicy decides exactly as it
        // does with LdapRoleResolver.
        throw new UnsupportedOperationException("not implemented yet");
    }
}
