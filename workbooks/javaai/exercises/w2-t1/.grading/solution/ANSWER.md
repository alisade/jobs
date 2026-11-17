# ANSWER: javaai/w2-t1 The quiz shows the previous lesson's questions

## Approach

Read the HAR first: the lesson-2 request started before lesson 3's but finished 2.6 s after it. The
409 body names item 201 for lesson 3. Reproduced with the fake API: select(2), select(3), respond
to 3 then to 2: state ends with lessonId 3 and lesson-2 items.

## Root cause

mergeMap keeps both requests and the last response to arrive wins. select() sets lessonId at once
and never clears quiz or answers, so the stale lesson-2 quiz is shown under lesson 3 and submitted
with lesson 3's id; the backend correctly rejects it with 409. Slow networks reorder responses,
which is why it happens on the train. It started with app 1.6 (reactive store).
Not the cache: both requests were misses, URLs are per lesson, max-age=300 predates the reports.

## Fix

switchMap cancels the previous request; select() clears quiz, answers and errors; answer() ignores
foreign items; submit() is gated on loading and lessonId match. 8/8 tests.

## Trade-offs / what I would do in production

Out-of-order tests for each user-driven stream, a throttled e2e run, exhaustMap on the submit
button, and keep the server 409 as the backstop. Leave the CDN caching as it is.
