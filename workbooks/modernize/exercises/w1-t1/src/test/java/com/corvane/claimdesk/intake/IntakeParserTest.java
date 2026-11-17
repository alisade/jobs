package com.corvane.claimdesk.intake;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class IntakeParserTest {

    @Test
    void parsesInboxFile() throws Exception {
        FnolRecord r = IntakeParser.parse(Paths.get("inbox/FNOL-20261112-0001.json"));
        assertEquals("CLM-2026-118204", r.claimId());
        assertEquals(LocalDate.of(2026, 11, 11), r.lossDate());
    }

    @Test
    void keyOrderDoesNotMatter() throws Exception {
        assertEquals("AU-9920114", IntakeParser.parse(Paths.get("inbox/FNOL-20261112-0002.json")).policyNumber());
    }

    @Test
    void rejectsMissingLossDate(@TempDir Path dir) throws Exception {
        Path f = dir.resolve("bad.json");
        Files.writeString(f, "{\"claimId\":\"X\",\"policyNumber\":\"Y\"}");
        assertThrows(IOException.class, () -> IntakeParser.parse(f));
    }
}
