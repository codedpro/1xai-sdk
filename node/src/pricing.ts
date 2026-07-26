/**
 * Toman cost estimation.
 *
 * 1xAi publishes a public, unauthenticated price catalogue at
 * https://1xai.ir/api/models -- every token-billed model with its Toman price
 * per 1000 input and output tokens. This module bundles a snapshot of it (so the
 * helper works offline and in CI) and can refresh from the live endpoint.
 *
 * What it covers, honestly:
 *
 * - Token-billed models -- chat, reasoning and embedding models. Covered.
 * - Audio (`/v1/audio/transcriptions`, `/v1/audio/speech`) -- billed per second
 *   and per character, and **not present in the catalogue**. Not covered.
 * - Images (`/v1/images/generations`) -- billed per image. Not covered.
 *
 * For the uncovered endpoints `estimateCost` throws `UnknownModelError` with
 * that explanation rather than silently returning zero.
 */

import { PRICING_URL, routeProvider } from "./constants.js";
import { UnknownModelError } from "./errors.js";
import { PRICING_SNAPSHOT } from "./pricing-snapshot.js";
import type { CostEstimate, ModelPrice, PricingSnapshot } from "./types.js";

let liveCache: PricingSnapshot | undefined;

/** The bundled snapshot: no network, no key. */
export function snapshot(): PricingSnapshot {
  return PRICING_SNAPSHOT;
}

/**
 * Fetch the current catalogue from https://1xai.ir/api/models (public, no key).
 * Cached in-process. Falls back to the bundled snapshot if the fetch fails,
 * which offline or filtered networks make a normal condition.
 */
export async function fetchPricing(timeoutMs = 10_000): Promise<PricingSnapshot> {
  if (liveCache) return liveCache;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(PRICING_URL, {
      signal: controller.signal,
      headers: { "User-Agent": "onexai-node" },
    });
    if (!response.ok) return PRICING_SNAPSHOT;
    const body = (await response.json()) as { models?: ModelPrice[] };
    if (!Array.isArray(body.models) || body.models.length === 0) return PRICING_SNAPSHOT;
    liveCache = {
      ...PRICING_SNAPSHOT,
      source: PRICING_URL,
      generated_at: "live",
      models: body.models,
    };
    return liveCache;
  } catch {
    return PRICING_SNAPSHOT;
  } finally {
    clearTimeout(timer);
  }
}

/** Every priced model in the given catalogue (the bundled snapshot by default). */
export function allPrices(catalogue: PricingSnapshot = PRICING_SNAPSHOT): readonly ModelPrice[] {
  return catalogue.models;
}

/**
 * Look up one model's Toman price, or `undefined` if it is not priced.
 *
 * A handful of model names appear under two providers (Anthropic's Claude models
 * are also resold through Google Vertex, and the two are not always priced
 * identically). We disambiguate with the gateway's own documented routing rule,
 * so the price you get is the price you will be charged.
 */
export function findPrice(
  model: string,
  catalogue: PricingSnapshot = PRICING_SNAPSHOT,
): ModelPrice | undefined {
  if (!model) return undefined;
  const wanted = model.trim();
  let candidates = catalogue.models.filter((row) => row.model === wanted);
  if (candidates.length === 0) {
    const lowered = wanted.toLowerCase();
    candidates = catalogue.models.filter((row) => row.model.toLowerCase() === lowered);
  }
  if (candidates.length === 0) return undefined;
  if (candidates.length === 1) return candidates[0];

  const routed = routeProvider(wanted);
  return candidates.find((row) => row.provider === routed) ?? candidates[0];
}

/** Cheap Levenshtein, used only to suggest near-miss model names. */
function distance(a: string, b: string): number {
  const rows = a.length + 1;
  const cols = b.length + 1;
  let previous = Array.from({ length: cols }, (_, i) => i);
  for (let i = 1; i < rows; i++) {
    const current = [i];
    for (let j = 1; j < cols; j++) {
      current[j] = Math.min(
        previous[j] + 1,
        current[j - 1] + 1,
        previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
    }
    previous = current;
  }
  return previous[cols - 1];
}

function suggest(model: string, catalogue: PricingSnapshot): string[] {
  return [...new Set(catalogue.models.map((row) => row.model))]
    .map((name) => ({ name, score: distance(model.toLowerCase(), name.toLowerCase()) }))
    .filter((entry) => entry.score <= Math.max(2, Math.floor(model.length * 0.34)))
    .sort((a, b) => a.score - b.score)
    .slice(0, 3)
    .map((entry) => entry.name);
}

/**
 * Estimate what a call costs in Toman.
 *
 * ```ts
 * estimateCost("gpt-4o-mini", 1000, 500).totalToman; // 100.602
 * ```
 *
 * Throws `UnknownModelError` -- with near-miss suggestions -- when the model is
 * not in the catalogue, rather than pretending the call was free.
 */
export function estimateCost(
  model: string,
  inputTokens = 0,
  outputTokens = 0,
  catalogue: PricingSnapshot = PRICING_SNAPSHOT,
): CostEstimate {
  const price = findPrice(model, catalogue);

  if (!price) {
    const near = suggest(model, catalogue);
    const hint = near.length ? ` Did you mean: ${near.join(", ")}?` : "";
    throw new UnknownModelError(
      `\`${model}\` is not in the 1xAi Toman price catalogue.${hint} ` +
        "Note that audio (billed per second) and image (billed per image) models are " +
        "deliberately absent -- this helper only prices token-billed models. " +
        "See https://1xai.ir/pricing for those.",
    );
  }

  const inTokens = Math.max(0, Math.trunc(inputTokens));
  const outTokens = Math.max(0, Math.trunc(outputTokens));
  const inputToman = (inTokens / 1000) * price.input_per_1k_toman;
  const outputToman = (outTokens / 1000) * price.output_per_1k_toman;
  const round = (value: number) => Math.round(value * 1e4) / 1e4;

  return {
    model: price.model,
    provider: price.provider,
    inputTokens: inTokens,
    outputTokens: outTokens,
    inputToman: round(inputToman),
    outputToman: round(outputToman),
    totalToman: round(inputToman + outputToman),
    pricedFrom: catalogue.generated_at === "live" ? "live" : "snapshot",
    generatedAt: catalogue.generated_at,
  };
}

/**
 * Price a completed call straight from the SDK response object.
 *
 * Reads `response.model` and `response.usage`, so it works with chat completions
 * and embeddings alike -- no manual token counting.
 *
 * ```ts
 * const r = await client.chat.completions.create({ ... });
 * console.log(costOfResponse(r).totalToman);
 * ```
 */
export function costOfResponse(
  response: unknown,
  catalogue: PricingSnapshot = PRICING_SNAPSHOT,
): CostEstimate {
  const body = (response ?? {}) as {
    model?: string;
    usage?: { prompt_tokens?: number; completion_tokens?: number };
  };
  if (!body.model) {
    throw new UnknownModelError("Response carried no `model` field to price.");
  }
  return estimateCost(
    body.model,
    body.usage?.prompt_tokens ?? 0,
    body.usage?.completion_tokens ?? 0,
    catalogue,
  );
}

/** Human-readable one-liner, e.g. `"101 Toman (gpt-4o-mini, 1000in/500out)"`. */
export function formatCost(estimate: CostEstimate): string {
  const toman = Math.round(estimate.totalToman).toLocaleString("en-US");
  return `${toman} Toman (${estimate.model}, ${estimate.inputTokens}in/${estimate.outputTokens}out)`;
}
