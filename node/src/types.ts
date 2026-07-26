/** Shared types for the 1xAi helpers. */

/** The upstream a model name routes to, per the gateway's documented rule. */
export type Provider = "openai" | "anthropic" | "gemini" | "deepseek";

/** Toman price per 1000 tokens for one model on one provider. */
export interface ModelPrice {
  readonly provider: string;
  readonly model: string;
  readonly input_per_1k_toman: number;
  readonly output_per_1k_toman: number;
}

/** The shape of the bundled snapshot and of https://1xai.ir/api/models. */
export interface PricingSnapshot {
  readonly source: string;
  readonly generated_at: string;
  readonly currency: string;
  readonly unit: string;
  readonly note: string;
  readonly models: readonly ModelPrice[];
}

/** The Toman cost of a single call. */
export interface CostEstimate {
  readonly model: string;
  readonly provider: string;
  readonly inputTokens: number;
  readonly outputTokens: number;
  readonly inputToman: number;
  readonly outputToman: number;
  readonly totalToman: number;
  /** `"snapshot"` (bundled, possibly stale) or `"live"` (just fetched). */
  readonly pricedFrom: "snapshot" | "live";
  readonly generatedAt: string;
}

/** One line of `doctor` output. */
export interface Check {
  readonly name: string;
  readonly ok: boolean;
  readonly detail: string;
}

export interface Diagnosis {
  readonly checks: Check[];
  readonly ok: boolean;
}

/** Options accepted by the client factories. */
export interface ClientOptions {
  /** Your `1xai-` key. Defaults to ONEXAI_API_KEY, then OPENAI_API_KEY. */
  apiKey?: string;
  /** Override only if you are proxying the gateway yourself. */
  baseURL?: string;
  /** Set false to downgrade key-shape errors to a console warning. */
  strictKey?: boolean;
  /** Anything else the official OpenAI client accepts. */
  [key: string]: unknown;
}
