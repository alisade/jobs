import { BehaviorSubject, Observable, Subject, catchError, of, switchMap, timeout } from "rxjs";
import { createLeakGuard } from "./leakGuard";
import { parseSse } from "./sse";
import { ChatState, INITIAL, TutorEvent } from "./types";

export interface TutorApi {
  stream(question: string, lessonId: string): Observable<Uint8Array>;
}

export interface Ask {
  question: string;
  lessonId: string;
  answerKey: string[];
}

/** State for the tutor chat panel (expose with toSignal() in the component). */
export class TutorChatStore {
  readonly state$ = new BehaviorSubject<ChatState>(INITIAL);
  private readonly asks$ = new Subject<Ask>();

  constructor(private readonly api: TutorApi, private readonly opts: { firstTokenTimeoutMs: number } = { firstTokenTimeoutMs: 8000 }) {
    // switchMap: a new question unsubscribes the previous stream (cancels the HTTP request)
    this.asks$.pipe(switchMap((a) => this.run(a))).subscribe((s) => this.state$.next(s));
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
      const fail = (message: string) => {
        s = { ...s, text: s.text + guard.flush(), status: "error", error: message, withheld: guard.leaked };
        sub.next(s);
        sub.complete();
      };
      const inner = parseSse(this.api.stream(a.question, a.lessonId))
        .pipe(
          timeout({ first: this.opts.firstTokenTimeoutMs }),
          catchError((e) => of<TutorEvent>({ type: "error", message: e?.name === "TimeoutError" ? "timeout" : String(e?.message ?? e) })),
        )
        .subscribe({
          next: (ev: TutorEvent) => {
            if (s.status !== "streaming") return;
            if (ev.type === "token") {
              s = { ...s, text: s.text + guard.push(ev.text), withheld: guard.leaked };
            } else if (ev.type === "citation") {
              if (!s.citations.includes(ev.sectionId)) s = { ...s, citations: [...s.citations, ev.sectionId] };
            } else if (ev.type === "done") {
              s = { ...s, text: s.text + guard.flush(), status: "done", withheld: guard.leaked };
              sub.next(s);
              sub.complete();
              return;
            } else if (ev.type === "error") {
              fail(ev.message);
              return;
            }
            sub.next(s);
          },
          complete: () => {
            if (s.status === "streaming") fail("stream ended before done");
          },
        });
      return () => inner.unsubscribe();
    });
  }
}
