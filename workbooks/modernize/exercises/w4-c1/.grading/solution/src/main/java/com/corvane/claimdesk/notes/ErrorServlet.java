package com.corvane.claimdesk.notes;

import java.io.IOException;

import jakarta.servlet.RequestDispatcher;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * The container forwards every error here; clients (the agent portal) parse this JSON.
 * Attribute names come from the RequestDispatcher constants: Servlet 5+ renamed them to
 * jakarta.servlet.error.*, and a string literal would silently read null.
 */
public class ErrorServlet extends HttpServlet {

    @Override
    protected void service(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Object code = req.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);
        Object message = req.getAttribute(RequestDispatcher.ERROR_MESSAGE);
        Object exception = req.getAttribute(RequestDispatcher.ERROR_EXCEPTION);
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
