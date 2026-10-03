"""SMS conversation, same order as the Telegram bot: START -> language -> name -> pincode -> crop (numbered list)
-> quintals -> advice. Works on any phone: every answer is a number or a word.
Step is kept in memory per number and rebuilt from the farmer's saved row after a restart.
"""
import api, nlu
from api import CROP_MENU, crop_label, farmer, pincodes, save_farmer

STEP = {}  # "sms:+91..." -> lang | name | pin | crop | qty ; ponytail: in-memory, fine on one Render instance
LANGS = {"1": "mr", "2": "hi", "3": "en"}
T = {
    "lang": "Sell Smart 🙏 भाषा निवडा / भाषा चुनें / Choose language:\n1 मराठी\n2 हिंदी\n3 English",
    "name": {"mr": "नमस्कार 🙏 सेल-स्मार्ट. तुमचे नाव पाठवा.", "hi": "नमस्ते 🙏 सेल-स्मार्ट। अपना नाम भेजें।",
             "en": "Welcome to Sell Smart 🙏 Please send your name."},
    "pin": {"mr": "धन्यवाद {n}! तुमचा 6 अंकी पिनकोड पाठवा.", "hi": "धन्यवाद {n}! अपना 6 अंकों का पिनकोड भेजें।",
            "en": "Thank you {n}! Send your 6-digit pincode."},
    "bad_pin": {"mr": "पिनकोड सापडला नाही. 6 अंकी पिनकोड पाठवा, उदा. 422001", "hi": "पिनकोड नहीं मिला। 6 अंकों का पिनकोड भेजें, जैसे 422001",
                "en": "Pincode not found. Send a 6-digit Maharashtra pincode, e.g. 422001"},
    "crop": {"mr": "कोणते पीक? क्रमांक पाठवा:", "hi": "कौन सी फसल? नंबर भेजें:", "en": "Which crop? Send the number:"},
    "qty": {"mr": "{c} — किती क्विंटल? आकडा पाठवा, उदा. 50", "hi": "{c} — कितने क्विंटल? अंक भेजें, जैसे 50",
            "en": "{c} — how many quintals? Send a number, e.g. 50"},
    "next": {"mr": "नवीन सल्ल्यासाठी पिकाचा क्रमांक पाठवा. सुरुवातीपासून: START", "hi": "नई सलाह के लिए फसल का नंबर भेजें। शुरू से: START",
             "en": "For new advice send a crop number. To start over: START"},
}


def crop_list(lang):
    return T["crop"][lang] + "\n" + "\n".join(f"{i + 1} {crop_label(c, lang)}" for i, (c, _) in enumerate(CROP_MENU))


def current_step(uid, f):
    if uid in STEP:
        return STEP[uid]
    if not f or not f.get("lang"):
        return "lang"
    return "name" if not f.get("name") else "pin" if f.get("lat") is None else "crop"


def reply(uid, text):
    text = (text or "").strip()
    f = farmer(uid)
    if text.upper() in ("START", "RESET", "HELP", "MENU", "HI", "HELLO", "नमस्कार", "नमस्ते") or not f:
        save_farmer(uid, lang=None, name=None, lat=None, lon=None, last_crop=None, last_qty=None)
        STEP[uid] = "lang"
        return T["lang"]
    lang = f.get("lang") or "mr"
    step = current_step(uid, f)
    if step == "lang":
        if text[:1] not in LANGS:
            return T["lang"]
        lang = LANGS[text[:1]]
        save_farmer(uid, lang=lang)
        STEP[uid] = "name"
        return T["name"][lang]
    if step == "name":
        save_farmer(uid, name=text[:40])
        STEP[uid] = "pin"
        return T["pin"][lang].format(n=text[:40])
    if step == "pin":
        pin = nlu.parse(text)["pin"] or "".join(ch for ch in text if ch.isdigit())
        if pin not in pincodes():
            return T["bad_pin"][lang]
        lat, lon = pincodes()[pin]
        save_farmer(uid, lat=lat, lon=lon)
        STEP[uid] = "crop"
        return crop_list(lang)
    if step == "crop":
        if text.isdigit() and 1 <= int(text) <= len(CROP_MENU):
            crop = CROP_MENU[int(text) - 1][0]
        else:
            p = nlu.parse(text)
            if p["crop"] and p["qty_qtl"]:  # "कांदा 50" in one message also works
                STEP[uid] = "crop"
                return api.answer(uid, text, "sms")[0] + "\n\n" + T["next"][lang]
            if not p["crop"]:
                return crop_list(lang)
            crop = p["crop"]
        save_farmer(uid, last_crop=crop)
        STEP[uid] = "qty"
        return T["qty"][lang].format(c=crop_label(crop, lang))
    # step == "qty"
    p = nlu.parse(text)
    if not p["qty_qtl"]:
        return T["qty"][lang].format(c=crop_label(f.get("last_crop") or "", lang))
    STEP[uid] = "crop"
    return api.answer(uid, text, "sms")[0] + "\n\n" + T["next"][lang]
