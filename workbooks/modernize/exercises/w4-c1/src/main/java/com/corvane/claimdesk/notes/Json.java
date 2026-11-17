package com.corvane.claimdesk.notes;

import java.util.List;
import java.util.stream.Collectors;

/** Tiny JSON writer (the service predates the platform JSON library). */
final class Json {

    private Json() {
    }

    static String str(String s) {
        if (s == null) {
            return "null";
        }
        StringBuilder b = new StringBuilder("\"");
        for (char ch : s.toCharArray()) {
            switch (ch) {
                case '"' -> b.append("\\\"");
                case '\\' -> b.append("\\\\");
                case '\n' -> b.append("\\n");
                default -> b.append(ch < 0x20 ? String.format("\\u%04x", (int) ch) : String.valueOf(ch));
            }
        }
        return b.append('"').toString();
    }

    static String claim(Claim c) {
        return "{\"number\":" + str(c.number()) + ",\"policy\":" + str(c.policy()) + ",\"status\":" + str(c.status())
                + ",\"notes\":[" + c.notes().stream().map(Json::str).collect(Collectors.joining(",")) + "]}";
    }

    static String claims(List<Claim> cs) {
        return "[" + cs.stream().map(Json::claim).collect(Collectors.joining(",")) + "]";
    }
}
