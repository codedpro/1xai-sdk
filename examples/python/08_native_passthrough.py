"""Native Anthropic and Gemini passthroughs.

The OpenAI-compatible path translates every request into the OpenAI shape, which
means provider-specific features are silently dropped. When you need them, 1xAi
exposes the vendors' own APIs at /anthropic and /gemini.

Use the native path when you need:
  Anthropic -- `cache_control` prompt caching, `thinking` budgets, citations,
               server-side tool use, cache-token usage accounting.
  Gemini    -- `cachedContents`, the full `generationConfig` surface.

Otherwise the /v1 path is simpler.

    pip install "onexai[all]"
    python 08_native_passthrough.py
"""

from onexai import anthropic_client, gemini_client

BIG_DOCUMENT = "..." * 1000  # something worth caching

# --- Anthropic: prompt caching, which /v1 cannot express -------------------
claude = anthropic_client()  # -> https://1xai.ir/anthropic

message = claude.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": BIG_DOCUMENT,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "این سند را در سه جمله خلاصه کن."}],
)

print(message.content[0].text)
print(
    "cache: created={} read={}".format(
        message.usage.cache_creation_input_tokens,
        message.usage.cache_read_input_tokens,
    )
)

# --- Gemini: the official Google SDK, same key -----------------------------
gemini = gemini_client()  # -> https://1xai.ir/gemini

result = gemini.models.generate_content(
    model="gemini-2.5-flash",
    contents="یک هایکو درباره تهران بنویس.",
)
print(result.text)
