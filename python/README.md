# onexai — Python SDK for the 1xAi gateway

[1xAi](https://1xai.ir) is an OpenAI-compatible AI gateway for Iran: one key and one
base URL for OpenAI, Anthropic Claude, Google Gemini and DeepSeek — no VPN, no
foreign card, billed in Toman.

```bash
pip install 1xai-sdk
```

```python
from onexai import OneXAI, cost_of_response

client = OneXAI()  # reads ONEXAI_API_KEY, falls back to OPENAI_API_KEY

reply = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "سلام! یک جوک فارسی بگو"}],
)
print(reply.choices[0].message.content)
print(cost_of_response(reply))     # -> 102 Toman (gpt-4o-mini, 14in/23out)
```

## Why this package is thin (and why that is the point)

1xAi's whole claim is that it **is** the OpenAI API at a different base URL. So this
package does not re-implement an SDK — it depends on the official `openai` package and
pre-configures it. Writing our own HTTP, streaming, retry and tool-call layer would
mean shipping a worse copy of a client OpenAI already maintains, and it would drift
every time the API gains a field.

You do not strictly need this package at all:

```python
from openai import OpenAI
client = OpenAI(api_key="1xai-...", base_url="https://1xai.ir/v1")
```

That is the entire integration. What `onexai` adds is the small set of things the
generic SDK cannot know about a gateway in Iran:

| | |
|---|---|
| **Toman cost** | `estimate_cost()` / `cost_of_response()` priced from 1xAi's public catalogue |
| **Real errors** | the gateway answers in Persian; `explain()` turns that into one actionable English sentence — including `402`, which on this gateway means *your wallet is empty*, not *your code is broken* |
| **Key validation** | pasting an `sk-...` key fails loudly at construction instead of as a confusing 401 later |
| **Native passthroughs** | `anthropic_client()` and `gemini_client()` for prompt caching, thinking budgets and `cachedContents` |
| **`onexai doctor`** | one command that tells you which of key / network / credit / upstream is actually broken |

## CLI

```bash
onexai doctor                        # diagnose key, connectivity, credit, upstream health
onexai price gpt-4o-mini 1000 500    # Toman cost of a call
onexai models --provider anthropic   # what you can call, with prices
onexai status                        # live upstream health, as seen from Iran
```

## Cost estimation

Prices come from `https://1xai.ir/api/models` — public, no key required. A snapshot
ships with the package so the helper works offline; pass `live=True` to fetch current
prices.

```python
from onexai import estimate_cost

e = estimate_cost("claude-opus-4-5", input_tokens=50_000, output_tokens=2_000)
print(e.total_toman)   # 66,067.0
print(e.provider)      # anthropic
```

Audio and image endpoints are billed per second and per image, so they are **not** in
the token catalogue. `estimate_cost("whisper-1", ...)` raises `UnknownModelError`
explaining that, rather than quietly returning zero.

## Native passthroughs

The OpenAI-compatible path silently drops provider-specific features. When you need
them, use the native endpoints:

```python
from onexai import anthropic_client       # pip install '1xai-sdk[anthropic]

claude = anthropic_client()               # -> https://1xai.ir/anthropic
msg = claude.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system=[{"type": "text", "text": BIG_DOC,
             "cache_control": {"type": "ephemeral"}}],   # dropped on /v1
    messages=[{"role": "user", "content": "خلاصه کن"}],
)
print(msg.usage.cache_read_input_tokens)
```

## Full cookbook

Runnable recipes for Cursor, Continue, Cline, Open WebUI, n8n, streaming, Persian
Whisper transcription, image generation and cost control live in the
[repository README](https://github.com/codedpro/1xai-sdk).

## License

MIT. Not an official 1xAi product unless the 1xAi team adopts it; see the repository.
