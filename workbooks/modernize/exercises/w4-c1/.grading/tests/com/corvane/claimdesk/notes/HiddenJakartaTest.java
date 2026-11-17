package com.corvane.claimdesk.notes;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;

class HiddenJakartaTest {

    static List<Path> mainSources() throws Exception {
        try (Stream<Path> s = Files.walk(Paths.get("src/main/java"))) {
            return s.filter(p -> p.toString().endsWith(".java")).collect(Collectors.toList());
        }
    }

    @Test
    void runsOnServlet6Container() {
        jakarta.servlet.http.HttpServlet probe = new ErrorServlet();
        assertTrue(probe instanceof jakarta.servlet.Servlet);
        assertTrue(org.apache.catalina.util.ServerInfo.getServerNumber().startsWith("10.1."),
                "expected Tomcat 10.1 (Servlet 6.0), got " + org.apache.catalina.util.ServerInfo.getServerNumber());
    }

    @Test
    void noJavaxServletLeft() throws Exception {
        for (Path p : mainSources()) {
            String src = Files.readString(p);
            assertFalse(src.contains("javax.servlet"), p + " still references javax.servlet (imports or string literals)");
        }
        assertFalse(Files.readString(Paths.get("pom.xml")).contains("<version>9.0."), "pom.xml still pins Tomcat 9");
    }

    @Test
    void jdkJavaxPackagesWereNotRenamed() throws Exception {
        assertEquals("javax.sql.DataSource", JdbcSupport.class.getMethod("lookup", String.class).getReturnType().getName(),
                "javax.sql and javax.naming belong to the JDK, not Jakarta EE");
        String src = Files.readString(Paths.get("src/main/java/com/corvane/claimdesk/notes/JdbcSupport.java"));
        assertTrue(src.contains("javax.naming.InitialContext"));
    }

    @Test
    void errorPagesKeepTheirContractOnTheNewContainer() throws Exception {
        NotesServer s = new NotesServer();
        int port = s.start(0, ClaimRepository.seeded());
        try {
            for (String name : List.of("02-get-unknown-claim", "04-list-missing-param", "07-unmapped-path", "08-server-defect")) {
                assertEquals(Flows.golden(name), Flows.run(port, Flows.all().get(name)), name);
            }
        } finally {
            s.stop();
        }
    }

    @Test
    void notesPersistAcrossRequests() throws Exception {
        NotesServer s = new NotesServer();
        ClaimRepository repo = ClaimRepository.seeded();
        int port = s.start(0, repo);
        try {
            Flows.run(port, new String[] {"POST", "/claimdesk/claims/CLM-2026-117990/notes", "Reopened for subrogation"});
            String got = Flows.run(port, new String[] {"GET", "/claimdesk/claims/CLM-2026-117990", null});
            assertTrue(got.contains("\"notes\":[\"Paid in full\",\"File closed\",\"Reopened for subrogation\"]"), got);
        } finally {
            s.stop();
        }
    }
}
