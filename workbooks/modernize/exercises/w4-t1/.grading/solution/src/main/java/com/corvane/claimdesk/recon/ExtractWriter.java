package com.corvane.claimdesk.recon;

import java.io.IOException;
import java.io.Writer;
import java.math.RoundingMode;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeFormatterBuilder;
import java.time.temporal.ChronoField;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Fixed-width extract for the CLMRECON reconciliation job on the mainframe (copybook CLMRECRD,
 * see evidence/CLMRECRD.cpy). 45 bytes per record, LF line ends, ASCII. Written since 2011.
 *
 * <pre>
 * cols  1-15  claim number, left aligned, space padded
 * cols 16-24  paid date dd-MMM-yy with the copybook's month abbreviations
 * cols 25-37  amount, right aligned, 2 decimals, no grouping
 * cols 38-45  status, left aligned, space padded
 * </pre>
 *
 * The month names are part of the file contract, so they are spelled out here instead of coming
 * from locale data: JDK 9+ uses CLDR locale data (JEP 252), where en_GB abbreviates September as
 * "Sept", which made every September record 46 bytes.
 */
public final class ExtractWriter {

    public static final int RECORD_LENGTH = 45;

    private static final Map<Long, String> MONTHS = Map.ofEntries(
            Map.entry(1L, "Jan"), Map.entry(2L, "Feb"), Map.entry(3L, "Mar"), Map.entry(4L, "Apr"),
            Map.entry(5L, "May"), Map.entry(6L, "Jun"), Map.entry(7L, "Jul"), Map.entry(8L, "Aug"),
            Map.entry(9L, "Sep"), Map.entry(10L, "Oct"), Map.entry(11L, "Nov"), Map.entry(12L, "Dec"));

    static final DateTimeFormatter PAID_DATE = new DateTimeFormatterBuilder()
            .appendPattern("dd-")
            .appendText(ChronoField.MONTH_OF_YEAR, MONTHS)
            .appendPattern("-yy")
            .toFormatter(Locale.ROOT);

    private ExtractWriter() {
    }

    public static String record(PaidLoss p) {
        String r = field(p.claimNumber(), 15, false, "claim number")
                + field(PAID_DATE.format(p.paidDate()), 9, false, "paid date")
                + field(p.amount().setScale(2, RoundingMode.HALF_UP).toPlainString(), 13, true, "amount")
                + field(p.status(), 8, false, "status");
        if (r.length() != RECORD_LENGTH) {
            throw new IllegalStateException("record length " + r.length() + " for " + p.claimNumber());
        }
        return r;
    }

    public static void write(List<PaidLoss> rows, Writer out) throws IOException {
        for (PaidLoss p : rows) {
            out.write(record(p));
            out.write('\n');
        }
    }

    /** Fail fast on overflow: a shifted record is rejected by CLMRECON (or worse, misread). */
    static String field(String s, int width, boolean rightAlign, String name) {
        if (s.length() > width) {
            throw new IllegalArgumentException(name + " '" + s + "' is wider than " + width);
        }
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) > 0x7e || s.charAt(i) < 0x20) {
                throw new IllegalArgumentException(name + " '" + s + "' is not printable ASCII");
            }
        }
        String pad = " ".repeat(width - s.length());
        return rightAlign ? pad + s : s + pad;
    }

    static String padRight(String s, int w) {
        return field(s, w, false, "field");
    }

    static String padLeft(String s, int w) {
        return field(s, w, true, "field");
    }
}
