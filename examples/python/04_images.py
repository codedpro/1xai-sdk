"""Image generation.

Billed per image, not per token, so `estimate_cost` deliberately refuses to
price it. Check https://1xai.ir/pricing for the per-image Toman rate.

    python 04_images.py
"""

import base64

from onexai import OneXAI

client = OneXAI()

result = client.images.generate(
    model="gpt-image-1",
    prompt=(
        "A minimalist poster of the Milad Tower at sunrise, flat vector style, "
        "warm ochre and deep teal palette, no text."
    ),
    size="1024x1024",
    n=1,
)

image = result.data[0]

# gpt-image-1 returns base64; DALL-E 3 returns a URL. Handle both.
if getattr(image, "b64_json", None):
    with open("out.png", "wb") as handle:
        handle.write(base64.b64decode(image.b64_json))
    print("wrote out.png")
else:
    print(image.url)
