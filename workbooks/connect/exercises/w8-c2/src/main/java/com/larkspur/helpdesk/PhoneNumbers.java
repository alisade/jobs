package com.larkspur.helpdesk;

/** E.164 normalization for numbers Connect passes in CustomerEndpoint.Address. */
public final class PhoneNumbers {
    private PhoneNumbers() {}

    /**
     * "+1 (617) 555-0142" -> "+16175550142". Connect already sends E.164 for PSTN calls, but the
     * directory sync and test events do not always, so the key is normalized before lookup.
     * Returns null when nothing usable is left (anonymous / withheld callers).
     */
    public static String normalize(String raw) {
        if (raw == null) {
            return null;
        }
        String digits = raw.replaceAll("[^0-9]", "");
        if (digits.isEmpty()) {
            return null;
        }
        if (digits.length() == 10) {
            digits = "1" + digits; // NANP without country code
        }
        return "+" + digits;
    }
}
