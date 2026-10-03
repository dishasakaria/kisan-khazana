"""Spoilage Clock: photo of stored crop -> condition, approx quantity, spoilage rate/day.

Gemini Flash (vision, JSON mode) only *describes* the photo. Everything the decision engine
uses as a number (spoil_rate_per_day, est_qty_qtl) is computed here in Python from documented tables.
If Gemini fails, assess() returns None and the caller asks the farmer to type the quantity.
"""
import base64, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
# gemini-2.5-flash now returns 404 "no longer available to new users" for our key; the -latest aliases
# resolve to the current flash (3.8 as of Oct 2026). Lite is the fallback when flash is overloaded (503).
MODELS = [os.environ.get("GEMINI_MODEL", "gemini-flash-latest"), "gemini-flash-lite-latest"]
TIMEOUT = 25

CROPS = ["Onion", "Tomato", "Soyabean", "Potato", "Wheat", "Bengal Gram (Gram)(Whole)",
         "Arhar (Tur/Red Gram)(Whole)", "Maize", "Pomegranate", "Grapes", "other"]
STORAGES = ["chawl", "godown", "bags", "heap", "crates", "field", "other"]
CONDITIONS = ["good", "early_sprouting", "some_rot", "heavy_rot", "damp_mould", "unclear"]
CONFIDENCE = ["low", "medium", "high"]

# Baseline loss (fraction of stock per day) in normal farm storage, condition "good".
# Onion 0.3%/day (chawl, 8-10%/month, ICAR-DOGR), tomato 1.5%/day (ambient), soybean 0.03%/day (dry),
# potato 0.2%/day (NABCONS). The rest are our assumptions, same order of magnitude as similar produce:
# dry grains/pulses like soybean, fruit ambient like tomato -- replace when better data arrives.
BASE_RATE = {
    "Onion": 0.003, "Tomato": 0.015, "Soyabean": 0.0003, "Potato": 0.002,
    "Wheat": 0.0003, "Bengal Gram (Gram)(Whole)": 0.0003, "Arhar (Tur/Red Gram)(Whole)": 0.0003,
    "Maize": 0.0004, "Pomegranate": 0.01, "Grapes": 0.03, "other": 0.005,
}
# How much faster the stock loses weight/value once a problem is visible.
MULT = {"good": 1, "early_sprouting": 2, "some_rot": 3, "heavy_rot": 5, "damp_mould": 4, "unclear": 1}
MIN_RATE, MAX_RATE = 0.0001, 0.05  # 0.01%..5% per day
HUMID_CROPS = {"Onion", "Potato"}

# Typical pack sizes (kg). Bags: onion/potato ~50 kg; grains/pulses 50-100 kg -> midpoint 75.
KG_PER_BAG = {"Onion": 50, "Potato": 50, "Soyabean": 75, "Wheat": 75, "Bengal Gram (Gram)(Whole)": 75,
              "Arhar (Tur/Red Gram)(Whole)": 75, "Maize": 75}
KG_PER_CRATE = {"Tomato": 25, "Pomegranate": 20, "Grapes": 8}
DEFAULT_BAG_KG, DEFAULT_CRATE_KG = 50, 20
MAX_QTY_QTL = 5000  # anything above is a hallucination, not a farm store


def spoil_rate(crop, condition, sprouting=False):
    """Fraction lost per day for crop+condition, bounded to [MIN_RATE, MAX_RATE]."""
    m = max(MULT.get(condition, 1), 2 if sprouting else 1)
    return round(min(MAX_RATE, max(MIN_RATE, BASE_RATE.get(crop, BASE_RATE["other"]) * m)), 5)


def adjust_for_humidity(rate, rh_7day_mean, crop="Onion"):
    """Humid weeks rot onion/potato faster: x1.5 above 80% RH, x1.25 above 70%. Other crops unchanged."""
    if crop not in HUMID_CROPS or rh_7day_mean is None:
        return rate
    k = 1.5 if rh_7day_mean > 80 else 1.25 if rh_7day_mean > 70 else 1.0
    return round(min(MAX_RATE, rate * k), 5)


def weekly_loss_pct(rate):
    return round((1 - (1 - rate) ** 7) * 100, 1)


def _key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    f = Path(__file__).with_name(".env")  # same .env format db.py reads
    for line in (f.read_text().splitlines() if f.exists() else []):
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


LANG_NAME = {"mr": "Marathi (Devanagari)", "hi": "Hindi (Devanagari)", "en": "simple English"}

PROMPT = """You are inspecting a photo sent by an Indian farmer of produce they have IN STORAGE
(onion chawl / kanda chawl, godown, gunny or plastic bags, heap on the floor, crates, or still in field).
{hint}Describe ONLY what you can actually see.

Rules (honesty matters more than a complete answer):
- If the photo does not clearly show produce (blurry, dark, a person, a document, empty room), set
  condition="unclear", confidence="low", bags_visible=null, heap_qty_qtl=null.
- bags_visible = number of filled bags/sacks (or crates, if storage is crates) you can actually count in
  the photo. Do NOT extrapolate hidden rows of a stack; if you cannot count them, use null.
- heap_qty_qtl = only for loose heaps/chawl with no bags: a rough volume-based guess in quintals
  (1 quintal = 100 kg; onion ~ 0.6-0.7 t per cubic metre). Otherwise null.
- condition: good | early_sprouting (green shoots/sprouts) | some_rot (a few soft, black, wet or
  mouldy pieces) | heavy_rot (many) | damp_mould (wet bags, fungus, damp floor) | unclear.
- rot_pct_est = share of visible produce that looks rotten (0-100).
- message: ONE short sentence for the farmer in {lang}, plain village words, no English jargon,
  about the condition and how soon to sell (e.g. "कांद्याला कोंब येऊ लागले आहेत — ७-१० दिवसांत विकणे चांगले").
  If unclear, politely ask for a clearer photo of the stored produce."""

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "crop": {"type": "STRING", "enum": CROPS},
        "storage": {"type": "STRING", "enum": STORAGES},
        "condition": {"type": "STRING", "enum": CONDITIONS},
        "rot_pct_est": {"type": "NUMBER"},
        "sprouting": {"type": "BOOLEAN"},
        "moisture_signs": {"type": "BOOLEAN"},
        "bags_visible": {"type": "INTEGER", "nullable": True},
        "heap_qty_qtl": {"type": "NUMBER", "nullable": True},
        "confidence": {"type": "STRING", "enum": CONFIDENCE},
        "message": {"type": "STRING"},
    },
    "required": ["crop", "storage", "condition", "rot_pct_est", "sprouting", "moisture_signs",
                 "bags_visible", "heap_qty_qtl", "confidence", "message"],
    "propertyOrdering": ["crop", "storage", "condition", "rot_pct_est", "sprouting", "moisture_signs",
                         "bags_visible", "heap_qty_qtl", "confidence", "message"],
}


def _gemini(image_bytes, mime, crop_hint, lang):
    hint = f"The farmer says the crop is {crop_hint}; trust that unless the photo clearly shows otherwise.\n" if crop_hint else ""
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode()}},
            {"text": PROMPT.format(hint=hint, lang=LANG_NAME.get(lang, LANG_NAME["mr"]))},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": SCHEMA, "temperature": 0.1},
    }
    # key in a header, not the URL, so it never shows up in logs or exception text
    for i, model in enumerate(MODELS):
        # no thinking on flash: ~3x faster. Lite rejects thinkingBudget (400) and doesn't need it.
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0} if "lite" not in model else None
        body["generationConfig"] = {k: v for k, v in body["generationConfig"].items() if v is not None}
        req = urllib.request.Request(URL.format(model), json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "x-goog-api-key": _key()})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                out = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:  # fast failures (404/429/503): try the next model; timeouts are not retried
            print(f"spoilage: {model} HTTP {e.code}: {e.read()[:200]!r}", file=sys.stderr)
            if i == len(MODELS) - 1:
                raise
    parts = out["candidates"][0]["content"]["parts"]
    return json.loads(next(p["text"] for p in parts if not p.get("thought")))


def _finalize(raw, crop_hint=None):
    """Validate model output and add the Python-computed numbers. Pure function (tested offline)."""
    pick = lambda v, allowed, d: v if v in allowed else d
    crop = pick(raw.get("crop"), CROPS, "other")
    if crop == "other" and crop_hint in CROPS:
        crop = crop_hint
    storage = pick(raw.get("storage"), STORAGES, "other")
    cond = pick(raw.get("condition"), CONDITIONS, "unclear")
    conf = pick(raw.get("confidence"), CONFIDENCE, "low")
    sprouting, moist = bool(raw.get("sprouting")), bool(raw.get("moisture_signs"))
    try:
        rot = max(0.0, min(100.0, float(raw.get("rot_pct_est") or 0)))
    except (TypeError, ValueError):
        rot = 0.0
    bags = raw.get("bags_visible")
    bags = int(bags) if isinstance(bags, (int, float)) and 0 < bags < 10000 else None

    qty = None
    if cond != "unclear":
        if bags:
            kg = KG_PER_CRATE.get(crop, DEFAULT_CRATE_KG) if storage == "crates" else KG_PER_BAG.get(crop, DEFAULT_BAG_KG)
            qty = bags * kg / 100
        elif isinstance(raw.get("heap_qty_qtl"), (int, float)) and raw["heap_qty_qtl"] > 0:
            qty = float(raw["heap_qty_qtl"])
        if qty is not None:
            qty = round(min(qty, MAX_QTY_QTL), 1)
    else:
        bags, conf = None, "low"

    return {"crop": crop, "storage": storage, "condition": cond, "rot_pct_est": round(rot),
            "sprouting": sprouting, "moisture_signs": moist, "bags_visible": bags, "est_qty_qtl": qty,
            "confidence": conf, "spoil_rate_per_day": spoil_rate(crop, cond, sprouting),
            "message": str(raw.get("message") or "")[:300]}


def assess(image_bytes, mime="image/jpeg", crop_hint=None, lang="mr"):
    """Photo of stored crop -> dict (see module doc), or None if Gemini is unavailable."""
    if not image_bytes or not _key():
        return None
    t = time.time()
    try:
        raw = _gemini(image_bytes, mime, crop_hint, lang)
    except Exception as e:  # network, quota (429), bad JSON: caller falls back to typed quantity
        print(f"spoilage: gemini failed: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
        return None
    res = _finalize(raw, crop_hint)
    res["latency_s"] = round(time.time() - t, 1)
    return res


_DEV = str.maketrans("0123456789", "०१२३४५६७८९")
COND_TEXT = {
    "good": {"mr": "माल चांगल्या स्थितीत दिसतो.", "hi": "माल अच्छी हालत में दिखता है।", "en": "Your produce looks in good condition."},
    "early_sprouting": {"mr": "मालाला कोंब येऊ लागले आहेत.", "hi": "माल में अंकुर निकलने लगे हैं।", "en": "Sprouting has started."},
    "some_rot": {"mr": "काही माल सडू लागला आहे.", "hi": "कुछ माल सड़ने लगा है।", "en": "Some of the produce has started rotting."},
    "heavy_rot": {"mr": "बराच माल सडलेला दिसतो — लवकर विका.", "hi": "काफ़ी माल सड़ा हुआ दिखता है — जल्दी बेचें।", "en": "A lot of it looks rotten — sell soon."},
    "damp_mould": {"mr": "ओलावा / बुरशी दिसते — माल कोरडा ठेवा.", "hi": "नमी / फफूंद दिख रही है — माल सूखा रखें।", "en": "Damp or mould is visible — keep it dry."},
    "unclear": {"mr": "फोटोवरून मालाची स्थिती नीट कळत नाही.", "hi": "फोटो से माल की हालत साफ़ नहीं दिखती।", "en": "I can't judge the condition from this photo."},
}
LOSS_TEXT = {"mr": "दर आठवड्याला सुमारे {p}% माल खराब/कमी होऊ शकतो.",
             "hi": "हर हफ़्ते लगभग {p}% माल ख़राब/कम हो सकता है।",
             "en": "It loses about {p}% per week."}
UNIT = {"mr": ("पोती", "क्रेट"), "hi": ("बोरी", "क्रेट"), "en": ("bags", "crates")}
QTY_TEXT = {"mr": "अंदाजे {q} क्विंटल{u} — बरोबर आहे का? नसेल तर खरा आकडा पाठवा.",
            "hi": "अंदाज़न {q} क्विंटल{u} — क्या यह सही है? नहीं तो सही मात्रा भेजें।",
            "en": "Roughly {q} quintals{u} — is that right? If not, send the real figure."}
NO_QTY_TEXT = {"mr": "फोटोवरून माल किती आहे ते कळत नाही — किती क्विंटल आहे ते टाइप करा.",
               "hi": "फोटो से मात्रा पता नहीं चलती — कितने क्विंटल हैं, लिखकर भेजें।",
               "en": "I can't tell the quantity from the photo — please type how many quintals."}


def farmer_message(result, lang="mr"):
    """2-3 line reply: condition, weekly loss, approximate quantity + ask to confirm."""
    lang = lang if lang in LOSS_TEXT else "mr"
    num = (lambda s: str(s).translate(_DEV)) if lang in ("mr", "hi") else str
    cond = result.get("condition", "unclear")
    lines = [COND_TEXT.get(cond, COND_TEXT["unclear"])[lang]]
    if cond != "unclear":
        lines.append(LOSS_TEXT[lang].format(p=num(weekly_loss_pct(result["spoil_rate_per_day"]))))
    q = result.get("est_qty_qtl")
    if q:
        b = result.get("bags_visible")
        u = f" ({num(b)} {UNIT[lang][result.get('storage') == 'crates']})" if b else ""
        lines.append(QTY_TEXT[lang].format(q=num(f"{q:g}"), u=u))
    else:
        lines.append(NO_QTY_TEXT[lang])
    return "\n".join(lines)


if __name__ == "__main__":  # python spoilage.py photo.jpg [crop_hint] [lang]
    a = sys.argv[1:]
    r = assess(Path(a[0]).read_bytes(), "image/png" if a[0].lower().endswith(".png") else "image/jpeg",
               a[1] if len(a) > 1 else None, a[2] if len(a) > 2 else "mr")
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if r:
        print(farmer_message(r, a[2] if len(a) > 2 else "mr"))
