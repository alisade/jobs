import { BehaviorSubject, Observable, Subject, mergeMap } from "rxjs";
import { createLeakGuard } from "./leakGuard";
import { parseSse } from "./sse";
import { ChatState, INITIAL, TutorEvent } from "./types";

export interface TutorApi {
  /** POST /api/tutor/stream -> the raw response body as chunks (fetch ReadableStream, HttpClient events). */
  stream(question: string, lessonId: string): Observable<Uint8Array>;
}

export interface Ask {
  question: string;
  lessonId: string;
  answerKey: string[]; // correct option text(s) of the learner's current quiz
}

/**
 * State for the tutor chat panel. In the Angular app a component exposes state$ via toSignal()
 * and calls ask() from the form. Kept framework-free so it tests without TestBed.
 *
 * TODO(w2-c1): see README "Requirements: TutorChatStore".
 */
export class TutorChatStore {
  readonly state$ = new BehaviorSubject<ChatState>(INITIAL);
  private readonly asks$ = new Subject<Ask>();

  constructor(private readonly api: TutorApi, private readonly opts: { firstTokenTimeoutMs: number } = { firstTokenTimeoutMs: 8000 }) {
    this.asks$
      .pipe(mergeMap((a) => this.run(a)))
      .subscribe((s) => this.state$.next(s));
  }

  ask(a: Ask): void {
    this.asks$.next(a);
  }

  get snapshot(): ChatState {
    return this.state$.value;
  }

  private run(a: Ask): Observable<ChatState> {
    return new Observable<ChatState>((sub) => {
      const guard = createLeakGuard(a.answerKey);
      let s: ChatState = { ...INITIAL, status: "streaming", question: a.question };
      sub.next(s);
      const inner = parseSse(this.api.stream(a.question, a.lessonId)).subscribe((ev: TutorEvent) => {
        if (ev.type === "token") s = { ...s, text: s.text + guard.push(ev.text) };
        else if (ev.type === "citation") s = { ...s, citations: [...s.citations, ev.sectionId] };
        else if (ev.type === "done") s = { ...s, status: "done" };
        sub.next(s);
      });
      return () => inner.unsubscribe();
    });
  }
}
