# onexai — Node/TypeScript SDK for the 1xAi gateway

[1xAi](https://1xai.ir) is an OpenAI-compatible AI gateway for Iran: one key and one
base URL for OpenAI, Anthropic Claude, Google Gemini and DeepSeek — no VPN, no
foreign card, billed in Toman.

```bash
npm install 1xai-sdk
```

```ts
import { OneXAI, costOfResponse, formatCost } from "1xai-sdk";

const client = new OneXAI(); // reads ONEXAI_API_KEY, falls back to OPENAI_API_KEY

const reply = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "سلام! یک جوک فارسی بگو" }],
});

console.log(reply.choices[0].message.content);
console.log(formatCost(costOfResponse(reply))); // -> 102 Toman (gpt-4o-mini, 14in/23out)
```

Ships ESM + CommonJS + type declarations. Node >= 18.

## Why this package is thin (and why that is the point)

1xAi's whole claim is that it **is** the OpenAI API at a different base URL. So this
package does not re-implement an SDK — `OneXAI` extends the official `openai` client
and pre-configures it. Writing our own HTTP, streaming, retry and tool-call layer
would mean shipping a worse copy of a client OpenAI already maintains, and it would
drift every time the API gains a field.

You do not strictly need this package:

```ts
import OpenAI from "openai";
const client = new OpenAI({ apiKey: "1xai-...", baseURL: "https://1xai.ir/v1" });
```

That is the entire integration. What `onexai` adds is the small set of things the
generic SDK cannot know about a gateway in Iran:

| | |
|---|---|
| **Toman cost** | `estimateCost()` / `costOfResponse()` priced from 1xAi's public catalogue |
| **Real errors** | the gateway answers in Persian; `explain()` turns that into one actionable English sentence — including `402`, which here means *your wallet is empty*, not *your code is broken* |
| **Key validation** | pasting an `sk-...` key throws at construction instead of a confusing 401 later |
| **Native passthroughs** | `anthropicConfig()` and `geminiConfig()` for prompt caching, thinking budgets and `cachedContents` |
| **`npx onexai doctor`** | one command that tells you which of key / network / credit / upstream is actually broken |

## CLI

```bash
npx onexai doctor                        # diagnose key, connectivity, credit, upstream health
npx onexai price gpt-4o-mini 1000 500    # Toman cost of a call
npx onexai models --provider anthropic   # what you can call, with prices
npx onexai status                        # live upstream health, as seen from Iran
```

## Cost estimation

Prices come from `https://1xai.ir/api/models` — public, no key required. A snapshot
ships with the package so the helper works offline; call `fetchPricing()` for live
prices.

```ts
import { estimateCost, fetchPricing } from "1xai-sdk";

estimateCost("claude-opus-4-5", 50_000, 2_000).totalToman; // 67068
estimateCost("gpt-4o-mini", 1000, 500, await fetchPricing()).totalToman;
```

Audio and image endpoints are billed per second and per image, so they are **not** in
the token catalogue. `estimateCost("whisper-1", ...)` throws `UnknownModelError`
explaining that, rather than quietly returning zero.

## Model routing

You never choose a provider — the model name does it. `claude-*` → Anthropic,
`gemini-*`/`gemma-*` → Google, `deepseek-*` → DeepSeek, everything else → OpenAI.

```ts
import { routeProvider } from "1xai-sdk";
routeProvider("claude-opus-4-5"); // "anthropic"
```

## Full cookbook

Runnable recipes for Cursor, Continue, Cline, Open WebUI, n8n, streaming, Persian
Whisper transcription, image generation and cost control live in the
[repository README](https://github.com/codedpro/1xai-sdk).

## License

MIT. Community-maintained; not an official 1xAi product unless the 1xAi team adopts it.
