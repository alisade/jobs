import { QuizPageStore } from "../../src/quizPageStore";
import { FakeQuizApi, quiz } from "../fakeApi";

test("latest selection wins when responses arrive out of order", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  store.select(3);
  api.respond(1, quiz(3));
  api.respond(0, quiz(2)); // the slow lesson-2 response lands last
  expect(store.snapshot.lessonId).toBe(3);
  expect(store.snapshot.quiz?.lessonId).toBe(3);
});

test("switching lessons cancels the request in flight", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  store.select(3);
  expect(api.gets[0].unsubscribed).toBe(true);
});

test("old quiz and answers are cleared on select, and submit is disabled while loading", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  api.respond(0, quiz(2));
  store.answer(201, 0);
  store.answer(202, 0);
  expect(store.canSubmit).toBe(true);
  store.select(3);
  expect(store.snapshot.loading).toBe(true);
  expect(store.snapshot.quiz).toBeNull();
  expect(store.snapshot.answers).toEqual({});
  expect(store.canSubmit).toBe(false);
});

test("submit never mixes a lesson id with another lesson's items", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  store.select(3);
  api.respond(1, quiz(3));
  api.respond(0, quiz(2));
  const items = store.snapshot.quiz!.items;
  items.forEach((it) => store.answer(it.id, 1));
  store.submit();
  expect(api.submits.length).toBe(1);
  const sent = api.submits[0];
  expect(sent.answers.every((a) => Math.floor(a.quizItemId / 100) === sent.lessonId)).toBe(true);
});

test("a load error is shown and the next lesson still loads", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(4);
  api.gets[0].res.error(new Error("503"));
  expect(store.snapshot.error).toBeTruthy();
  expect(store.snapshot.loading).toBe(false);
  store.select(5);
  api.respond(1, quiz(5));
  expect(store.snapshot.quiz?.lessonId).toBe(5);
  expect(store.snapshot.error).toBeNull();
});

test("answers that do not belong to the quiz are ignored", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  api.respond(0, quiz(2));
  store.answer(999, 1);
  expect(store.snapshot.answers).toEqual({});
});

test("reselecting the same lesson still works (guard)", () => {
  const api = new FakeQuizApi();
  const store = new QuizPageStore(api);
  store.select(2);
  api.respond(0, quiz(2));
  store.select(2);
  api.respond(1, quiz(2));
  expect(store.snapshot.quiz?.lessonId).toBe(2);
  expect(store.snapshot.loading).toBe(false);
});
