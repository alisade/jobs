package com.corvane.claimdesk.auth;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import com.unboundid.ldap.sdk.Filter;
import com.unboundid.ldap.sdk.LDAPException;
import com.unboundid.ldap.sdk.LDAPInterface;
import com.unboundid.ldap.sdk.SearchResult;
import com.unboundid.ldap.sdk.SearchResultEntry;
import com.unboundid.ldap.sdk.SearchScope;

/**
 * Today's resolver: groups from the corporate directory, including nested groups, mapped to roles.
 * Disabled accounts (accountStatus=disabled) get no roles.
 */
public final class LdapRoleResolver implements RoleResolver {

    static final String PEOPLE = "ou=people,dc=corvane,dc=local";
    static final String GROUPS = "ou=groups,dc=corvane,dc=local";

    static final Map<String, Role> GROUP_TO_ROLE = Map.of(
            "claims-users", Role.USER,
            "claims-adjusters", Role.ADJUSTER,
            "claims-senior-adjusters", Role.SENIOR_ADJUSTER,
            "claims-managers", Role.MANAGER,
            "claims-auditors", Role.AUDITOR);

    private final LDAPInterface ldap;

    public LdapRoleResolver(LDAPInterface ldap) {
        this.ldap = ldap;
    }

    @Override
    public Set<Role> rolesFor(String uid) {
        try {
            String userDn = "uid=" + Filter.encodeValue(uid) + "," + PEOPLE;
            SearchResultEntry user = ldap.getEntry(userDn, "accountStatus");
            if (user == null || "disabled".equalsIgnoreCase(user.getAttributeValue("accountStatus"))) {
                return EnumSet.noneOf(Role.class);
            }
            Set<Role> roles = EnumSet.noneOf(Role.class);
            Set<String> seen = new HashSet<>();
            Deque<String> todo = new ArrayDeque<>();
            todo.add(userDn);
            while (!todo.isEmpty()) {
                String member = todo.poll();
                SearchResult r = ldap.search(GROUPS, SearchScope.SUB, Filter.createEqualityFilter("member", member), "cn");
                for (SearchResultEntry g : r.getSearchEntries()) {
                    if (seen.add(g.getDN())) {
                        Role role = GROUP_TO_ROLE.get(g.getAttributeValue("cn"));
                        if (role != null) {
                            roles.add(role);
                        }
                        todo.add(g.getDN()); // nested groups: a group that is a member of a group
                    }
                }
            }
            return roles;
        } catch (LDAPException e) {
            throw new IllegalStateException("LDAP lookup failed for " + uid, e);
        }
    }
}
