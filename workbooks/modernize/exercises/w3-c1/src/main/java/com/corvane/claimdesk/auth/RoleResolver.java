package com.corvane.claimdesk.auth;

import java.util.Set;

/** Turns a credential (an LDAP uid today, a bearer token tomorrow) into application roles. */
public interface RoleResolver {
    Set<Role> rolesFor(String credential);
}
