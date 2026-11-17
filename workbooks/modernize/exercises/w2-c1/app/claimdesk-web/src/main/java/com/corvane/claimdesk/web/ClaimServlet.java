package com.corvane.claimdesk.web;

import java.io.IOException;

import javax.inject.Inject;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.corvane.claimdesk.dao.ClaimDao;

public class ClaimServlet extends HttpServlet {

    @Inject
    private ClaimDao claims;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String number = req.getPathInfo().substring(1);
        if (req.getParameter("archiveYear") != null) {
            req.setAttribute("claim", claims.findArchived(number, Integer.parseInt(req.getParameter("archiveYear"))));
        } else {
            req.setAttribute("claim", claims.findByNumber(number));
        }
        req.getRequestDispatcher("/claim.jsp").forward(req, resp);
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String number = req.getPathInfo().substring(1);
        claims.addNote(number, req.getRemoteUser(), req.getParameter("text"));
        resp.sendRedirect(req.getContextPath() + "/claims/" + number);
    }
}
