package com.corvane.claimdesk.integration;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

import javax.annotation.Resource;
import javax.enterprise.context.ApplicationScoped;

/** Calls the fraud scoring service (Sentinel, run by the SIU team). */
@ApplicationScoped
public class FraudClient {

    @Resource(lookup = "java:global/claimdesk/fraudScoreUrl")
    private String fraudScoreUrl;

    public int score(String claim, BigDecimal amount) {
        try {
            HttpURLConnection con = (HttpURLConnection) new URL(fraudScoreUrl).openConnection();
            con.setRequestMethod("POST");
            con.setConnectTimeout(2000);
            con.setReadTimeout(5000);
            con.setDoOutput(true);
            con.setRequestProperty("Content-Type", "application/json");
            try (OutputStream out = con.getOutputStream()) {
                out.write(("{\"claim\":\"" + claim + "\",\"amount\":" + amount + "}").getBytes(StandardCharsets.UTF_8));
            }
            try (InputStream in = con.getInputStream()) {
                return Integer.parseInt(new String(in.readAllBytes(), StandardCharsets.UTF_8).trim());
            }
        } catch (IOException e) {
            return 0; // fail open: SIU agreed in 2018 that a down scorer must not block payments
        }
    }
}
