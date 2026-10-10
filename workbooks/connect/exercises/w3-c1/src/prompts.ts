// WAV prompts recorded by LFG's voice talent, stored in S3 (bucket policy grants s3:GetObject to
// voiceconnector.chime.amazonaws.com scoped by aws:SourceAccount). Do not change the keys:
// the prompts were re-recorded for the Connect migration under the same names.
import { S3AudioSource } from "./types";

export const PROMPT_BUCKET = "lfg-oncall-hotline-prompts-111122223333";
const s3 = (Key: string): S3AudioSource => ({ Type: "S3", BucketName: PROMPT_BUCKET, Key });

export const PROMPTS = {
  enterEmployeeId: s3("enter-employee-id.wav"),       // "Enter your six digit employee ID, then press pound."
  invalidEntry: s3("invalid-entry.wav"),              // "Sorry, that entry is not valid."
  menu: s3("oncall-menu.wav"),                        // "For a severity one outage, press 1. For the help desk, press 2."
  connectingOnCall: s3("connecting-oncall.wav"),      // "Connecting you to the on-call engineer."
  ringback: s3("ringback.wav"),                       // ring tone loop
  onCallUnavailable: s3("oncall-unavailable.wav"),    // "The on-call engineers are not answering. Transferring you to the help desk."
  engineerLeft: s3("engineer-disconnected.wav"),      // "The engineer has disconnected. Goodbye."
  goodbye: s3("goodbye.wav"),                         // "We could not verify your entry. Goodbye."
};
