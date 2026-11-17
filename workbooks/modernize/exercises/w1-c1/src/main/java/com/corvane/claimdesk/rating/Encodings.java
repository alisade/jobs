package com.corvane.claimdesk.rating;

import java.lang.reflect.Field;
import java.nio.charset.Charset;

/**
 * Forces UTF-8 for the whole JVM. Added in 2017 (CLM-1840) because the JBoss hosts ran with
 * LANG=en_US.ISO-8859-1 and insured names with accents were mangled in the feed.
 */
public final class Encodings {

    private static volatile boolean initialised;

    private Encodings() {
    }

    public static synchronized void forceUtf8() {
        if (initialised) {
            return;
        }
        try {
            System.setProperty("file.encoding", "UTF-8");
            // Reset the cached default so the JVM re-reads file.encoding.
            Field cached = Charset.class.getDeclaredField("defaultCharset");
            cached.setAccessible(true);
            cached.set(null, null);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("could not force UTF-8", e);
        }
        initialised = true;
    }

    public static Charset feedCharset() {
        forceUtf8();
        return Charset.defaultCharset();
    }
}
