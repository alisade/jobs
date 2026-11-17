package com.corvane.claimdesk.recon;

import java.io.IOException;
import java.io.Writer;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Nightly: data/paid-losses-<month>.csv -> target/CLMRECON.<month>.dat */
public final class ExtractJob {

    private ExtractJob() {
    }

    public static List<PaidLoss> read(Path csv) throws IOException {
        List<PaidLoss> rows = new ArrayList<>();
        List<String> lines = Files.readAllLines(csv, StandardCharsets.US_ASCII);
        for (String line : lines.subList(1, lines.size())) {
            String[] f = line.split(",");
            rows.add(new PaidLoss(f[0], LocalDate.parse(f[1]), new BigDecimal(f[2]), f[3]));
        }
        return rows;
    }

    public static void main(String[] args) throws IOException {
        Path in = Paths.get(args.length > 0 ? args[0] : "data/paid-losses-2025-09.csv");
        Path out = Paths.get(args.length > 1 ? args[1] : "target/CLMRECON.dat");
        Files.createDirectories(out.toAbsolutePath().getParent());
        try (Writer w = Files.newBufferedWriter(out, StandardCharsets.US_ASCII)) {
            ExtractWriter.write(read(in), w);
        }
        System.out.println("wrote " + out);
    }
}
