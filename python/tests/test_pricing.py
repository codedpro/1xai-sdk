"""Offline tests -- no API key, no network."""

from __future__ import annotations

import pytest

from onexai import (
    InvalidKeyError,
    MissingKeyError,
    UnknownModelError,
    all_prices,
    check_key,
    estimate_cost,
    explain,
    find_price,
    route_provider,
)


def test_snapshot_loads_and_is_populated():
    prices = all_prices()
    assert len(prices) > 100
    assert all(p.input_per_1k_toman >= 0 for p in prices)
    assert {"openai", "anthropic", "gemini", "deepseek"} <= {p.provider for p in prices}


@pytest.mark.parametrize(
    "model,provider",
    [
        ("claude-opus-4-5", "anthropic"),
        ("gemini-2.5-flash", "gemini"),
        ("gemma-3-27b", "gemini"),
        ("deepseek-v4-flash", "deepseek"),
        ("gpt-5.2", "openai"),
        ("ft:gpt-4o-2024-08-06", "openai"),
        ("o3-mini", "openai"),
    ],
)
def test_routing_rule_matches_documented_behaviour(model, provider):
    assert route_provider(model) == provider


def test_cost_arithmetic_is_exact():
    # Expectations are DERIVED from the snapshot, never hardcoded: these are
    # Toman figures behind a daily FX rate, so a frozen constant turns every
    # rate move into a red build (it did — the rate shifted under this test).
    # What must hold is the arithmetic: n tokens cost n/1000 x the per-1k rate.
    row = find_price("gpt-4o-mini")
    assert row is not None, "gpt-4o-mini must be in the snapshot"
    estimate = estimate_cost("gpt-4o-mini", 1000, 500)
    assert estimate.input_toman == pytest.approx(row.input_per_1k_toman)
    assert estimate.output_toman == pytest.approx(row.output_per_1k_toman * 0.5)
    assert estimate.total_toman == pytest.approx(
        row.input_per_1k_toman + row.output_per_1k_toman * 0.5)
    assert estimate.provider == "openai"


def test_zero_tokens_costs_nothing():
    assert estimate_cost("gpt-4o-mini", 0, 0).total_toman == 0


def test_duplicate_model_name_resolves_via_routing_rule():
    # claude-3-5-haiku is listed under BOTH anthropic and gemini (Vertex resale)
    # at different prices. The gateway routes claude-* to Anthropic, so that is
    # the price the caller will actually be charged.
    price = find_price("claude-3-5-haiku")
    assert price is not None
    assert price.provider == "anthropic"
    # The POINT is which of the two duplicate rows wins, not the absolute
    # Toman figure — assert it differs from the Vertex resale row.
    vertex = next(
        (m for m in all_prices()
         if m.model == "claude-3-5-haiku" and m.provider == "gemini"), None)
    if vertex is not None:
        assert price.input_per_1k_toman != pytest.approx(vertex.input_per_1k_toman)
    assert price.input_per_1k_toman > 0


def test_unknown_model_raises_with_suggestions():
    with pytest.raises(UnknownModelError) as excinfo:
        estimate_cost("gpt-4o-mimi", 10, 10)
    assert "gpt-4o-mini" in str(excinfo.value)


def test_audio_and_image_models_are_explicitly_unpriced():
    # These are billed per second / per image, so they are absent from the
    # token catalogue. Silently returning 0 would be a lie.
    for model in ("whisper-1", "gpt-image-1", "dall-e-3", "tts-1"):
        with pytest.raises(UnknownModelError) as excinfo:
            estimate_cost(model, 100, 100)
        assert "audio" in str(excinfo.value).lower()


def test_cost_of_response_reads_usage_dict():
    from onexai import cost_of_response

    fake = {
        "model": "gpt-4o-mini",
        "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
    }
    row = find_price("gpt-4o-mini")
    assert cost_of_response(fake).total_toman == pytest.approx(
        row.input_per_1k_toman + row.output_per_1k_toman * 0.5)


class _FakeUsage:
    prompt_tokens = 2000
    completion_tokens = 0


class _FakeResponse:
    model = "gpt-4o-mini"
    usage = _FakeUsage()


def test_cost_of_response_reads_sdk_objects():
    from onexai import cost_of_response

    row = find_price("gpt-4o-mini")
    # 2000 prompt tokens, no completion -> exactly 2x the per-1k input rate.
    assert cost_of_response(_FakeResponse()).total_toman == pytest.approx(
        row.input_per_1k_toman * 2)


def test_missing_key_message_names_the_env_vars():
    with pytest.raises(MissingKeyError) as excinfo:
        check_key(None)
    assert "ONEXAI_API_KEY" in str(excinfo.value)


def test_openai_key_is_rejected_with_a_useful_message():
    with pytest.raises(InvalidKeyError) as excinfo:
        check_key("sk-proj-abc123")
    assert "OpenAI key" in str(excinfo.value)


def test_anthropic_key_is_rejected():
    with pytest.raises(InvalidKeyError):
        check_key("sk-ant-api03-abc")


def test_valid_key_shape_passes():
    assert check_key("1xai-abc123") == "1xai-abc123"


def test_non_strict_mode_only_warns():
    with pytest.warns(UserWarning):
        assert check_key("weird-key", strict=False) == "weird-key"


def test_explain_translates_the_persian_401_body():
    body = {"error": {"message": "کلید API نامعتبر است", "type": "api_error"}}
    message = explain(body)
    assert "invalid" in message.lower()


def test_explain_402_is_about_the_wallet_not_the_code():
    assert "credit" in explain(402).lower()


def test_explain_never_raises():
    for value in (None, object(), "", {}, 999):
        assert isinstance(explain(value), str)
