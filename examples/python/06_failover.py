"""Fail over across vendors when one upstream is down.

This is the case a gateway makes uniquely easy: three vendors behind one key, so
a 503 from OpenAI does not have to end the request. 1xAi's own status endpoint
reports per-provider health as seen from Iran, and the model name alone picks
the vendor.

    python 06_failover.py
"""

from onexai import OneXAI, cost_of_response, explain

client = OneXAI()

# Deliberately spread across vendors -- if one upstream is down, the next is not.
LADDER = ["gpt-4o-mini", "claude-haiku-4-5", "gemini-2.5-flash", "deepseek-v4-flash"]

messages = [{"role": "user", "content": "به فارسی توضیح بده: تفاوت TCP و UDP چیست؟"}]

for model in LADDER:
    try:
        reply = client.chat.completions.create(model=model, messages=messages, timeout=30)
        print(f"[{model}] {reply.choices[0].message.content}")
        print("cost:", cost_of_response(reply))
        break
    except Exception as exc:  # noqa: BLE001
        print(f"[{model}] failed: {explain(exc)}")
        # A 402 means the wallet is empty -- no other model will help.
        if getattr(exc, "status_code", None) == 402:
            raise
else:
    raise SystemExit("every provider failed -- check https://1xai.ir/api/status")
