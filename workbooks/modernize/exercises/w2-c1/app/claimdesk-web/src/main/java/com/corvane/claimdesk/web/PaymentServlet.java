package com.corvane.claimdesk.web;

import java.io.IOException;
import java.math.BigDecimal;

import javax.annotation.Resource;
import javax.inject.Inject;
import javax.jms.JMSContext;
import javax.jms.Queue;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.corvane.claimdesk.dao.PaymentDao;
import com.corvane.claimdesk.dao.ReserveDao;
import com.corvane.claimdesk.integration.FraudClient;
import com.corvane.claimdesk.integration.MailNotifier;

public class PaymentServlet extends HttpServlet {

    private static final BigDecimal SUPERVISOR_LIMIT = new BigDecimal("25000");

    @Inject private PaymentDao payments;
    @Inject private ReserveDao reserves;
    @Inject private FraudClient fraud;
    @Inject private MailNotifier mail;
    @Inject private JMSContext jms;

    @Resource(lookup = "java:/jms/queue/ReservingEvents")
    private Queue reservingEvents;

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String claim = req.getParameter("claim");
        BigDecimal amount = new BigDecimal(req.getParameter("amount"));
        if (amount.compareTo(SUPERVISOR_LIMIT) > 0 && !req.isUserInRole("CLAIMS_SUPERVISOR")) {
            resp.sendError(HttpServletResponse.SC_FORBIDDEN, "payments over 25000 need a supervisor");
            return;
        }
        int score = fraud.score(claim, amount);
        if (score > 80) {
            mail.notifySiu(claim, score);
        }
        long id = payments.record(claim, amount, req.getRemoteUser());
        reserves.release(claim, amount);
        jms.createProducer().send(reservingEvents, "payment.recorded " + claim + " " + id);
        resp.setStatus(HttpServletResponse.SC_CREATED);
    }
}
