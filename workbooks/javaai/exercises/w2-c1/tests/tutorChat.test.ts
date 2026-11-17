import { firstValueFrom, from, toArray } from "rxjs";
import { parseSse } from "../src/sse";
import { TutorChatStore } from "../src/tutorChat";
import { bytes, FakeApi, sse } from "./helpers";

test("parses whole events delivered in one chunk", async () => {
  const body = sse("token", { text: "Think about " }) + sse("citation", { sectionId: "l5-s1" }) + sse("done");
  const events = await firstValueFrom(parseSse(from([bytes(body)])).pipe(toArray()));
  expect(events).toEqual([{ type: "token", text: "Think about " }, { type: "citation", sectionId: "l5-s1" }, { type: "done" }]);
});

test("store streams tokens into state", () => {
  const api = new FakeApi();
  const store = new TutorChatStore(api);
  store.ask({ question: "What do vaccines train?", lessonId: "l5", answerKey: ["memory cells"] });
  expect(store.snapshot.status).toBe("streaming");
  api.calls[0].body.next(bytes(sse("token", { text: "The adaptive " }) + sse("token", { text: "immune system." }) + sse("done")));
  expect(store.snapshot.text).toBe("The adaptive immune system.");
  expect(store.snapshot.status).toBe("done");
});
