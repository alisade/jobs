package com.corvane.claimdesk.intake;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Reads one FNOL file from the inbox. */
public final class IntakeParser {

    private IntakeParser() {
    }

    public static FnolRecord parse(Path file) throws IOException {
        FnolRecord r = Json.MAPPER.readValue(Files.readAllBytes(file), FnolRecord.class);
        if (r.claimId() == null || r.policyNumber() == null || r.lossDate() == null) {
            throw new IOException(file.getFileName() + ": claimId, policyNumber and lossDate are required");
        }
        return r;
    }
}
