/**
 * Pre-configured OpenAI clients pointed at 1xAi.
 *
 * Why depend on the official `openai` package instead of writing a new SDK?
 *
 * Because 1xAi's entire product claim is that it *is* the OpenAI API. Re-implementing
 * HTTP, retries, streaming, tool calls and file uploads would mean shipping a worse
 * copy of a client OpenAI already maintains, and it would silently drift every time
 * the API adds a field. Wrapping means you get the real SDK -- every method, every
 * type, every future feature -- with the base URL, key discovery and key validation
 * already correct. The wrapper below is deliberately tiny; if it were large, it would
 * be doing something wrong.
 *
 * If you would rather not add a dependency at all, you do not need this package:
 *
 * ```ts
 * import OpenAI from "openai";
 * const client = new OpenAI({ apiKey: "1xai-...", baseURL: "https://1xai.ir/v1" });
 * ```
 *
 * That is the whole integration. What you lose is the key validation, the Toman cost
 * helper and the translated errors.
 */

import OpenAI from "openai";

import { ANTHROPIC_BASE_URL, BASE_URL, ENV_VARS, GEMINI_BASE_URL } from "./constants.js";
import { checkKey } from "./errors.js";
import type { ClientOptions } from "./types.js";

/** Return the first key found: the argument, then ONEXAI_API_KEY, then OPENAI_API_KEY. */
export function resolveKey(apiKey?: string): string | undefined {
  if (apiKey) return apiKey;
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  if (!env) return undefined;
  for (const name of ENV_VARS) {
    if (env[name]) return env[name];
  }
  return undefined;
}

/**
 * An `OpenAI` client wired to 1xAi.
 *
 * ```ts
 * import { OneXAI, costOfResponse, formatCost } from "1xai-sdk";
 *
 * const client = new OneXAI();           // reads ONEXAI_API_KEY / OPENAI_API_KEY
 * const reply = await client.chat.completions.create({
 *   model: "gpt-4o-mini",
 *   messages: [{ role: "user", content: "سلام" }],
 * });
 * console.log(reply.choices[0].message.content);
 * console.log(formatCost(costOfResponse(reply)));
 * ```
 *
 * This extends the official client, so `.chat`, `.embeddings`, `.audio`, `.images`,
 * `.models` and `.responses` behave exactly as OpenAI documents them.
 */
export class OneXAI extends OpenAI {
  constructor(options: ClientOptions = {}) {
    const { apiKey, baseURL = BASE_URL, strictKey = true, ...rest } = options;
    super({
      apiKey: checkKey(resolveKey(apiKey), strictKey),
      baseURL,
      ...rest,
    } as ConstructorParameters<typeof OpenAI>[0]);
  }
}

/** Functional alias, for `const client = createClient()` style. */
export function createClient(options: ClientOptions = {}): OneXAI {
  return new OneXAI(options);
}

/**
 * Config for the official `@anthropic-ai/sdk` on 1xAi's native passthrough.
 *
 * Use this only when you need what the OpenAI-compatible path drops:
 * `cache_control` prompt caching, `thinking` budgets, citations, server-side tool
 * use, or cache-token usage accounting. For ordinary chat, `OneXAI` with a
 * `claude-*` model is simpler.
 *
 * ```ts
 * import Anthropic from "@anthropic-ai/sdk";
 * import { anthropicConfig } from "1xai-sdk";
 *
 * const claude = new Anthropic(anthropicConfig());
 * ```
 *
 * Returned as config rather than a constructed client so this package never has to
 * depend on the Anthropic SDK.
 */
export function anthropicConfig(options: ClientOptions = {}): {
  apiKey: string;
  baseURL: string;
} & Record<string, unknown> {
  const { apiKey, strictKey = true, baseURL = ANTHROPIC_BASE_URL, ...rest } = options;
  return { apiKey: checkKey(resolveKey(apiKey), strictKey), baseURL, ...rest };
}

/**
 * Config for the official `@google/genai` SDK on 1xAi's native Gemini passthrough.
 *
 * Use this when you need `cachedContents` or the full `generationConfig` surface.
 *
 * ```ts
 * import { GoogleGenAI } from "@google/genai";
 * import { geminiConfig } from "1xai-sdk";
 *
 * const gemini = new GoogleGenAI(geminiConfig());
 * ```
 */
export function geminiConfig(options: ClientOptions = {}): {
  apiKey: string;
  httpOptions: { baseUrl: string };
} & Record<string, unknown> {
  const { apiKey, strictKey = true, baseURL = GEMINI_BASE_URL, ...rest } = options;
  return {
    apiKey: checkKey(resolveKey(apiKey), strictKey),
    httpOptions: { baseUrl: baseURL },
    ...rest,
  };
}
