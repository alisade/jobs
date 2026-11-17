import { QuizPageStore } from "../src/quizPageStore";
import { FakeQuizApi, quiz } from "./fakeApi";

test("loads and submits one lesson", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  api.respond(0, quiz(2));
  expect(store.snapshot.quiz?.lessonId).toBe(2);
  store.answer(201, 1);
  store.answer(202, 3);
  store.submit();
  expect(api.submits).toEqual([{ lessonId: 2, answers: [{ quizItemId: 201, chosenIndex: 1 }, { quizItemId: 202, chosenIndex: 3 }] }]);
});
