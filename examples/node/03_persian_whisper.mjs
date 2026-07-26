/**
 * Persian speech-to-text with Whisper.
 *
 * Two things matter for Persian accuracy:
 *
 * - Pass `language: "fa"`. Without it Whisper guesses from the first seconds of
 *   audio and often mislabels Persian as Arabic or Urdu, wrecking the output.
 * - Use `prompt` to seed proper nouns and spelling conventions. Whisper
 *   conditions on it and will spell those terms your way.
 *
 * Audio is billed per second, not per token, so the Toman cost helper
 * deliberately does not price it -- see https://1xai.ir/pricing .
 *
 *   node 03_persian_whisper.mjs voice.m4a
 */

import { createReadStream } from "node:fs";
import { writeFile } from "node:fs/promises";

import { OneXAI } from "onexai";

const client = new OneXAI();
const path = process.argv[2] ?? "voice.m4a";

const transcript = await client.audio.transcriptions.create({
  model: "whisper-1",
  file: createReadStream(path),
  language: "fa",
  prompt: "اصطلاحات فنی: کوبرنتیز، داکر، ری‌اکت، پایتون.",
});

console.log(transcript.text);

// ...and speak it back. TTS is billed per character.
const speech = await client.audio.speech.create({
  model: "tts-1",
  voice: "alloy",
  input: transcript.text.slice(0, 500),
});

await writeFile("reply.mp3", Buffer.from(await speech.arrayBuffer()));
console.log("wrote reply.mp3");
