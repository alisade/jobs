/**
 * Deterministic PII redaction, applied to the transcript before it is sent to the model and to
 * the model output before it is written anywhere. Conversational analytics redaction is ML-based
 * and can miss entities (the docs say so); this is defense in depth, not a replacement.
 */
export interface Redacted { text: string; entities: string[] }

function luhn(digits: string): boolean {
  let sum = 0;
  let dbl = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits.charCodeAt(i) - 48;
    if (dbl) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    sum += d;
    dbl = !dbl;
  }
  return sum % 10 === 0;
}

export function redactPii(input: string): Redacted {
  const entities: string[] = [];
  const note = (e: string) => { if (!entities.includes(e)) entities.push(e); };
  let text = input.replace(/\b(?:\d[ -]?){12,18}\d\b/g, (m) => {
    const digits = m.replace(/[ -]/g, "");
    if (digits.length >= 13 && digits.length <= 19 && luhn(digits)) {
      note("CREDIT_DEBIT_NUMBER");
      return "[CREDIT_DEBIT_NUMBER]";
    }
    return m;
  });
  text = text.replace(/\b\d{3}-\d{2}-\d{4}\b/g, () => { note("SSN"); return "[SSN]"; });
  text = text.replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, () => { note("EMAIL"); return "[EMAIL]"; });
  text = text.replace(/(?:\+?1[ .-]?)?(?:\(\d{3}\)|\b\d{3})[ .-]?\d{3}[ .-]\d{4}\b/g, () => { note("PHONE"); return "[PHONE]"; });
  text = text.replace(/\b(password|passcode|pin)(\s+is|:)\s*\S+/gi, (_m, w, sep) => { note("PASSWORD"); return `${w}${sep} [PASSWORD]`; });
  return { text, entities };
}
