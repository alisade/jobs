// Events the tutor-agent streams over SSE (text/event-stream) through the Spring Boot API.
export type TutorEvent =
  | { type: "token"; text: string }
  | { type: "citation"; sectionId: string }
  | { type: "done" }
  | { type: "error"; message: string };

export type ChatStatus = "idle" | "streaming" | "done" | "error";

export interface ChatState {
  status: ChatStatus;
  question: string | null;
  text: string;          // what the learner sees so far
  citations: string[];   // section ids, in arrival order, no duplicates
  withheld: boolean;     // the leak guard replaced something
  error: string | null;  // "timeout" or the server's message
}

export const INITIAL: ChatState = { status: "idle", question: null, text: "", citations: [], withheld: false, error: null };
