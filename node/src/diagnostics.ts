/**
 * Answer "why isn't it working?" without needing a support ticket.
 *
 * `diagnose()` checks, in order: is a key present, does it look like a 1xAi key,
 * can this machine reach the gateway at all, is the key accepted, and are the
 * upstream providers healthy right now. Each step returns a plain sentence.
 */

import { resolveKey } from "./client.js";
import { BASE_URL, ENV_VARS, KEY_PREFIX, PRICING_URL, STATUS_URL } from "./constants.js";
import { explain } from "./errors.js";
import type { Check, Diagnosis } from "./types.js";

async function getJson(
  url: string,
  key?: string,
  timeoutMs = 15_000,
): Promise<{ status: number; body: unknown }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers: Record<string, string> = { "User-Agent": "onexai-node/doctor" };
    if (key) headers.Authorization = `Bearer ${key}`;
    const response = await fetch(url, { headers, signal: controller.signal });
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    return { status: response.status, body };
  } finally {
    clearTimeout(timer);
  }
}

/** Run every connectivity and configuration check and report. */
export async function diagnose(apiKey?: string, timeoutMs = 15_000): Promise<Diagnosis> {
  const checks: Check[] = [];
  const key = resolveKey(apiKey);
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};

  // 1. Is a key present at all?
  if (key) {
    const source = apiKey ? "argument" : ENV_VARS.find((name) => env[name]) ?? "environment";
    checks.push({ name: "api key present", ok: true, detail: `found via ${source}` });
  } else {
    checks.push({
      name: "api key present",
      ok: false,
      detail: "not set -- export ONEXAI_API_KEY=1xai-...",
    });
  }

  // 2. Does it look like a 1xAi key?
  if (key) {
    if (key.startsWith(KEY_PREFIX)) {
      checks.push({
        name: "api key shape",
        ok: true,
        detail: `starts with ${KEY_PREFIX} as expected`,
      });
    } else if (key.startsWith("sk-")) {
      checks.push({
        name: "api key shape",
        ok: false,
        detail: "this is an OpenAI key (sk-...), not a 1xAi key -- it will 401",
      });
    } else {
      checks.push({
        name: "api key shape",
        ok: false,
        detail: `does not start with ${KEY_PREFIX}`,
      });
    }
  }

  // 3. Can we reach the gateway at all? (public endpoint, no key needed)
  try {
    const { status, body } = await getJson(PRICING_URL, undefined, timeoutMs);
    const count = Array.isArray((body as { models?: unknown[] })?.models)
      ? (body as { models: unknown[] }).models.length
      : 0;
    checks.push({
      name: "gateway reachable",
      ok: status === 200,
      detail: `HTTP ${status} from ${PRICING_URL} (${count} models priced)`,
    });
  } catch (error) {
    checks.push({
      name: "gateway reachable",
      ok: false,
      detail: `cannot reach ${PRICING_URL}: ${String(error)}`,
    });
  }

  // 4. Is the key actually accepted?
  if (key) {
    try {
      const { status, body } = await getJson(`${BASE_URL}/models`, key, timeoutMs);
      if (status === 200) {
        const count = Array.isArray((body as { data?: unknown[] })?.data)
          ? (body as { data: unknown[] }).data.length
          : 0;
        checks.push({
          name: "api key accepted",
          ok: true,
          detail: `GET /v1/models returned ${count} models`,
        });
      } else {
        checks.push({
          name: "api key accepted",
          ok: false,
          detail: `HTTP ${status} -- ${explain(body ?? status)}`,
        });
      }
    } catch (error) {
      checks.push({
        name: "api key accepted",
        ok: false,
        detail: `request failed: ${String(error)}`,
      });
    }
  }

  // 5. Are the upstreams healthy?
  try {
    const { status, body } = await getJson(STATUS_URL, undefined, timeoutMs);
    const payload = body as {
      overall?: string;
      providers?: { provider?: string; state?: string }[];
    };
    if (status === 200 && payload?.providers) {
      const parts = payload.providers.map((p) => `${p.provider}=${p.state}`);
      checks.push({
        name: "upstream health",
        ok: payload.overall !== "down",
        detail: `overall=${payload.overall}; ${parts.join(", ")}`,
      });
    } else {
      checks.push({
        name: "upstream health",
        ok: false,
        detail: `HTTP ${status} from ${STATUS_URL}`,
      });
    }
  } catch (error) {
    checks.push({
      name: "upstream health",
      ok: false,
      detail: `cannot reach ${STATUS_URL}: ${String(error)}`,
    });
  }

  return { checks, ok: checks.every((check) => check.ok) };
}

/** Render a `Diagnosis` the way the CLI prints it. */
export function formatDiagnosis(diagnosis: Diagnosis): string {
  const lines = diagnosis.checks.map(
    (check) => `${check.ok ? "PASS" : "FAIL"}  ${check.name}: ${check.detail}`,
  );
  lines.push("");
  lines.push(diagnosis.ok ? "All checks passed." : "Some checks failed -- see above.");
  return lines.join("\n");
}
