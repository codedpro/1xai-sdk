"""Endpoint constants and the model -> provider routing rule.

Everything here mirrors what 1xAi documents at https://1xai.ir/llms.txt and
https://1xai.ir/openapi.json. Nothing is invented.
"""

from __future__ import annotations

#: OpenAI-compatible surface. Point any OpenAI SDK here.
BASE_URL = "https://1xai.ir/v1"

#: Native Anthropic Messages passthrough. Use with the official ``anthropic``
#: SDK when you need prompt caching (``cache_control``), extended ``thinking``
#: budgets, citations, or fine-grained cache-token usage accounting -- all of
#: which the OpenAI-compatible path silently drops.
ANTHROPIC_BASE_URL = "https://1xai.ir/anthropic"

#: Native Google Gemini passthrough. Use with the official ``google-genai``
#: SDK when you need ``cachedContents`` or the full ``generationConfig``.
GEMINI_BASE_URL = "https://1xai.ir/gemini"

#: Public, unauthenticated Toman price catalogue.
PRICING_URL = "https://1xai.ir/api/models"

#: Public, unauthenticated per-provider health, as seen from Iran.
STATUS_URL = "https://1xai.ir/api/status"

#: Every key minted by the dashboard carries this prefix.
KEY_PREFIX = "1xai-"

DASHBOARD_URL = "https://1xai.ir/dashboard"
DOCS_URL = "https://1xai.ir/docs"

#: Environment variables checked, in order, when no key is passed explicitly.
ENV_VARS = ("ONEXAI_API_KEY", "OPENAI_API_KEY")


def route_provider(model: str) -> str:
    """Return the upstream provider 1xAi will route ``model`` to.

    The gateway picks the upstream purely from the model name:
    ``claude-*`` goes to Anthropic, ``gemini-*``/``gemma-*`` to Google,
    ``deepseek-*`` to DeepSeek, and everything else to OpenAI.

    >>> route_provider("claude-opus-4-5")
    'anthropic'
    >>> route_provider("gpt-5.2")
    'openai'
    """
    name = (model or "").strip().lower()
    # Fine-tuned OpenAI models arrive as "ft:gpt-4o-2024-08-06:org::id".
    if name.startswith("ft:"):
        return "openai"
    if name.startswith("claude-"):
        return "anthropic"
    if name.startswith("gemini-") or name.startswith("gemma-"):
        return "gemini"
    if name.startswith("deepseek-"):
        return "deepseek"
    return "openai"
