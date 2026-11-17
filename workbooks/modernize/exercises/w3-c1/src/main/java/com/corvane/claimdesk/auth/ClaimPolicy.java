package com.corvane.claimdesk.auth;

import java.math.BigDecimal;
import java.util.Set;

/**
 * The authorization rules, unchanged since 2014 (CLM-311). Payment approval limits:
 * adjuster 10,000; senior adjuster 50,000; manager unlimited.
 */
public final class ClaimPolicy {

    static final BigDecimal ADJUSTER_LIMIT = new BigDecimal("10000");
    static final BigDecimal SENIOR_LIMIT = new BigDecimal("50000");

    private ClaimPolicy() {
    }

    public static boolean allowed(Set<Role> roles, Action action, BigDecimal amount) {
        switch (action) {
            case VIEW_CLAIM:
                return roles.contains(Role.USER) || roles.contains(Role.AUDITOR);
            case ADD_NOTE:
                return roles.contains(Role.USER);
            case VIEW_AUDIT:
                return roles.contains(Role.AUDITOR) || roles.contains(Role.MANAGER);
            case REASSIGN_CLAIM:
                return roles.contains(Role.MANAGER);
            case APPROVE_PAYMENT:
                if (roles.contains(Role.MANAGER)) {
                    return true;
                }
                if (roles.contains(Role.SENIOR_ADJUSTER)) {
                    return amount.compareTo(SENIOR_LIMIT) <= 0;
                }
                if (roles.contains(Role.ADJUSTER)) {
                    return amount.compareTo(ADJUSTER_LIMIT) <= 0;
                }
                return false;
            default:
                return false;
        }
    }
}
