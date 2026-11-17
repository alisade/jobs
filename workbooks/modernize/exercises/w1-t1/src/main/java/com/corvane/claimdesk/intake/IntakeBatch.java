package com.corvane.claimdesk.intake;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/** Nightly intake: inbox/*.json -> outbox/events.jsonl + outbox/audit.csv */
public final class IntakeBatch {

    private IntakeBatch() {
    }

    public static int run(Path inbox, Path outbox) throws IOException {
        Files.createDirectories(outbox);
        List<Path> files = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(inbox, "*.json")) {
            ds.forEach(files::add);
        }
        files.sort(null);
        List<String> events = new ArrayList<>();
        List<String> audit = new ArrayList<>();
        audit.add("file,claimId,sha256");
        for (Path f : files) {
            FnolRecord r = IntakeParser.parse(f);
            System.out.println("[intake] parsed " + f.getFileName() + " claim=" + r.claimId());
            events.add(ClaimEventPublisher.claimOpened(r));
            audit.add(f.getFileName() + "," + r.claimId() + "," + AuditTrail.fingerprint(Files.readAllBytes(f)));
        }
        Files.write(outbox.resolve("events.jsonl"), events, StandardCharsets.UTF_8);
        Files.write(outbox.resolve("audit.csv"), audit, StandardCharsets.UTF_8);
        return files.size();
    }

    public static void main(String[] args) throws IOException {
        Path inbox = Paths.get(args.length > 0 ? args[0] : "inbox");
        Path outbox = Paths.get(args.length > 1 ? args[1] : "target/outbox");
        int n = run(inbox, outbox);
        System.out.println("[intake] done: " + n + " FNOL files");
    }
}
