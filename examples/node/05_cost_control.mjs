/**
 * Know the cost before you spend it, and cap a job's budget.
 *
 * `estimateCost` prices a call from a token count; `costOfResponse` reads the
 * real usage off the response. Use the first as a budget guard and the second
 * as the truth.
 *
 * Honest caveat on pre-flight counting: any local tokenizer you use will be
 * OpenAI's, so for `claude-*` and `gemini-*` the count is an approximation
 * (usually within 10-20%). Persian text tokenizes worse than English on every
 * one of these models -- roughly 2-3 tokens per word.
 *
 *   node 05_cost_control.mjs
 */

import { OneXAI, costOfResponse, estimateCost } from "onexai";

const BUDGET_TOMAN = 50_000;
const MODEL = "gpt-4o-mini";

const prompt = "خلاصه‌ای از تاریخچه زبان فارسی در ۳ پاراگراف بنویس.".repeat(20);

// A rough pre-flight count. Persian averages ~3 chars/token on these models.
const approxInputTokens = Math.ceil(prompt.length / 3);

const projected = estimateCost(MODEL, approxInputTokens, 1500);
console.log(
  `projected: ${Math.round(projected.totalToman).toLocaleString()} Toman ` +
    `for ~${approxInputTokens.toLocaleString()} input tokens`,
);

if (projected.totalToman > BUDGET_TOMAN) {
  console.error(`refusing to spend more than ${BUDGET_TOMAN.toLocaleString()} Toman`);
  process.exit(1);
}

const client = new OneXAI();
const reply = await client.chat.completions.create({
  model: MODEL,
  messages: [{ role: "user", content: prompt }],
  max_tokens: 1500,
});

const actual = costOfResponse(reply);
console.log(
  `actual:    ${Math.round(actual.totalToman).toLocaleString()} Toman ` +
    `(${actual.inputTokens} in / ${actual.outputTokens} out)`,
);

console.log("\nsame job, other models:");
for (const model of ["gpt-5.2", "claude-haiku-4-5", "gemini-2.5-flash", "deepseek-v4-flash"]) {
  const e = estimateCost(model, actual.inputTokens, actual.outputTokens);
  console.log(
    `  ${model.padEnd(22)} ${Math.round(e.totalToman).toLocaleString().padStart(12)} Toman  (${e.provider})`,
  );
}
