import { Observable } from "rxjs";
import { TutorEvent } from "./types";

/**
 * Turn raw response body chunks into tutor events.
 *
 * Wire format (one event per block, blocks separated by a blank line):
 *   event: token
 *   data: {"text":"Think about "}
 *
 * TODO(w2-c1): the prototype assumes every chunk holds whole events and whole characters.
 * Fetch and HttpClient give you chunks cut anywhere. See README "Requirements: parseSse".
 */
export function parseSse(chunks: Observable<Uint8Array>): Observable<TutorEvent> {
  return new Observable<TutorEvent>((sub) => {
    const s = chunks.subscribe({
      next: (chunk) => {
        const text = new TextDecoder().decode(chunk);
        for (const block of text.split("\n\n")) {
          const ev = toEvent(block);
          if (ev) sub.next(ev);
        }
      },
      error: (e) => sub.error(e),
      complete: () => sub.complete(),
    });
    return () => s.unsubscribe();
  });
}

function toEvent(block: string): TutorEvent | null {
  let name = "message";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) data = line.slice(5).trim();
  }
  if (!data && name !== "done") return null;
  const payload = data ? JSON.parse(data) : {};
  if (name === "token") return { type: "token", text: payload.text };
  if (name === "citation") return { type: "citation", sectionId: payload.sectionId };
  if (name === "done") return { type: "done" };
  if (name === "error") return { type: "error", message: payload.message };
  return null;
}
