"""Streaming, with a cost figure at the end.

The gateway forwards Server-Sent Events unchanged, so streaming is exactly the
OpenAI flow. The one wrinkle: usage is not included in stream chunks unless you
ask for it with `stream_options={"include_usage": True}` -- so ask, otherwise you
cannot price the call.

    python 02_streaming.py
"""

from onexai import OneXAI, cost_of_response

client = OneXAI()

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "یک داستان کوتاه سه جمله‌ای بنویس."}],
    stream=True,
    stream_options={"include_usage": True},
)

final_chunk = None
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        final_chunk = chunk

print()
if final_chunk:
    print("cost:", cost_of_response(final_chunk))
