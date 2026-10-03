"""Voice in/out. Sarvam first (built for Indian languages), automatic fallback to Groq Whisper (free)
when Sarvam fails or its credits run out. Spoken replies: Sarvam Bulbul (MP3, plays in WhatsApp)."""
import base64, json, os, uuid, urllib.request

LANG = {"mr": "mr-IN", "hi": "hi-IN", "en": "en-IN"}


def _multipart(fields, audio, filename):
    b = uuid.uuid4().hex
    body = b"".join(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in fields.items())
    body += (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
             f"Content-Type: application/octet-stream\r\n\r\n").encode() + audio + f"\r\n--{b}--\r\n".encode()
    return body, f"multipart/form-data; boundary={b}"


def _sarvam_stt(audio, filename):
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        return ""
    body, ctype = _multipart({"model": "saaras:v4", "language_code": "unknown"}, audio, filename)
    req = urllib.request.Request("https://api.sarvam.ai/speech-to-text", body,
                                 {"api-subscription-key": key, "Content-Type": ctype, "User-Agent": "sell-smart/0.1"})
    return json.load(urllib.request.urlopen(req, timeout=30)).get("transcript", "").strip()


def _groq_stt(audio, filename, lang):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return ""
    fields = {"model": "whisper-large-v3", "response_format": "json", "temperature": "0"}
    if lang in LANG:
        fields["language"] = lang
    body, ctype = _multipart(fields, audio, filename)
    req = urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions", body,
                                 {"Authorization": f"Bearer {key}", "Content-Type": ctype,
                                  "User-Agent": "sell-smart/0.1"})  # Groq rejects urllib's default UA
    return json.load(urllib.request.urlopen(req, timeout=30)).get("text", "").strip()


def transcribe(audio, filename="voice.ogg", lang=None):
    """bytes -> text. Sarvam, then Groq. '' if both fail (the bot then asks the farmer to type)."""
    for engine in (lambda: _sarvam_stt(audio, filename), lambda: _groq_stt(audio, filename, lang)):
        try:
            text = engine()
            if text:
                return text
        except Exception:
            continue  # credits exhausted / outage -> next engine
    return ""


def speak(text, lang="mr"):
    """text -> MP3 bytes via Sarvam Bulbul, or None (caller then sends text only)."""
    key = os.environ.get("SARVAM_API_KEY")
    if not key or not text:
        return None
    body = {"text": text[:1500], "target_language_code": LANG.get(lang, "mr-IN"), "model": "bulbul:v3",
            "speaker": "shubh", "output_audio_codec": "mp3", "speech_sample_rate": 22050}
    req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", json.dumps(body).encode(),
                                 {"api-subscription-key": key, "Content-Type": "application/json", "User-Agent": "sell-smart/0.1"})
    try:
        return base64.b64decode(json.load(urllib.request.urlopen(req, timeout=20))["audios"][0])
    except Exception:
        return None
