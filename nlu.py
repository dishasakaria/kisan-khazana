"""Understand a farmer's message: crop, quantity (quintals), pincode, language.

Rules first (free, instant; handle SMS keywords like "KANDA 50 422001" and most voice transcripts).
Groq (free tier) only as a fallback for messages the rules can't read. The LLM never produces prices.
"""
import json, os, re, urllib.request

# canonical names = Agmarknet names used in our price data
CROPS = {
    "Onion": ["प्याज", "प्याज़", "कांदा", "कांदे", "kanda", "pyaj", "pyaaz", "pyaz", "onion"],
    "Tomato": ["टमाटर", "टोमॅटो", "टोमाटो", "tamatar", "tomato", "tamater"],
    "Soyabean": ["सोयाबीन", "सोयाबिन", "soyabean", "soybean", "soya"],
    "Wheat": ["गेहूं", "गेहूँ", "गहू", "gehu", "gahu", "wheat"],
    "Bengal Gram (Gram)(Whole)": ["हरभरा", "चना", "चणा", "harbhara", "chana", "gram"],
    "Arhar (Tur/Red Gram)(Whole)": ["तूर", "तुअर", "अरहर", "tur", "toor", "arhar"],
    "Potato": ["आलू", "बटाटा", "aloo", "alu", "batata", "potato"],
    "Pomegranate": ["अनार", "डाळिंब", "dalimb", "anar", "pomegranate"],
    "Grapes": ["अंगूर", "द्राक्ष", "draksh", "angoor", "grapes", "grape"],
    "Maize": ["मक्का", "मका", "makka", "maka", "maize", "corn"],
    "Jowar (Sorghum)": ["ज्वारी", "ज्वार", "jowar", "jwari"],
    "Bajra (Pearl Millet/Cumbu)": ["बाजरी", "बाजरा", "bajra", "bajri"],
    "Cotton": ["कापूस", "कपास", "kapus", "kapas", "cotton"],
    "Green Chilli": ["हरी मिर्च", "मिरची", "mirchi", "chilli", "chili"],
    "Garlic": ["लहसुन", "लसूण", "lasun", "lahsun", "garlic"],
    "Cabbage": ["पत्ता गोभी", "कोबी", "kobi", "cabbage"],
    "Cauliflower": ["फूलगोभी", "फ्लॉवर", "phool gobhi", "cauliflower"],
    "Brinjal": ["बैंगन", "वांगी", "वांगे", "vangi", "baingan", "brinjal"],
    "Coriander (Leaves)": ["कोथिंबीर", "धनिया", "kothimbir", "dhaniya", "coriander"],
    "Green Gram (Moong)(Whole)": ["मूग", "मूंग", "moong", "mung"],
}
UNITS = [  # (words, multiplier to quintals)
    (["टन", "ton", "tonne", "tonnes", "tons"], 10.0),
    (["किलो", "kg", "kilo", "किलोग्राम"], 0.01),
    (["क्विंटल", "quintal", "qtl", "q", "क्वि"], 1.0),
]
NUMBER_WORDS = {  # hi + mr spoken numbers that speech-to-text often writes as words
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "पाच": 5, "दस": 10, "बीस": 20, "वीस": 20,
    "तीस": 30, "चालीस": 40, "चाळीस": 40, "पचास": 50, "पन्नास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80,
    "ऐंशी": 80, "नब्बे": 90, "नव्वद": 90, "सौ": 100, "शंभर": 100,
}
HINDI_HINTS = ["है", "हैं", "मेरे", "मेरा", "कितना", "कितने", "बेचूं", "बेचना", "प्याज", "गेहूं", "चना", "आलू", "क्या", "नमस्ते"]
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def language(text):
    if re.search(r"[ऀ-ॿ]", text):
        return "hi" if any(h in text for h in HINDI_HINTS) else "mr"  # Maharashtra: Devanagari defaults to Marathi
    return "en"


def parse(text):
    """-> {crop, qty_qtl, pin, lang}; missing fields are None."""
    t = text.translate(DEVANAGARI_DIGITS).lower()
    out = {"crop": None, "qty_qtl": None, "pin": None, "lang": language(text)}
    hits = [(t.find(w), crop) for crop, words in CROPS.items() for w in words
            if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t)]
    if hits:
        out["crop"] = min(hits)[1]  # first crop mentioned
    pin = re.search(r"\b(4\d{5})\b", t)  # Maharashtra pincodes start with 4
    if pin:
        out["pin"] = pin.group(1)
        t = t.replace(pin.group(1), " ")
    num = re.search(r"(\d+(?:\.\d+)?)\s*([^\s\d]*)", t)
    if num:
        qty, unit_word = float(num.group(1)), num.group(2)
    else:
        words = [NUMBER_WORDS[w] for w in t.split() if w in NUMBER_WORDS]
        qty, unit_word = (float(words[0]), "") if words else (None, "")
    if qty is not None:
        mult = 1.0
        for words, m in UNITS:
            if any(unit_word.startswith(w) for w in words) or any(re.search(rf"(?<![a-z]){w}(?![a-z])", t) for w in words if len(w) > 1):
                mult = m
                break
        out["qty_qtl"] = round(qty * mult, 2)
    if out["crop"] is None or out["qty_qtl"] is None:
        out = _groq_fallback(text, out)
    return out


def _groq_fallback(text, out):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return out
    prompt = ("A farmer in Maharashtra sent this message (Marathi/Hindi/English, maybe a speech transcript). "
              f"Return JSON {{\"crop\": one of {list(CROPS)} or null, \"qty_qtl\": number or null}}. "
              "1 ton = 10 quintals, 100 kg = 1 quintal. Use null if not stated.\nMessage: " + text)
    body = {"model": "openai/gpt-oss-20b", "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}]}
    try:
        req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", json.dumps(body).encode(),
                                     {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                      "User-Agent": "sell-smart/0.1"})  # Groq rejects urllib default UA (403/1010)
        a = json.loads(json.load(urllib.request.urlopen(req, timeout=15))["choices"][0]["message"]["content"])
        crop = a.get("crop") if a.get("crop") in CROPS else None
        qty = a.get("qty_qtl") if isinstance(a.get("qty_qtl"), (int, float)) and a.get("qty_qtl") > 0 else None
        return {**out, "crop": out["crop"] or crop, "qty_qtl": out["qty_qtl"] or qty}
    except Exception:
        return out  # optional help; the bot then asks for the missing piece


if __name__ == "__main__":
    os.environ.pop("GROQ_API_KEY", None)  # test the rules alone
    assert parse("KANDA 50 422001") == {"crop": "Onion", "qty_qtl": 50.0, "pin": "422001", "lang": "en"}
    assert parse("मेरे पास ५० क्विंटल प्याज है") == {"crop": "Onion", "qty_qtl": 50.0, "pin": None, "lang": "hi"}
    assert parse("माझ्याकडे 2 टन कांदा आहे")["qty_qtl"] == 20.0
    assert parse("माझ्याकडे 2 टन कांदा आहे")["lang"] == "mr"
    assert parse("soyabean 800 kg 413001") == {"crop": "Soyabean", "qty_qtl": 8.0, "pin": "413001", "lang": "en"}
    assert parse("टमाटर पचास क्विंटल")["qty_qtl"] == 50.0
    assert parse("हरभरा 30 क्विंटल")["crop"] == "Bengal Gram (Gram)(Whole)"
    assert parse("gehu 12 qtl")["crop"] == "Wheat"
    assert parse("tur 5 quintal")["crop"] == "Arhar (Tur/Red Gram)(Whole)"
    assert parse("hello")["crop"] is None
    print("nlu self-checks ok")
