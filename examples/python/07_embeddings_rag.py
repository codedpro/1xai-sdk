"""Embeddings for Persian text, and what they cost.

Embedding models are token-billed, so the Toman helper prices them exactly.
Note that embeddings have no output tokens -- the catalogue lists
`output_per_1k_toman = 0` for every one of them.

    python 07_embeddings_rag.py
"""

import math

from onexai import OneXAI, estimate_cost

client = OneXAI()

DOCS = [
    "کوبرنتیز یک سامانه متن‌باز برای مدیریت کانتینرهاست.",
    "داکر ابزاری برای بسته‌بندی برنامه‌ها در کانتینر است.",
    "پایتون یک زبان برنامه‌نویسی سطح بالا و همه‌منظوره است.",
]

response = client.embeddings.create(model="text-embedding-3-small", input=DOCS)
vectors = [item.embedding for item in response.data]

print(f"embedded {len(vectors)} docs, {len(vectors[0])} dimensions each")
print("cost:", estimate_cost("text-embedding-3-small", response.usage.prompt_tokens, 0))


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


query = client.embeddings.create(
    model="text-embedding-3-small", input=["ابزار مدیریت کانتینر چیست؟"]
).data[0].embedding

ranked = sorted(zip(DOCS, vectors), key=lambda pair: -cosine(query, pair[1]))
print("\nbest match:", ranked[0][0])
