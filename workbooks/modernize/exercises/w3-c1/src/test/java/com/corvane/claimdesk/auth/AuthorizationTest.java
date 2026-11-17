package com.corvane.claimdesk.auth;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.EnumSet;
import java.util.Set;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.unboundid.ldap.listener.InMemoryDirectoryServer;

class AuthorizationTest {

    static InMemoryDirectoryServer ds;
    static LdapRoleResolver ldap;
    static TestIssuer okta;
    static JwtRoleResolver jwt;

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
    void ldapBaselineNestedSeniorAdjuster() {
        assertEquals(EnumSet.of(Role.USER, Role.ADJUSTER, Role.SENIOR_ADJUSTER), ldap.rolesFor("ben"));
    }

    @Test
    void ldapBaselineDisabledAccountHasNoRoles() {
        assertTrue(ldap.rolesFor("fay").isEmpty());
    }

    @Test
    void ldapBaselineLimits() {
        Set<Role> ana = ldap.rolesFor("ana");
        assertTrue(ClaimPolicy.allowed(ana, Action.APPROVE_PAYMENT, new BigDecimal("10000")));
        assertFalse(ClaimPolicy.allowed(ana, Action.APPROVE_PAYMENT, new BigDecimal("10000.01")));
    }

    @Test
    void jwtAdjusterMatchesLdap() throws Exception {
        assertEquals(ldap.rolesFor("ana"), jwt.rolesFor(okta.tokenFor("ana")));
    }
}
