"""Synthesize narration.json -> audio/<lang>_<i>.mp3 via Sarvam (skips files that exist, to save credits)."""
import base64, json, os, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
key = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(os.path.join(HERE, "..", ".env")) if l.startswith("SARVAM_API_KEY="))
for lang in sys.argv[1:]:
    for i, text in enumerate(json.load(open(os.path.join(HERE, "narration.json")))[lang]):
        out = os.path.join(HERE, "audio", f"{lang}_{i}.mp3")
        if os.path.exists(out):
            continue
        body = {"text": text, "target_language_code": f"{lang}-IN", "model": "bulbul:v3", "speaker": "shubh",
                "output_audio_codec": "mp3", "speech_sample_rate": 22050}
        req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", json.dumps(body).encode(),
                                     {"api-subscription-key": key, "Content-Type": "application/json", "User-Agent": "sell-smart-video/0.1"})
        open(out, "wb").write(base64.b64decode(json.load(urllib.request.urlopen(req, timeout=60))["audios"][0]))
        print("wrote", out)
