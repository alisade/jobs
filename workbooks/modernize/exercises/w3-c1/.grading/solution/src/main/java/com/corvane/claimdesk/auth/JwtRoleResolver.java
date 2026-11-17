package com.corvane.claimdesk.auth;

import java.text.ParseException;
import java.util.Collection;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import com.nimbusds.jose.proc.BadJOSEException;
import com.nimbusds.jose.proc.JWSVerificationKeySelector;
import com.nimbusds.jose.proc.SecurityContext;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.proc.ConfigurableJWTProcessor;
import com.nimbusds.jwt.proc.DefaultJWTClaimsVerifier;
import com.nimbusds.jwt.proc.DefaultJWTProcessor;

/**
 * Roles from the groups claim of an Okta access token. The decision ClaimPolicy makes must be
 * identical to the LDAP one, so this resolver reproduces two things LDAP gave for free:
 * nested groups (a senior adjuster is also an adjuster) and ignoring groups ClaimDesk does not know.
 */
public final class JwtRoleResolver implements RoleResolver {

    public static final long MAX_CLOCK_SKEW_SECONDS = 60;

    /** Okta group (synced from AD by the Okta AD agent) to the ClaimDesk roles it implies. */
    static final Map<String, Set<Role>> GROUP_TO_ROLES = Map.of(
            "APP_ClaimDesk_Users", EnumSet.of(Role.USER),
            "APP_ClaimDesk_Adjusters", EnumSet.of(Role.ADJUSTER),
            // LDAP: claims-senior-adjusters is nested in claims-adjusters; Okta emits direct groups only
            "APP_ClaimDesk_SeniorAdjusters", EnumSet.of(Role.SENIOR_ADJUSTER, Role.ADJUSTER),
            "APP_ClaimDesk_Managers", EnumSet.of(Role.MANAGER),
            "APP_ClaimDesk_Auditors", EnumSet.of(Role.AUDITOR));

    private final ConfigurableJWTProcessor<SecurityContext> processor;

    public JwtRoleResolver(JWKSet keys, String issuer, String audience) {
        DefaultJWTProcessor<SecurityContext> p = new DefaultJWTProcessor<>();
        // RS256 only: "none" and HS256 (algorithm confusion with the public key as secret) never verify.
        p.setJWSKeySelector(new JWSVerificationKeySelector<>(JWSAlgorithm.RS256, new ImmutableJWKSet<>(keys)));
        DefaultJWTClaimsVerifier<SecurityContext> v = new DefaultJWTClaimsVerifier<>(
                audience, new JWTClaimsSet.Builder().issuer(issuer).build(), Set.of("exp", "iat", "sub"));
        v.setMaxClockSkew((int) MAX_CLOCK_SKEW_SECONDS);
        p.setJWTClaimsSetVerifier(v);
        this.processor = p;
    }

    @Override
    public Set<Role> rolesFor(String bearerToken) {
        JWTClaimsSet claims;
        try {
            claims = processor.process(bearerToken, null);
        } catch (ParseException | BadJOSEException | JOSEException | RuntimeException e) {
            throw new InvalidTokenException("token rejected: " + e.getMessage(), e);
        }
        Set<Role> roles = EnumSet.noneOf(Role.class);
        for (String group : groups(claims.getClaim("groups"))) {
            Set<Role> mapped = GROUP_TO_ROLES.get(group);
            if (mapped != null) {
                roles.addAll(mapped);
            }
        }
        return roles;
    }

    private static Collection<String> groups(Object claim) {
        if (claim instanceof String s) {
            return List.of(s);
        }
        if (claim instanceof Collection<?> c) {
            return c.stream().filter(String.class::isInstance).map(String.class::cast).toList();
        }
        return List.of();
    }
}
