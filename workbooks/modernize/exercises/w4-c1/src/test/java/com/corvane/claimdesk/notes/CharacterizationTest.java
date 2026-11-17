package com.corvane.claimdesk.notes;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Map;
import java.util.stream.Stream;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

/** Must be green before, during and after the migration. Do not edit the golden files. */
class CharacterizationTest {

    static NotesServer server;
    static int port;

    @BeforeAll
    static void start() throws Exception {
        server = new NotesServer();
        port = server.start(0, ClaimRepository.seeded());
    }

    @AfterAll
    static void stop() throws Exception {
        server.stop();
    }

    static Stream<Arguments> flows() {
        return Flows.all().entrySet().stream().map(e -> Arguments.of(e.getKey(), e.getValue()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("flows")
    void flowMatchesGoldenMaster(String name, String[] flow) throws Exception {
        String actual = Flows.run(port, flow);
        if (Boolean.getBoolean("golden.record")) {
            Flows.record(name, actual);
        }
        assertEquals(Flows.golden(name), actual, name);
    }
}
