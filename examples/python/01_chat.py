"""Hello world: one chat call, with its Toman cost.

    pip install onexai
    export ONEXAI_API_KEY=1xai-...
    python 01_chat.py
"""

from onexai import OneXAI, cost_of_response

client = OneXAI()

reply = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "تو یک دستیار فارسی‌زبان و مختصرگو هستی."},
        {"role": "user", "content": "سه نکته برای بهینه‌سازی کوئری‌های SQL بگو."},
    ],
)

print(reply.choices[0].message.content)
print()
print("cost:", cost_of_response(reply))
