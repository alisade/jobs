package com.corvane.claimdesk.recon;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PaidLoss(String claimNumber, LocalDate paidDate, BigDecimal amount, String status) {
}
