/**
 * Image generation.
 *
 * Billed per image, not per token, so `estimateCost` deliberately refuses to
 * price it. Check https://1xai.ir/pricing for the per-image Toman rate.
 *
 *   node 04_images.mjs
 */

import { writeFile } from "node:fs/promises";

import { OneXAI } from "1xai-sdk";

const client = new OneXAI();

const result = await client.images.generate({
  model: "gpt-image-1",
  prompt:
    "A minimalist poster of the Milad Tower at sunrise, flat vector style, " +
    "warm ochre and deep teal palette, no text.",
  size: "1024x1024",
  n: 1,
});

const image = result.data[0];

// gpt-image-1 returns base64; DALL-E 3 returns a URL. Handle both.
if (image.b64_json) {
  await writeFile("out.png", Buffer.from(image.b64_json, "base64"));
  console.log("wrote out.png");
} else {
  console.log(image.url);
}
