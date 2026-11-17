package com.corvane.claimdesk.integration;

import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;

/**
 * Sent adjuster assignments to the RightFax server. Replaced by MailNotifier in 2016 (CLM-902);
 * nothing calls this any more. Kept "for reference".
 */
@Deprecated
public class LegacyFaxGateway {

    private static final String HOST = "rightfax01.corvane.local";
    private static final int PORT = 8099;

    public void send(String number, byte[] tiff) throws IOException {
        try (Socket s = new Socket(HOST, PORT); OutputStream out = s.getOutputStream()) {
            out.write(("FAX " + number + "\n").getBytes());
            out.write(tiff);
        }
    }
}
