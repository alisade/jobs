package com.corvane.claimdesk.notes;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Characterization (golden master) harness: the HTTP flows the agent portal depends on, rendered as
 * status + content type + X-Request-Id + body. Run with -Dgolden.record=true to re-record (only with
 * an approved reason: the goldens are the contract).
 */
final class Flows {

    static final Path GOLDEN = Paths.get("src/test/resources/golden");
    static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    private Flows() {
    }

    /** name -> {method, path, body or null} */
    static Map<String, String[]> all() {
        Map<String, String[]> f = new LinkedHashMap<>();
        f.put("01-get-claim", new String[] {"GET", "/claimdesk/claims/CLM-2026-118204", null});
        f.put("02-get-unknown-claim", new String[] {"GET", "/claimdesk/claims/CLM-1999-000001", null});
        f.put("03-list-open", new String[] {"GET", "/claimdesk/claims?status=OPEN", null});
        f.put("04-list-missing-param", new String[] {"GET", "/claimdesk/claims", null});
        f.put("05-add-note", new String[] {"POST", "/claimdesk/claims/CLM-2026-118205/notes", "Inspector booked for 2026-11-14"});
        f.put("06-empty-note", new String[] {"POST", "/claimdesk/claims/CLM-2026-118205/notes", "   "});
        f.put("07-unmapped-path", new String[] {"GET", "/claimdesk/policies/HO-3318820", null});
        f.put("08-server-defect", new String[] {"GET", "/claimdesk/claims/BOOM-1", null});
        return f;
    }

    static String run(int port, String[] flow) throws Exception {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create("http://localhost:" + port + flow[1]))
                .timeout(Duration.ofSeconds(10)).header("X-Request-Id", "golden-1");
        b = flow[2] == null ? b.method(flow[0], HttpRequest.BodyPublishers.noBody())
                : b.method(flow[0], HttpRequest.BodyPublishers.ofString(flow[2]));
        HttpResponse<String> r = HTTP.send(b.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        return "status: " + r.statusCode() + "\n"
                + "content-type: " + r.headers().firstValue("Content-Type").orElse("-").toLowerCase().replace(" ", "") + "\n"
                + "x-request-id: " + r.headers().firstValue("X-Request-Id").orElse("-") + "\n"
                + "location: " + r.headers().firstValue("Location").orElse("-") + "\n"
                + "\n" + r.body() + "\n";
    }

    static String golden(String name) throws Exception {
        return Files.readString(GOLDEN.resolve(name + ".txt"));
    }

    static void record(String name, String text) throws Exception {
        Files.createDirectories(GOLDEN);
        Files.writeString(GOLDEN.resolve(name + ".txt"), text);
    }
}
