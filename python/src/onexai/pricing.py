"""Toman cost estimation.

1xAi publishes a public, unauthenticated price catalogue at
https://1xai.ir/api/models -- every token-billed model with its Toman price per
1000 input and output tokens. This module bundles a snapshot of it (so the
helper works offline and in CI) and can refresh from the live endpoint.

What it covers, honestly:

* Token-billed models -- chat, reasoning, and embedding models. Covered.
* Audio (``/v1/audio/transcriptions``, ``/v1/audio/speech``) -- billed per second
  and per character, and **not present in the catalogue**. Not covered.
* Images (``/v1/images/generations``) -- billed per image. Not covered.

For the uncovered endpoints ``estimate_cost`` raises ``UnknownModelError`` with
that explanation rather than silently returning zero.
"""

from __future__ import annotations

import difflib
import json
import pathlib
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

from .constants import PRICING_URL, route_provider
from .errors import UnknownModelError

_SNAPSHOT_PATH = pathlib.Path(__file__).with_name("pricing_snapshot.json")
_cache: dict[str, Any] | None = None


@dataclass(frozen=True)
class ModelPrice:
    """Toman price per 1000 tokens for one model on one provider."""

    provider: str
    model: str
    input_per_1k_toman: float
    output_per_1k_toman: float


@dataclass(frozen=True)
class CostEstimate:
    """The Toman cost of a single call."""

    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    input_toman: float
    output_toman: float
    total_toman: float
    #: ``"snapshot"`` (bundled, possibly stale) or ``"live"`` (fetched just now).
    priced_from: str
    #: When the price data was generated, ISO-8601 UTC.
    generated_at: str

    def __str__(self) -> str:
        return f"{self.total_toman:,.0f} Toman ({self.model}, {self.input_tokens}in/{self.output_tokens}out)"


def load_pricing(*, live: bool = False, timeout: float = 10.0) -> dict[str, Any]:
    """Return the raw price catalogue.

    By default reads the snapshot bundled with this package -- no network, no
    key. Pass ``live=True`` to fetch the current catalogue from
    https://1xai.ir/api/models (public, still no key needed); the result is
    cached in-process. Falls back to the snapshot if the fetch fails.
    """
    global _cache

    if live:
        if _cache is not None:
            return _cache
        try:
            request = urllib.request.Request(
                PRICING_URL, headers={"User-Agent": "onexai-python"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
            rows = payload.get("models")
            if isinstance(rows, list) and rows:
                _cache = {
                    "source": PRICING_URL,
                    "generated_at": "live",
                    "priced_from": "live",
                    "models": rows,
                }
                return _cache
        except Exception:  # noqa: BLE001 -- offline/blocked is normal in Iran
            pass  # fall through to the snapshot

    snapshot = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    snapshot.setdefault("priced_from", "snapshot")
    return snapshot


def all_prices(*, live: bool = False) -> list[ModelPrice]:
    """Every priced model in the catalogue."""
    catalogue = load_pricing(live=live)
    return [
        ModelPrice(
            provider=row["provider"],
            model=row["model"],
            input_per_1k_toman=float(row["input_per_1k_toman"]),
            output_per_1k_toman=float(row["output_per_1k_toman"]),
        )
        for row in catalogue["models"]
    ]


def find_price(model: str, *, live: bool = False) -> ModelPrice | None:
    """Look up one model's Toman price, or ``None`` if it is not priced.

    A handful of model names appear under two providers (Anthropic's Claude
    models are also resold through Google Vertex, and the two are not always
    priced identically). We disambiguate with the gateway's own documented
    routing rule, so the price you get is the price you will be charged.
    """
    if not model:
        return None
    wanted = model.strip()
    candidates = [p for p in all_prices(live=live) if p.model == wanted]
    if not candidates:
        lowered = wanted.lower()
        candidates = [p for p in all_prices(live=live) if p.model.lower() == lowered]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    routed = route_provider(wanted)
    for candidate in candidates:
        if candidate.provider == routed:
            return candidate
    return candidates[0]


def _suggest(model: str, known: Iterable[str]) -> list[str]:
    return difflib.get_close_matches(model, sorted(set(known)), n=3, cutoff=0.6)


def estimate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    *,
    live: bool = False,
) -> CostEstimate:
    """Estimate what a call costs in Toman.

    >>> estimate_cost("gpt-4o-mini", 1000, 500).total_toman
    100.602

    Raises ``UnknownModelError`` -- with near-miss suggestions -- when the model
    is not in the catalogue, rather than pretending the call was free.
    """
    catalogue = load_pricing(live=live)
    price = find_price(model, live=live)

    if price is None:
        known = [row["model"] for row in catalogue["models"]]
        suggestions = _suggest(model, known)
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        raise UnknownModelError(
            f"`{model}` is not in the 1xAi Toman price catalogue.{hint} "
            "Note that audio (billed per second) and image (billed per image) "
            "models are deliberately absent -- this helper only prices "
            "token-billed models. See https://1xai.ir/pricing for those."
        )

    input_tokens = max(0, int(input_tokens))
    output_tokens = max(0, int(output_tokens))
    input_toman = input_tokens / 1000.0 * price.input_per_1k_toman
    output_toman = output_tokens / 1000.0 * price.output_per_1k_toman

    return CostEstimate(
        model=price.model,
        provider=price.provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_toman=round(input_toman, 4),
        output_toman=round(output_toman, 4),
        total_toman=round(input_toman + output_toman, 4),
        priced_from=catalogue.get("priced_from", "snapshot"),
        generated_at=str(catalogue.get("generated_at", "unknown")),
    )


def cost_of_response(response: Any, *, live: bool = False) -> CostEstimate:
    """Price a completed call straight from the SDK response object.

    Reads ``response.model`` and ``response.usage`` (dict or object), so it
    works with chat completions and embeddings alike -- no manual token counting.

        r = client.chat.completions.create(model="gpt-4o-mini", messages=[...])
        print(cost_of_response(r))
    """
    model = getattr(response, "model", None)
    usage = getattr(response, "usage", None)
    if model is None and isinstance(response, dict):
        model = response.get("model")
        usage = response.get("usage")

    if not model:
        raise UnknownModelError("Response carried no `model` field to price.")

    def field(name: str) -> int:
        if usage is None:
            return 0
        if isinstance(usage, dict):
            return int(usage.get(name) or 0)
        return int(getattr(usage, name, 0) or 0)

    return estimate_cost(
        str(model),
        field("prompt_tokens"),
        field("completion_tokens"),
        live=live,
    )
