package com.corvane.claimdesk.auth;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Date;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import com.unboundid.ldap.listener.InMemoryDirectoryServer;

class HiddenParityTest {

    static InMemoryDirectoryServer ds;
    static LdapRoleResolver ldap;
    static TestIssuer okta;
    static JwtRoleResolver jwt;
    static final List<String> USERS = List.of("ana", "ben", "cara", "dev", "eli", "gus");
    static final List<BigDecimal> AMOUNTS = List.of(new BigDecimal("500"), new BigDecimal("10000"), new BigDecimal("10000.01"),
            new BigDecimal("50000"), new BigDecimal("50000.01"), new BigDecimal("2000000"));

    @BeforeAll
    static void start() throws Exception {
        ds = Directory.start();
        ldap = new LdapRoleResolver(ds);
        okta = new TestIssuer("k-2026-10");
        jwt = new JwtRoleResolver(okta.publicJwks(), TestIssuer.ISSUER, TestIssuer.AUDIENCE);
    }

    @AfterAll
    static void stop() {
        ds.shutDown(true);
    }

    @Test
    void fullAuthorizationMatrixIsIdentical() throws Exception {
        int cells = 0;
        for (String u : USERS) {
            Set<Role> a = ldap.rolesFor(u);
            Set<Role> b = jwt.rolesFor(okta.tokenFor(u));
            for (Action action : Action.values()) {
                for (BigDecimal amt : AMOUNTS) {
                    assertEquals(ClaimPolicy.allowed(a, action, amt), ClaimPolicy.allowed(b, action, amt),
                            u + " " + action + " " + amt);
                    cells++;
                }
            }
        }
        assertEquals(USERS.size() * Action.values().length * AMOUNTS.size(), cells);
    }

    @Test
    void seniorAdjusterKeepsImpliedAdjusterRole() throws Exception {
        assertEquals(ldap.rolesFor("ben"), jwt.rolesFor(okta.tokenFor("ben")));
    }

    @Test
    void unknownGroupsGiveNoRoles() throws Exception {
        assertTrue(jwt.rolesFor(okta.tokenFor("gus")).isEmpty());
    }

    @Test
    void missingGroupsClaimMeansNoRoles() throws Exception {
        assertTrue(jwt.rolesFor(okta.sign(okta.claims("eli", null).build())).isEmpty());
    }

    @Test
    void singleStringGroupsClaim() throws Exception {
        assertEquals(Set.of(Role.MANAGER), jwt.rolesFor(okta.sign(okta.claims("cara", "APP_ClaimDesk_Managers").build())));
    }

    @Test
    void groupNamesAreExact() throws Exception {
        assertTrue(jwt.rolesFor(okta.sign(okta.claims("x", List.of("app_claimdesk_managers", "APP_ClaimDesk_Managers_Old")).build())).isEmpty());
    }

    @Test
    void wrongAudienceRejected() throws Exception {
        String t = okta.sign(okta.claims("cara", List.of("APP_ClaimDesk_Managers")).audience("api://policy-portal").build());
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(t));
    }

    @Test
    void wrongIssuerRejected() throws Exception {
        String t = okta.sign(okta.claims("cara", List.of("APP_ClaimDesk_Managers")).issuer("https://corvane.okta.example/oauth2/default").build());
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(t));
    }

    @Test
    void expiredBeyondSkewRejectedWithinSkewAccepted() throws Exception {
        long now = System.currentTimeMillis();
        String stale = okta.sign(okta.claims("ana", List.of("APP_ClaimDesk_Users")).expirationTime(new Date(now - 120_000)).build());
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(stale));
        String justExpired = okta.sign(okta.claims("ana", List.of("APP_ClaimDesk_Users")).expirationTime(new Date(now - 20_000)).build());
        assertEquals(Set.of(Role.USER), jwt.rolesFor(justExpired));
    }

    @Test
    void notYetValidRejected() throws Exception {
        long now = System.currentTimeMillis();
        String t = okta.sign(okta.claims("ana", List.of("APP_ClaimDesk_Users")).notBeforeTime(new Date(now + 600_000)).build());
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(t));
    }

    @Test
    void foreignKeyRejected() throws Exception {
        TestIssuer attacker = new TestIssuer("k-2026-10");
        String t = attacker.sign(attacker.claims("eve", List.of("APP_ClaimDesk_Managers")).build());
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(t));
    }

    @Test
    void unsignedTokenRejected() {
        String header = Base64.getUrlEncoder().withoutPadding().encodeToString("{\"alg\":\"none\"}".getBytes(StandardCharsets.UTF_8));
        long exp = System.currentTimeMillis() / 1000 + 3600;
        String body = Base64.getUrlEncoder().withoutPadding().encodeToString(("{\"iss\":\"" + TestIssuer.ISSUER + "\",\"aud\":\""
                + TestIssuer.AUDIENCE + "\",\"sub\":\"eve\",\"exp\":" + exp + ",\"iat\":" + (exp - 3600) + ",\"groups\":[\"APP_ClaimDesk_Managers\"]}")
                .getBytes(StandardCharsets.UTF_8));
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(header + "." + body + "."));
    }

    @Test
    void hmacWithPublicKeyRejected() throws Exception {
        byte[] secret = okta.publicJwks().toString().getBytes(StandardCharsets.UTF_8);
        JWTClaimsSet c = okta.claims("eve", List.of("APP_ClaimDesk_Managers")).build();
        SignedJWT forged = new SignedJWT(new JWSHeader.Builder(JWSAlgorithm.HS256).keyID("k-2026-10").build(), c);
        forged.sign(new MACSigner(secret));
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor(forged.serialize()));
    }

    @Test
    void garbageRejectedWithTheContractException() {
        assertThrows(InvalidTokenException.class, () -> jwt.rolesFor("not-a-jwt"));
    }

    @Test
    void secondKeyInJwksAccepted() throws Exception {
        TestIssuer next = new TestIssuer("k-2026-11");
        JWKSet both = new JWKSet(List.of(okta.key.toPublicJWK(), next.key.toPublicJWK()));
        JwtRoleResolver r = new JwtRoleResolver(both, TestIssuer.ISSUER, TestIssuer.AUDIENCE);
        assertEquals(Set.of(Role.USER, Role.AUDITOR), r.rolesFor(next.tokenFor("dev")));
    }
}
