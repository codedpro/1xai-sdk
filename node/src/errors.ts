/**
 * Clear, actionable errors.
 *
 * Two things make 1xAi failures confusing for a newcomer:
 *
 * 1. The gateway replies in Persian (`{"error":{"message":"کلید API نامعتبر است"}}`),
 *    which is right for its audience but opaque in an English stack trace.
 * 2. A `402` from an OpenAI SDK is unusual -- on api.openai.com you would never
 *    see one. Here it means your Toman wallet is empty, which is a completely
 *    different fix from a `401`.
 *
 * So we translate. `explain()` turns any gateway failure into one sentence that
 * says what to actually do.
 */

import { DASHBOARD_URL, ENV_VARS, KEY_PREFIX, STATUS_URL } from "./constants.js";

/** Base class for every error this package raises itself. */
export class OneXAIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

/** No API key was passed and none was found in the environment. */
export class MissingKeyError extends OneXAIError {}

/** A key was supplied but it is not a 1xAi key. */
export class InvalidKeyError extends OneXAIError {}

/** A model name is absent from the Toman price catalogue. */
export class UnknownModelError extends OneXAIError {}

/**
 * Persian error strings the gateway is known to return, mapped to English.
 * Matched as substrings so upstream wording tweaks do not break us.
 */
const PERSIAN_HINTS: ReadonlyArray<readonly [string, string]> = [
  ["کلید API ارسال نشده", "No API key reached the gateway -- the Authorization header was missing or empty."],
  ["کلید API نامعتبر", "The gateway rejected this API key as invalid."],
  ["اعتبار", "Your Toman wallet does not have enough credit for this request."],
  ["موجودی", "Your Toman wallet does not have enough credit for this request."],
];

const BY_STATUS: Readonly<Record<number, string>> = {
  400:
    "The gateway rejected the request body. Most often this is a model name that " +
    "does not exist upstream, or a parameter the target provider does not accept " +
    "(remember: `claude-*` and `gemini-*` are translated from the OpenAI shape, so " +
    "provider-specific fields can be dropped or refused).",
  401:
    `Authentication failed. Check that your key is set (tried: ${ENV_VARS.join(", ")}) ` +
    `and that it starts with \`${KEY_PREFIX}\`. An \`sk-...\` key belongs to OpenAI ` +
    `directly and will never work here. Mint a key at ${DASHBOARD_URL}.`,
  402:
    "Out of credit. 1xAi bills a prepaid Toman wallet, so a 402 means the wallet is " +
    `empty rather than anything being wrong with your code. Top up at ${DASHBOARD_URL}.`,
  403: "The key is valid but not allowed to perform this action.",
  404:
    "No such endpoint or model. Check the path against https://1xai.ir/openapi.json -- " +
    "the OpenAI-compatible routes live under /v1, while the native passthroughs are " +
    "/anthropic/v1/... and /gemini/v1beta/... .",
  408: "The request timed out before the upstream provider answered. Retry, ideally with backoff.",
  413: "The request body was too large. Trim the prompt, the file, or the batch.",
  429:
    "Rate limited. This can be your own throughput or the shared upstream capacity. " +
    "Back off exponentially and retry.",
  500: "The gateway hit an internal error. Retry; if it persists, contact https://1xai.ir/contact .",
  502: `The upstream provider returned a bad response through the gateway. Check ${STATUS_URL} .`,
  503:
    "The upstream provider (OpenAI / Anthropic / Google / DeepSeek) is unavailable as " +
    `seen from the gateway. Check live per-provider health at ${STATUS_URL} -- and ` +
    "consider failing over to a model from a different provider.",
  504: `The upstream provider timed out. Check ${STATUS_URL} and retry.`,
};

function statusOf(error: unknown): number | undefined {
  if (typeof error !== "object" || error === null) return undefined;
  const candidate = error as Record<string, unknown>;
  for (const key of ["status", "statusCode", "code"]) {
    const value = candidate[key];
    if (typeof value === "number" && value >= 100 && value <= 599) return value;
  }
  const response = candidate.response as Record<string, unknown> | undefined;
  if (response && typeof response.status === "number") return response.status;
  return undefined;
}

function messageOf(error: unknown): string {
  if (typeof error === "string") return error;
  if (typeof error !== "object" || error === null) return "";
  const candidate = error as Record<string, unknown>;
  const nested = candidate.error as Record<string, unknown> | undefined;
  if (nested && typeof nested.message === "string") return nested.message;
  if (typeof candidate.message === "string") return candidate.message;
  return "";
}

/**
 * Return one actionable English sentence for a gateway failure.
 *
 * Accepts anything: an `APIError` from the OpenAI SDK, a `Response`, an HTTP
 * status number, or the decoded `{ error: { ... } }` body. Never throws -- the
 * whole point is to be safe to call inside a `catch`.
 *
 * ```ts
 * try { await client.chat.completions.create(...) }
 * catch (err) { console.error(explain(err)); }
 * ```
 */
export function explain(error: unknown): string {
  if (typeof error === "number") {
    return BY_STATUS[error] ?? `The gateway returned HTTP ${error}.`;
  }

  const text = messageOf(error);
  const status = statusOf(error);

  for (const [needle, english] of PERSIAN_HINTS) {
    if (text.includes(needle)) {
      const tail = status !== undefined ? BY_STATUS[status] ?? "" : "";
      return `${english} ${tail}`.trim();
    }
  }

  if (status !== undefined && BY_STATUS[status]) return BY_STATUS[status];
  if (status !== undefined) {
    return `The gateway returned HTTP ${status}: ${text || "(no message)"}`;
  }
  return text || "The gateway request failed for an unknown reason.";
}

/**
 * Validate a 1xAi key's shape and return it, or throw a clear error.
 *
 * Catches the two mistakes that actually happen: forgetting to set the key at
 * all, and pasting a key from the wrong provider.
 */
export function checkKey(apiKey: string | undefined | null, strict = true): string {
  if (!apiKey || !apiKey.trim()) {
    throw new MissingKeyError(
      `No 1xAi API key found. Pass { apiKey } or set one of ${ENV_VARS.join(" / ")}. ` +
        `Keys start with \`${KEY_PREFIX}\` and are minted at ${DASHBOARD_URL}.`,
    );
  }

  const key = apiKey.trim();

  if (key.startsWith("sk-ant-")) {
    throw new InvalidKeyError(
      "That is an Anthropic key, not a 1xAi key. 1xAi holds the upstream provider keys " +
        `for you -- you only ever send your own \`${KEY_PREFIX}\` key. Mint one at ${DASHBOARD_URL}.`,
    );
  }
  if (key.startsWith("sk-")) {
    throw new InvalidKeyError(
      "That is an OpenAI key, not a 1xAi key. Pointing an `sk-...` key at 1xai.ir will " +
        `always fail with 401. 1xAi holds the upstream keys for you -- send your own ` +
        `\`${KEY_PREFIX}\` key instead, minted at ${DASHBOARD_URL}.`,
    );
  }
  if (key.startsWith("AIza")) {
    throw new InvalidKeyError(
      "That is a Google AI Studio key, not a 1xAi key. Send your own " +
        `\`${KEY_PREFIX}\` key instead, minted at ${DASHBOARD_URL}.`,
    );
  }

  if (!key.startsWith(KEY_PREFIX)) {
    const message =
      `This key does not start with \`${KEY_PREFIX}\`, which every key minted by the 1xAi ` +
      `dashboard does. Double-check it at ${DASHBOARD_URL}. Pass { strictKey: false } if ` +
      "you are deliberately using a custom gateway.";
    if (strict) throw new InvalidKeyError(message);
    console.warn(`[onexai] ${message}`);
  }

  return key;
}
