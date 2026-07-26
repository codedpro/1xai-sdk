# 1xAi SDK — cookbook

Open-source Python and Node SDKs for **[1xAi](https://1xai.ir)**, an
OpenAI-compatible AI gateway for Iran: one key and one base URL for **OpenAI,
Anthropic Claude, Google Gemini and DeepSeek** — no VPN, no foreign card, billed
in Toman.

```bash
pip install 1xai-sdk        # Python
npm install 1xai-sdk        # Node / TypeScript
```

The packages are deliberately thin. **This README is the actual product**: every
recipe below is copy-paste runnable, and every model name and endpoint in it was
verified against the live gateway.

---

## The 10-second version

1xAi *is* the OpenAI API at a different base URL. You do not need any of this to
use it:

```python
from openai import OpenAI

client = OpenAI(api_key="1xai-...", base_url="https://1xai.ir/v1")
```

```ts
import OpenAI from "openai";

const client = new OpenAI({ apiKey: "1xai-...", baseURL: "https://1xai.ir/v1" });
```

That is the whole integration. Three env vars cover most tools:

```bash
export OPENAI_API_KEY="1xai-..."
export OPENAI_BASE_URL="https://1xai.ir/v1"   # some tools call it OPENAI_API_BASE
```

## So why does this package exist?

Because there are exactly four things a generic OpenAI SDK cannot know about a
gateway in Iran, and all four cost you an afternoon the first time you hit them:

| | |
|---|---|
| **Toman cost** | `estimateCost()` / `costOfResponse()`, priced from 1xAi's public catalogue. Your bill is in Toman; your SDK thinks in dollars it never shows you. |
| **Persian errors** | The gateway answers `{"error":{"message":"کلید API نامعتبر است"}}`. `explain()` turns that into one actionable English sentence. |
| **`402` means something else** | On api.openai.com you would never see a 402. Here it means *your wallet is empty*, not *your code is broken*. That is a top-up, not a debugging session. |
| **Wrong-key confusion** | Pasting an `sk-...` key fails at construction with an explanation, instead of a mystery 401 twenty lines later. |

**We depend on the official `openai` package and pre-configure it.** That is a
deliberate design choice: re-implementing HTTP, streaming, retries, tool calls
and file uploads would ship a worse copy of a client OpenAI already maintains,
and it would drift every time the API gains a field. You get the real SDK, with
the base URL, key discovery and validation already correct. If our wrapper were
large, it would be doing something wrong.

---

## Point your existing tools at 1xAi

No code — just a base URL and a key. Get a key from
[the dashboard](https://1xai.ir/dashboard); new accounts get free credit from
[the signup wheel](https://1xai.ir/free).

### Cursor

Settings → **Models** → scroll to *OpenAI API Key*:

1. Paste your `1xai-...` key.
2. Enable **Override OpenAI Base URL** and set it to `https://1xai.ir/v1`.
3. Add a model name under *Model Names* — e.g. `gpt-4o-mini` or `gpt-5.2` — then
   click **Verify**.

> Caveat, honestly: with a custom base URL Cursor routes chat and inline edits
> through your key, but some agent features stay on Cursor's own backend. If a
> feature does not appear to bill against your 1xAi wallet, that is why.

### Continue (VS Code / JetBrains)

`~/.continue/config.yaml`:

```yaml
name: 1xai
version: 0.0.1
schema: v1
models:
  - name: GPT-4o mini
    provider: openai
    model: gpt-4o-mini
    apiBase: https://1xai.ir/v1
    apiKey: 1xai-...
    roles: [chat, edit, apply]
  - name: Claude Opus 4.5
    provider: openai          # keep "openai" — 1xAi routes claude-* to Anthropic
    model: claude-opus-4-5
    apiBase: https://1xai.ir/v1
    apiKey: 1xai-...
    roles: [chat, edit]
  - name: Embeddings
    provider: openai
    model: text-embedding-3-small
    apiBase: https://1xai.ir/v1
    apiKey: 1xai-...
    roles: [embed]
```

The key detail: leave `provider` as `openai` even for Claude and Gemini models.
The gateway picks the upstream from the **model name**, not the provider field.

<details>
<summary>Legacy <code>config.json</code> (Continue &lt; 1.0)</summary>

```json
{
  "models": [
    {
      "title": "GPT-4o mini",
      "provider": "openai",
      "model": "gpt-4o-mini",
      "apiBase": "https://1xai.ir/v1",
      "apiKey": "1xai-..."
    }
  ]
}
```
</details>

### Cline (VS Code)

Open the Cline settings panel:

- **API Provider**: `OpenAI Compatible`
- **Base URL**: `https://1xai.ir/v1`
- **API Key**: `1xai-...`
- **Model ID**: `claude-opus-4-5` (or `gpt-5.2`, `gemini-2.5-flash`, …)

Cline is agentic and re-sends the whole context on every step, so it burns
tokens fast. Start on a cheap model and watch the wallet:

```bash
onexai price claude-opus-4-5 50000 2000    # 67,068 Toman
onexai price claude-haiku-4-5 50000 2000   # 5,589 Toman
```

### Claude Code

Claude Code speaks the native Anthropic API, so point it at the `/anthropic`
passthrough rather than `/v1`:

```bash
export ANTHROPIC_BASE_URL="https://1xai.ir/anthropic"
export ANTHROPIC_AUTH_TOKEN="1xai-..."
claude
```

### Open WebUI

```bash
docker run -d -p 3000:8080 \
  -e OPENAI_API_BASE_URL="https://1xai.ir/v1" \
  -e OPENAI_API_KEY="1xai-..." \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

Or at runtime: **Settings → Connections → OpenAI API**, set the base URL to
`https://1xai.ir/v1` and paste the key. All OpenAI, Claude, Gemini and DeepSeek
models then appear in one model picker.

### n8n

Add an **OpenAI** credential:

- **API Key**: `1xai-...`
- **Base URL**: `https://1xai.ir/v1`

Then use any *OpenAI* or *Basic LLM Chain* node and type the model name by hand
(`claude-opus-4-5`, `gemini-2.5-flash`, …) — n8n's dropdown is populated from
`GET /v1/models`, which the gateway does serve, but free-typing always works.

### Aider

```bash
export OPENAI_API_BASE="https://1xai.ir/v1"
export OPENAI_API_KEY="1xai-..."
aider --model gpt-5.2
```

### LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="claude-opus-4-5",              # routed to Anthropic by name
    api_key="1xai-...",
    base_url="https://1xai.ir/v1",
)
```

### Vercel AI SDK

```ts
import { createOpenAI } from "@ai-sdk/openai";
import { generateText } from "ai";

const oneXai = createOpenAI({
  apiKey: process.env.ONEXAI_API_KEY,
  baseURL: "https://1xai.ir/v1",
});

const { text } = await generateText({
  model: oneXai("gpt-4o-mini"),
  prompt: "سلام",
});
```

---

## Recipes

Full runnable files live in [`examples/`](examples/).

### Chat, with the Toman cost

```python
from onexai import OneXAI, cost_of_response

client = OneXAI()  # reads ONEXAI_API_KEY, falls back to OPENAI_API_KEY

reply = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "تو یک دستیار فارسی‌زبان و مختصرگو هستی."},
        {"role": "user", "content": "سه نکته برای بهینه‌سازی کوئری‌های SQL بگو."},
    ],
)

print(reply.choices[0].message.content)
print(cost_of_response(reply))   # -> 102 Toman (gpt-4o-mini, 41in/230out)
```

```ts
import { OneXAI, costOfResponse, formatCost } from "1xai-sdk";

const client = new OneXAI();

const reply = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "سه نکته برای بهینه‌سازی کوئری‌های SQL بگو." }],
});

console.log(reply.choices[0].message.content);
console.log(formatCost(costOfResponse(reply)));
```

### Streaming

SSE is forwarded unchanged. The one wrinkle worth knowing: **usage is not in the
stream unless you ask for it**, and without usage you cannot price the call.

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "یک داستان کوتاه سه جمله‌ای بنویس."}],
    stream=True,
    stream_options={"include_usage": True},   # <- ask, or you get no token counts
)

final = None
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        final = chunk

print("\n", cost_of_response(final))
```

```ts
const stream = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "یک داستان کوتاه سه جمله‌ای بنویس." }],
  stream: true,
  stream_options: { include_usage: true },
});

let usageChunk = null;
for await (const chunk of stream) {
  const delta = chunk.choices?.[0]?.delta?.content;
  if (delta) process.stdout.write(delta);
  if (chunk.usage) usageChunk = chunk;
}
console.log("\n", formatCost(costOfResponse(usageChunk)));
```

### Counting tokens and estimating Toman cost

Prices come from `https://1xai.ir/api/models` — **public, no key required**. A
snapshot ships with the package so this works offline; pass `live=True` /
`fetchPricing()` for current prices.

```python
from onexai import estimate_cost

e = estimate_cost("claude-opus-4-5", input_tokens=50_000, output_tokens=2_000)
print(e.total_toman)   # 67068.0
print(e.provider)      # anthropic
```

Compare before you commit:

```bash
$ onexai price gpt-4o-mini 1000 500
model      gpt-4o-mini  (routed to openai)
input          1,000 tokens  ->         33.53 Toman
output           500 tokens  ->         67.07 Toman
total                            ->        100.60 Toman
priced from snapshot (2026-07-26T15:49:35Z)
```

Counting input tokens *before* sending, with an honest caveat — `tiktoken`'s
encodings are OpenAI's, so for `claude-*` and `gemini-*` the count is an
approximation (usually within 10–20%). Persian also tokenizes worse than English
on every one of these models, roughly 2–3 tokens per word:

```python
import tiktoken
from onexai import estimate_cost

encoding = tiktoken.get_encoding("o200k_base")
tokens = len(encoding.encode(prompt))

projected = estimate_cost("gpt-4o-mini", tokens, output_tokens=1500)
if projected.total_toman > 50_000:
    raise SystemExit(f"too expensive: {projected.total_toman:,.0f} Toman")
```

Audio and image endpoints are billed **per second** and **per image**, so they
are not in the token catalogue. `estimate_cost("whisper-1", ...)` raises
`UnknownModelError` saying exactly that, rather than quietly returning zero.

### Persian audio with Whisper

Two things decide whether Persian transcription is good or garbage:

```python
with open("voice.m4a", "rb") as audio:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        language="fa",                                    # 1. pin the language
        prompt="اصطلاحات فنی: کوبرنتیز، داکر، ری‌اکت.",   # 2. seed proper nouns
    )
print(transcript.text)
```

- **`language="fa"`** — without it Whisper guesses from the first seconds and
  regularly mislabels Persian as Arabic or Urdu, which ruins the whole output.
- **`prompt=`** — Whisper conditions on it, so seeding product names and
  technical terms makes it spell them your way.

And back to speech (billed per character):

```python
speech = client.audio.speech.create(model="tts-1", voice="alloy", input="سلام دنیا")
speech.write_to_file("out.mp3")
```

### Image generation

```python
import base64

result = client.images.generate(
    model="gpt-image-1",
    prompt="A minimalist poster of the Milad Tower at sunrise, flat vector style, no text.",
    size="1024x1024",
    n=1,
)

image = result.data[0]
if getattr(image, "b64_json", None):        # gpt-image-1 returns base64
    open("out.png", "wb").write(base64.b64decode(image.b64_json))
else:                                        # dall-e-3 returns a URL
    print(image.url)
```

### Embeddings

```python
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["کوبرنتیز یک سامانه متن‌باز برای مدیریت کانتینرهاست."],
)
vector = response.data[0].embedding

from onexai import estimate_cost
print(estimate_cost("text-embedding-3-small", response.usage.prompt_tokens, 0))
```

Embeddings have no output tokens — the catalogue lists `output_per_1k_toman = 0`
for all of them.

### Cross-vendor failover

The thing a gateway makes uniquely easy: three vendors behind one key, so a 503
from one upstream does not end the request.

```python
from onexai import OneXAI, explain

client = OneXAI()
LADDER = ["gpt-4o-mini", "claude-haiku-4-5", "gemini-2.5-flash", "deepseek-v4-flash"]

for model in LADDER:
    try:
        reply = client.chat.completions.create(model=model, messages=messages)
        break
    except Exception as exc:
        print(f"[{model}] {explain(exc)}")
        if getattr(exc, "status_code", None) == 402:
            raise        # empty wallet — no other model will help
```

Live per-provider health, as seen from Iran:

```bash
$ onexai status
overall: operational  (updated 2026-07-26T15:50:05Z)
  anthropic  operational  24h ok 75%     reqs/24h 1281
  deepseek   operational  24h ok 66.7%   reqs/24h 3
  gemini     operational  24h ok 99.9%   reqs/24h 808
  openai     operational  24h ok 99.9%   reqs/24h 9102
```

### Native Anthropic / Gemini passthrough

The `/v1` path translates everything into the OpenAI shape, which means
provider-specific features are **silently dropped**. When you need them, 1xAi
exposes the vendors' own APIs:

| Need | Endpoint |
|---|---|
| `cache_control` prompt caching, `thinking` budgets, citations, cache-token usage | `https://1xai.ir/anthropic` |
| `cachedContents`, full `generationConfig` | `https://1xai.ir/gemini` |

```python
from onexai import anthropic_client       # pip install "onexai[anthropic]"

claude = anthropic_client()
message = claude.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system=[{"type": "text", "text": BIG_DOC,
             "cache_control": {"type": "ephemeral"}}],   # dropped on /v1
    messages=[{"role": "user", "content": "خلاصه کن"}],
)
print(message.usage.cache_read_input_tokens)
```

```ts
import Anthropic from "@anthropic-ai/sdk";
import { anthropicConfig } from "1xai-sdk";

const claude = new Anthropic(anthropicConfig());
```

---

## How model routing works

You never choose a provider. The **model name** does it:

| Model name starts with | Routed to |
|---|---|
| `claude-` | Anthropic |
| `gemini-` / `gemma-` | Google |
| `deepseek-` | DeepSeek |
| anything else (`gpt-`, `o3`, `ft:…`) | OpenAI |

```python
from onexai import route_provider
route_provider("claude-opus-4-5")   # "anthropic"
```

One consequence worth knowing: a few Claude models are listed under **both**
Anthropic and Google (Vertex resale) at different prices — `claude-3-5-haiku` is
178.85 Toman/1k input via Anthropic but 223.56 via Vertex. Our price lookup
applies the routing rule above, so you get the price you will actually be
charged.

Browse what is available and what it costs:

```bash
onexai models --provider anthropic
onexai models --search embedding
```

## Errors you will actually hit

```python
from onexai import explain

try:
    client.chat.completions.create(...)
except Exception as exc:
    print(explain(exc))
```

| Status | What it really means |
|---|---|
| `401` | Key missing, or not a `1xai-` key. An `sk-...` key will never work here. |
| **`402`** | **Your Toman wallet is empty.** Not a code bug — [top up](https://1xai.ir/dashboard). |
| `429` | Rate limited, yours or shared upstream capacity. Back off and retry. |
| `503` | The upstream vendor is down. Check [status](https://1xai.ir/api/status) and fail over to another vendor's model. |

## When something is broken, ask the doctor

```bash
$ onexai doctor
FAIL  api key present: not set -- export ONEXAI_API_KEY=1xai-...
PASS  gateway reachable: HTTP 200 from https://1xai.ir/api/models (227 models priced)
PASS  upstream health: overall=operational; anthropic=operational, deepseek=operational, gemini=operational, openai=operational

Some checks failed -- see above.
```

It separates the five things that are usually conflated: key present, key shape,
network reachability, key accepted, upstream health.

---

## Verify any of this yourself

Two endpoints are public — no key, no account. Everything this README claims
about shapes and prices comes from them:

```bash
# 227 token-billed models with Toman prices
curl -s -A onexai https://1xai.ir/api/models | head -c 400

# live per-provider health as seen from Iran
curl -s https://1xai.ir/api/status

# proves the base URL and the auth scheme (Persian error, as designed)
curl -s https://1xai.ir/v1/models
# {"error":{"message":"کلید API ارسال نشده است","type":"api_error"}}
```

> Note: `https://1xai.ir/api/models` rejects requests with no `User-Agent`
> (HTTP 403). Both SDKs set one; add `-A` if you are using bare `curl`.

The test suites run these live against production, with no key:

```bash
cd python && pytest -m live      # 5 passed
cd node   && npm test            # 21 passed
```

They include a **staleness check** that fails if the bundled price snapshot has
drifted from the live catalogue, so a release can never ship a wrong Toman
number.

## Repo layout

```
python/     the `onexai` PyPI package  (pytest, hatchling)
node/       the `onexai` npm package   (TypeScript, dual ESM+CJS, node:test)
examples/   runnable scripts for every recipe above
scripts/    refresh_pricing.py — regenerates the bundled price snapshot
```

Refresh prices before a release:

```bash
python3 scripts/refresh_pricing.py   # rewrites the snapshot in both packages
```

## Why "onexai" and not "1xai"?

`1xai` is free on both registries, but `import 1xai` is a syntax error in Python
and an invalid identifier in JavaScript — a package you cannot name in an import
statement is a bad package. `onexai` reads the same aloud, works as an
identifier in both languages, and was free on npm and PyPI.

## Contributing

Issues and PRs welcome. Two rules that keep this honest:

1. **Never invent an endpoint.** Check it against
   [`llms.txt`](https://1xai.ir/llms.txt) or
   [`openapi.json`](https://1xai.ir/openapi.json) first.
2. **Every snippet must run.** Examples are syntax-checked and model names are
   validated against the live catalogue.

Never commit a real key. The test suites use `1xai-not-a-real-key` on purpose.

## License

[MIT](LICENSE).

Community-maintained. Not an official 1xAi product unless and until the 1xAi
team adopts it. "1xAi" is the operator's name, used here to identify the service
these packages talk to.
