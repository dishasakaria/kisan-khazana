"""Sell Smart web server (Render). One brain (advice.py) for every channel.

  GET  /health                 -> ok
  POST /advice   (JSON)        -> {crop, qty_qtl, lat, lon | pin, lang} -> advice + text   (website / testing)
  POST /telegram (Bot API)     -> 200 at once; reply sent in the background via sendMessage/sendAudio (logged).
  POST /whatsapp (Twilio form) -> TwiML reply (kept for later; Twilio sandbox limits made Telegram the demo channel).
Security: Telegram secret-token header / Twilio signature; farmer ids only in private tables; public feed anonymised.
Run: uvicorn api:app --host 0.0.0.0 --port $PORT
"""
import base64, csv, hashlib, hmac, json, os, secrets, time, urllib.error, urllib.parse, urllib.request, uuid
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import Response

import advice, db, fpo_api, ivr, nlu, speech

app = FastAPI(title="Sell Smart")
app.include_router(ivr.router)  # calling agent (Exotel IVR)
app.include_router(fpo_api.router)  # Kisaan Khazana FPO dashboard API
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")  # e.g. https://sell-smart.onrender.com
TWILIO_SID, TWILIO_TOKEN = os.environ.get("TWILIO_ACCOUNT_SID", ""), os.environ.get("TWILIO_AUTH_TOKEN", "")
VIDEO = os.environ.get("ONBOARDING_VIDEO_URL", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or hashlib.sha256(("sell-smart" + TG_TOKEN).encode()).hexdigest()[:40]

MSG = {
    "welcome": {"mr": "नमस्कार 🙏 मी सेल-स्मार्ट. कोणत्या बाजारात, कधी विकले तर जास्त पैसे मिळतील ते सांगतो.\n1️⃣ 📎 → Location दाबून तुमचे ठिकाण पाठवा (एकदाच).\n2️⃣ मग पीक आणि क्विंटल लिहा किंवा बोला: \"कांदा 50 क्विंटल\"",
                "hi": "नमस्ते 🙏 मैं सेल-स्मार्ट हूँ। किस मंडी में, कब बेचने से ज़्यादा पैसा मिलेगा — यह बताता हूँ।\n1️⃣ 📎 → Location दबाकर अपनी जगह भेजें (एक बार)।\n2️⃣ फिर फसल और क्विंटल लिखें या बोलें: \"प्याज 50 क्विंटल\"",
                "en": "Hello 🙏 I'm Sell Smart. I tell you which mandi and when to sell for the most money in hand.\n1️⃣ Tap 📎 → Location to share where you are (once).\n2️⃣ Then type or say your crop and quantity: \"onion 50 quintal\""},
    "got_location": {"mr": "✅ ठिकाण मिळाले. आता पीक आणि क्विंटल पाठवा, उदा. \"कांदा 50 क्विंटल\"",
                     "hi": "✅ जगह मिल गई। अब फसल और क्विंटल भेजें, जैसे \"प्याज 50 क्विंटल\"",
                     "en": "✅ Location saved. Now send crop and quantity, e.g. \"onion 50 quintal\""},
    "need_location": {"mr": "📍 तुमचे ठिकाण पाठवा: 📎 → Location (किंवा 6 अंकी पिनकोड लिहा)",
                      "hi": "📍 अपनी जगह भेजें: 📎 → Location (या 6 अंकों का पिनकोड लिखें)",
                      "en": "📍 Please share your location: 📎 → Location (or type your 6-digit pincode)"},
    "need_crop": {"mr": "🌾 कोणते पीक? उदा. \"कांदा 50 क्विंटल\"", "hi": "🌾 कौन सी फसल? जैसे \"प्याज 50 क्विंटल\"",
                  "en": "🌾 Which crop? e.g. \"onion 50 quintal\""},
    "need_qty": {"mr": "⚖️ किती क्विंटल?", "hi": "⚖️ कितने क्विंटल?", "en": "⚖️ How many quintals?"},
    "sms_welcome": {"mr": "नमस्कार! सेल-स्मार्ट: कोणत्या बाजारात विकायचे ते सांगतो. पीक, क्विंटल आणि पिनकोड पाठवा. उदा: कांदा 50 422001",
                    "hi": "नमस्ते! सेल-स्मार्ट: किस मंडी में बेचें, बताता हूँ। फसल, क्विंटल और पिनकोड भेजें। जैसे: प्याज 50 422001",
                    "en": "Hello! Sell Smart tells you where to sell. Send crop, quintals and pincode, e.g. onion 50 422001"},
    "sms_need_location": {"mr": "तुमचा 6 अंकी पिनकोड पाठवा. उदा: कांदा 50 422001", "hi": "अपना 6 अंकों का पिनकोड भेजें। जैसे: प्याज 50 422001",
                          "en": "Send your 6-digit pincode, e.g. onion 50 422001"},
    "no_voice": {"mr": "🎙️ आवाज समजला नाही. कृपया लिहून पाठवा.", "hi": "🎙️ आवाज़ समझ नहीं आई। कृपया लिखकर भेजें।",
                 "en": "🎙️ Couldn't understand the voice note. Please type it."},
}


# ---------------- shared ----------------
@lru_cache(maxsize=1)
def pincodes():
    with open(Path(__file__).with_name("static") / "pincodes_mh.csv") as f:
        return {r["pin"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)}


def farmer(phone):
    r = db.select("farmers", f"select=*&phone=eq.{urllib.request.quote(phone)}&limit=1")
    return r[0] if r else None


def save_farmer(phone, **kw):
    db.upsert("farmers", [{"phone": phone, **kw}])


def log(phone, channel, message, parsed, a):
    db._req("POST", "queries", [{"phone": phone, "channel": channel, "message": message[:500], "commodity": parsed.get("crop"),
                                 "qty_qtl": parsed.get("qty_qtl"), "advice": _slim(a)}], prefer="return=minimal")
    if a:
        p = a["pick"]
        lat, lon = parsed.get("lat"), parsed.get("lon")
        db._req("POST", "live_events", [{"channel": channel, "commodity": a["crop"], "qty_qtl": a["qty"],
                                         "lat": round(lat, 1) if lat else None, "lon": round(lon, 1) if lon else None,
                                         "mandi": p["mandi"], "action": a["action"]}], prefer="return=minimal")


def _slim(a):
    if not a:
        return None
    p = a["pick"]
    return {"action": a["action"], "mandi": p["mandi"], "days": p["days"], "total": a["total"], "net_per_qtl": round(p["net"]),
            "p10": p["p10"], "p50": p["p50"], "p90": p["p90"], "km": p["km"]}


AUDIO = {}  # id -> (created, mp3 bytes); short-lived voice replies that Twilio fetches


def voice_url(text, lang):
    """Make a spoken version (Sarvam) and return a hard-to-guess URL, or None if TTS is unavailable."""
    mp3 = speech.speak(text, lang)
    if not mp3 or not PUBLIC_URL:
        return None
    now = time.time()
    for k in [k for k, (t, _) in AUDIO.items() if now - t > 600]:  # keep 10 minutes
        AUDIO.pop(k, None)
    aid = secrets.token_urlsafe(16)
    AUDIO[aid] = (now, mp3)
    return f"{PUBLIC_URL}/audio/{aid}.mp3"


def answer(phone, text, channel, lat=None, lon=None):
    """Core conversation step for any text channel. Returns (reply text, spoken text or None)."""
    return answer_full(phone, text, channel, lat, lon)[:2]


def answer_full(phone, text, channel, lat=None, lon=None):
    """Same as answer() plus the advice dict (Telegram uses it for the map pin)."""
    f = farmer(phone) if phone else None
    parsed = nlu.parse(text or "")
    lang = parsed["lang"] if parsed["lang"] != "en" or not f else (f.get("lang") or "en")
    if f is None and phone:
        save_farmer(phone, lang=lang)
        f = {"lang": lang}
    if parsed["pin"] and parsed["pin"] in pincodes():
        lat, lon = pincodes()[parsed["pin"]]
        save_farmer(phone, lat=lat, lon=lon, lang=lang)
    lat = lat if lat is not None else (f or {}).get("lat")
    lon = lon if lon is not None else (f or {}).get("lon")
    if lang != (f or {}).get("lang") and parsed["lang"] != "en":
        save_farmer(phone, lang=lang)
    if not parsed["crop"] and parsed["qty_qtl"] and (f or {}).get("last_crop"):
        parsed["crop"] = f["last_crop"]  # "50" right after picking a crop from the menu
    sms = channel == "sms"
    if not parsed["crop"] and not parsed["qty_qtl"]:
        if parsed["pin"] and lat is not None:
            return MSG["got_location"][lang], None, None
        return (MSG["sms_welcome"][lang] if sms else MSG["welcome"][lang] + (f"\n🎬 {VIDEO}" if VIDEO else "")), None, None
    if lat is None:
        return MSG["sms_need_location" if sms else "need_location"][lang], None, None
    if not parsed["crop"]:
        return MSG["need_crop"][lang], None, None
    if not parsed["qty_qtl"]:
        try:
            save_farmer(phone, last_crop=parsed["crop"])
        except Exception:
            pass
        return MSG["need_qty"][lang], None, None
    a = advice.advise(parsed["crop"], parsed["qty_qtl"], float(lat), float(lon), spoil_rate=(f or {}).get("spoil_rate"))
    parsed.update(lat=float(lat), lon=float(lon))
    if a:
        try:
            p = a["pick"]
            save_farmer(phone, last_crop=a["crop"], last_qty=a["qty"], last_mandi=p["mandi"], last_days=p["days"],
                        last_mandi_price=p["p50"], last_net=round(p["net"]))
        except Exception as e:  # needs sql/schema_v2.sql; advice still goes out
            print("save last advice failed:", repr(e)[:200], flush=True)
    try:
        log(phone, channel, text, parsed, a)
    except Exception:
        pass  # logging must never block the farmer's answer
    return advice.render(a, lang, "sms" if channel == "sms" else "chat"), (advice.render(a, lang, "voice") if a else None), a


# ---------------- routes ----------------
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/advice")
async def advice_api(req: Request):
    b = await req.json()
    lat, lon = b.get("lat"), b.get("lon")
    if lat is None and b.get("pin") in pincodes():
        lat, lon = pincodes()[b["pin"]]
    if not (b.get("crop") and b.get("qty_qtl") and lat is not None):
        raise HTTPException(400, "need crop, qty_qtl and lat/lon or pin")
    a = advice.advise(b["crop"], float(b["qty_qtl"]), float(lat), float(lon))
    lang = b.get("lang", "en")
    return {"advice": _slim(a), "options": [{k: o[k] for k in ("mandi", "km", "net", "p50", "price_date")} for o in (a or {}).get("options", [])],
            "text": advice.render(a, lang)}


def twilio_ok(url, params, signature):
    """Twilio request signing: HMAC-SHA1(auth token, url + sorted key+value), base64."""
    if not TWILIO_TOKEN:
        return False
    s = url + "".join(k + params[k] for k in sorted(params))
    digest = base64.b64encode(hmac.new(TWILIO_TOKEN.encode(), s.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(digest, signature or "")


def twiml(text, media=None):
    extra = f"<Message><Media>{escape(media)}</Media></Message>" if media else ""  # voice note as its own message
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(text)}</Message>{extra}</Response>',
                    media_type="application/xml")


@app.get("/audio/{aid}.mp3")
def audio(aid: str):
    hit = AUDIO.get(aid)
    if not hit:
        raise HTTPException(404)
    return Response(hit[1], media_type="audio/mpeg")


# ---------------- SMS: an Android phone + SIM runs "SMS Gateway for Android" (cloud mode, free) ----------------
# Farmer texts the SIM number -> app -> webhook POST /sms (HMAC signed) -> advice -> reply SMS sent by the same phone.
SMSGATE = "https://api.sms-gate.app/3rdparty/v1"
SMS_USER, SMS_PASS = os.environ.get("SMSGATE_USER", ""), os.environ.get("SMSGATE_PASS", "")
SMS_KEY = os.environ.get("SMSGATE_SIGNING_KEY", "")
SMS_SEEN = {}  # number -> recent reply times; ponytail: in-memory rate limit, fine on one instance


def sms_api(method, path, body=None):
    auth = base64.b64encode(f"{SMS_USER}:{SMS_PASS}".encode()).decode()
    req = urllib.request.Request(SMSGATE + path, json.dumps(body).encode() if body is not None else None,
                                 {"Authorization": "Basic " + auth, "Content-Type": "application/json",
                                  "User-Agent": "sell-smart/1.0"}, method=method)  # Cloudflare blocks the default urllib agent (1010)
    out = json.load(urllib.request.urlopen(req, timeout=20))
    print("smsgate", method, path, json.dumps(out)[:200], flush=True)
    return out


def sms_number(sender):
    """+91XXXXXXXXXX for Indian mobiles; None for shortcodes like 'AX-AIRTEL' (never reply to those)."""
    d = "".join(ch for ch in sender if ch.isdigit())
    return "+91" + d[-10:] if len(d) >= 10 and d[-10] in "6789" else None


def sms_text(sender, text):
    """The reply SMS for an incoming SMS, or None (shortcode sender / over the hourly limit)."""
    num = sms_number(sender)
    now = time.time()
    hits = [t for t in SMS_SEEN.get(num, []) if now - t < 3600]
    if not num or len(hits) >= 30:  # max 30 replies per number per hour (the SIM pays for every SMS)
        return None
    SMS_SEEN[num] = hits + [now]
    try:
        import sms_flow  # START -> language -> name -> pincode -> crop list -> quintals -> advice (like Telegram)
        return sms_flow.reply("sms:" + num, text)
    except Exception as e:
        print("sms answer error:", repr(e)[:200], flush=True)
        return "Sell Smart: sorry, please send again. उदा: कांदा 50 422001"


def sms_reply(sender, text):
    reply = sms_text(sender, text)
    if reply:
        try:
            sms_api("POST", "/messages", {"textMessage": {"text": reply}, "phoneNumbers": [sms_number(sender)]})
        except Exception as e:
            print("sms send failed:", repr(e)[:200], flush=True)


SMS_PHONE_KEY = os.environ.get("SMS_PHONE_KEY", "")


@app.post("/sms/phone")
async def sms_phone(req: Request):
    """MacroDroid on the SIM phone: 'SMS received' -> POST here {from, text} with header X-Key -> reply text -> 'Send SMS'."""
    if not SMS_PHONE_KEY or not hmac.compare_digest(req.headers.get("X-Key", ""), SMS_PHONE_KEY):
        raise HTTPException(403, "bad key")
    raw = (await req.body()).decode("utf-8", "ignore")
    try:
        b = json.loads(raw, strict=False)  # strict=False: a newline inside the SMS must not break the JSON
    except ValueError:
        b = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
    sender = str(b.get("from", ""))
    reply = sms_text(sender, str(b.get("text", "")))
    masked = "".join("x" if ch.isdigit() else ch for ch in sender[:-2]) + sender[-2:]  # no phone numbers in logs
    print("sms/phone reply" if reply else f"sms/phone skipped: from={masked!r} (not a mobile number, or >30 SMS/hour)", flush=True)
    return Response(reply or "", media_type="text/plain; charset=utf-8")


@app.post("/sms")
async def sms_in(req: Request, background: BackgroundTasks):
    raw, ts = await req.body(), req.headers.get("X-Timestamp", "")
    sig = hmac.new(SMS_KEY.encode(), raw + ts.encode(), hashlib.sha256).hexdigest()
    if not SMS_KEY or not ts.isdigit() or abs(time.time() - int(ts)) > 300 \
            or not hmac.compare_digest(sig, req.headers.get("X-Signature", "").lower()):
        raise HTTPException(403, "bad signature")
    ev = json.loads(raw)
    if ev.get("event") == "sms:received":
        p = ev.get("payload") or {}
        background.add_task(sms_reply, p.get("sender") or p.get("phoneNumber") or "", p.get("message") or "")
    return {"ok": True}


@app.on_event("startup")
def sms_register():
    """Register our webhook with the SMS gateway (skipped if already there). Also at GET /sms/setup to see why not."""
    missing = [k for k, v in {"SMSGATE_USER": SMS_USER, "SMSGATE_PASS": SMS_PASS, "SMSGATE_SIGNING_KEY": SMS_KEY,
                              "PUBLIC_URL": PUBLIC_URL}.items() if not v]
    if missing:
        out = {"ok": False, "missing_env": missing}
    else:
        try:
            hooks = sms_api("GET", "/webhooks")
            mine = [h for h in hooks if h.get("url") == f"{PUBLIC_URL}/sms" and h.get("event") == "sms:received"]
            if not mine:
                sms_api("POST", "/webhooks", {"url": f"{PUBLIC_URL}/sms", "event": "sms:received"})
            out = {"ok": True, "webhook": f"{PUBLIC_URL}/sms", "already_registered": bool(mine), "all_webhooks": len(hooks)}
            try:  # is the Android phone connected to the gateway cloud? (it is the phone that POSTs to /sms)
                out["phones"] = [{"name": d.get("name"), "last_seen": d.get("lastSeen")} for d in sms_api("GET", "/devices")]
            except Exception as e:
                out["phones"] = repr(e)[:120]
        except urllib.error.HTTPError as e:
            out = {"ok": False, "gateway_http": e.code, "gateway_said": e.read().decode(errors="ignore")[:200],
                   "hint": "401 = wrong SMSGATE_USER/SMSGATE_PASS (copy them from the app's Home tab, Cloud server)"}
        except Exception as e:
            out = {"ok": False, "error": repr(e)[:200]}
    print("sms setup:", json.dumps(out), flush=True)
    return out


@app.get("/sms/setup")
def sms_setup():
    return sms_register()


@app.post("/whatsapp")
async def whatsapp(req: Request):
    form = {k: str(v) for k, v in (await req.form()).items()}
    if not twilio_ok(f"{PUBLIC_URL}/whatsapp", form, req.headers.get("X-Twilio-Signature")):
        raise HTTPException(403, "bad signature")
    phone = form.get("From", "").replace("whatsapp:", "")
    f = farmer(phone) or {}
    lang = f.get("lang") or "mr"
    if form.get("Latitude") and form.get("Longitude"):
        save_farmer(phone, lat=float(form["Latitude"]), lon=float(form["Longitude"]), lang=lang)
        return twiml(MSG["got_location"][lang])
    text = form.get("Body", "")
    if int(form.get("NumMedia", "0")) and form.get("MediaContentType0", "").startswith("audio"):
        auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
        media = urllib.request.urlopen(urllib.request.Request(form["MediaUrl0"], headers={"Authorization": f"Basic {auth}"}), timeout=20).read()
        text = speech.transcribe(media, "voice.ogg", None)
        if not text:
            return twiml(MSG["no_voice"][lang])
    reply, spoken = answer(phone, text, "whatsapp")
    lang = (farmer(phone) or {}).get("lang") or lang
    return twiml(reply, voice_url(spoken, lang) if spoken and lang in ("mr", "hi") else None)


# ---------------- web app API (FPO dashboard + buyer app) ----------------
import market
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

WEB = Path(__file__).with_name("web")


@app.get("/")
def home():
    return RedirectResponse("/app/fpo.html")  # websites are for FPOs and wholesale buyers; farmers use Telegram / calls / SMS


if WEB.exists():
    app.mount("/app", StaticFiles(directory=WEB, html=True), name="web")


def _latest(table, crop=None):
    filt = f"&commodity=eq.{urllib.request.quote(crop)}" if crop else ""
    last = db.select(table, f"select=made_on{filt}&order=made_on.desc&limit=1")
    return last[0]["made_on"] if last else None


@app.get("/api/crops")
def api_crops():
    day = _latest("forecasts")
    rows = db.select("forecasts", f"select=commodity&made_on=eq.{day}&horizon_days=eq.0&limit=2000") if day else []
    return sorted({r["commodity"] for r in rows})


@app.get("/api/mandis")
def api_mandis():
    with open(Path(__file__).with_name("static") / "mandis.csv") as f:
        return [{"market": r["market"], "district": r["district"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                 "name_mr": r.get("name_mr"), "name_hi": r.get("name_hi")} for r in csv.DictReader(f) if r["lat"]]


@app.get("/api/forecasts")
def api_forecasts(crop: str = "Onion"):
    day = _latest("forecasts", crop)
    return db.select("forecasts", f"select=market,horizon_days,target_date,p10,p50,p90&commodity=eq.{urllib.request.quote(crop)}"
                                  f"&made_on=eq.{day}&limit=2000") if day else []


@app.get("/api/live")
def api_live():
    return db.select("live_events", "select=created_at,channel,commodity,qty_qtl,lat,lon,mandi,action&order=created_at.desc&limit=50")


@app.get("/api/track")
def api_track():
    """Live scores once forecasts mature (forecast_scores view) + the 2025 backtest per crop (static/backtest.json)."""
    rows = []
    live = db.select("forecast_scores", "select=commodity,horizon_days,abs_pct_error,inside_range&limit=5000")
    agg = {}
    for r in live:
        k = (r["commodity"], r["horizon_days"])
        a = agg.setdefault(k, [0, 0.0, 0])
        a[0] += 1; a[1] += float(r["abs_pct_error"] or 0); a[2] += 1 if r["inside_range"] else 0
    rows += [{"commodity": c, "horizon_days": h, "n": n, "mape_pct": round(100 * e / n, 1), "inside_range_pct": round(100 * i / n),
              "source": "live"} for (c, h), (n, e, i) in agg.items()]
    bt = Path(__file__).with_name("static") / "backtest.json"
    if bt.exists():
        rows += json.loads(bt.read_text())
    return rows


@app.get("/api/carpools")
def api_carpools(crop: str = None):
    try:
        ps = market.pools([t for t in market.recent_trips() if not crop or t["crop"] == crop])
    except Exception as e:  # e.g. sql/schema_v2.sql not run yet
        print("carpools:", repr(e)[:200], flush=True)
        return []
    return [{k: v for k, v in p.items() if k != "members"} for p in ps]  # never expose who


@app.get("/api/stock")
def api_stock():
    """FPO dashboard 'member stock': totals per crop + district (never one farmer's quantity)."""
    try:
        rows = db.select("listings", "select=crop,qty_qtl,district,condition,ready_date&status=eq.open&limit=2000")
    except Exception as e:
        print("stock:", repr(e)[:200], flush=True)
        return []
    agg = {}
    for r in rows:
        a = agg.setdefault((r["crop"], r.get("district")), {"crop": r["crop"], "district": r.get("district"), "qty_qtl": 0.0,
                                                            "lots": 0, "ready_date": r.get("ready_date"), "condition": None})
        a["qty_qtl"] = round(a["qty_qtl"] + float(r["qty_qtl"] or 0), 1)
        a["lots"] += 1
        a["ready_date"] = min(filter(None, (a["ready_date"], r.get("ready_date"))), default=None)
    return [{**a, "spoil_rate_per_day": None} for a in agg.values()]


# ---------------- Kisaan Khazana API: buyers (app) and FPOs (web dashboard) ----------------
# Identity always comes from the bearer token, never from the request body.
def _token(req):
    h = req.headers.get("Authorization", "")
    return h[7:].strip() if h[:7].lower() == "bearer " else None


def _buyer(req):
    b = market.buyer_by_token(_token(req))
    if not b:
        raise HTTPException(401, "register_first")
    return b


def _fpo(req):
    f = market.fpo_by_token(_token(req))
    if not f:
        raise HTTPException(401, "login_first")
    return f


def _call(fn, *a):
    """market errors -> HTTP: ValueError 400, Conflict 409, LookupError 404 (detail = machine-readable code)."""
    try:
        return fn(*a)
    except market.Conflict as e:
        raise HTTPException(409, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))


HITS = {}  # (kind, key) -> recent attempt times; ponytail: in-memory limiter, fine on one Render instance


def _limit(kind, key, n):
    now = time.time()
    hits = [t for t in HITS.get((kind, key), []) if now - t < 3600]
    if len(hits) >= n:
        raise HTTPException(429, "too_many")
    HITS[(kind, key)] = hits + [now]


def _ip(req):
    return (req.headers.get("X-Forwarded-For") or (req.client.host if req.client else "")).split(",")[0].strip()


@app.post("/api/buyers")
async def api_buyer_register(req: Request):
    _limit("reg", _ip(req), 20)
    token = _call(market.register_buyer, await req.json())
    return {"buyer_token": token, "buyer": market.buyer_me(market.buyer_by_token(token))}


@app.post("/api/buyers/login")
async def api_buyer_login(req: Request):
    b = await req.json()
    _limit("login", _ip(req), 30)
    _limit("login", str(b.get("phone"))[-10:], 10)  # 4-6 digit PIN: cap guesses per phone
    token = market.login_buyer(b.get("phone"), b.get("pin"))
    if not token:
        raise HTTPException(401, "bad_login")
    return {"buyer_token": token, "buyer": market.buyer_me(market.buyer_by_token(token))}


@app.get("/api/buyers/me")
def api_buyer_me(req: Request):
    return market.buyer_me(_buyer(req))


@app.patch("/api/buyers/me")
async def api_buyer_update(req: Request):
    b, body = _buyer(req), await req.json()
    fields = {k: body[k] for k in ("name", "company", "type", "phone", "lat", "lon", "location_text", "pin") if k in body}
    return market.buyer_me(_call(market.update_buyer, b, fields))


@app.get("/api/fpo-lots")
def api_lots(req: Request):
    return _call(market.search_lots, _buyer(req), dict(req.query_params))


@app.get("/api/fpo-lots/{lot_id}")
def api_lot(req: Request, lot_id: int):
    out = market.lot_detail(lot_id, _buyer(req))
    if not out:
        raise HTTPException(404, "not_found")
    return out


@app.post("/api/offers")
async def api_offer(req: Request):
    b, body = _buyer(req), await req.json()
    o = _call(market.make_offer, b, body.get("fpo_lot_id"), body.get("qty_qtl"), body.get("price_rs_qtl"))
    return {"offer_id": o["id"], "status": o["status"], "offer": market.buyer_offers(b, o["id"])[0]}


@app.get("/api/offers")
def api_offers(req: Request):
    return market.buyer_offers(_buyer(req))


@app.get("/api/offers/{offer_id}")
def api_offer_one(req: Request, offer_id: int):
    rows = market.buyer_offers(_buyer(req), offer_id)  # filtered by buyer_id: another buyer's offer is simply not found
    if not rows:
        raise HTTPException(404, "not_found")
    return rows[0]


@app.post("/api/fpos")
async def api_fpo_register(req: Request):
    _limit("fporeg", _ip(req), 10)
    token = _call(market.register_fpo, await req.json())
    return {"fpo_token": token, "fpo": market.fpo_me(market.fpo_by_token(token))}


@app.post("/api/fpos/login")
async def api_fpo_login(req: Request):
    b = await req.json()
    _limit("fpologin", _ip(req), 30)
    _limit("fpologin", str(b.get("login")).lower(), 10)
    token = market.login_fpo(b.get("login"), b.get("password"))
    if not token:
        raise HTTPException(401, "bad_login")
    return {"fpo_token": token, "fpo": market.fpo_me(market.fpo_by_token(token))}


@app.get("/api/fpos/me")
def api_fpo_me(req: Request):
    return market.fpo_me(_fpo(req))


@app.patch("/api/fpos/me")
async def api_fpo_update(req: Request):
    f, body = _fpo(req), await req.json()
    return market.fpo_me(_call(market.update_fpo, f, body))


@app.get("/api/fpos/inventory")
def api_fpo_inventory(req: Request):
    return market.fpo_inventory(_fpo(req))


@app.get("/api/fpos/reference-price")
def api_fpo_reference(req: Request, crop: str):
    f = _fpo(req)
    return market.reference_price(crop, f.get("lat") and float(f["lat"]), f.get("lon") and float(f["lon"])) or {}


@app.get("/api/fpos/lots")
def api_fpo_lots(req: Request):
    return market.fpo_lots_of(_fpo(req))


@app.post("/api/fpos/lots")
async def api_fpo_lot_create(req: Request):
    f, body = _fpo(req), await req.json()
    return _call(market.create_lot, f, body)


@app.patch("/api/fpos/lots/{lot_id}")
async def api_fpo_lot_update(req: Request, lot_id: int):
    f, body = _fpo(req), await req.json()
    return _call(market.update_lot, f, lot_id, body)


@app.get("/api/fpos/offers")
def api_fpo_offers(req: Request):
    return market.fpo_offers(_fpo(req))


@app.post("/api/fpos/offers/{offer_id}/{action}")
def api_fpo_decide(req: Request, offer_id: int, action: str, background: BackgroundTasks):
    if action not in ("accept", "reject"):
        raise HTTPException(404, "not_found")
    f = _fpo(req)
    out = _call(market.decide, f, offer_id, action == "accept")
    if action == "accept" and TG_TOKEN:
        background.add_task(tg_lot_sold, f, offer_id)
    return out


def tg_lot_sold(f, offer_id):
    """Tell the member farmers on Telegram that part of their FPO lot sold (no buyer details)."""
    try:
        o = db.select("offers", f"select=qty_qtl,fpo_lot_id&id=eq.{int(offer_id)}")[0]
        crop = db.select("fpo_lots", f"select=crop&id=eq.{o['fpo_lot_id']}")[0]["crop"]
        for fid in {i["farmer_id"] for i in db.select("fpo_lot_items", f"select=farmer_id&lot_id=eq.{o['fpo_lot_id']}")}:
            if fid.startswith("tg:"):
                lg = (farmer(fid) or {}).get("lang") or "mr"
                tg_send(fid[3:], TXT["lot_sold"][lg].format(f=f["name"], c=crop_label(crop, lg), q=float(o["qty_qtl"])), lg)
    except Exception as e:
        print("lot sold notice failed:", repr(e)[:200], flush=True)


TXT = {
    "fpo_ok": {"mr": "✅ तुमचा {q:g} क्विंटल {c} *{f}* ({km} किमी) या FPO च्या साठ्यात जोडला. FPO इतर सभासदांच्या मालासोबत एकत्र विकेल; विक्री झाली की इथे कळवू.",
               "hi": "✅ आपका {q:g} क्विंटल {c} *{f}* ({km} किमी) FPO के स्टॉक में जोड़ा गया। FPO बाकी सदस्यों के माल के साथ मिलाकर बेचेगा; बिक्री होते ही यहाँ बताएँगे।",
               "en": "✅ Your {q:g} quintal {c} was added to the stock of *{f}* ({km} km away). The FPO sells it together with other members' produce; we'll tell you here when it sells."},
    "no_fpo": {"mr": "तुमच्या 60 किमी परिसरात अजून कोणतीही FPO नोंदलेली नाही. जवळची FPO जोडली गेली की पुन्हा प्रयत्न करा.",
               "hi": "आपके 60 किमी के दायरे में अभी कोई FPO पंजीकृत नहीं है। पास की FPO जुड़ने पर फिर कोशिश करें।",
               "en": "No FPO is registered within 60 km of you yet. Please try again once one nearby joins."},
    "lot_sold": {"mr": "🎉 {f}: तुमचा {c} असलेल्या लॉटमधून {q:g} क्विंटल विकले गेले. पैसे आणि हिशोबासाठी तुमच्या FPO शी बोला.",
                 "hi": "🎉 {f}: आपके {c} वाले लॉट से {q:g} क्विंटल बिक गया। भुगतान और हिसाब के लिए अपनी FPO से बात करें।",
                 "en": "🎉 {f}: {q:g} quintal sold from the {c} lot that includes your stock. Talk to your FPO about payment."},
    "no_last": {"mr": "आधी पीक आणि क्विंटल पाठवा.", "hi": "पहले फसल और क्विंटल भेजें।", "en": "Send crop and quantity first."},
    "pool": {"mr": "🤝 तुमच्या जवळचे {n} शेतकरी {d} रोजी {m} ला जात आहेत. एकत्र ट्रक घेतला तर तुमचे अंदाजे {s} वाचतील.",
             "hi": "🤝 आपके पास के {n} किसान {d} को {m} जा रहे हैं। साथ में ट्रक लेने से आपके लगभग {s} बचेंगे।",
             "en": "🤝 {n} farmers near you are going to {m} on {d}. Sharing a truck saves you about {s}."},
    "no_pool": {"mr": "सध्या जवळ कोणी त्याच बाजारात जात नाही. कोणी आले की कळवू.", "hi": "अभी पास में कोई उसी मंडी नहीं जा रहा। कोई आया तो बताएँगे।",
                "en": "No one near you is going to that mandi yet. We'll tell you when someone is."},
    "pool_joined": {"mr": "✅ ट्रक शेअरसाठी नोंद झाली. सामील शेतकरी: {names}", "hi": "✅ ट्रक शेयर के लिए नाम दर्ज। जुड़े किसान: {names}",
                    "en": "✅ You're in for the shared truck. Farmers in: {names}"},
    "photo": {"mr": "📸 फोटो तपासत आहे…", "hi": "📸 फोटो देख रहे हैं…", "en": "📸 Checking your photo…"},
}


# ---------------- Telegram ----------------
# Bank-style flow: name -> location -> crop (list) -> quantity (list) -> advice card + map pin + menu. Typing/voice still works.
LANG_BUTTONS = {"मराठी": "mr", "हिंदी": "hi", "English": "en"}
LOC_BUTTON = {"mr": "📍 माझे ठिकाण पाठवा", "hi": "📍 मेरी जगह भेजें", "en": "📍 Share my location"}
CROP_MENU = [("Onion", "🧅"), ("Tomato", "🍅"), ("Soyabean", "🫘"), ("Wheat", "🌾"), ("Bengal Gram (Gram)(Whole)", "🟤"),
             ("Arhar (Tur/Red Gram)(Whole)", "🟡"), ("Potato", "🥔"), ("Pomegranate", "🔴"), ("Maize", "🌽"), ("Cotton", "☁️")]
QTY_MENU = [10, 20, 50, 100, 200]
FLOW = {
    "ask_name": {"mr": "नमस्कार 🙏 *सेल-स्मार्ट*मध्ये स्वागत!\nकोणत्या बाजारात, कधी विकले तर जास्त पैसे हातात येतील ते मी सांगतो.\n\n✍️ तुमचे *नाव* लिहा.",
                 "hi": "नमस्ते 🙏 *सेल-स्मार्ट* में स्वागत है!\nकिस मंडी में, कब बेचने से ज़्यादा पैसा हाथ में आएगा — मैं बताता हूँ।\n\n✍️ अपना *नाम* लिखें।",
                 "en": "Hello 🙏 Welcome to *Sell Smart*!\nI tell you which mandi and when to sell for the most money in hand.\n\n✍️ Type your *name*."},
    "ask_loc": {"mr": "धन्यवाद, {n}! 🙏\n📍 तुमचे *ठिकाण* पाठवा — खालचे बटण दाबा 👇\n(किंवा 6 अंकी पिनकोड लिहा)",
                "hi": "धन्यवाद, {n}! 🙏\n📍 अपनी *जगह* भेजें — नीचे का बटन दबाएँ 👇\n(या 6 अंकों का पिनकोड लिखें)",
                "en": "Thank you, {n}! 🙏\n📍 Share your *location* — tap the button below 👇\n(or type your 6-digit pincode)"},
    "ask_crop": {"mr": "🌾 कोणते *पीक* विकायचे आहे? निवडा 👇", "hi": "🌾 कौन सी *फसल* बेचनी है? चुनें 👇", "en": "🌾 Which *crop* do you want to sell? Pick 👇"},
    "ask_qty": {"mr": "⚖️ {c} — किती *क्विंटल*? निवडा 👇", "hi": "⚖️ {c} — कितने *क्विंटल*? चुनें 👇", "en": "⚖️ {c} — how many *quintals*? Pick 👇"},
    "loc_ok": {"mr": "✅ ठिकाण मिळाले.", "hi": "✅ जगह मिल गई।", "en": "✅ Location saved."},
    "other": {"mr": "इतर", "hi": "दूसरी", "en": "Other"}, "type": {"mr": "✍️ लिहा", "hi": "✍️ लिखें", "en": "✍️ Type"},
    "type_crop": {"mr": "✍️ पिकाचे नाव लिहा किंवा 🎙️ बोलून पाठवा.", "hi": "✍️ फसल का नाम लिखें या 🎙️ बोलकर भेजें।", "en": "✍️ Type the crop name or send a 🎙️ voice note."},
    "type_qty": {"mr": "✍️ क्विंटल आकड्यात लिहा, उदा. 35", "hi": "✍️ क्विंटल अंकों में लिखें, जैसे 35", "en": "✍️ Type quintals as a number, e.g. 35"},
    "menu": {"mr": "पुढे काय करायचे? 👇", "hi": "आगे क्या करें? 👇", "en": "What next? 👇"},
    "buttons": {"mr": ("🏢 FPO ला द्या", "🤝 ट्रक शेअर", "📸 साठवण फोटो", "🔁 नवीन सल्ला"),
                "hi": ("🏢 FPO को दें", "🤝 ट्रक शेयर", "📸 भंडारण फोटो", "🔁 नई सलाह"),
                "en": ("🏢 Give to FPO", "🤝 Share truck", "📸 Stock photo", "🔁 New advice")},
    "photo_help": {"mr": "📸 साठवलेल्या मालाचा जवळून एक फोटो पाठवा. माल किती दिवस टिकेल ते सांगतो, आणि पुढचा सल्ला त्यानुसार देतो.",
                   "hi": "📸 रखे हुए माल की पास से एक फोटो भेजें। माल कितने दिन टिकेगा बताएँगे, और अगली सलाह उसी हिसाब से देंगे।",
                   "en": "📸 Send one close-up photo of your stored produce. I'll tell you how long it will keep and adjust the next advice."},
}


def crop_label(crop, lang):
    return advice.CROP_NAME.get(lang, {}).get(crop, crop)


def tg_crop_menu(chat, lang):
    b = [{"text": f"{e} {crop_label(c, lang)}", "callback_data": f"C:{i}"} for i, (c, e) in enumerate(CROP_MENU)]
    rows = [b[k:k + 3] for k in range(0, len(b), 3)] + [[{"text": "➕ " + FLOW["other"][lang], "callback_data": "C:x"}]]
    tg("sendMessage", {"chat_id": chat, "text": FLOW["ask_crop"][lang], "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": rows}})


def tg_qty_menu(chat, lang, crop):
    b = [{"text": f"{q}", "callback_data": f"Q:{q}"} for q in QTY_MENU] + [{"text": FLOW["type"][lang], "callback_data": "Q:x"}]
    tg("sendMessage", {"chat_id": chat, "text": FLOW["ask_qty"][lang].format(c=crop_label(crop, lang)), "parse_mode": "Markdown",
                       "reply_markup": {"inline_keyboard": [b[:3], b[3:]]}})


def tg_menu(chat, lang):
    t = FLOW["buttons"][lang]
    tg("sendMessage", {"chat_id": chat, "text": FLOW["menu"][lang], "reply_markup": {"inline_keyboard": [
        [{"text": t[0], "callback_data": "L"}, {"text": t[1], "callback_data": "P"}],
        [{"text": t[2], "callback_data": "F"}, {"text": t[3], "callback_data": "N"}]]}})


def tg_lang_menu(chat):
    tg("sendMessage", {"chat_id": chat, "text": "🙏 नमस्कार · नमस्ते · Hello!\n🌐 भाषा निवडा · भाषा चुनें · Choose language 👇",
                       "reply_markup": {"inline_keyboard": [[{"text": k, "callback_data": f"G:{v}"} for k, v in LANG_BUTTONS.items()]]}})


def tg_next(chat, uid, lang):
    """Ask for whatever is still missing: name -> location -> crop."""
    f = farmer(uid) or {}
    if not f.get("name"):
        return tg_send(chat, FLOW["ask_name"][lang], lang)
    if f.get("lat") is None:
        return tg("sendMessage", {"chat_id": chat, "text": FLOW["ask_loc"][lang].format(n=f["name"]), "parse_mode": "Markdown",
                                  "reply_markup": tg_keyboard(lang)})
    return tg_crop_menu(chat, lang)


def tg_reply(chat, uid, lang, reply, spoken, a):
    """Send the answer; after advice: map pin of the mandi, voice note, then the action menu."""
    if reply == MSG["need_crop"][lang]:
        return tg_crop_menu(chat, lang)
    if reply == MSG["need_qty"][lang]:
        return tg_qty_menu(chat, lang, (farmer(uid) or {}).get("last_crop") or "")
    if reply == MSG["need_location"][lang] or reply.startswith(MSG["welcome"][lang][:20]):
        return tg_next(chat, uid, lang)
    tg_send(chat, reply, lang)
    if not a:
        return
    m = a["pick"]["mandi"]
    if m in advice.mandis():
        lat, lon, dist = advice.mandis()[m]
        tg("sendVenue", {"chat_id": chat, "latitude": lat, "longitude": lon, "title": "🏪 " + advice.mandi_name(m, lang),
                         "address": f"{advice.DISTRICT.get(dist, {}).get(lang, dist)} · {a['pick']['km']} km"})
    if spoken and lang in ("mr", "hi"):
        mp3 = speech.speak(spoken, lang)
        if mp3:
            tg("sendAudio", {"chat_id": chat, "title": "Sell Smart"}, files={"audio": ("salla.mp3", mp3, "audio/mpeg")})
    tg_menu(chat, lang)


def tg(method, data=None, files=None):
    """Call the Telegram Bot API; log every response (visible in Render logs)."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/{method}"
    if files:  # multipart upload (voice reply)
        b = uuid.uuid4().hex
        body = b"".join(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in (data or {}).items())
        for field, (name, blob, ctype) in files.items():
            body += (f"--{b}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n"
                     f"Content-Type: {ctype}\r\n\r\n").encode() + blob + b"\r\n"
        req = urllib.request.Request(url, body + f"--{b}--\r\n".encode(), {"Content-Type": f"multipart/form-data; boundary={b}"})
    else:
        req = urllib.request.Request(url, json.dumps(data or {}).encode(), {"Content-Type": "application/json"})
    try:
        out = json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        out = {"ok": False, "status": e.code, "error": e.read().decode()[:300]}
    except Exception as e:
        out = {"ok": False, "error": str(e)[:300]}
    print("telegram", method, json.dumps(out, ensure_ascii=False)[:300], flush=True)
    return out


def tg_keyboard(lang):
    return {"keyboard": [[{"text": LOC_BUTTON[lang], "request_location": True}]], "resize_keyboard": True, "one_time_keyboard": True}


def tg_send(chat, text, lang, keyboard=False):
    data = {"chat_id": chat, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        data["reply_markup"] = tg_keyboard(lang)
    if not tg("sendMessage", data).get("ok"):  # Markdown can fail on odd characters: resend as plain text
        data.pop("parse_mode")
        tg("sendMessage", data)


def tg_handle(update):
    msg = update.get("message") or update.get("edited_message") or {}
    chat = (msg.get("chat") or {}).get("id")
    if not chat:
        return
    uid = f"tg:{chat}"
    f = farmer(uid) or {}
    lang = f.get("lang") or "mr"
    try:
        if msg.get("location"):
            save_farmer(uid, lat=msg["location"]["latitude"], lon=msg["location"]["longitude"], lang=lang)
            tg("sendMessage", {"chat_id": chat, "text": FLOW["loc_ok"][lang], "reply_markup": {"remove_keyboard": True}})
            return tg_next(chat, uid, lang)
        text = (msg.get("text") or "").strip()
        if text in LANG_BUTTONS:
            save_farmer(uid, lang=LANG_BUTTONS[text])
            return tg_next(chat, uid, LANG_BUTTONS[text])
        if text.startswith("/start"):  # fresh start every time (e.g. after "clear history"): language -> name -> location -> crop
            save_farmer(uid, name=None, lat=None, lon=None, last_crop=None, last_qty=None, spoil_rate=None, stock_condition=None)
            return tg_lang_menu(chat)
        if text.startswith("/menu"):
            return tg_next(chat, uid, lang)
        if msg.get("photo"):
            return tg_photo(chat, uid, lang, msg)
        voice = msg.get("voice") or msg.get("audio")
        if voice:
            path = tg("getFile", {"file_id": voice["file_id"]}).get("result", {}).get("file_path")
            audio = urllib.request.urlopen(f"https://api.telegram.org/file/bot{TG_TOKEN}/{path}", timeout=30).read() if path else b""
            text = speech.transcribe(audio, "voice.ogg", lang) if audio else ""
            if not text:
                return tg_send(chat, MSG["no_voice"][lang], lang)
            tg_send(chat, f"🎙️ _{text}_", lang)  # show what we heard, so the farmer can correct us
        if not text:
            return
        parsed = nlu.parse(text)
        if f and not f.get("name") and not voice and not parsed["crop"] and not parsed["qty_qtl"] and not parsed["pin"]:
            save_farmer(uid, name=text[:40])  # first free text after /start is the farmer's name
            return tg_next(chat, uid, lang)
        if parsed["pin"] and not parsed["crop"] and parsed["pin"] in pincodes():
            lat, lon = pincodes()[parsed["pin"]]
            save_farmer(uid, lat=lat, lon=lon)
            tg("sendMessage", {"chat_id": chat, "text": FLOW["loc_ok"][lang], "reply_markup": {"remove_keyboard": True}})
            return tg_next(chat, uid, lang)
        reply, spoken, a = answer_full(uid, text, "telegram")
        lang = (farmer(uid) or {}).get("lang") or lang
        tg_reply(chat, uid, lang, reply, spoken, a)
    except Exception as e:  # never leave the farmer without a reply
        print("telegram handler error:", repr(e), flush=True)
        tg_send(chat, {"mr": "माफ करा, काहीतरी चुकले. पुन्हा पाठवा.", "hi": "माफ़ कीजिए, कुछ गड़बड़ हुई। फिर भेजें।",
                       "en": "Sorry, something went wrong. Please send again."}[lang], lang)


def tg_photo(chat, uid, lang, msg):
    """Spoilage Clock: photo of stored crop -> condition, approx quantity, spoilage rate (used in later advice)."""
    try:
        import spoilage
    except ImportError:
        return tg_send(chat, "📸 …", lang)
    tg_send(chat, TXT["photo"][lang], lang)
    file_id = msg["photo"][-1]["file_id"]  # largest size
    path = tg("getFile", {"file_id": file_id}).get("result", {}).get("file_path")
    img = urllib.request.urlopen(f"https://api.telegram.org/file/bot{TG_TOKEN}/{path}", timeout=30).read() if path else b""
    f = farmer(uid) or {}
    res = spoilage.assess(img, "image/jpeg", crop_hint=f.get("last_crop"), lang=lang) if img else None
    if not res:
        return tg_send(chat, MSG["no_voice"][lang].replace("🎙️", "📸"), lang)
    try:
        save_farmer(uid, spoil_rate=res.get("spoil_rate_per_day"), stock_condition=res.get("condition"))
    except Exception as e:
        print("save spoilage failed:", repr(e)[:200], flush=True)
    tg_send(chat, spoilage.farmer_message(res, lang), lang)


def tg_callback(cq):
    chat = cq["message"]["chat"]["id"]
    uid, data = f"tg:{chat}", cq.get("data", "")
    tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
    f = farmer(uid) or {}
    lang = f.get("lang") or "mr"
    if data.startswith("G:") and data[2:] in ("mr", "hi", "en"):
        save_farmer(uid, lang=data[2:])
        if not f.get("name") and PUBLIC_URL:  # onboarding: 1-minute how-to video in the language they just picked
            tg("sendVideo", {"chat_id": chat, "video": f"{PUBLIC_URL}/app/video/onboarding_{data[2:]}.mp4", "supports_streaming": True})
        return tg_next(chat, uid, data[2:])
    if data == "C:x":
        return tg_send(chat, FLOW["type_crop"][lang], lang)
    if data.startswith("C:") and data[2:].isdigit() and int(data[2:]) < len(CROP_MENU):
        crop = CROP_MENU[int(data[2:])][0]
        save_farmer(uid, last_crop=crop)
        return tg_qty_menu(chat, lang, crop)
    if data == "Q:x":
        return tg_send(chat, FLOW["type_qty"][lang], lang)
    if data.startswith("Q:") and data[2:].isdigit() and f.get("last_crop"):
        reply, spoken, a = answer_full(uid, data[2:], "telegram")  # "50" + the crop picked from the menu
        return tg_reply(chat, uid, lang, reply, spoken, a)
    if data == "F":
        return tg_send(chat, FLOW["photo_help"][lang], lang)
    if data == "N":
        return tg_next(chat, uid, lang)
    if data == "L":
        status, fpo, km = market.give_to_fpo(uid, f)  # farmer's stock -> nearest FPO's inventory (buyers never see farmers)
        if status != "ok":
            return tg_send(chat, TXT[status][lang], lang)
        return tg_send(chat, TXT["fpo_ok"][lang].format(q=float(f["last_qty"]), c=crop_label(f["last_crop"], lang), f=fpo["name"], km=km), lang)
    if data == "P":
        p = market.pool_for(uid)
        if not p:
            return tg_send(chat, TXT["no_pool"][lang], lang)
        me = next(m for m in p["members"] if m["farmer"] == uid)
        db.upsert("carpool_optin", [{"farmer": uid, "mandi": p["mandi"], "sell_date": p["date"], "crop": f.get("last_crop"),
                                     "qty_qtl": me["qty"], "lat": round(float(f["lat"]), 2), "lon": round(float(f["lon"]), 2)}])
        tg_send(chat, TXT["pool"][lang].format(n=p["farmers"] - 1, d=advice.when(p["date"], lang), m=advice.mandi_name(p["mandi"], lang),
                                               s=advice.rs(me["saving_rs"])), lang)
        joined = db.select("carpool_optin", f"select=farmer&mandi=eq.{urllib.request.quote(p['mandi'])}&sell_date=eq.{p['date']}")
        ids = [j["farmer"] for j in joined if j["farmer"] in {m["farmer"] for m in p["members"]}]
        if len(ids) >= 2:  # introduce everyone who opted in (Telegram profile links; no phone numbers shared)
            names = ", ".join(f"[{(farmer(i) or {}).get('name') or 'Farmer'}](tg://user?id={i[3:]})" for i in ids if i.startswith("tg:"))
            for i in ids:
                if i.startswith("tg:"):
                    li = (farmer(i) or {}).get("lang") or "mr"
                    tg_send(i[3:], TXT["pool_joined"][li].format(names=names), li)
        return


@app.post("/telegram")
async def telegram(req: Request, background: BackgroundTasks):
    if not TG_TOKEN or not hmac.compare_digest(req.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), TG_SECRET):
        raise HTTPException(403, "bad secret")
    upd = await req.json()
    background.add_task(tg_callback if upd.get("callback_query") else tg_handle,
                        upd.get("callback_query") or upd)  # reply asynchronously; Telegram gets 200 immediately
    return {"ok": True}


@app.get("/telegram/status")
def tg_status():
    """Ask Telegram what it thinks of our webhook (no token shown), and re-point it at this server."""
    if not TG_TOKEN or not PUBLIC_URL:
        return {"ok": False, "missing_env": [k for k, v in {"TELEGRAM_BOT_TOKEN": TG_TOKEN, "PUBLIC_URL": PUBLIC_URL}.items() if not v]}
    before = tg("getWebhookInfo").get("result", {})
    tg_register()
    after = tg("getWebhookInfo").get("result", {})
    me = tg("getMe").get("result", {})
    keep = ("url", "pending_update_count", "last_error_date", "last_error_message")
    return {"ok": True, "bot": me.get("username"), "before": {k: before.get(k) for k in keep}, "now": {k: after.get(k) for k in keep}}


@app.on_event("startup")
def tg_register():
    """Point the bot at this server on every deploy (idempotent)."""
    if TG_TOKEN and PUBLIC_URL:
        tg("setWebhook", {"url": f"{PUBLIC_URL}/telegram", "secret_token": TG_SECRET,
                          "allowed_updates": ["message", "edited_message", "callback_query"], "drop_pending_updates": False})
        tg("setMyCommands", {"commands": [{"command": "start", "description": "सुरुवात / Start"},
                                          {"command": "menu", "description": "नवीन सल्ला / New advice"}]})
        tg("setMyDescription", {"description": "🌾 सेल-स्मार्ट: कोणत्या बाजारात, कधी विकले तर हातात जास्त पैसे येतील — ट्रक भाडे, हमाली वजा करून. "
                                               "मराठी, हिंदी, English. बोलून किंवा बटण दाबून विचारा. निर्णय तुमचाच. 👇 Start दाबा"})
        tg("setMyShortDescription", {"short_description": "कोणत्या बाजारात, कधी विकायचे — हातात किती पैसे येतील ते सांगतो. 🌾"})
