/** @jest-environment node */
import { SseParser, type SseEvent } from "../../src/sse";
import { createOpenStream, StreamHttpError } from "../../src/openStream";
import { fixture } from "../helpers";

const REC = fixture("tent-question.sse");
const parseAll = (chunks: string[]): SseEvent[] => {
  const p = new SseParser();
  const out = chunks.flatMap((c) => p.push(c));
  return out.concat(p.flush());
};
const whole = parseAll([REC]);

describe("SseParser", () => {
  test("whole recording yields 33 events", () => {
    expect(whole).toHaveLength(33);
  });

  test("every two-chunk split of the recording yields the same events", () => {
    for (let i = 1; i < REC.length; i++) {
      const got = parseAll([REC.slice(0, i), REC.slice(i)]);
      if (got.length !== whole.length) throw new Error(`split at ${i}: ${got.length} events`);
      expect(got).toEqual(whole);
    }
  });

  test("one character per chunk yields the same events", () => {
    expect(parseAll(REC.split(""))).toEqual(whole);
  });

  test("CRLF line endings, including a CRLF split across chunks", () => {
    const crlf = REC.replace(/\n/g, "\r\n");
    expect(parseAll([crlf])).toEqual(whole);
    const i = crlf.indexOf("\r\n\r\n") + 1; // split between \r and \n
    expect(parseAll([crlf.slice(0, i), crlf.slice(i)])).toEqual(whole);
    expect(parseAll(crlf.split(""))).toEqual(whole);
  });

  test("bare CR line endings", () => {
    expect(parseAll([REC.replace(/\n/g, "\r")])).toEqual(whole);
  });

  test("multi-line data, no space after colon, only one leading space stripped", () => {
    const evs = parseAll(["data: line one\ndata:line two\ndata:  indented\n\n"]);
    expect(evs).toEqual([{ event: "message", data: "line one\nline two\n indented" }]);
  });

  test("comments are ignored and an event without data is not dispatched", () => {
    const evs = parseAll([": ping\n\nevent: token\n\nevent: token\ndata: {\"text\":\"a\"}\n\n"]);
    expect(evs).toEqual([{ event: "token", data: '{"text":"a"}' }]);
  });

  test("event type resets after dispatch; id persists to later events", () => {
    const evs = parseAll(["id: 41\nevent: token\ndata: a\n\ndata: b\n\n"]);
    expect(evs).toEqual([
      { event: "token", data: "a", id: "41" },
      { event: "message", data: "b", id: "41" },
    ]);
  });

  test("an event without its blank line at end of stream is discarded", () => {
    const p = new SseParser();
    const a = p.push('event: token\ndata: {"text":"x"}\n\nevent: token\ndata: {"text":"y"}\n');
    const b = p.flush();
    expect(a).toHaveLength(1);
    expect(b).toEqual([]);
  });
});

function sseResponse(parts: Uint8Array[], opts: { status?: number; type?: string } = {}) {
  let i = 0;
  const cancel = jest.fn(async () => undefined);
  const reader = {
    read: jest.fn(async () => (i < parts.length ? { done: false, value: parts[i++] } : { done: true, value: undefined })),
    cancel,
    releaseLock: jest.fn(),
  };
  const status = opts.status ?? 200;
  const res = {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (h: string) => (h.toLowerCase() === "content-type" ? (opts.type ?? "text/event-stream; charset=utf-8") : null) },
    body: { getReader: () => reader },
    text: async () => "",
  } as unknown as Response;
  return { res, reader };
}

async function collect(it: AsyncIterable<string>): Promise<string> {
  let s = "";
  for await (const c of it) s += c;
  return s;
}

describe("createOpenStream", () => {
  test("decodes a multi-byte character split across network chunks", async () => {
    const bytes = new TextEncoder().encode('data: {"text": "caf\u00e9 \u00fcber"}\n\n');
    const cut = bytes.indexOf(0xc3) + 1; // inside the 2-byte e-acute
    const { res } = sseResponse([bytes.slice(0, cut), bytes.slice(cut)]);
    const open = createOpenStream(async () => res);
    const got = await collect(open({ prompt: "x" }, new AbortController().signal));
    expect(got).toBe('data: {"text": "caf\u00e9 \u00fcber"}\n\n');
  });

  test("POSTs JSON with Accept: text/event-stream, conversation id and the signal", async () => {
    const { res } = sseResponse([]);
    const fetchImpl = jest.fn(async () => res);
    const ctrl = new AbortController();
    await collect(createOpenStream(fetchImpl, "/api/x")({ prompt: "hi", conversationId: "c-1" }, ctrl.signal));
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/x");
    expect(init.method).toBe("POST");
    const headers = init.headers as Record<string, string>;
    expect(headers.Accept || headers.accept).toBe("text/event-stream");
    expect(JSON.parse(String(init.body))).toMatchObject({ prompt: "hi", conversation_id: "c-1" });
    expect(init.signal).toBe(ctrl.signal);
  });

  test("non-2xx throws StreamHttpError with the status", async () => {
    const { res } = sseResponse([], { status: 429 });
    const open = createOpenStream(async () => res);
    await expect(collect(open({ prompt: "x" }, new AbortController().signal))).rejects.toMatchObject({ status: 429 });
    await expect(collect(open({ prompt: "x" }, new AbortController().signal))).rejects.toBeInstanceOf(StreamHttpError);
  });

  test("a 200 that is not an event stream (proxy error page) throws StreamHttpError", async () => {
    const { res } = sseResponse([new TextEncoder().encode("<html>Bad gateway</html>")], { type: "text/html" });
    const open = createOpenStream(async () => res);
    await expect(collect(open({ prompt: "x" }, new AbortController().signal))).rejects.toBeInstanceOf(StreamHttpError);
  });

  test("stopping early cancels the reader", async () => {
    const enc = new TextEncoder();
    const { res, reader } = sseResponse([enc.encode("data: a\n\n"), enc.encode("data: b\n\n"), enc.encode("data: c\n\n")]);
    const open = createOpenStream(async () => res);
    for await (const c of open({ prompt: "x" }, new AbortController().signal)) {
      expect(c).toContain("a");
      break;
    }
    expect(reader.cancel).toHaveBeenCalled();
  });
});
