package com.corvane.claimdesk.recon;

import java.io.IOException;
import java.io.Writer;
import java.math.RoundingMode;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.time.ZoneId;

/**
 * Fixed-width extract for the CLMRECON reconciliation job on the mainframe (copybook CLMRECRD,
 * see evidence/CLMRECRD.cpy). 45 bytes per record, LF line ends, ASCII. Written since 2011.
 *
 * <pre>
 * cols  1-15  claim number, left aligned, space padded
 * cols 16-24  paid date dd-MMM-yy (UK style, agreed with the mainframe team in 2011)
 * cols 25-37  amount, right aligned, 2 decimals, no grouping
 * cols 38-45  status, left aligned, space padded
 * </pre>
 */
public final class ExtractWriter {

    public static final int RECORD_LENGTH = 45;

    private ExtractWriter() {
    }

    public static String record(PaidLoss p) {
        SimpleDateFormat date = new SimpleDateFormat("dd-MMM-yy", Locale.UK);
        Date d = Date.from(p.paidDate().atStartOfDay(ZoneId.of("America/New_York")).toInstant());
        date.setTimeZone(java.util.TimeZone.getTimeZone("America/New_York"));
        return padRight(p.claimNumber(), 15)
                + date.format(d)
                + padLeft(p.amount().setScale(2, RoundingMode.HALF_UP).toPlainString(), 13)
                + padRight(p.status(), 8);
    }

    public static void write(List<PaidLoss> rows, Writer out) throws IOException {
        for (PaidLoss p : rows) {
            out.write(record(p));
            out.write('\n');
        }
    }

    static String padRight(String s, int w) {
        StringBuilder b = new StringBuilder(s);
        while (b.length() < w) {
            b.append(' ');
        }
        return b.toString();
    }

    static String padLeft(String s, int w) {
        StringBuilder b = new StringBuilder();
        while (b.length() + s.length() < w) {
            b.append(' ');
        }
        return b.append(s).toString();
    }
}
