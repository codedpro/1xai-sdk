#!/usr/bin/env node
/**
 * Command line entry point: `npx onexai ...`
 *
 *   onexai doctor                       # why isn't my setup working?
 *   onexai price gpt-4o-mini 1000 500   # what does that cost in Toman?
 *   onexai models --provider anthropic  # what can I call?
 *   onexai status                       # are the upstreams up right now?
 */

import { BASE_URL, STATUS_URL } from "./constants.js";
import { diagnose, formatDiagnosis } from "./diagnostics.js";
import { OneXAIError } from "./errors.js";
import { allPrices, estimateCost, fetchPricing, snapshot } from "./pricing.js";
import type { PricingSnapshot } from "./types.js";

const USAGE = `onexai -- helpers for the 1xAi gateway (https://1xai.ir)

  onexai doctor                          diagnose key and connectivity problems
  onexai price <model> [in] [out]        estimate the Toman cost of a call
  onexai models [--provider p] [--search s]   list priced models
  onexai status                          live upstream provider health

Options:
  --live     fetch current prices instead of the bundled snapshot
  --json     machine-readable output (price only)
`;

function hasFlag(argv: string[], name: string): boolean {
  return argv.includes(`--${name}`);
}

function flagValue(argv: string[], name: string): string | undefined {
  const index = argv.indexOf(`--${name}`);
  return index >= 0 ? argv[index + 1] : undefined;
}

async function catalogueFor(argv: string[]): Promise<PricingSnapshot> {
  return hasFlag(argv, "live") ? await fetchPricing() : snapshot();
}

async function cmdDoctor(): Promise<number> {
  const diagnosis = await diagnose();
  console.log(formatDiagnosis(diagnosis));
  return diagnosis.ok ? 0 : 1;
}

async function cmdPrice(argv: string[]): Promise<number> {
  const positional = argv.filter((arg) => !arg.startsWith("--"));
  const [model, inTokens, outTokens] = positional;
  if (!model) {
    console.error("Usage: onexai price <model> [input_tokens] [output_tokens]");
    return 1;
  }

  try {
    const estimate = estimateCost(
      model,
      Number(inTokens ?? 0) || 0,
      Number(outTokens ?? 0) || 0,
      await catalogueFor(argv),
    );

    if (hasFlag(argv, "json")) {
      console.log(JSON.stringify(estimate, null, 2));
      return 0;
    }

    const toman = (value: number) => value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    console.log(`model      ${estimate.model}  (routed to ${estimate.provider})`);
    console.log(`input      ${estimate.inputTokens.toLocaleString("en-US").padStart(9)} tokens  ->  ${toman(estimate.inputToman).padStart(12)} Toman`);
    console.log(`output     ${estimate.outputTokens.toLocaleString("en-US").padStart(9)} tokens  ->  ${toman(estimate.outputToman).padStart(12)} Toman`);
    console.log(`total                            ->  ${toman(estimate.totalToman).padStart(12)} Toman`);
    console.log(`priced from ${estimate.pricedFrom} (${estimate.generatedAt})`);
    return 0;
  } catch (error) {
    if (error instanceof OneXAIError) {
      console.error(error.message);
      return 1;
    }
    throw error;
  }
}

async function cmdModels(argv: string[]): Promise<number> {
  let prices = [...allPrices(await catalogueFor(argv))];
  const provider = flagValue(argv, "provider");
  const search = flagValue(argv, "search");

  if (provider) prices = prices.filter((price) => price.provider === provider);
  if (search) {
    const needle = search.toLowerCase();
    prices = prices.filter((price) => price.model.toLowerCase().includes(needle));
  }
  if (prices.length === 0) {
    console.error("No models matched.");
    return 1;
  }

  const width = Math.max(...prices.map((price) => price.model.length));
  const money = (value: number) =>
    value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).padStart(12);

  console.log(`${"MODEL".padEnd(width)}  ${"PROVIDER".padEnd(10)} ${"IN/1k".padStart(12)} ${"OUT/1k".padStart(12)}   (Toman)`);
  for (const price of prices) {
    console.log(
      `${price.model.padEnd(width)}  ${price.provider.padEnd(10)} ${money(price.input_per_1k_toman)} ${money(price.output_per_1k_toman)}`,
    );
  }
  console.log(`\n${prices.length} models. Base URL: ${BASE_URL}`);
  return 0;
}

async function cmdStatus(): Promise<number> {
  const response = await fetch(STATUS_URL, { headers: { "User-Agent": "onexai-node/cli" } });
  if (!response.ok) {
    console.error(`Could not read ${STATUS_URL} (HTTP ${response.status})`);
    return 1;
  }
  const body = (await response.json()) as {
    overall?: string;
    updated_at?: string;
    providers?: { provider?: string; state?: string; ok_pct_24h?: number; reqs_24h?: number }[];
  };
  console.log(`overall: ${body.overall}  (updated ${body.updated_at})`);
  for (const provider of body.providers ?? []) {
    console.log(
      `  ${String(provider.provider).padEnd(10)} ${String(provider.state).padEnd(12)} ` +
        `24h ok ${provider.ok_pct_24h}%   reqs/24h ${provider.reqs_24h}`,
    );
  }
  return 0;
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2);
  const command = argv[0];
  const rest = argv.slice(1);

  switch (command) {
    case "doctor":
      return cmdDoctor();
    case "price":
      return cmdPrice(rest);
    case "models":
      return cmdModels(rest);
    case "status":
      return cmdStatus();
    case "--help":
    case "-h":
    case undefined:
      console.log(USAGE);
      return command === undefined ? 1 : 0;
    default:
      console.error(`Unknown command: ${command}\n\n${USAGE}`);
      return 1;
  }
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
