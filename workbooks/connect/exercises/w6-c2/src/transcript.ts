// Provided: flatten turns into the text sent to the model, and an S3-backed source shape.
import { Turn } from "./types";

export function toTranscriptText(turns: Turn[]): string {
  return [...turns]
    .sort((a, b) => a.beginMillis - b.beginMillis)
    .map((t) => `${t.participant}: ${t.text}`)
    .join("\n");
}
