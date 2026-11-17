package com.corvane.claimdesk.rating;

import java.io.StringWriter;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;

import sun.misc.BASE64Encoder;

/**
 * Builds the Halberd Re feed envelope for one rated claim:
 *
 * <pre>
 * BEGIN CORVANE-RATING 1
 * id: RT-2026-000184
 * sha256: (hex of the XML bytes)
 * (base64 of the XML, wrapped the way the partner's parser expects)
 * END CORVANE-RATING
 * </pre>
 *
 * The partner's parser is a COBOL job; it is strict about line lengths and line endings.
 */
public final class RatingExporter {

    private static final JAXBContext CONTEXT;

    static {
        try {
            CONTEXT = JAXBContext.newInstance(RatingResult.class);
        } catch (JAXBException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private RatingExporter() {
    }

    public static String toXml(RatingResult result) {
        try {
            Marshaller m = CONTEXT.createMarshaller();
            m.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, Boolean.TRUE);
            m.setProperty(Marshaller.JAXB_ENCODING, "UTF-8");
            StringWriter out = new StringWriter();
            m.marshal(result, out);
            return out.toString();
        } catch (JAXBException e) {
            throw new IllegalStateException("cannot marshal " + result.getId(), e);
        }
    }

    public static String envelope(RatingResult result) {
        byte[] xml = toXml(result).getBytes(Encodings.feedCharset());
        StringBuilder sb = new StringBuilder();
        sb.append("BEGIN CORVANE-RATING 1\n");
        sb.append("id: ").append(result.getId()).append('\n');
        sb.append("sha256: ").append(sha256Hex(xml)).append('\n');
        sb.append(new BASE64Encoder().encodeBuffer(xml));
        sb.append("END CORVANE-RATING\n");
        return sb.toString();
    }

    static String sha256Hex(byte[] data) {
        try {
            byte[] d = MessageDigest.getInstance("SHA-256").digest(data);
            StringBuilder hex = new StringBuilder();
            for (byte b : d) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
