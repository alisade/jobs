package com.corvane.claimdesk.notes;

import java.io.IOException;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/** The container forwards every error here; clients (the agent portal) parse this JSON. */
public class ErrorServlet extends HttpServlet {

    @Override
    protected void service(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Object code = req.getAttribute("javax.servlet.error.status_code");
        Object message = req.getAttribute("javax.servlet.error.message");
        Object exception = req.getAttribute("javax.servlet.error.exception");
        int status = code instanceof Integer i ? i : 500;
        String error;
        if (exception instanceof Throwable) {
            error = "internal error";
        } else if (message instanceof String m && !m.isEmpty()) {
            error = m;
        } else {
            error = status == 404 ? "not found" : "error";
        }
        ClaimServlet.json(resp, status, "{\"status\":" + status + ",\"error\":" + Json.str(error) + "}");
    }
}
