package com.corvane.claimdesk.integration;

import javax.annotation.Resource;
import javax.enterprise.context.ApplicationScoped;
import javax.mail.Message;
import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeMessage;

@ApplicationScoped
public class MailNotifier {

    @Resource(lookup = "java:/mail/ClaimDesk")
    private Session session;

    public void notifySiu(String claim, int score) {
        try {
            MimeMessage m = new MimeMessage(session);
            m.setRecipients(Message.RecipientType.TO, InternetAddress.parse("siu-alerts@corvane.example"));
            m.setSubject("High fraud score on " + claim + ": " + score);
            m.setText("Review before the payment is released.");
            Transport.send(m);
        } catch (MessagingException e) {
            throw new IllegalStateException(e);
        }
    }
}
