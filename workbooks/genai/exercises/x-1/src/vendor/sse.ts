// Incremental Server-Sent Events parser (WHATWG "event stream interpretation").
// push() takes arbitrary network chunks; events are only dispatched on a blank line, so an event
// split across chunks (or a CRLF split between two chunks) is reassembled correctly.

export interface SseEvent {
  event: string;
  data: string;
  id?: string;
}

export class SseParser {
  private buf = "";
  private pendingCR = false;
  private dataLines: string[] = [];
  private eventName = "";
  private lastId: string | undefined;

  push(chunk: string): SseEvent[] {
    const out: SseEvent[] = [];
    let text = chunk;
    if (this.pendingCR) {
      // a CR ended the previous chunk; a LF at the start of this one belongs to it
      if (text.startsWith("\n")) text = text.slice(1);
      this.pendingCR = false;
    }
    this.buf += text;
    for (;;) {
      const m = /\r\n|\r|\n/.exec(this.buf);
      if (!m) break;
      if (m[0] === "\r" && m.index === this.buf.length - 1) {
        // cannot tell yet whether this CR is half of a CRLF
        const line = this.buf.slice(0, m.index);
        this.buf = "";
        this.pendingCR = true;
        this.line(line, out);
        break;
      }
      const line = this.buf.slice(0, m.index);
      this.buf = this.buf.slice(m.index + m[0].length);
      this.line(line, out);
    }
    return out;
  }

  /** End of stream: an event without its terminating blank line is discarded (per spec). */
  flush(): SseEvent[] {
    this.buf = "";
    this.dataLines = [];
    this.eventName = "";
    this.pendingCR = false;
    return [];
  }

  get lastEventId(): string | undefined {
    return this.lastId;
  }

  private line(line: string, out: SseEvent[]): void {
    if (line === "") {
      if (this.dataLines.length > 0) {
        const ev: SseEvent = { event: this.eventName || "message", data: this.dataLines.join("\n") };
        if (this.lastId !== undefined) ev.id = this.lastId;
        out.push(ev);
      }
      this.dataLines = [];
      this.eventName = "";
      return;
    }
    if (line.startsWith(":")) return; // comment / keepalive
    const idx = line.indexOf(":");
    const field = idx === -1 ? line : line.slice(0, idx);
    let value = idx === -1 ? "" : line.slice(idx + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    switch (field) {
      case "data":
        this.dataLines.push(value);
        break;
      case "event":
        this.eventName = value;
        break;
      case "id":
        if (!value.includes("\u0000")) this.lastId = value;
        break;
      default:
        break; // "retry" and unknown fields are ignored here
    }
  }
}
