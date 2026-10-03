"""lines.json -> audio/<id>_<speaker>.mp3 via Sarvam bulbul:v3. Cached: existing files are never re-synthesized.
python3 tts.py                 # all lines with VOICES below
python3 tts.py s2 anand        # one line with a specific speaker (voice audition)"""
import base64, json, os, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = {"narr": "kavya", "ramu": "gokul", "shamu": "kabir"}  # picked after auditioning anand/ratan/gokul, aditya/rohan/kabir, kavya/shubh
key = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(os.path.join(HERE, "..", "..", ".env")) if l.startswith("SARVAM_API_KEY="))
lines = {l["id"]: l for l in json.load(open(os.path.join(HERE, "lines.json")))}

def synth(line_id, speaker):
    out = os.path.join(HERE, "audio", f"{line_id}_{speaker}.mp3")
    if os.path.exists(out):
        return out
    body = {"text": lines[line_id]["text"], "target_language_code": "hi-IN", "model": "bulbul:v3", "speaker": speaker,
            "output_audio_codec": "mp3", "speech_sample_rate": 24000}
    req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", json.dumps(body).encode(),
                                 {"api-subscription-key": key, "Content-Type": "application/json", "User-Agent": "sell-smart-video/0.1"})
    open(out, "wb").write(base64.b64decode(json.load(urllib.request.urlopen(req, timeout=60))["audios"][0]))
    print("wrote", out)
    return out

if __name__ == "__main__":
    if len(sys.argv) == 3:
        synth(sys.argv[1], sys.argv[2])
    else:
        for l in lines.values():
            synth(l["id"], VOICES[l["who"]])
