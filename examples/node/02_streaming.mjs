/**
 * Streaming, with a cost figure at the end.
 *
 * The gateway forwards Server-Sent Events unchanged, so streaming is exactly the
 * OpenAI flow. The one wrinkle: usage is not included in stream chunks unless
 * you ask for it with `stream_options: { include_usage: true }` -- so ask,
 * otherwise you cannot price the call.
 *
 *   node 02_streaming.mjs
 */

import { OneXAI, costOfResponse, formatCost } from "1xai-sdk";

const client = new OneXAI();

const stream = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "یک داستان کوتاه سه جمله‌ای بنویس." }],
  stream: true,
  stream_options: { include_usage: true },
});

let usageChunk = null;
for await (const chunk of stream) {
  const delta = chunk.choices?.[0]?.delta?.content;
  if (delta) process.stdout.write(delta);
  if (chunk.usage) usageChunk = chunk;
}

console.log();
if (usageChunk) console.log("cost:", formatCost(costOfResponse(usageChunk)));
