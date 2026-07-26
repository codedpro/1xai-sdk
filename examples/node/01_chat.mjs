/**
 * Hello world: one chat call, with its Toman cost.
 *
 *   npm i onexai
 *   export ONEXAI_API_KEY=1xai-...
 *   node 01_chat.mjs
 */

import { OneXAI, costOfResponse, formatCost } from "1xai-sdk";

const client = new OneXAI();

const reply = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [
    { role: "system", content: "تو یک دستیار فارسی‌زبان و مختصرگو هستی." },
    { role: "user", content: "سه نکته برای بهینه‌سازی کوئری‌های SQL بگو." },
  ],
});

console.log(reply.choices[0].message.content);
console.log("\ncost:", formatCost(costOfResponse(reply)));
