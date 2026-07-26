"""Live tests against 1xAi's PUBLIC endpoints. No API key required.

These prove the base URL, the auth scheme and the response shapes this package
assumes are actually real. Run them with:

    pytest -m live

Skipped automatically when the network is unavailable (which, given the
audience, is a normal condition).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from onexai import BASE_URL, PRICING_URL, STATUS_URL, explain

pytestmark = pytest.mark.live

UA = {"User-Agent": "onexai-python/tests"}


def _get(url, headers=None):
    request = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return exc.code, None
    except urllib.error.URLError as exc:
        pytest.skip(f"network unavailable: {exc}")


def test_public_price_catalogue_shape():
    status, body = _get(PRICING_URL)
    assert status == 200
    models = body["models"]
    assert len(models) > 100
    row = models[0]
    assert {"provider", "model", "input_per_1k_toman", "output_per_1k_toman"} <= set(row)


def test_models_endpoint_requires_a_key_and_says_so():
    # Proves BASE_URL is right (we get a JSON gateway error, not a 404 or an
    # HTML page) and that our error translation handles the real body.
    status, body = _get(f"{BASE_URL}/models")
    assert status == 401
    assert "error" in body
    assert "auth" in explain(body).lower() or "key" in explain(body).lower()


def test_a_wrong_key_is_rejected_as_invalid():
    status, body = _get(
        f"{BASE_URL}/models", headers={"Authorization": "Bearer 1xai-not-a-real-key"}
    )
    assert status == 401
    assert "error" in body


def test_status_endpoint_reports_every_upstream():
    status, body = _get(STATUS_URL)
    assert status == 200
    providers = {p["provider"] for p in body["providers"]}
    assert {"openai", "anthropic", "gemini"} <= providers


def test_bundled_snapshot_still_matches_live_prices():
    """Catches a stale snapshot before it ships a wrong Toman number."""
    from onexai import all_prices

    status, body = _get(PRICING_URL)
    assert status == 200
    live = {(m["provider"], m["model"]): m["input_per_1k_toman"] for m in body["models"]}
    drifted = [
        (p.provider, p.model, p.input_per_1k_toman, live[(p.provider, p.model)])
        for p in all_prices()
        if (p.provider, p.model) in live
        and abs(live[(p.provider, p.model)] - p.input_per_1k_toman) > 0.01
    ]
    assert not drifted, (
        f"{len(drifted)} models drifted from the live catalogue, e.g. {drifted[:3]}. "
        "Run: python3 scripts/refresh_pricing.py"
    )
