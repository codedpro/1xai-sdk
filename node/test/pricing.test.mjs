/** Offline tests -- no API key, no network. Run with: node --test test/ */

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  InvalidKeyError,
  MissingKeyError,
  UnknownModelError,
  allPrices,
  checkKey,
  costOfResponse,
  estimateCost,
  explain,
  findPrice,
  formatCost,
  routeProvider,
} from "../dist/esm/index.js";

const close = (actual, expected, epsilon = 1e-6) =>
  assert.ok(Math.abs(actual - expected) < epsilon, `${actual} !~= ${expected}`);

test("snapshot loads and is populated", () => {
  const prices = allPrices();
  assert.ok(prices.length > 100);
  assert.ok(prices.every((p) => p.input_per_1k_toman >= 0));
  const providers = new Set(prices.map((p) => p.provider));
  for (const provider of ["openai", "anthropic", "gemini", "deepseek"]) {
    assert.ok(providers.has(provider), `missing provider ${provider}`);
  }
});

test("routing rule matches documented behaviour", () => {
  assert.equal(routeProvider("claude-opus-4-5"), "anthropic");
  assert.equal(routeProvider("gemini-2.5-flash"), "gemini");
  assert.equal(routeProvider("gemma-3-27b"), "gemini");
  assert.equal(routeProvider("deepseek-v4-flash"), "deepseek");
  assert.equal(routeProvider("gpt-5.2"), "openai");
  assert.equal(routeProvider("ft:gpt-4o-2024-08-06"), "openai");
  assert.equal(routeProvider("o3-mini"), "openai");
});

test("cost arithmetic is exact", () => {
  // gpt-4o-mini: 33.534 Toman / 1k in, 134.136 Toman / 1k out.
  const estimate = estimateCost("gpt-4o-mini", 1000, 500);
  close(estimate.inputToman, 33.534);
  close(estimate.outputToman, 67.068);
  close(estimate.totalToman, 100.602);
  assert.equal(estimate.provider, "openai");
  assert.equal(estimate.pricedFrom, "snapshot");
});

test("zero tokens costs nothing", () => {
  assert.equal(estimateCost("gpt-4o-mini", 0, 0).totalToman, 0);
});

test("duplicate model name resolves via the routing rule", () => {
  // claude-3-5-haiku is listed under BOTH anthropic and gemini (Vertex resale)
  // at different prices. The gateway routes claude-* to Anthropic, so that is
  // the price the caller will actually be charged.
  const price = findPrice("claude-3-5-haiku");
  assert.ok(price);
  assert.equal(price.provider, "anthropic");
  close(price.input_per_1k_toman, 178.848);
});

test("unknown model throws with suggestions", () => {
  assert.throws(
    () => estimateCost("gpt-4o-mimi", 10, 10),
    (error) => error instanceof UnknownModelError && error.message.includes("gpt-4o-mini"),
  );
});

test("audio and image models are explicitly unpriced", () => {
  for (const model of ["whisper-1", "gpt-image-1", "dall-e-3", "tts-1"]) {
    assert.throws(
      () => estimateCost(model, 100, 100),
      (error) =>
        error instanceof UnknownModelError && error.message.toLowerCase().includes("audio"),
      `${model} should be reported as unpriced`,
    );
  }
});

test("costOfResponse reads an SDK-shaped response", () => {
  const fake = {
    model: "gpt-4o-mini",
    usage: { prompt_tokens: 1000, completion_tokens: 500 },
  };
  close(costOfResponse(fake).totalToman, 100.602);
  assert.match(formatCost(costOfResponse(fake)), /Toman/);
});

test("costOfResponse tolerates missing usage", () => {
  assert.equal(costOfResponse({ model: "gpt-4o-mini" }).totalToman, 0);
});

test("missing key message names the env vars", () => {
  assert.throws(
    () => checkKey(undefined),
    (error) => error instanceof MissingKeyError && error.message.includes("ONEXAI_API_KEY"),
  );
});

test("an OpenAI key is rejected with a useful message", () => {
  assert.throws(
    () => checkKey("sk-proj-abc123"),
    (error) => error instanceof InvalidKeyError && error.message.includes("OpenAI key"),
  );
});

test("an Anthropic key is rejected", () => {
  assert.throws(() => checkKey("sk-ant-api03-abc"), InvalidKeyError);
});

test("a valid key shape passes", () => {
  assert.equal(checkKey("1xai-abc123"), "1xai-abc123");
});

test("explain translates the Persian 401 body", () => {
  const body = { error: { message: "کلید API نامعتبر است", type: "api_error" } };
  assert.match(explain(body).toLowerCase(), /invalid/);
});

test("explain 402 is about the wallet, not the code", () => {
  assert.match(explain(402).toLowerCase(), /credit/);
});

test("explain never throws", () => {
  for (const value of [null, undefined, {}, "", 999, new Error("boom")]) {
    assert.equal(typeof explain(value), "string");
  }
});
