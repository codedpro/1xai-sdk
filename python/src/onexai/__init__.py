"""onexai -- a thin, honest SDK for the 1xAi gateway (https://1xai.ir).

1xAi is an OpenAI-compatible AI gateway for Iran. This package does not
re-implement an SDK: it pre-configures the official ``openai`` client, adds a
Toman cost helper built on 1xAi's public price catalogue, and translates the
gateway's Persian errors into actionable English.

    from onexai import OneXAI, cost_of_response

    client = OneXAI()  # reads ONEXAI_API_KEY, falls back to OPENAI_API_KEY
    reply = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "سلام! حالت چطوره؟"}],
    )
    print(reply.choices[0].message.content)
    print(cost_of_response(reply))  # -> "102 Toman (gpt-4o-mini, 14in/23out)"
"""

from __future__ import annotations

from .client import AsyncOneXAI, OneXAI, anthropic_client, gemini_client, resolve_key
from .constants import (
    ANTHROPIC_BASE_URL,
    BASE_URL,
    DOCS_URL,
    GEMINI_BASE_URL,
    KEY_PREFIX,
    PRICING_URL,
    STATUS_URL,
    route_provider,
)
from .diagnostics import Check, Diagnosis, diagnose
from .errors import (
    InvalidKeyError,
    MissingKeyError,
    OneXAIError,
    UnknownModelError,
    check_key,
    explain,
)
from .pricing import (
    CostEstimate,
    ModelPrice,
    all_prices,
    cost_of_response,
    estimate_cost,
    find_price,
    load_pricing,
)

__version__ = "0.1.0"

__all__ = [
    # clients
    "OneXAI",
    "AsyncOneXAI",
    "anthropic_client",
    "gemini_client",
    "resolve_key",
    # constants
    "BASE_URL",
    "ANTHROPIC_BASE_URL",
    "GEMINI_BASE_URL",
    "PRICING_URL",
    "STATUS_URL",
    "DOCS_URL",
    "KEY_PREFIX",
    "route_provider",
    # pricing
    "estimate_cost",
    "cost_of_response",
    "find_price",
    "all_prices",
    "load_pricing",
    "CostEstimate",
    "ModelPrice",
    # errors
    "explain",
    "check_key",
    "OneXAIError",
    "MissingKeyError",
    "InvalidKeyError",
    "UnknownModelError",
    # diagnostics
    "diagnose",
    "Diagnosis",
    "Check",
    "__version__",
]
