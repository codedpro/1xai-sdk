"""Know the cost before you spend it, and cap a job's budget.

Counting tokens locally with tiktoken lets you price a prompt *before* sending
it. Note the honest caveat: tiktoken's encodings are OpenAI's. For `claude-*`
and `gemini-*` the count is an approximation -- usually within about 10-20%,
and Persian text tokenizes worse than English on every one of these models
(roughly 2-3 tokens per word). Treat pre-flight numbers as a budget guard, and
use `cost_of_response()` for the real figure.

    pip install onexai tiktoken
    python 05_cost_control.py
"""

from onexai import OneXAI, cost_of_response, estimate_cost

BUDGET_TOMAN = 50_000
MODEL = "gpt-4o-mini"

prompt = "خلاصه‌ای از تاریخچه زبان فارسی در ۳ پاراگراف بنویس." * 20


def count_tokens(text: str, model: str) -> int:
    """Approximate token count. Exact for OpenAI models, close for the rest."""
    try:
        import tiktoken
    except ModuleNotFoundError:
        # 4 chars/token is a decent fallback for Latin, worse for Persian.
        return len(text) // 3
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")
    return len(encoding.encode(text))


# 1. Price it before sending.
input_tokens = count_tokens(prompt, MODEL)
projected = estimate_cost(MODEL, input_tokens, output_tokens=1500)
print(f"projected: {projected.total_toman:,.0f} Toman for {input_tokens:,} input tokens")

if projected.total_toman > BUDGET_TOMAN:
    raise SystemExit(f"refusing to spend more than {BUDGET_TOMAN:,} Toman")

# 2. Send it, then read the real cost off the response.
client = OneXAI()
reply = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1500,
)

actual = cost_of_response(reply)
print(f"actual:    {actual.total_toman:,.0f} Toman "
      f"({actual.input_tokens:,} in / {actual.output_tokens:,} out)")

# 3. Compare models before committing to one.
print("\nsame job, other models:")
for model in ("gpt-5.2", "claude-haiku-4-5", "gemini-2.5-flash", "deepseek-v4-flash"):
    e = estimate_cost(model, actual.input_tokens, actual.output_tokens)
    print(f"  {model:<22} {e.total_toman:>12,.0f} Toman  ({e.provider})")
