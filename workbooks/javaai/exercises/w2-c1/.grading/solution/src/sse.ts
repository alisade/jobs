import { Observable } from "rxjs";
import { TutorEvent } from "./types";

/**
 * Turn raw response body chunks into tutor events. Chunks may cut events, lines and UTF-8
 * characters anywhere: decode with a streaming TextDecoder and keep the unfinished tail.
 */
export function parseSse(chunks: Observable<Uint8Array>): Observable<TutorEvent> {
  return new Observable<TutorEvent>((sub) => {
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    const drain = () => {
      buffer = buffer.replace(/\r\n/g, "\n");
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const ev = toEvent(block);
        if (ev) sub.next(ev);
      }
    };
    const s = chunks.subscribe({
      next: (chunk) => {
        buffer += decoder.decode(chunk, { stream: true });
        // a lone trailing CR may be half of a CRLF: keep it for the next chunk
        if (buffer.endsWith("\r")) {
          const keep = "\r";
          buffer = buffer.slice(0, -1);
          drain();
          buffer += keep;
        } else {
          drain();
        }
      },
      error: (e) => sub.error(e),
      complete: () => {
        buffer += decoder.decode();
        drain();
        // whatever is left is an unterminated event: drop it
        sub.complete();
      },
    });
    return () => s.unsubscribe();
  });
}

function toEvent(block: string): TutorEvent | null {
  let name = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line === "" || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon < 0 ? line : line.slice(0, colon);
    let value = colon < 0 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") name = value.trim();
    else if (field === "data") data.push(value);
  }
  if (data.length === 0 && name !== "done") return null;
  let payload: any = {};
  if (data.length) {
    try { payload = JSON.parse(data.join("\n")); } catch { return { type: "error", message: "malformed event from server" }; }
  }
  if (name === "token" && typeof payload.text === "string") return { type: "token", text: payload.text };
  if (name === "citation" && typeof payload.sectionId === "string") return { type: "citation", sectionId: payload.sectionId };
  if (name === "done") return { type: "done" };
  if (name === "error") return { type: "error", message: String(payload.message ?? "unknown error") };
  return null;
}
