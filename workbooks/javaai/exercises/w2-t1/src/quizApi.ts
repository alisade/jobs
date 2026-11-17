import { Observable } from "rxjs";

export interface QuizItem { id: number; stem: string; options: string[] }
export interface Quiz { lessonId: number; items: QuizItem[] }
export interface Answer { quizItemId: number; chosenIndex: number }
export interface SubmitResult { correct: number; total: number }

/** Thin wrapper over HttpClient: GET /api/lessons/{id}/quiz-items, POST /api/lessons/{id}/attempts. */
export interface QuizApi {
  getQuiz(lessonId: number): Observable<Quiz>;
  submit(lessonId: number, answers: Answer[]): Observable<SubmitResult>;
}
