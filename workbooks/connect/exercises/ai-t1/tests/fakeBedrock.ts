// A fake HTTP handler for BedrockRuntimeClient: the real SDK middleware (serialization, retries,
// backoff, error parsing) runs; only the network is replaced. Each request takes the next scripted
// step: { status, delayMs, text?, outputTokens? }. Honors abortSignal like the real handler.
import { Readable } from "stream";

export type Step = { status: 200 | 429 | 500; delayMs: number; text?: string; outputTokens?: number };

export class FakeBedrockHttp {
  public metadata = { handlerProtocol: "http/1.1" };
  public requests: { at: number; body: any }[] = [];
  private i = 0;
  constructor(private steps: Step[], private repeatLast = true) {}

  async handle(request: any, opts: { abortSignal?: AbortSignal } = {}) {
    const step = this.steps[Math.min(this.i++, this.steps.length - 1)];
    if (!this.repeatLast && this.i > this.steps.length) throw new Error("fake: no more scripted steps");
    let body: any = {};
    try { body = JSON.parse(String(request.body || "{}")); } catch { /* keep {} */ }
    this.requests.push({ at: Date.now(), body });
    const abort = () => Object.assign(new Error("Request aborted"), { name: "AbortError" });
    if (opts.abortSignal?.aborted) throw abort();
    await new Promise<void>((resolve, reject) => {
      const t = setTimeout(resolve, step.delayMs);
      opts.abortSignal?.addEventListener("abort", () => { clearTimeout(t); reject(abort()); });
    });
    const json = (o: any) => Readable.from([Buffer.from(JSON.stringify(o))]);
    if (step.status === 429) {
      return { response: { statusCode: 429, headers: { "content-type": "application/json", "x-amzn-errortype": "ThrottlingException:http://internal.amazon.com/coral/com.amazon.bedrock/" }, body: json({ message: "Too many requests, please wait before trying again." }) } };
    }
    if (step.status === 500) {
      return { response: { statusCode: 500, headers: { "content-type": "application/json", "x-amzn-errortype": "InternalServerException:http://internal.amazon.com/coral/com.amazon.bedrock/" }, body: json({ message: "Internal server error" }) } };
    }
    const out = step.outputTokens || 60;
    return { response: { statusCode: 200, headers: { "content-type": "application/json" }, body: json({
      output: { message: { role: "assistant", content: [{ text: step.text || "Caller locked out after MFA phone change; self-service reset failed twice; needs MFA re-enrolment." }] } },
      stopReason: "end_turn", usage: { inputTokens: 420, outputTokens: out, totalTokens: 420 + out }, metrics: { latencyMs: step.delayMs },
    }) } };
  }
  updateHttpClientConfig() {}
  httpHandlerConfigs() { return {}; }
  destroy() {}
}

export const event = (transcript = "Caller: I got a new phone and my MFA app is gone. Bot: I can send a reset link. Caller: it failed twice.") => ({
  Name: "ContactFlowEvent",
  Details: { ContactData: { ContactId: "c-1", Channel: "VOICE", Attributes: { lexTranscript: transcript } }, Parameters: {} },
});
export const ctx = (remainingMs = 8000) => {
  const t0 = Date.now();
  return { getRemainingTimeInMillis: () => remainingMs - (Date.now() - t0) };
};
