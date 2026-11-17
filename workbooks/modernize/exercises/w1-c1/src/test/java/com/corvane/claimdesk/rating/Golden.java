package com.corvane.claimdesk.rating;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;

/** Golden-master helpers. The files under src/test/resources/golden were captured from production (JDK 8). */
final class Golden {

    static final RatingEngine ENGINE = new RatingEngine(new BigDecimal("250000"), new BigDecimal("4750000"));

    private Golden() {
    }

    static String read(String name) throws IOException {
        try (InputStream in = Golden.class.getResourceAsStream("/golden/" + name)) {
            if (in == null) {
                throw new IOException("missing golden file " + name);
            }
            return new String(in.readAllBytes(), StandardCharsets.US_ASCII);
        }
    }

    static RatingResult harborPoint() {
        return ENGINE.rate("RT-2026-000184", "CMP-0042117", "Harbor Point Marina LLC", "WINDSTORM", new BigDecimal("1385000.00"));
    }
}
