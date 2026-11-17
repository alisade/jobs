/**
 * Deterministic PII redaction, applied to the transcript before it is sent to the model and to
 * the model output before it is written anywhere. See README "Redaction".
 */
export interface Redacted { text: string; entities: string[] }

export function redactPii(input: string): Redacted {
  // TODO: CREDIT_DEBIT_NUMBER (13-19 digits, spaces/dashes allowed, Luhn-valid only), SSN, EMAIL,
  // PHONE, PASSWORD ("password is X" / "pin: X"); return entity types in order of first detection.
  return { text: input, entities: [] };
}
