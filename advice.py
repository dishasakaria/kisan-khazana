"""Decision engine: where + when to sell, in ₹ in hand. Reads only Supabase + static/ (light enough for Render).

For each mandi m and day d (0 = today, 7/14/21 = forecast):
  ₹ in hand = qty x (1 - spoilage x d) x price(m,d) - transport(road km, today's diesel) - handling x qty - interest x d
Hold only if it beats selling today with >=70% probability (from the P10/P50/P90 range), by >=₹50/qtl, and the
mandi is open that day. Perishables are never held. Extra options: MSAMB private markets / direct buyers, MSP, pledge loan.
"""
import csv, datetime as dt, json, math, urllib.request
from functools import lru_cache
from pathlib import Path

import db
from transport import best_transport, diesel_price

STATIC = Path(__file__).with_name("static")
HANDLING_PER_QTL = 20.0        # hamali + weighing (2026 reports ~₹16/qtl; knob — check with farmer sale slips)
INTEREST_PER_DAY = 0.12 / 365  # cost of waiting for cash (informal credit ~12%/yr; knob)
HOLD_MIN_PROB, HOLD_MIN_GAIN = 0.70, 50.0
MAX_KM = 200
KM_PENALTY = 0.5  # ₹/quintal per km, used only to CHOOSE: a far mandi must beat a near one by more (farmer's day, rejection risk)
# crops where the model did NOT beat "price stays the same" in the 2025 backtest: never show "high" confidence
WEAK_MODEL = {"Onion"}
# spoilage per day and max sensible holding days, by shelf-life class (ICAR-CIPHET / NABCONS / DOGR ranges)
PERISHABLE = {"Tomato", "Brinjal", "Cabbage", "Cauliflower", "Green Chilli", "Coriander (Leaves)", "Methi (Leaves)",
              "Spinach", "Bhindi (Ladies Finger)", "Cucumbar (Kheera)", "Bitter gourd", "Bottle gourd", "Grapes",
              "Chilly Capsicum", "Carrot", "Beans", "French Beans (Frasbean)", "Ridgeguard (Tori)", "Drumstick"}
SEMI = {"Onion", "Potato", "Garlic", "Pomegranate", "Ginger (Green)", "Banana"}
STORABLE_PLEDGE = {"Soyabean", "Wheat", "Bengal Gram (Gram)(Whole)", "Arhar (Tur/Red Gram)(Whole)", "Maize",
                   "Jowar (Sorghum)", "Bajra (Pearl Millet/Cumbu)", "Green Gram (Moong)(Whole)",
                   "Black Gram (Urd Beans)(Whole)", "Cotton"}  # Shetmal Taran pledge-loan crops (MSAMB)


def shelf(crop):
    if crop in PERISHABLE:
        return 0.015, 0
    if crop in SEMI:
        return 0.003, 21
    return 0.0003, 21


@lru_cache(maxsize=1)
def mandis():
    with open(STATIC / "mandis.csv") as f:
        return {r["market"]: (float(r["lat"]), float(r["lon"]), r["district"]) for r in csv.DictReader(f) if r["lat"]}


@lru_cache(maxsize=1)
def local_names():
    with open(STATIC / "mandis.csv") as f:
        return {r["market"]: {"mr": r.get("name_mr") or r["market"], "hi": r.get("name_hi") or r["market"]} for r in csv.DictReader(f)}


def mandi_name(m, lang):
    return local_names().get(m, {}).get(lang, m) if lang in ("mr", "hi") else m


@lru_cache(maxsize=1)
def closed_days():
    with open(STATIC / "holidays.csv") as f:
        return {r["date"] for r in csv.DictReader(f) if r["type"] in ("mandi_closure", "public")}


@lru_cache(maxsize=1)
def msp_table():
    with open(STATIC / "msp.csv") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: r["marketing_year"])
    return {r["commodity"]: float(r["msp_rs_qtl"]) for r in rows}  # latest year wins


def forecasts(crop):
    latest = db.select("forecasts", f"select=made_on&commodity=eq.{_q(crop)}&order=made_on.desc&limit=1")
    if not latest:
        return {}
    rows = db.select("forecasts", f"select=market,horizon_days,target_date,p10,p50,p90&commodity=eq.{_q(crop)}"
                                  f"&made_on=eq.{latest[0]['made_on']}&limit=2000")
    out = {}
    for r in rows:
        out.setdefault(r["market"], {})[r["horizon_days"]] = r
    return out


def other_buyers(crop, days=7):
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    rows = db.select("prices", f"select=date,market,modal,source&source=in.(msamb_private,msamb_direct)"
                               f"&commodity=ilike.{_q(crop.split(' (')[0])}*&date=gte.{since}&order=modal.desc&limit=50")
    area = ("nashik", "pune", "ahmednagar", "ahilyanagar", "sangamner", "niphad", "rahata", "shrirampur", "baramati")
    seen, out = set(), []
    for r in rows:  # best price per buyer, pilot area only
        if any(a in r["market"].lower() for a in area) and r["market"] not in seen:
            seen.add(r["market"])
            out.append(r)
    return out[:5]  # names carry "Dist. X"; keep pilot area


def _q(s):
    return urllib.request.quote(s, safe="")


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def road_km(farm, points):
    """One OSRM table call (real roads); falls back to straight line x1.3 if OSRM is down."""
    try:
        coords = ";".join(f"{lon},{lat}" for lat, lon in [farm] + points)
        url = f"https://router.project-osrm.org/table/v1/driving/{coords}?sources=0&annotations=distance,duration"
        js = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "sell-smart/0.1"}), timeout=10))
        return [(d / 1000, t / 3600) for d, t in zip(js["distances"][0][1:], js["durations"][0][1:])]
    except Exception:
        return [(1.3 * haversine(farm, p), 1.3 * haversine(farm, p) / 40) for p in points]


def prob_above(threshold, p10, p50, p90):
    """P(price > threshold) from 3 quantiles, piecewise-linear CDF, tails extended."""
    pts = [(p10 - (p50 - p10), 0.0), (p10, 0.1), (p50, 0.5), (p90, 0.9), (p90 + (p90 - p50), 1.0)]
    if threshold <= pts[0][0]:
        return 1.0
    for (x0, c0), (x1, c1) in zip(pts, pts[1:]):
        if threshold <= x1:
            return 1 - (c0 + (c1 - c0) * (threshold - x0) / max(x1 - x0, 1e-9))
    return 0.0


def advise(crop, qty, lat, lon, today=None, spoil_rate=None):
    """spoil_rate: per-day loss from the farmer's stock photo (Spoilage Clock); overrides the crop default."""
    today = today or dt.date.today()
    fc, places = forecasts(crop), mandis()
    cand = [m for m in fc if m in places and haversine((lat, lon), places[m][:2]) <= MAX_KM / 1.3 and 0 in fc[m]]
    if not cand:
        return None
    roads = road_km((lat, lon), [places[m][:2] for m in cand])
    diesel, _, _ = diesel_price("pune")
    spoil, max_hold = shelf(crop)
    if spoil_rate:
        spoil = min(max(float(spoil_rate), spoil), 0.05)  # photo can only make it worse than default, capped 5%/day
        max_hold = 0 if spoil >= 0.015 else max_hold
    opts = []
    for m, (km, hrs) in zip(cand, roads):
        if km > MAX_KM:
            continue
        t = best_transport(qty, round(km), diesel)  # rounded so "km × ₹25" on the card adds up
        for h, r in fc[m].items():
            day = today + dt.timedelta(days=h)
            if h > max_hold or (h and day.isoformat() in closed_days()):
                continue
            keep = 1 - spoil * h
            def net(price):
                return keep * price - t["per_qtl"] - HANDLING_PER_QTL - keep * price * INTEREST_PER_DAY * h
            o = {"mandi": m, "days": h, "date": day.isoformat(), "km": round(km), "hours": round(hrs, 1), "transport": t,
                 "price_date": r["target_date"], "p10": r["p10"], "p50": r["p50"], "p90": r["p90"],
                 "net": net(r["p50"]), "net_lo": net(r["p10"]), "net_hi": net(r["p90"]), "keep": keep}
            o["score"] = o["net"] - KM_PENALTY * km
            opts.append(o)
    now = [o for o in opts if o["days"] == 0]
    if not now:
        return None
    nearest = min(now, key=lambda o: o["km"])
    best_now = max(now, key=lambda o: o["score"])
    hold = None
    for o in (o for o in opts if o["days"] > 0):
        # price at which holding just matches selling now at the best mandi
        need = (best_now["net"] + o["transport"]["per_qtl"] + HANDLING_PER_QTL) / (o["keep"] * (1 - INTEREST_PER_DAY * o["days"]))
        o["prob"] = prob_above(need, o["p10"], o["p50"], o["p90"])
        if o["prob"] >= HOLD_MIN_PROB and o["score"] - best_now["score"] >= HOLD_MIN_GAIN and (hold is None or o["score"] > hold["score"]):
            hold = o
    pick = hold or best_now
    msp = msp_table().get(crop)
    # the bill the farmer sees; every line rounded so the card adds up exactly
    price = round(pick["p50"])
    gross = round(qty * price)
    bill = {"gross": gross, "spoil": round(qty * (1 - pick["keep"]) * price), "truck": pick["transport"]["total"],
            "handling": round(qty * HANDLING_PER_QTL), "interest": round(qty * pick["keep"] * price * INTEREST_PER_DAY * pick["days"])}
    bill["in_hand"] = gross - bill["spoil"] - bill["truck"] - bill["handling"] - bill["interest"]
    return {"bill": bill, "today": today.isoformat(), "farm": (lat, lon), "crop": crop, "qty": qty, "action": "hold" if hold else "sell_now", "pick": pick, "best_now": best_now,
            "nearest": nearest, "total": bill["in_hand"], "extra_vs_nearest": round((pick["net"] - nearest["net"]) * qty),
            "confidence": "medium" if crop in WEAK_MODEL and hold else
                          ("high" if (hold and hold["prob"] >= 0.85) or (not hold and len(now) >= 3) else "medium"),
            "msp": msp, "below_msp": bool(msp and pick["p50"] < msp), "pledge": bool(hold and crop in STORABLE_PLEDGE),
            "perishable": max_hold == 0, "diesel": diesel, "options": sorted(now, key=lambda o: -o["net"])[:5],
            "other_buyers": other_buyers(crop)}


# ---------------- replies (fixed templates: numbers come only from the engine, never from an LLM) ----------------
CROP_NAME = {
    "mr": {"Onion": "कांदा", "Tomato": "टोमॅटो", "Soyabean": "सोयाबीन", "Wheat": "गहू", "Bengal Gram (Gram)(Whole)": "हरभरा",
           "Arhar (Tur/Red Gram)(Whole)": "तूर", "Potato": "बटाटा", "Pomegranate": "डाळिंब", "Grapes": "द्राक्ष", "Maize": "मका",
           "Jowar (Sorghum)": "ज्वारी", "Bajra (Pearl Millet/Cumbu)": "बाजरी", "Cotton": "कापूस"},
    "hi": {"Onion": "प्याज", "Tomato": "टमाटर", "Soyabean": "सोयाबीन", "Wheat": "गेहूं", "Bengal Gram (Gram)(Whole)": "चना",
           "Arhar (Tur/Red Gram)(Whole)": "तूर", "Potato": "आलू", "Pomegranate": "अनार", "Grapes": "अंगूर", "Maize": "मक्का",
           "Jowar (Sorghum)": "ज्वार", "Bajra (Pearl Millet/Cumbu)": "बाजरा", "Cotton": "कपास"},
}
T = {  # every user-facing sentence, in 3 languages
    "sell_now": {"mr": "आज {m} येथे विका", "hi": "आज {m} में बेचें", "en": "Sell today at {m}"},
    "hold": {"mr": "{d} दिवस थांबा, नंतर {m} येथे विका", "hi": "{d} दिन रुकें, फिर {m} में बेचें", "en": "Wait {d} days, then sell at {m}"},
    "in_hand": {"mr": "💰 हातात (सर्व खर्च वजा): *{t}* ({p}/क्विंटल)", "hi": "💰 हाथ में (सारे खर्च काटकर): *{t}* ({p}/क्विंटल)",
                "en": "💰 In hand (after all costs): *{t}* ({p}/quintal)"},
    "extra": {"mr": "📈 जवळच्या बाजारापेक्षा {x} जास्त", "hi": "📈 पास की मंडी से {x} ज़्यादा", "en": "📈 {x} more than the nearest mandi"},
    "range": {"mr": "🎯 भाव अंदाज {lo}–{hi} (खात्री: {c})", "hi": "🎯 भाव अनुमान {lo}–{hi} (भरोसा: {c})", "en": "🎯 Expected price {lo}–{hi} (confidence: {c})"},
    "conf": {"high": {"mr": "🟢 जास्त", "hi": "🟢 ज़्यादा", "en": "🟢 high"}, "medium": {"mr": "🟡 मध्यम", "hi": "🟡 मध्यम", "en": "🟡 medium"}},
    "truck": {"mr": "🚚 {km} किमी, {v}: {c} (डिझेल ₹{d}/लि)", "hi": "🚚 {km} किमी, {v}: {c} (डीज़ल ₹{d}/ली)", "en": "🚚 {km} km by {v}: {c} (diesel ₹{d}/L)"},
    "perishable": {"mr": "⏱️ लवकर खराब होणारे पीक — थांबू नका", "hi": "⏱️ जल्दी खराब होने वाली फसल — रुकें नहीं", "en": "⏱️ Perishable — don't wait"},
    "pledge": {"mr": "🏦 पैसे लगेच हवे? APMC मध्ये शेतमाल तारण कर्ज: किंमतीच्या 75%, 6% व्याज", "hi": "🏦 पैसा अभी चाहिए? APMC में शेतमाल तारण कर्ज: कीमत का 75%, 6% ब्याज",
               "en": "🏦 Need cash now? APMC pledge loan (Shetmal Taran): 75% of value at 6%"},
    "msp": {"mr": "ℹ️ भाव हमीभावापेक्षा (₹{msp}) कमी — सरकारी खरेदी केंद्र तपासा", "hi": "ℹ️ भाव MSP (₹{msp}) से कम — सरकारी खरीद केंद्र देखें",
            "en": "ℹ️ Below MSP (₹{msp}) — check govt procurement centre"},
    "buyers": {"mr": "🏪 इतर खरेदीदार: {b}", "hi": "🏪 दूसरे खरीदार: {b}", "en": "🏪 Other buyers: {b}"},
    "choice": {"mr": "निर्णय तुमचा आहे 🙏", "hi": "फैसला आपका है 🙏", "en": "The decision is yours 🙏"},
    "none": {"mr": "माफ करा, जवळच्या बाजाराचा ताजा भाव मिळाला नाही.", "hi": "माफ़ कीजिए, पास की मंडी का ताज़ा भाव नहीं मिला।",
             "en": "Sorry, no recent nearby mandi price for this crop."},
}


def rs(x):
    """Indian digit grouping: 1,23,456."""
    s = f"{abs(round(x)):d}"
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        tail = head[-2:] + "," + tail
        head = head[:-2]
    return ("-" if x < 0 else "") + "₹" + (head + "," + tail if head else tail)


MONTHS = {"mr": "जानेवारी फेब्रुवारी मार्च एप्रिल मे जून जुलै ऑगस्ट सप्टेंबर ऑक्टोबर नोव्हेंबर डिसेंबर".split(),
          "hi": "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split(),
          "en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}
DAYS = {"mr": "सोमवार मंगळवार बुधवार गुरुवार शुक्रवार शनिवार रविवार".split(),
        "hi": "सोमवार मंगलवार बुधवार गुरुवार शुक्रवार शनिवार रविवार".split(),
        "en": "Mon Tue Wed Thu Fri Sat Sun".split()}
CARD = {  # the advice card, line by line
    "you": {"mr": "📍 तुमचे ठिकाण: {p} जवळ", "hi": "📍 आपकी जगह: {p} के पास", "en": "📍 You are near: {p}"},
    "sell_now": {"mr": "✅ *सल्ला: आजच विका*", "hi": "✅ *सलाह: आज ही बेचें*", "en": "✅ *Advice: sell today*"},
    "hold": {"mr": "⏳ *सल्ला: {d} दिवस थांबा*, मग विका", "hi": "⏳ *सलाह: {d} दिन रुकें*, फिर बेचें", "en": "⏳ *Advice: wait {d} days*, then sell"},
    "mandi": {"mr": "🏪 *{m} बाजार समिती* ({dist} जिल्हा)", "hi": "🏪 *{m} मंडी* ({dist} ज़िला)", "en": "🏪 *{m} APMC* ({dist} district)"},
    "road": {"mr": "🛣️ {km} किमी · सुमारे {t}", "hi": "🛣️ {km} किमी · लगभग {t}", "en": "🛣️ {km} km · about {t}"},
    "hrs": {"mr": "{h} तास", "hi": "{h} घंटे", "en": "{h} h"}, "mins": {"mr": "{m} मिनिटे", "hi": "{m} मिनट", "en": "{m} min"},
    "date": {"mr": "📅 विक्रीचा दिवस: {d}", "hi": "📅 बेचने का दिन: {d}", "en": "📅 Sell on: {d}"},
    "bill": {"mr": "🧾 *हिशोब*", "hi": "🧾 *हिसाब*", "en": "🧾 *Your money*"},
    "price_now": {"mr": "आजचा भाव {p}/क्विंटल × {q} = {g}", "hi": "आज का भाव {p}/क्विंटल × {q} = {g}", "en": "Today's price {p}/qtl × {q} = {g}"},
    "price_fc": {"mr": "अंदाजे भाव {p}/क्विंटल × {q} = {g}\n   (बहुधा {lo} ते {hi} दरम्यान)",
                 "hi": "अनुमानित भाव {p}/क्विंटल × {q} = {g}\n   (संभवतः {lo} से {hi} के बीच)",
                 "en": "Expected price {p}/qtl × {q} = {g}\n   (likely between {lo} and {hi})"},
    "spoil": {"mr": "➖ साठवणीत घट ({pc}%): {x}", "hi": "➖ भंडारण में नुकसान ({pc}%): {x}", "en": "➖ Storage loss ({pc}%): {x}"},
    "truck": {"mr": "➖ ट्रक भाडे ({km} किमी × ₹{r}{t}): {x}", "hi": "➖ ट्रक भाड़ा ({km} किमी × ₹{r}{t}): {x}", "en": "➖ Truck rent ({km} km × ₹{r}{t}): {x}"},
    "trips": {"mr": " × {n} ट्रक", "hi": " × {n} ट्रक", "en": " × {n} trucks"},
    "handling": {"mr": "➖ हमाली/तोलाई: {x}", "hi": "➖ हमाली/तुलाई: {x}", "en": "➖ Loading/weighing: {x}"},
    "interest": {"mr": "➖ थांबण्याचा खर्च (व्याज): {x}", "hi": "➖ रुकने का खर्च (ब्याज): {x}", "en": "➖ Cost of waiting (interest): {x}"},
    "in_hand": {"mr": "💰 *तुमच्या हातात: {x}*", "hi": "💰 *आपके हाथ में: {x}*", "en": "💰 *In your hand: {x}*"},
    "compare": {"mr": "📊 *आज इतर बाजारात (हातात)*", "hi": "📊 *आज दूसरी मंडियों में (हाथ में)*", "en": "📊 *Other mandis today (in hand)*"},
    "if_today": {"mr": "📊 आज {m} ला विकले तर: {x}", "hi": "📊 आज {m} में बेचें तो: {x}", "en": "📊 If you sell today at {m}: {x}"},
    "gain": {"mr": "➕ थांबल्यास अंदाजे {x} जास्त. पण भाव पडला तर फक्त {lo} मिळू शकतात.",
             "hi": "➕ रुकने पर लगभग {x} ज़्यादा। पर भाव गिरा तो सिर्फ़ {lo} मिल सकते हैं।",
             "en": "➕ Waiting gives about {x} more. But if prices fall you may get only {lo}."},
    "conf": {"high": {"mr": "🟢 खात्री: जास्त", "hi": "🟢 भरोसा: ज़्यादा", "en": "🟢 Confidence: high"},
             "medium": {"mr": "🟡 खात्री: मध्यम — भाव बदलू शकतो", "hi": "🟡 भरोसा: मध्यम — भाव बदल सकता है", "en": "🟡 Confidence: medium — prices can move"}},
}


SMS_WORDS = {"price": {"mr": "भाव", "hi": "भाव", "en": "Price"}, "truck": {"mr": "ट्रक", "hi": "ट्रक", "en": "Truck"},
             "hamali": {"mr": "हमाली", "hi": "हमाली", "en": "Loading"}, "hand": {"mr": "हातात", "hi": "हाथ में", "en": "In hand"},
             "today": {"mr": "आज विकल्यास", "hi": "आज बेचें तो", "en": "If sold today"}}


def when(iso, lang):
    d = dt.date.fromisoformat(iso)
    return f"{DAYS[lang][d.weekday()]}, {d.day} {MONTHS[lang][d.month - 1]}"


DISTRICT = {"Nashik": {"mr": "नाशिक", "hi": "नासिक"}, "Pune": {"mr": "पुणे", "hi": "पुणे"},
            "Ahmednagar": {"mr": "अहिल्यानगर", "hi": "अहिल्यानगर", "en": "Ahilyanagar"}}


def travel(hours, lang):
    h, m = divmod(max(5, round(hours * 60 / 5) * 5), 60)
    return " ".join(([CARD["hrs"][lang].format(h=h)] if h else []) + ([CARD["mins"][lang].format(m=m)] if m else []))


def near_town(lat, lon, lang):
    """Farmer's location shown as the nearest mandi town (offline, already has Marathi/Hindi names)."""
    m = min(mandis(), key=lambda k: haversine((lat, lon), mandis()[k][:2]))
    return mandi_name(m, lang)


def render(a, lang="mr", channel="chat"):
    if a is None:
        return T["none"][lang]
    p, c = a["pick"], CROP_NAME.get(lang, {}).get(a["crop"], a["crop"])
    m = mandi_name(p["mandi"], lang)
    act = T["sell_now" if a["action"] == "sell_now" else "hold"][lang].format(m=m, d=p["days"])
    if channel == "sms":  # ~2-3 Unicode SMS parts; every number from the engine
        L = {k: v[lang] for k, v in SMS_WORDS.items()}
        b = a["bill"]
        out = f"{c} {a['qty']:g}q: {act} ({p['km']}km, {when(p['date'], lang)}). {L['price']} {rs(p['p50'])}/q"
        if p["days"]:
            out += f" ({rs(p['p10'])}-{rs(p['p90'])})"
        out += f". {L['truck']} {rs(b['truck'])}, {L['hamali']} {rs(b['handling'])}. {L['hand']} {rs(b['in_hand'])}."
        if a["action"] == "hold":
            out += f" {L['today']} ({mandi_name(a['best_now']['mandi'], lang)}): {rs(a['best_now']['net'] * a['qty'])}."
        return out + " -Sell Smart"
    if channel == "voice":
        unit = {"mr": "रुपये", "hi": "रुपये", "en": "rupees"}[lang]
        qtl = {"mr": "क्विंटल", "hi": "क्विंटल", "en": "quintal"}[lang]
        return f"{c}, {a['qty']:g} {qtl}. {act}. {rs(a['total']).replace('₹', '')} {unit}."
    b, q, L = a["bill"], f"{a['qty']:g}", lambda k, **kw: CARD[k][lang].format(**kw)
    dist = mandis()[p["mandi"]][2] if p["mandi"] in mandis() else ""
    dist = DISTRICT.get(dist, {}).get(lang, dist)
    lines = [f"🌾 *{c} · {q} {'quintal' if lang == 'en' else 'क्विंटल'}*", L("you", p=near_town(*a["farm"], lang)), "",
             L("sell_now") if a["action"] == "sell_now" else L("hold", d=p["days"]),
             L("mandi", m=m, dist=dist), L("road", km=p["km"], t=travel(p["hours"], lang)), L("date", d=when(p["date"], lang)), "",
             L("bill"),
             L("price_now", p=rs(p["p50"]), q=q, g=rs(b["gross"])) if not p["days"] else
             L("price_fc", p=rs(p["p50"]), q=q, g=rs(b["gross"]), lo=rs(p["p10"]), hi=rs(p["p90"]))]
    if b["spoil"]:
        lines.append(L("spoil", pc=round((1 - p["keep"]) * 100, 1), x=rs(b["spoil"])))
    t = p["transport"]
    lines.append(L("truck", km=p["km"], r=f"{t['rate']:g}", t=L("trips", n=t["trips"]) if t["trips"] > 1 else "", x=rs(b["truck"])))
    lines.append(L("handling", x=rs(b["handling"])))
    if b["interest"]:
        lines.append(L("interest", x=rs(b["interest"])))
    lines += ["━━━━━━━━━━━━", L("in_hand", x=rs(b["in_hand"])), ""]
    if a["action"] == "hold":
        bn = a["best_now"]
        lines.append(L("if_today", m=mandi_name(bn["mandi"], lang), x=rs(bn["net"] * a["qty"])))
        lines.append(L("gain", x=rs(b["in_hand"] - bn["net"] * a["qty"]), lo=rs(p["net_lo"] * a["qty"])))
    else:
        others = [o for o in a["options"] if o["mandi"] != p["mandi"]][:3]
        if others:
            lines.append(L("compare"))
            lines += [f"• {mandi_name(o['mandi'], lang)} ({o['km']} {'km' if lang == 'en' else 'किमी'}): {rs(o['net'] * a['qty'])}" for o in others]
    if a["perishable"]:
        lines.append(T["perishable"][lang])
    if a["pledge"]:
        lines.append(T["pledge"][lang])
    if a["below_msp"]:
        lines.append(T["msp"][lang].format(msp=f"{a['msp']:,.0f}"))
    lines += ["", CARD["conf"][a["confidence"]][lang], T["choice"][lang]]
    return "\n".join(lines)


if __name__ == "__main__":
    assert travel(1.8, "mr") == "1 तास 50 मिनिटे" and travel(0.3, "en") == "20 min"
    assert rs(123456) == "₹1,23,456" and rs(999) == "₹999" and rs(1234567) == "₹12,34,567"
    assert abs(prob_above(100, 90, 100, 110) - 0.5) < 1e-9 and prob_above(80, 90, 100, 110) > 0.9 and prob_above(120, 90, 100, 110) < 0.1
    print("advice self-checks ok")
