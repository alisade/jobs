// Incremental Server-Sent Events parser for the assistant gateway stream.
//
// The prototype below works in the demo because the dev server flushes one whole event per
// chunk. Behind the CDN and the ALB, chunks arrive at arbitrary byte boundaries.
//
// TODO (see README "Stream contract" and the WHATWG event-stream rules):
//   - events split across chunks, including a CRLF split between two chunks
//   - line endings: LF, CRLF and bare CR
//   - comment lines (":" keepalives) are ignored
//   - several data: lines join with "\n"; one leading space after the colon is stripped
//   - event: sets the type (default "message"); id: sets the last event id (it persists)
//   - an event with no data lines is not dispatched
//   - flush() at end of stream discards an incomplete event (no blank line yet)

export interface SseEvent {
  event: string;
  data: string;
  id?: string;
}

export class SseParser {
  push(chunk: string): SseEvent[] {
    const out: SseEvent[] = [];
    for (const block of chunk.split("\n\n")) {
      if (!block.trim()) continue;
      let event = "message";
      let data = "";
      let id: string | undefined;
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data = line.slice(6);
        else if (line.startsWith("id: ")) id = line.slice(4);
      }
      out.push(id === undefined ? { event, data } : { event, data, id });
    }
    return out;
  }

  flush(): SseEvent[] {
    return [];
  }

  get lastEventId(): string | undefined {
    return undefined;
  }
}
