"""Command line entry point: ``python -m onexai ...`` (or just ``onexai ...``).

    onexai doctor                       # why isn't my setup working?
    onexai price gpt-4o-mini 1000 500   # what does that cost in Toman?
    onexai models --provider anthropic  # what can I call?
    onexai status                       # are the upstreams up right now?
"""

from __future__ import annotations

import argparse
import json
import sys

from .constants import BASE_URL, STATUS_URL
from .diagnostics import _get, diagnose
from .errors import OneXAIError
from .pricing import all_prices, estimate_cost


def _cmd_doctor(args: argparse.Namespace) -> int:
    result = diagnose()
    print(result)
    return 0 if result.ok else 1


def _cmd_price(args: argparse.Namespace) -> int:
    try:
        estimate = estimate_cost(
            args.model, args.input_tokens, args.output_tokens, live=args.live
        )
    except OneXAIError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(estimate.__dict__, ensure_ascii=False, indent=2))
        return 0

    print(f"model      {estimate.model}  (routed to {estimate.provider})")
    print(f"input      {estimate.input_tokens:>9,} tokens  ->  {estimate.input_toman:>12,.2f} Toman")
    print(f"output     {estimate.output_tokens:>9,} tokens  ->  {estimate.output_toman:>12,.2f} Toman")
    print(f"total                            ->  {estimate.total_toman:>12,.2f} Toman")
    print(f"priced from {estimate.priced_from} ({estimate.generated_at})")
    return 0


def _cmd_models(args: argparse.Namespace) -> int:
    prices = all_prices(live=args.live)
    if args.provider:
        prices = [p for p in prices if p.provider == args.provider]
    if args.search:
        needle = args.search.lower()
        prices = [p for p in prices if needle in p.model.lower()]
    if not prices:
        print("No models matched.", file=sys.stderr)
        return 1
    width = max(len(p.model) for p in prices)
    print(f"{'MODEL'.ljust(width)}  {'PROVIDER':<10} {'IN/1k':>12} {'OUT/1k':>12}   (Toman)")
    for price in prices:
        print(
            f"{price.model.ljust(width)}  {price.provider:<10} "
            f"{price.input_per_1k_toman:>12,.2f} {price.output_per_1k_toman:>12,.2f}"
        )
    print(f"\n{len(prices)} models. Base URL: {BASE_URL}")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    status, body = _get(STATUS_URL)
    if status != 200 or not isinstance(body, dict):
        print(f"Could not read {STATUS_URL} (HTTP {status})", file=sys.stderr)
        return 1
    print(f"overall: {body.get('overall')}  (updated {body.get('updated_at')})")
    for provider in body.get("providers", []):
        print(
            f"  {provider.get('provider'):<10} {provider.get('state'):<12} "
            f"24h ok {provider.get('ok_pct_24h')}%   reqs/24h {provider.get('reqs_24h')}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="onexai", description="Helpers for the 1xAi gateway (https://1xai.ir)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="diagnose key and connectivity problems")
    doctor.set_defaults(func=_cmd_doctor)

    price = sub.add_parser("price", help="estimate the Toman cost of a call")
    price.add_argument("model")
    price.add_argument("input_tokens", type=int, nargs="?", default=0)
    price.add_argument("output_tokens", type=int, nargs="?", default=0)
    price.add_argument("--live", action="store_true", help="fetch current prices instead of the bundled snapshot")
    price.add_argument("--json", action="store_true")
    price.set_defaults(func=_cmd_price)

    models = sub.add_parser("models", help="list priced models")
    models.add_argument("--provider", choices=["openai", "anthropic", "gemini", "deepseek"])
    models.add_argument("--search", help="substring match on the model name")
    models.add_argument("--live", action="store_true")
    models.set_defaults(func=_cmd_models)

    status = sub.add_parser("status", help="live upstream provider health")
    status.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
