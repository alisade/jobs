// LFG help desk bot code hook (Lex V2, messageVersion 1.0). One Lambda serves every intent of the
// bot alias's en_US locale (Lex allows one code hook Lambda per alias locale), so it routes by
// intent name and invocationSource. See README.md for the contract Connect relies on.
import { Deps } from "./deps";
import { LexEvent, LexResponse } from "./lex-types";

export function normalizeEmployeeId(raw: string | undefined): string | null {
  // TODO: accept "44129", "E44129", "E 44129", "e-44129"; return the five digits or null.
  return raw && /^\d{5}$/.test(raw) ? raw : null;
}

export function createHandler(deps: Deps) {
  return async function handler(event: LexEvent): Promise<LexResponse> {
    // First cut from the pilot: lets Lex drive every turn. It never validates, never confirms,
    // never fulfills, and drops the session attributes Connect sent in.
    // TODO: implement the dialog and fulfillment behavior in README.md "Requirements".
    void deps;
    return {
      sessionState: {
        dialogAction: { type: "Delegate" },
        intent: event.sessionState.intent,
      },
    };
  };
}
