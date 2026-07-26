/**
 * Fail over across vendors when one upstream is down.
 *
 * This is the case a gateway makes uniquely easy: three vendors behind one key,
 * so a 503 from OpenAI does not have to end the request. The model name alone
 * picks the vendor.
 *
 *   node 06_failover.mjs
 */

import { OneXAI, costOfResponse, explain, formatCost } from "1xai-sdk";

const client = new OneXAI();

// Deliberately spread across vendors -- if one upstream is down, the next is not.
const LADDER = ["gpt-4o-mini", "claude-haiku-4-5", "gemini-2.5-flash", "deepseek-v4-flash"];

const messages = [{ role: "user", content: "به فارسی توضیح بده: تفاوت TCP و UDP چیست؟" }];

let done = false;
for (const model of LADDER) {
  try {
    const reply = await client.chat.completions.create({ model, messages });
    console.log(`[${model}] ${reply.choices[0].message.content}`);
    console.log("cost:", formatCost(costOfResponse(reply)));
    done = true;
    break;
  } catch (error) {
    console.error(`[${model}] failed: ${explain(error)}`);
    // A 402 means the wallet is empty -- no other model will help.
    if (error?.status === 402) throw error;
  }
}

if (!done) {
  console.error("every provider failed -- check https://1xai.ir/api/status");
  process.exit(1);
}
