"""Answer "why isn't it working?" without needing a support ticket.

``diagnose()`` checks, in order: is a key present, does it look like a 1xAi key,
can this machine reach the gateway at all, is the key accepted, and are the
upstream providers healthy right now. Each step returns a plain sentence.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .client import resolve_key
from .constants import BASE_URL, ENV_VARS, KEY_PREFIX, PRICING_URL, STATUS_URL
from .errors import explain


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


@dataclass
class Diagnosis:
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def __str__(self) -> str:
        lines = [f"{'PASS' if c.ok else 'FAIL'}  {c.name}: {c.detail}" for c in self.checks]
        lines.append("")
        lines.append("All checks passed." if self.ok else "Some checks failed -- see above.")
        return "\n".join(lines)


def _get(url: str, *, key: str | None = None, timeout: float = 15.0) -> tuple[int, Any]:
    headers = {"User-Agent": "onexai-python/doctor"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body: Any
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            body = None
        return exc.code, body


def diagnose(api_key: str | None = None, *, timeout: float = 15.0) -> Diagnosis:
    """Run every connectivity and configuration check and report."""
    result = Diagnosis()
    key = resolve_key(api_key)

    # 1. Is a key present at all?
    if key:
        source = "argument" if api_key else next(
            (name for name in ENV_VARS if os.environ.get(name)), "environment"
        )
        result.checks.append(Check("api key present", True, f"found via {source}"))
    else:
        result.checks.append(
            Check("api key present", False, "not set -- export ONEXAI_API_KEY=1xai-...")
        )

    # 2. Does it look like a 1xAi key?
    if key:
        if key.startswith(KEY_PREFIX):
            result.checks.append(
                Check("api key shape", True, f"starts with {KEY_PREFIX} as expected")
            )
        elif key.startswith("sk-"):
            result.checks.append(
                Check(
                    "api key shape",
                    False,
                    "this is an OpenAI key (sk-...), not a 1xAi key -- it will 401",
                )
            )
        else:
            result.checks.append(
                Check("api key shape", False, f"does not start with {KEY_PREFIX}")
            )

    # 3. Can we reach the gateway at all? (public endpoint, no key needed)
    try:
        status, body = _get(PRICING_URL, timeout=timeout)
        count = len(body.get("models", [])) if isinstance(body, dict) else 0
        result.checks.append(
            Check("gateway reachable", status == 200, f"HTTP {status} from {PRICING_URL} ({count} models priced)")
        )
    except Exception as exc:  # noqa: BLE001
        result.checks.append(
            Check("gateway reachable", False, f"cannot reach {PRICING_URL}: {exc}")
        )

    # 4. Is the key actually accepted?
    if key:
        try:
            status, body = _get(f"{BASE_URL}/models", key=key, timeout=timeout)
            if status == 200:
                count = len(body.get("data", [])) if isinstance(body, dict) else 0
                result.checks.append(
                    Check("api key accepted", True, f"GET /v1/models returned {count} models")
                )
            else:
                result.checks.append(
                    Check("api key accepted", False, f"HTTP {status} -- {explain(body if body else status)}")
                )
        except Exception as exc:  # noqa: BLE001
            result.checks.append(Check("api key accepted", False, f"request failed: {exc}"))

    # 5. Are the upstreams healthy?
    try:
        status, body = _get(STATUS_URL, timeout=timeout)
        if status == 200 and isinstance(body, dict):
            overall = body.get("overall", "unknown")
            parts = [
                f"{p.get('provider')}={p.get('state')}" for p in body.get("providers", [])
            ]
            result.checks.append(
                Check("upstream health", overall != "down", f"overall={overall}; " + ", ".join(parts))
            )
        else:
            result.checks.append(Check("upstream health", False, f"HTTP {status} from {STATUS_URL}"))
    except Exception as exc:  # noqa: BLE001
        result.checks.append(Check("upstream health", False, f"cannot reach {STATUS_URL}: {exc}"))

    return result
