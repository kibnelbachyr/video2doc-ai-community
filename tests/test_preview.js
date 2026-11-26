"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { renderMarkdownPreview, PREVIEW_LIMIT } = require("../ui/preview.js");

function textSink() {
  return {
    textContent: "",
    set innerHTML(_) { throw new Error("HTML interpretation is forbidden"); }
  };
}

test("untrusted HTML and Markdown remain literal text", () => {
  const element = textSink();
  const payload = '<img src=x onerror=alert(1)>\n<script>alert(1)</script>\n[link](javascript:alert(1))';
  renderMarkdownPreview(element, payload);
  assert.equal(element.textContent, payload);
});

test("preview size is bounded without modifying source", () => {
  const element = textSink();
  const raw = "a".repeat(PREVIEW_LIMIT + 10);
  renderMarkdownPreview(element, raw);
  assert.ok(element.textContent.startsWith("a".repeat(PREVIEW_LIMIT)));
  assert.match(element.textContent, /Aperçu tronqué/);
  assert.equal(raw.length, PREVIEW_LIMIT + 10);
});

test("empty output stays empty", () => {
  const element = textSink();
  renderMarkdownPreview(element, "");
  assert.equal(element.textContent, "");
});
