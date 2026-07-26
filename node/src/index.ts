/**
 * onexai -- a thin, honest SDK for the 1xAi gateway (https://1xai.ir).
 *
 * 1xAi is an OpenAI-compatible AI gateway for Iran. This package does not
 * re-implement an SDK: it pre-configures the official `openai` client, adds a
 * Toman cost helper built on 1xAi's public price catalogue, and translates the
 * gateway's Persian errors into actionable English.
 *
 * ```ts
 * import { OneXAI, costOfResponse, formatCost } from "onexai";
 *
 * const client = new OneXAI(); // reads ONEXAI_API_KEY, falls back to OPENAI_API_KEY
 * const reply = await client.chat.completions.create({
 *   model: "gpt-4o-mini",
 *   messages: [{ role: "user", content: "سلام! حالت چطوره؟" }],
 * });
 * console.log(reply.choices[0].message.content);
 * console.log(formatCost(costOfResponse(reply)));
 * ```
 */

export { OneXAI, createClient, resolveKey, anthropicConfig, geminiConfig } from "./client.js";

export {
  ANTHROPIC_BASE_URL,
  BASE_URL,
  DASHBOARD_URL,
  DOCS_URL,
  ENV_VARS,
  GEMINI_BASE_URL,
  KEY_PREFIX,
  PRICING_URL,
  STATUS_URL,
  routeProvider,
} from "./constants.js";

export {
  InvalidKeyError,
  MissingKeyError,
  OneXAIError,
  UnknownModelError,
  checkKey,
  explain,
} from "./errors.js";

export {
  allPrices,
  costOfResponse,
  estimateCost,
  fetchPricing,
  findPrice,
  formatCost,
  snapshot,
} from "./pricing.js";

export { diagnose, formatDiagnosis } from "./diagnostics.js";

export type {
  Check,
  ClientOptions,
  CostEstimate,
  Diagnosis,
  ModelPrice,
  PricingSnapshot,
  Provider,
} from "./types.js";

export { OneXAI as default } from "./client.js";
