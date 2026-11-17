package com.corvane.claimdesk.rating;

import sun.misc.BASE64Encoder;

public final class RatingExporter {
    public static String body(byte[] xml) {
        return new BASE64Encoder().encodeBuffer(xml);
    }
}
