/**
 * Endpoint constants and the model -> provider routing rule.
 *
 * Everything here mirrors what 1xAi documents at https://1xai.ir/llms.txt and
 * https://1xai.ir/openapi.json. Nothing is invented.
 */

import type { Provider } from "./types.js";

/** OpenAI-compatible surface. Point any OpenAI SDK here. */
export const BASE_URL = "https://1xai.ir/v1";

/**
 * Native Anthropic Messages passthrough. Use with the official
 * `@anthropic-ai/sdk` when you need what the OpenAI-compatible path drops:
 * `cache_control` prompt caching, `thinking` budgets, citations, server-side
 * tool use, or cache-token usage accounting.
 */
export const ANTHROPIC_BASE_URL = "https://1xai.ir/anthropic";

/**
 * Native Google Gemini passthrough. Use with the official `@google/genai` SDK
 * when you need `cachedContents` or the full `generationConfig` surface.
 */
export const GEMINI_BASE_URL = "https://1xai.ir/gemini";

/** Public, unauthenticated Toman price catalogue. */
export const PRICING_URL = "https://1xai.ir/api/models";

/** Public, unauthenticated per-provider health, as seen from Iran. */
export const STATUS_URL = "https://1xai.ir/api/status";

/** Every key minted by the dashboard carries this prefix. */
export const KEY_PREFIX = "1xai-";

export const DASHBOARD_URL = "https://1xai.ir/dashboard";
export const DOCS_URL = "https://1xai.ir/docs";

/** Environment variables checked, in order, when no key is passed explicitly. */
export const ENV_VARS = ["ONEXAI_API_KEY", "OPENAI_API_KEY"] as const;

/**
 * Return the upstream provider 1xAi will route `model` to.
 *
 * The gateway picks the upstream purely from the model name: `claude-*` goes to
 * Anthropic, `gemini-*`/`gemma-*` to Google, `deepseek-*` to DeepSeek, and
 * everything else to OpenAI.
 *
 * ```ts
 * routeProvider("claude-opus-4-5"); // "anthropic"
 * routeProvider("gpt-5.2");         // "openai"
 * ```
 */
export function routeProvider(model: string): Provider {
  const name = (model ?? "").trim().toLowerCase();
  // Fine-tuned OpenAI models arrive as "ft:gpt-4o-2024-08-06:org::id".
  if (name.startsWith("ft:")) return "openai";
  if (name.startsWith("claude-")) return "anthropic";
  if (name.startsWith("gemini-") || name.startsWith("gemma-")) return "gemini";
  if (name.startsWith("deepseek-")) return "deepseek";
  return "openai";
}
