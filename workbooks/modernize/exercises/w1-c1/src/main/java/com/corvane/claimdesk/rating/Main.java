package com.corvane.claimdesk.rating;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

/** Nightly batch: read claims CSV, rate, write one envelope per claim into the outbox. */
public final class Main {

    private Main() {
    }

    public static void main(String[] args) throws IOException {
        Path in = Paths.get(args.length > 0 ? args[0] : "data/claims-2026-11-12.csv");
        Path outbox = Paths.get(args.length > 1 ? args[1] : "target/outbox");
        Files.createDirectories(outbox);
        RatingEngine engine = new RatingEngine(new BigDecimal("250000"), new BigDecimal("4750000"));
        List<String> lines = Files.readAllLines(in, StandardCharsets.UTF_8);
        int n = 0;
        for (String line : lines.subList(1, lines.size())) {
            String[] f = line.split(",", -1);
            RatingResult r = engine.rate(f[0], f[1], f[2], f[3], new BigDecimal(f[4]));
            Files.write(outbox.resolve(r.getId() + ".env"), RatingExporter.envelope(r).getBytes(StandardCharsets.US_ASCII));
            n++;
        }
        System.out.println("wrote " + n + " envelopes to " + outbox);
    }
}
