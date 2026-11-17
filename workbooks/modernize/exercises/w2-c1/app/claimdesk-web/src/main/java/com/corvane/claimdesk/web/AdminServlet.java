package com.corvane.claimdesk.web;

import java.io.IOException;
import java.util.Set;

import javax.inject.Inject;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.corvane.claimdesk.dao.RoleDao;

/** Admin console. Container security already limits /admin/* to CLAIMS_ADMIN. */
public class AdminServlet extends HttpServlet {

    @Inject
    private RoleDao roles;

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Set<String> appRoles = roles.rolesFor(req.getRemoteUser());
        if ("reassign".equals(req.getParameter("action")) && !appRoles.contains("REASSIGN_CLAIMS")) {
            resp.sendError(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        resp.setStatus(HttpServletResponse.SC_NO_CONTENT);
    }
}
