"""Clear, actionable errors.

Two things make 1xAi failures confusing for a newcomer:

1. The gateway replies in Persian (``{"error": {"message": "کلید API نامعتبر است"}}``),
   which is right for its audience but opaque if you are reading a stack trace
   in an English editor.
2. A ``402`` from an OpenAI SDK is unusual -- on api.openai.com you would never
   see one. On 1xAi it means your Toman wallet is empty, which is a completely
   different fix from a ``401``.

So we translate. ``explain()`` turns any gateway failure into one sentence that
says what to actually do.
"""

from __future__ import annotations

from typing import Any

from .constants import DASHBOARD_URL, ENV_VARS, KEY_PREFIX, STATUS_URL


class OneXAIError(Exception):
    """Base class for every error this package raises itself."""


class MissingKeyError(OneXAIError):
    """No API key was passed and none was found in the environment."""


class InvalidKeyError(OneXAIError):
    """A key was supplied but it is not a 1xAi key."""


class UnknownModelError(OneXAIError):
    """A model name is absent from the Toman price catalogue."""


# Persian error strings the gateway is known to return, mapped to the English
# explanation. Matched as substrings so wording tweaks upstream do not break us.
_PERSIAN_HINTS: dict[str, str] = {
    "کلید API ارسال نشده": "No API key reached the gateway -- the Authorization header was missing or empty.",
    "کلید API نامعتبر": "The gateway rejected this API key as invalid.",
    "اعتبار": "Your Toman wallet does not have enough credit for this request.",
    "موجودی": "Your Toman wallet does not have enough credit for this request.",
}

_BY_STATUS: dict[int, str] = {
    400: (
        "The gateway rejected the request body. Most often this is a model name "
        "that does not exist upstream, or a parameter the target provider does "
        "not accept (remember: `claude-*` and `gemini-*` are translated from the "
        "OpenAI shape, so provider-specific fields can be dropped or refused)."
    ),
    401: (
        "Authentication failed. Check that your key is set (tried: "
        + ", ".join(ENV_VARS)
        + f") and that it starts with `{KEY_PREFIX}`. An `sk-...` key belongs to "
        f"OpenAI directly and will never work here. Mint a key at {DASHBOARD_URL}."
    ),
    402: (
        "Out of credit. 1xAi bills a prepaid Toman wallet, so a 402 means the "
        f"wallet is empty rather than anything being wrong with your code. Top up at {DASHBOARD_URL}."
    ),
    403: "The key is valid but not allowed to perform this action.",
    404: (
        "No such endpoint or model. Check the path against https://1xai.ir/openapi.json "
        "-- the OpenAI-compatible routes live under /v1, while the native "
        "passthroughs are /anthropic/v1/... and /gemini/v1beta/... ."
    ),
    408: "The request timed out before the upstream provider answered. Retry, ideally with backoff.",
    413: "The request body was too large. Trim the prompt, the file, or the batch.",
    429: (
        "Rate limited. This can be your own throughput or the shared upstream "
        "capacity. Back off exponentially and retry."
    ),
    500: "The gateway hit an internal error. Retry; if it persists, contact https://1xai.ir/contact .",
    502: f"The upstream provider returned a bad response through the gateway. Check {STATUS_URL} .",
    503: (
        "The upstream provider (OpenAI / Anthropic / Google / DeepSeek) is "
        f"unavailable as seen from the gateway. Check live per-provider health at {STATUS_URL} "
        "-- and consider failing over to a model from a different provider."
    ),
    504: f"The upstream provider timed out. Check {STATUS_URL} and retry.",
}


def _status_of(exc: Any) -> int | None:
    for attr in ("status_code", "status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int) and 100 <= value <= 599:
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
    return None


def explain(exc: Any) -> str:
    """Return one actionable English sentence for a gateway failure.

    Accepts anything: an ``openai.APIStatusError``, a raw ``httpx.Response``, an
    HTTP status ``int``, or the decoded ``{"error": {...}}`` dict. Never raises --
    the whole point is to be safe to call inside an ``except`` block.

    >>> explain(402)
    'Out of credit. ...'
    """
    if isinstance(exc, int):
        return _BY_STATUS.get(exc, f"The gateway returned HTTP {exc}.")

    text = ""
    if isinstance(exc, dict):
        error = exc.get("error")
        if isinstance(error, dict):
            text = str(error.get("message") or "")
        else:
            text = str(exc.get("message") or "")
    else:
        text = str(getattr(exc, "message", "") or exc)

    for needle, english in _PERSIAN_HINTS.items():
        if needle in text:
            status = _status_of(exc)
            tail = _BY_STATUS.get(status, "") if status else ""
            return f"{english} {tail}".strip()

    status = _status_of(exc)
    if status is not None and status in _BY_STATUS:
        return _BY_STATUS[status]
    if status is not None:
        return f"The gateway returned HTTP {status}: {text or '(no message)'}"
    return text or "The gateway request failed for an unknown reason."


def check_key(api_key: str | None, *, strict: bool = True) -> str:
    """Validate a 1xAi key shape and return it, or raise a clear error.

    Catches the two mistakes that actually happen: forgetting to set the key at
    all, and pasting a key from the wrong provider.
    """
    if not api_key or not api_key.strip():
        raise MissingKeyError(
            "No 1xAi API key found. Pass api_key=... or set one of "
            + " / ".join(ENV_VARS)
            + f". Keys start with `{KEY_PREFIX}` and are minted at {DASHBOARD_URL}."
        )

    key = api_key.strip()

    if key.startswith("sk-ant-"):
        raise InvalidKeyError(
            "That is an Anthropic key, not a 1xAi key. 1xAi holds the upstream "
            f"provider keys for you -- you only ever send your own `{KEY_PREFIX}` key. "
            f"Mint one at {DASHBOARD_URL}."
        )
    if key.startswith("sk-"):
        raise InvalidKeyError(
            "That is an OpenAI key, not a 1xAi key. Pointing an `sk-...` key at "
            "1xai.ir will always fail with 401. 1xAi holds the upstream keys for "
            f"you -- send your own `{KEY_PREFIX}` key instead, minted at {DASHBOARD_URL}."
        )
    if key.startswith("AIza"):
        raise InvalidKeyError(
            "That is a Google AI Studio key, not a 1xAi key. Send your own "
            f"`{KEY_PREFIX}` key instead, minted at {DASHBOARD_URL}."
        )

    if not key.startswith(KEY_PREFIX):
        message = (
            f"This key does not start with `{KEY_PREFIX}`, which every key minted by "
            f"the 1xAi dashboard does. Double-check it at {DASHBOARD_URL}. "
            "Pass strict_key=False if you are deliberately using a custom gateway."
        )
        if strict:
            raise InvalidKeyError(message)
        import warnings

        warnings.warn(message, stacklevel=3)

    return key
