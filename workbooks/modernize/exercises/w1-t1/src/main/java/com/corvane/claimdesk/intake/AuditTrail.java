package com.corvane.claimdesk.intake;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import com.fasterxml.jackson.databind.JsonNode;

/** Regulatory audit: a fingerprint of each FNOL as received, independent of whitespace and key order. */
public final class AuditTrail {

    private AuditTrail() {
    }

    public static String fingerprint(byte[] rawJson) throws IOException {
        JsonNode tree = Json.MAPPER.readTree(rawJson);
        String canonical = Json.MAPPER.copy()
                .configure(com.fasterxml.jackson.databind.SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS, true)
                .writeValueAsString(Json.MAPPER.convertValue(tree, java.util.TreeMap.class));
        try {
            byte[] d = MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(d);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
