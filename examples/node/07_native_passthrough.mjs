/**
 * Native Anthropic and Gemini passthroughs.
 *
 * The OpenAI-compatible path translates every request into the OpenAI shape,
 * which means provider-specific features are silently dropped. When you need
 * them, 1xAi exposes the vendors' own APIs at /anthropic and /gemini.
 *
 * Use the native path when you need:
 *   Anthropic -- `cache_control` prompt caching, `thinking` budgets, citations,
 *                server-side tool use, cache-token usage accounting.
 *   Gemini    -- `cachedContents`, the full `generationConfig` surface.
 *
 * Otherwise the /v1 path is simpler.
 *
 *   npm i onexai @anthropic-ai/sdk @google/genai
 *   node 07_native_passthrough.mjs
 */

import Anthropic from "@anthropic-ai/sdk";
import { GoogleGenAI } from "@google/genai";

import { anthropicConfig, geminiConfig } from "1xai-sdk";

const BIG_DOCUMENT = "...".repeat(1000); // something worth caching

// --- Anthropic: prompt caching, which /v1 cannot express -------------------
const claude = new Anthropic(anthropicConfig()); // -> https://1xai.ir/anthropic

const message = await claude.messages.create({
  model: "claude-opus-4-5",
  max_tokens: 1024,
  system: [
    { type: "text", text: BIG_DOCUMENT, cache_control: { type: "ephemeral" } },
  ],
  messages: [{ role: "user", content: "این سند را در سه جمله خلاصه کن." }],
});

console.log(message.content[0].text);
console.log(
  `cache: created=${message.usage.cache_creation_input_tokens} ` +
    `read=${message.usage.cache_read_input_tokens}`,
);

// --- Gemini: the official Google SDK, same key -----------------------------
const gemini = new GoogleGenAI(geminiConfig()); // -> https://1xai.ir/gemini

const result = await gemini.models.generateContent({
  model: "gemini-2.5-flash",
  contents: "یک هایکو درباره تهران بنویس.",
});
console.log(result.text);
