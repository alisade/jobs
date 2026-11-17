"use strict";
// Test helpers shared by the genai exercises.
//   chunksFrom(text, sizes)  split a recorded SSE transcript into network-sized chunks
//   asyncChunks(chunks, opts) async iterable over chunks; honours an AbortSignal and can fail midway
const fs = require("fs");

function chunksFrom(text, sizes) {
  const out = [];
  let i = 0;
  let k = 0;
  while (i < text.length) {
    const n = Array.isArray(sizes) ? sizes[k++ % sizes.length] : (sizes || 64);
    out.push(text.slice(i, i + n));
    i += n;
  }
  return out;
}

function readFixture(path) {
  return fs.readFileSync(path, "utf8");
}

function asyncChunks(chunks, opts = {}) {
  const { signal, failAfter, error, delayMs = 0 } = opts;
  const state = { returned: false, yielded: 0 };
  const iterable = {
    state,
    [Symbol.asyncIterator]() {
      let i = 0;
      return {
        async next() {
          if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
          if (signal && signal.aborted) {
            const e = new Error("The operation was aborted");
            e.name = "AbortError";
            throw e;
          }
          if (failAfter !== undefined && i >= failAfter) throw error || new Error("network error");
          if (i >= chunks.length) return { done: true, value: undefined };
          state.yielded += 1;
          return { done: false, value: chunks[i++] };
        },
        async return() {
          state.returned = true;
          return { done: true, value: undefined };
        },
      };
    },
  };
  return iterable;
}

module.exports = { chunksFrom, readFixture, asyncChunks };
