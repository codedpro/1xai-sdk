# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The Python and Node packages are versioned together.

## [0.1.0] — 2026-07-26

First release.

### Added

- **Python package `onexai`** — `OneXAI` / `AsyncOneXAI` factories returning a
  pre-configured official `openai` client pointed at `https://1xai.ir/v1`, plus
  `anthropic_client()` and `gemini_client()` for the native passthroughs.
- **Node package `onexai`** — `OneXAI` class extending the official `openai`
  client, plus `anthropicConfig()` / `geminiConfig()`. Ships ESM, CommonJS and
  type declarations.
- **Toman cost helpers** — `estimate_cost` / `estimateCost`, `cost_of_response` /
  `costOfResponse`, `find_price` / `findPrice`, built on 1xAi's public
  `https://1xai.ir/api/models` catalogue. A 227-model snapshot is bundled so the
  helpers work offline; live refresh is one call away.
- **Duplicate-name resolution** — a few Claude models are listed under both
  Anthropic and Google (Vertex resale) at different prices. Lookups apply the
  gateway's documented routing rule so the quoted price is the price charged.
- **Error translation** — `explain()` turns the gateway's Persian error bodies and
  HTTP statuses into one actionable English sentence, including the
  Iran-specific `402` (empty Toman wallet, not a code bug).
- **Key validation** — `check_key` / `checkKey` reject `sk-`, `sk-ant-` and
  `AIza` keys at construction with an explanation instead of a later 401.
- **`onexai` CLI** — `doctor`, `price`, `models`, `status`.
- **Cookbook README** — copy-paste configuration for Cursor, Continue, Cline,
  Claude Code, Open WebUI, n8n, Aider, LangChain and the Vercel AI SDK, plus
  runnable recipes for streaming, Persian Whisper, image generation, embeddings,
  cross-vendor failover and cost control.
- **Live test suites** — both packages test against 1xAi's public endpoints with
  no API key, including a staleness check that fails if the bundled price
  snapshot drifts from the live catalogue.

[0.1.0]: https://github.com/codedpro/1xai-sdk/releases/tag/v0.1.0
