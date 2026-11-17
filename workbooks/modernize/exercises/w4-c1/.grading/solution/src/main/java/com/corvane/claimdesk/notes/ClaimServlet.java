package com.corvane.claimdesk.notes;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/** GET /claims/{number}, GET /claims?status=X, POST /claims/{number}/notes */
public class ClaimServlet extends HttpServlet {

    private final ClaimRepository repo;

    public ClaimServlet(ClaimRepository repo) {
        this.repo = repo;
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String path = req.getPathInfo();
        if (path == null || "/".equals(path)) {
            String status = req.getParameter("status");
            if (status == null) {
                resp.sendError(HttpServletResponse.SC_BAD_REQUEST, "status parameter required");
                return;
            }
            json(resp, 200, Json.claims(repo.byStatus(status)));
            return;
        }
        String number = path.substring(1);
        if (number.startsWith("BOOM")) {
            throw new IllegalStateException("simulated defect for " + number);
        }
        var c = repo.find(number);
        if (c.isEmpty()) {
            resp.sendError(HttpServletResponse.SC_NOT_FOUND, "claim not found");
            return;
        }
        json(resp, 200, Json.claim(c.get()));
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String path = req.getPathInfo();
        if (path == null || !path.endsWith("/notes")) {
            resp.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED, "only notes can be posted");
            return;
        }
        String number = path.substring(1, path.length() - "/notes".length());
        if (repo.find(number).isEmpty()) {
            resp.sendError(HttpServletResponse.SC_NOT_FOUND, "claim not found");
            return;
        }
        String text = new String(req.getInputStream().readAllBytes(), StandardCharsets.UTF_8).trim();
        if (text.isEmpty() || text.length() > 2000) {
            resp.sendError(HttpServletResponse.SC_BAD_REQUEST, "note must be 1-2000 characters");
            return;
        }
        resp.setHeader("Location", req.getContextPath() + "/claims/" + number);
        json(resp, 201, Json.claim(repo.addNote(number, text)));
    }

    static void json(HttpServletResponse resp, int status, String body) throws IOException {
        resp.setStatus(status);
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(body);
    }
}
