"""Pre-configured OpenAI clients pointed at 1xAi.

Why subclass the official ``openai`` package instead of writing a new SDK?

Because 1xAi's entire product claim is that it *is* the OpenAI API. Re-implementing
HTTP, retries, streaming, tool calls, and file uploads would mean shipping a worse
copy of a client that OpenAI already maintains, and it would silently drift every
time the API adds a field. Subclassing means you get the real SDK -- every method,
every type, every future feature -- with the base URL, key discovery, and key
validation already correct. The subclass below is deliberately tiny; if it were
large, it would be doing something wrong.

If you would rather not add a dependency at all, you do not need this package:

    from openai import OpenAI
    client = OpenAI(api_key="1xai-...", base_url="https://1xai.ir/v1")

That is the whole integration. What you lose is the key validation, the Toman
cost helper, and the translated errors.
"""

from __future__ import annotations

import os
from typing import Any

from .constants import ANTHROPIC_BASE_URL, BASE_URL, ENV_VARS, GEMINI_BASE_URL
from .errors import check_key


def resolve_key(api_key: str | None = None) -> str | None:
    """Return the first key found: the argument, then ONEXAI_API_KEY, then OPENAI_API_KEY."""
    if api_key:
        return api_key
    for name in ENV_VARS:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _import_openai() -> Any:
    try:
        import openai
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency is declared
        raise ModuleNotFoundError(
            "onexai wraps the official OpenAI SDK, which is not installed. "
            "Run: pip install openai"
        ) from exc
    return openai


def OneXAI(  # noqa: N802 - deliberately reads like a class
    api_key: str | None = None,
    *,
    base_url: str = BASE_URL,
    strict_key: bool = True,
    **kwargs: Any,
) -> Any:
    """A synchronous ``openai.OpenAI`` client wired to 1xAi.

        from onexai import OneXAI
        client = OneXAI()                       # reads ONEXAI_API_KEY / OPENAI_API_KEY
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "سلام"}],
        )

    The returned object is a real ``openai.OpenAI`` instance, so ``.chat``,
    ``.embeddings``, ``.audio``, ``.images``, ``.models``, ``.responses`` and
    everything else behave exactly as documented by OpenAI.
    """
    openai = _import_openai()
    key = check_key(resolve_key(api_key), strict=strict_key)
    return openai.OpenAI(api_key=key, base_url=base_url, **kwargs)


def AsyncOneXAI(  # noqa: N802
    api_key: str | None = None,
    *,
    base_url: str = BASE_URL,
    strict_key: bool = True,
    **kwargs: Any,
) -> Any:
    """The ``asyncio`` twin of :func:`OneXAI` -- a configured ``openai.AsyncOpenAI``."""
    openai = _import_openai()
    key = check_key(resolve_key(api_key), strict=strict_key)
    return openai.AsyncOpenAI(api_key=key, base_url=base_url, **kwargs)


def anthropic_client(
    api_key: str | None = None,
    *,
    strict_key: bool = True,
    **kwargs: Any,
) -> Any:
    """An official ``anthropic.Anthropic`` client on 1xAi's native passthrough.

    Use this only when you need what the OpenAI-compatible path drops:
    ``cache_control`` prompt caching, ``thinking`` budgets, citations,
    server-side tool use, or cache-token usage accounting. For ordinary chat,
    :func:`OneXAI` with a ``claude-*`` model is simpler.

    Requires ``pip install anthropic``.
    """
    try:
        import anthropic
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "The native Anthropic passthrough needs the official Anthropic SDK. "
            "Run: pip install anthropic"
        ) from exc

    key = check_key(resolve_key(api_key), strict=strict_key)
    return anthropic.Anthropic(api_key=key, base_url=ANTHROPIC_BASE_URL, **kwargs)


def gemini_client(
    api_key: str | None = None,
    *,
    strict_key: bool = True,
    **kwargs: Any,
) -> Any:
    """An official ``google.genai.Client`` on 1xAi's native Gemini passthrough.

    Use this when you need ``cachedContents`` or the full ``generationConfig``
    surface. Requires ``pip install google-genai``.
    """
    try:
        from google import genai
        from google.genai import types as genai_types
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "The native Gemini passthrough needs the official Google GenAI SDK. "
            "Run: pip install google-genai"
        ) from exc

    key = check_key(resolve_key(api_key), strict=strict_key)
    http_options = genai_types.HttpOptions(base_url=GEMINI_BASE_URL)
    return genai.Client(api_key=key, http_options=http_options, **kwargs)
