import { BehaviorSubject, Subject, switchMap, map, catchError, of } from "rxjs";
import { Answer, Quiz, QuizApi, SubmitResult } from "./quizApi";

export interface QuizPageState {
  lessonId: number | null;
  quiz: Quiz | null;
  loading: boolean;
  answers: Record<number, number>; // quizItemId -> chosenIndex
  error: string | null;
  result: SubmitResult | null;
}

const INITIAL: QuizPageState = { lessonId: null, quiz: null, loading: false, answers: {}, error: null, result: null };

/**
 * State behind the lesson quiz screen. The lesson sidebar calls select(); the form calls
 * answer() and submit(). The component reads state$ through toSignal().
 */
export class QuizPageStore {
  readonly state$ = new BehaviorSubject<QuizPageState>(INITIAL);
  private readonly select$ = new Subject<number>();

  constructor(private readonly api: QuizApi) {
    this.select$
      .pipe(
        // switchMap, not mergeMap: a new selection unsubscribes (cancels) the previous request,
        // so a slow response for an old lesson can never overwrite the current one.
        switchMap((lessonId) =>
          this.api.getQuiz(lessonId).pipe(
            map((quiz) => ({ quiz, error: null as string | null })),
            catchError(() => of({ quiz: null as Quiz | null, error: "Could not load the quiz" })),
          ),
        ),
      )
      .subscribe(({ quiz, error }) => this.patch({ quiz, error, loading: false }));
  }

  get snapshot(): QuizPageState {
    return this.state$.value;
  }

  get canSubmit(): boolean {
    const s = this.snapshot;
    return !!s.quiz && Object.keys(s.answers).length === s.quiz.items.length;
  }

  select(lessonId: number): void {
    this.patch({ lessonId, quiz: null, answers: {}, loading: true, error: null, result: null });
    this.select$.next(lessonId);
  }

  answer(quizItemId: number, chosenIndex: number): void {
    const q = this.snapshot.quiz;
    if (!q || !q.items.some((it) => it.id === quizItemId)) return;
    this.patch({ answers: { ...this.snapshot.answers, [quizItemId]: chosenIndex } });
  }

  submit(): void {
    const s = this.snapshot;
    if (!this.canSubmit || s.lessonId === null || s.loading || s.quiz?.lessonId !== s.lessonId) return;
    const answers: Answer[] = Object.entries(s.answers).map(([id, idx]) => ({ quizItemId: Number(id), chosenIndex: idx }));
    this.api.submit(s.lessonId, answers).subscribe({
      next: (result) => this.patch({ result }),
      error: () => this.patch({ error: "Could not submit your answers" }),
    });
  }

  private patch(p: Partial<QuizPageState>): void {
    this.state$.next({ ...this.snapshot, ...p });
  }
}
