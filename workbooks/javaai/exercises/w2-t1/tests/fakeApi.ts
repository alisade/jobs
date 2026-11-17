import { Observable, Subject } from "rxjs";
import { Answer, Quiz, QuizApi, SubmitResult } from "../src/quizApi";

/** Each getQuiz() call gets a Subject; the test decides when (and in which order) responses arrive. */
export class FakeQuizApi implements QuizApi {
  gets: { lessonId: number; res: Subject<Quiz>; unsubscribed: boolean }[] = [];
  submits: { lessonId: number; answers: Answer[] }[] = [];

  getQuiz(lessonId: number): Observable<Quiz> {
    const res = new Subject<Quiz>();
    const rec = { lessonId, res, unsubscribed: false };
    this.gets.push(rec);
    return new Observable<Quiz>((sub) => {
      const s = res.subscribe(sub);
      return () => { rec.unsubscribed = true; s.unsubscribe(); };
    });
  }

  submit(lessonId: number, answers: Answer[]): Observable<SubmitResult> {
    this.submits.push({ lessonId, answers });
    return new Observable<SubmitResult>((sub) => { sub.next({ correct: 1, total: answers.length }); sub.complete(); });
  }

  respond(i: number, quiz: Quiz): void {
    this.gets[i].res.next(quiz);
    this.gets[i].res.complete();
  }
}

export const quiz = (lessonId: number): Quiz => ({
  lessonId,
  items: [
    { id: lessonId * 100 + 1, stem: `Lesson ${lessonId} question 1`, options: ["a", "b", "c", "d"] },
    { id: lessonId * 100 + 2, stem: `Lesson ${lessonId} question 2`, options: ["a", "b", "c", "d"] },
  ],
});
