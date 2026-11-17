package com.corvane.claimdesk.rating;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;

/**
 * The feed is always UTF-8. The 2017 reflection hack that reset Charset.defaultCharset (CLM-1840)
 * is gone: java.base does not open java.nio.charset on JDK 17+, and JDK 18+ defaults to UTF-8
 * anyway (JEP 400). Every byte conversion in the feed names the charset explicitly instead.
 */
public final class Encodings {

    private Encodings() {
    }

    /** Kept for callers that still invoke it; nothing to do any more. */
    public static void forceUtf8() {
        // no-op: see class comment
    }

    public static Charset feedCharset() {
        return StandardCharsets.UTF_8;
    }
}
