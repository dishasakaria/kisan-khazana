"""Calling agent (IVR) for feature-phone farmers: Exotel flow + a browser call simulator (web/call.html).

Keys only: language (1-3) -> crop (1-9) -> quintals then # -> 6-digit pincode (skipped for known callers)
-> advice spoken with Sarvam TTS. One flow logic (`need` / `feed` / `finish`).

Exotel flow (docs/IVR_SETUP.md): [Gather -> Passthru] x 5 -> Greeting -> Hangup, all applets pointing at the same URLs:
  GET  /ivr/exotel/gather     Gather dynamic URL -> JSON {gather_prompt, max_input_digits, finish_on_key, ...}
  GET  /ivr/exotel/passthru   reads `digits` ("\"2\""), 200 = ask the next thing, 302 = everything known -> Greeting
  GET  /ivr/exotel/advice     Greeting dynamic URL -> text/plain: mp3 URL (or text fallback)
  GET  /ivr/exotel/missed     missed-call number: rings the caller back into the flow (Exotel Connect API)
  GET  /ivr/prompt/{lang}/{key}.mp3   cached prompts (8 kHz mono for Exotel; ?hq=1 for the browser)
  GET  /ivr/say/{id}.mp3      spoken advice (kept 1 hour)
"""
import base64, json, os, secrets, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response

import advice, speech

router = APIRouter()
POOL = ThreadPoolExecutor(4)
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")
LANGS = ["mr", "hi", "en"]
CROP_KEYS = {"1": "Onion", "2": "Tomato", "3": "Soyabean", "4": "Cotton", "5": "Arhar (Tur/Red Gram)(Whole)",
             "6": "Bengal Gram (Gram)(Whole)", "7": "Wheat", "8": "Potato", "9": "Pomegranate"}
PROMPT = {
    "lang": {"mr": "नमस्कार, सेल स्मार्ट मध्ये स्वागत. फोनवरील बटणे दाबून उत्तर द्या. मराठीसाठी 1 दाबा.",
             "hi": "फ़ोन के बटन दबाकर जवाब दें। हिंदी के लिए 2 दबाएँ।", "en": "Answer by pressing the phone keys. For English, press 3."},
    "crop": {"mr": "कोणते पीक विकायचे? कांद्यासाठी 1 दाबा, टोमॅटोसाठी 2, सोयाबीनसाठी 3, कापसासाठी 4, तुरीसाठी 5, हरभऱ्यासाठी 6, "
                   "गव्हासाठी 7, बटाट्यासाठी 8, डाळिंबासाठी 9 दाबा.",
             "hi": "कौन सी फसल बेचनी है? प्याज़ के लिए 1 दबाएँ, टमाटर के लिए 2, सोयाबीन के लिए 3, कपास के लिए 4, तूर के लिए 5, "
                   "चने के लिए 6, गेहूँ के लिए 7, आलू के लिए 8, अनार के लिए 9 दबाएँ।",
             "en": "Which crop do you want to sell? Press 1 for onion, 2 for tomato, 3 for soybean, 4 for cotton, 5 for tur, "
                   "6 for gram, 7 for wheat, 8 for potato, 9 for pomegranate."},
    "qty": {"mr": "किती क्विंटल? बटणांनी आकडा दाबा, उदाहरणार्थ पाच शून्य, आणि शेवटी हॅश दाबा.",
            "hi": "कितने क्विंटल? बटन से संख्या दबाएँ, जैसे पाँच शून्य, और आख़िर में हैश दबाएँ।",
            "en": "How many quintals? Type the number on the keypad, for example five zero, then press hash."},
    "pin": {"mr": "तुमच्या गावाचा सहा अंकी पिनकोड बटणांनी दाबा.", "hi": "अपने गाँव का छह अंकों का पिनकोड बटन से दबाएँ।",
            "en": "Type your village's six digit pincode on the keypad."},
    "sorry": {"mr": "माफ करा, माहिती पूर्ण मिळाली नाही. कृपया पुन्हा कॉल करा.", "hi": "माफ़ कीजिए, जानकारी पूरी नहीं मिली। कृपया फिर से कॉल करें।",
              "en": "Sorry, we could not get all the details. Please call again."},
}
GATHER = {"lang": (1, ""), "crop": (1, ""), "qty": (4, "#"), "pin": (6, "")}  # max digits, finish key
CALLS = {}  # ponytail: in-memory per-call state keyed by CallSid; fine for one Render instance, Supabase/Redis if we scale out
SAID = {}   # audio id -> (created, mp3)


# ---------------- flow (shared by Exotel and the simulator) ----------------
def call(sid, phone=None, rate=8000):
    now = time.time()
    for k in [k for k, s in CALLS.items() if now - s["t"] > 3600]:
        CALLS.pop(k, None)
    if sid not in CALLS:
        s = CALLS[sid] = {"t": now, "phone": phone, "rate": rate}
        f = _api("farmer", phone) if phone else None  # known caller: skip the pincode
        if f and f.get("lat") is not None:
            s["lat"], s["lon"] = float(f["lat"]), float(f["lon"])
    return CALLS[sid]


def need(s):
    """The next thing to ask, or None when advice can be given."""
    for k in ("lang", "crop", "qty"):
        if s.get(k) is None:
            return k
    return "pin" if s.get("lat") is None else None


def feed(s, digits):
    """Apply the keys pressed for the current question; bad input is ignored, so the same question is asked again."""
    d = (digits or "").replace('"', "").strip().rstrip("#")
    k = need(s)
    if k == "lang" and d in ("1", "2", "3"):
        s["lang"] = LANGS[int(d) - 1]
        POOL.submit(lambda: [prompt_mp3(s["lang"], p, s["rate"]) for p in ("crop", "qty", "pin")])  # warm the cache
    elif k == "crop" and d in CROP_KEYS:
        s["crop"] = CROP_KEYS[d]
    elif k == "qty" and d.isdigit() and 0 < int(d) <= 5000:
        s["qty"] = int(d)
    elif k == "pin" and d in _api("pincodes"):
        s["pin"] = d
        s["lat"], s["lon"] = _api("pincodes")[d]


def finish(s):
    """Advice for a complete call -> {text, chat, audio id}. Saves the caller and logs the query like api.answer."""
    lang = s["lang"]
    a = advice.advise(s["crop"], s["qty"], s["lat"], s["lon"])
    text = advice.render(a, lang, "voice")
    out = {"text": text, "chat": advice.render(a, lang, "chat"), "audio": None}
    mp3 = tts(text, lang, s["rate"])
    if mp3:
        out["audio"] = secrets.token_urlsafe(12)
        SAID[out["audio"]] = (time.time(), mp3)
    phone = s.get("phone")
    try:
        if phone:
            _api("save_farmer", phone, lang=lang, **({"lat": s["lat"], "lon": s["lon"]} if s.get("pin") else {}))
        _api("log", phone or "call:web-sim", "call", f"keys: lang={lang} crop={s['crop']} qty={s['qty']} pin={s.get('pin') or 'known'}",
             {"crop": s["crop"], "qty_qtl": s["qty"], "lat": s["lat"], "lon": s["lon"]}, a)
    except Exception as e:  # logging must never block the farmer's answer
        print("ivr log failed:", repr(e)[:200], flush=True)
    for k in [k for k, (t, _) in SAID.items() if time.time() - t > 3600]:
        SAID.pop(k, None)
    return out


def _api(name, *a, **kw):
    import api  # lazy: api.py includes this router, so a top-level import would be circular
    return getattr(api, name)(*a, **kw)


def phone_of(frm):
    digits = "".join(c for c in frm or "" if c.isdigit())
    return f"call:+91{digits[-10:]}" if len(digits) >= 10 else None


# ---------------- audio ----------------
def tts(text, lang, rate):
    """Sarvam Bulbul like speech.speak, but with a sample rate: Exotel plays only 8 kHz mono wav/mp3."""
    key = os.environ.get("SARVAM_API_KEY")
    if not key or not text:
        return None
    body = {"text": text[:1500], "target_language_code": speech.LANG.get(lang, "mr-IN"), "model": "bulbul:v3",
            "speaker": "shubh", "output_audio_codec": "mp3", "speech_sample_rate": rate}
    req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", json.dumps(body).encode(),
                                 {"api-subscription-key": key, "Content-Type": "application/json", "User-Agent": "sell-smart/0.1"})
    try:
        return base64.b64decode(json.load(urllib.request.urlopen(req, timeout=20))["audios"][0])
    except Exception as e:
        print("ivr tts failed:", repr(e)[:200], flush=True)
        return None


PROMPTS = {}  # (lang, key, rate) -> mp3; like lru_cache but a TTS failure isn't cached forever


def prompt_mp3(lang, key, rate):
    if (lang, key, rate) not in PROMPTS:
        if key == "lang":  # one trilingual prompt: each part in its own voice; raw MP3 frames concatenate cleanly
            parts = [tts(PROMPT["lang"][l], l, rate) for l in LANGS]
            mp3 = b"".join(parts) if all(parts) else None
        else:
            mp3 = tts(PROMPT[key][lang], lang, rate)
        if not mp3:
            return None
        PROMPTS[lang, key, rate] = mp3
    return PROMPTS[lang, key, rate]


def prompt_text(lang, key):
    return " ".join(PROMPT["lang"].values()) if key == "lang" else PROMPT[key][lang]


def prompt_url(base, lang, key, hq=False):
    return f"{base}/ivr/prompt/{lang if key != 'lang' else 'x'}/{key}.mp3" + ("?hq=1" if hq else "")


@router.api_route("/ivr/prompt/{lang}/{key}.mp3", methods=["GET", "HEAD"], include_in_schema=False)
def prompt_audio(lang: str, key: str, hq: int = 0):
    if key not in PROMPT or (key != "lang" and lang not in LANGS):
        raise HTTPException(404)
    mp3 = prompt_mp3(lang if key != "lang" else "x", key, 22050 if hq else 8000)
    if not mp3:
        raise HTTPException(503, "tts unavailable")
    return Response(mp3, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=86400"})


@router.api_route("/ivr/say/{aid}.mp3", methods=["GET", "HEAD"], include_in_schema=False)
def said_audio(aid: str):
    hit = SAID.get(aid)
    if not hit:
        raise HTTPException(404)
    return Response(hit[1], media_type="audio/mpeg")


def _warm():
    if PUBLIC_URL and os.environ.get("EXOTEL_SID"):  # first caller after a deploy shouldn't wait for 3 TTS calls
        POOL.submit(prompt_mp3, "x", "lang", 8000)


router.on_startup.append(_warm)


def base_url(req):
    return PUBLIC_URL or str(req.base_url).rstrip("/")


# ---------------- Exotel ----------------
@router.api_route("/ivr/exotel/gather", methods=["GET", "HEAD"], include_in_schema=False)
def exotel_gather(req: Request, CallSid: str = "", From: str = "", CallFrom: str = ""):
    s = call(CallSid, phone_of(From or CallFrom))
    k = need(s) or "pin"  # complete calls never reach a Gather (Passthru sends them to the Greeting)
    lang = s.get("lang") or "x"
    mp3 = prompt_mp3(lang, k, 8000)
    p = {"audio_url": prompt_url(base_url(req), lang, k)} if mp3 else {"text": prompt_text(s.get("lang") or "en", k)}
    n, fin = GATHER[k]
    return {"gather_prompt": p, "max_input_digits": n, "finish_on_key": fin, "input_timeout": 8 if k in ("qty", "pin") else 6,
            "repeat_menu": 1, "repeat_gather_prompt": p}


@router.get("/ivr/exotel/passthru")
def exotel_passthru(CallSid: str = "", From: str = "", CallFrom: str = "", digits: str = ""):
    s = call(CallSid, phone_of(From or CallFrom))
    feed(s, digits)
    if need(s):
        return PlainTextResponse("ask")  # 200 -> next Gather
    if "job" not in s:
        s["job"] = POOL.submit(finish, s)  # start now; the Greeting waits for it
    return Response(status_code=302)   # 302 -> Greeting (advice)


@router.api_route("/ivr/exotel/advice", methods=["GET", "HEAD"], include_in_schema=False)
def exotel_advice(req: Request, CallSid: str = ""):
    s = CALLS.get(CallSid) or {}
    lang = s.get("lang") or "mr"
    try:
        out = s["job"].result(timeout=25)
    except Exception as e:
        print("ivr advice failed:", repr(e)[:200], flush=True)
        return PlainTextResponse(prompt_url(base_url(req), lang, "sorry") if prompt_mp3(lang, "sorry", 8000) else PROMPT["sorry"]["en"])
    return PlainTextResponse(f"{base_url(req)}/ivr/say/{out['audio']}.mp3" if out["audio"] else out["text"])


LAST_CALLBACK = {}


@router.get("/ivr/exotel/missed")
def exotel_missed(background: BackgroundTasks, From: str = "", CallFrom: str = ""):
    """Missed-call number: ring the farmer back into the IVR flow (free for the farmer)."""
    phone = phone_of(From or CallFrom)
    sid, key, token = (os.environ.get(k, "") for k in ("EXOTEL_SID", "EXOTEL_API_KEY", "EXOTEL_API_TOKEN"))
    flow, caller_id = os.environ.get("EXOTEL_FLOW_ID", ""), os.environ.get("EXOTEL_CALLER_ID", "")
    if not (phone and sid and key and token and flow and caller_id):
        return PlainTextResponse("not configured")
    if time.time() - LAST_CALLBACK.get(phone, 0) < 600:  # one callback per number per 10 min (stops call-bombing)
        return PlainTextResponse("recently called")
    LAST_CALLBACK[phone] = time.time()
    background.add_task(exotel_connect, phone[5:], sid, key, token, flow, caller_id)
    return PlainTextResponse("ok")


def exotel_connect(number, sid, key, token, flow, caller_id):
    host = os.environ.get("EXOTEL_SUBDOMAIN", "api.exotel.com")  # Mumbai cluster accounts: api.in.exotel.com
    data = urllib.parse.urlencode({"From": number, "CallerId": caller_id, "CallType": "trans",
                                   "Url": f"http://my.exotel.com/{sid}/exoml/start_voice/{flow}"}).encode()
    auth = base64.b64encode(f"{key}:{token}".encode()).decode()
    req = urllib.request.Request(f"https://{host}/v1/Accounts/{sid}/Calls/connect.json", data, {"Authorization": f"Basic {auth}", "User-Agent": "sell-smart/1.0"})
    try:
        print("exotel connect", urllib.request.urlopen(req, timeout=20).read()[:300], flush=True)
    except urllib.error.HTTPError as e:
        print("exotel connect failed", e.code, e.read()[:300], flush=True)
    except Exception as e:
        print("exotel connect failed", repr(e)[:200], flush=True)


if __name__ == "__main__":  # self-check of the key logic (no network)
    s = {"rate": 8000, "lat": None}
    assert need(s) == "lang"
    feed(s, '"7"'); assert need(s) == "lang"          # bad key -> asked again
    s["lang"] = "hi"; feed(s, '"9"'); assert s["crop"] == "Pomegranate"
    feed(s, '"0"'); assert need(s) == "qty"
    feed(s, '"45#"'); assert s["qty"] == 45 and need(s) == "pin"
    assert phone_of("09876543210") == "call:+919876543210" and phone_of("+919876543210") == "call:+919876543210"
    print("ivr self-checks ok")
