"""Persian speech-to-text with Whisper, and text-to-speech back again.

Two things matter for Persian accuracy:

* Pass `language="fa"`. Without it Whisper guesses from the first seconds of
  audio and often mislabels Persian as Arabic or Urdu, which wrecks the output.
* Use `prompt=` to seed proper nouns, product names and spelling conventions.
  Whisper conditions on it and will spell those terms your way.

Audio is billed per second, not per token, so the Toman cost helper deliberately
does not price it -- see https://1xai.ir/pricing .

    python 03_persian_whisper.py voice.m4a
"""

import sys

from onexai import OneXAI

client = OneXAI()
path = sys.argv[1] if len(sys.argv) > 1 else "voice.m4a"

with open(path, "rb") as audio:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        language="fa",
        prompt="اصطلاحات فنی: کوبرنتیز، داکر، ری‌اکت، پایتون.",
    )

print(transcript.text)

# ...and speak it back. TTS is billed per character.
speech = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=transcript.text[:500],
)
speech.write_to_file("reply.mp3")
print("wrote reply.mp3")
