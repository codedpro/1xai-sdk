#!/usr/bin/env python3
"""Regenerate the bundled Toman pricing snapshot from the live 1xAi catalogue.

    python3 scripts/refresh_pricing.py

Writes the snapshot into both packages:
    python/src/onexai/pricing_snapshot.json
    node/src/pricing-snapshot.ts   (a TS module, so it imports cleanly under
                                    both ESM and CommonJS without import
                                    attributes)

The catalogue at https://1xai.ir/api/models is public (no API key needed), so
this script is runnable by anyone. Prices change when the upstream providers
change theirs, so refresh before each release.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.request
from datetime import datetime, timezone

SOURCE = "https://1xai.ir/api/models"
ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_TARGET = ROOT / "python" / "src" / "onexai" / "pricing_snapshot.json"
TS_TARGET = ROOT / "node" / "src" / "pricing-snapshot.ts"

TS_TEMPLATE = """// GENERATED FILE -- do not edit by hand.
// Regenerate with:  python3 scripts/refresh_pricing.py
//
// Source: {source}
// Toman price per 1000 tokens for every token-billed model on 1xAi.
// Audio (per second) and image (per image) endpoints are not priced here.

import type {{ PricingSnapshot }} from "./types.js";

export const PRICING_SNAPSHOT: PricingSnapshot = {body} as const;

export default PRICING_SNAPSHOT;
"""


def main() -> int:
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "onexai-sdk/refresh-pricing"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)

    rows = payload.get("models")
    if not isinstance(rows, list) or not rows:
        print(f"unexpected payload from {SOURCE}: {list(payload)[:5]}", file=sys.stderr)
        return 1

    models = []
    for row in rows:
        try:
            models.append(
                {
                    "provider": str(row["provider"]),
                    "model": str(row["model"]),
                    "input_per_1k_toman": round(float(row["input_per_1k_toman"]), 6),
                    "output_per_1k_toman": round(float(row["output_per_1k_toman"]), 6),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            print(f"skipping malformed row {row!r}: {exc}", file=sys.stderr)

    models.sort(key=lambda m: (m["provider"], m["model"]))
    snapshot = {
        "source": SOURCE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "currency": "IRT",
        "unit": "toman_per_1k_tokens",
        "note": (
            "Token-billed models only. Audio (per second) and image (per image) "
            "endpoints are not priced in this catalogue."
        ),
        "models": models,
    }

    blob = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    PY_TARGET.parent.mkdir(parents=True, exist_ok=True)
    PY_TARGET.write_text(blob, encoding="utf-8")
    print(f"wrote {len(models)} models -> {PY_TARGET}")

    TS_TARGET.parent.mkdir(parents=True, exist_ok=True)
    TS_TARGET.write_text(
        TS_TEMPLATE.format(source=SOURCE, body=blob.rstrip("\n")), encoding="utf-8"
    )
    print(f"wrote {len(models)} models -> {TS_TARGET}")

    # The stale JSON copy from earlier versions, if present.
    legacy = ROOT / "node" / "src" / "pricing_snapshot.json"
    if legacy.exists():
        legacy.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
