package com.corvane.claimdesk.notes;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;

/** In-memory store for the service (production wires JdbcClaimRepository; see JdbcSupport). */
public final class ClaimRepository {

    private final Map<String, Claim> claims = new ConcurrentHashMap<>();

    public static ClaimRepository seeded() {
        ClaimRepository r = new ClaimRepository();
        r.put(new Claim("CLM-2026-118204", "HO-3318820", "OPEN", List.of("FNOL received from agent 4471")));
        r.put(new Claim("CLM-2026-118205", "AU-9920114", "OPEN", List.of()));
        r.put(new Claim("CLM-2026-117990", "CMP-0042117", "CLOSED", List.of("Paid in full", "File closed")));
        return r;
    }

    public void put(Claim c) {
        claims.put(c.number(), c);
    }

    public Optional<Claim> find(String number) {
        return Optional.ofNullable(claims.get(number));
    }

    public List<Claim> byStatus(String status) {
        List<Claim> out = new ArrayList<>();
        new TreeMap<>(claims).values().forEach(c -> {
            if (c.status().equals(status)) {
                out.add(c);
            }
        });
        return out;
    }

    public synchronized Claim addNote(String number, String text) {
        Claim c = claims.get(number);
        List<String> notes = new ArrayList<>(c.notes());
        notes.add(text);
        Claim updated = new Claim(c.number(), c.policy(), c.status(), List.copyOf(notes));
        claims.put(number, updated);
        return updated;
    }
}
