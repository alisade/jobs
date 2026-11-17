package com.corvane.claimdesk.notes;

import java.util.List;

public record Claim(String number, String policy, String status, List<String> notes) {
}
