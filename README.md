# Sell Smart · Kisaan Khazana

**Where and when to sell — in rupees in hand.** A market advisor for Maharashtra farmers over Telegram, SMS and a phone
call, plus an FPO-to-wholesale-buyer marketplace (Kisaan Khazana) on top of it.

Live: https://sell-smart.onrender.com · Telegram: [@SellSmartKisanBot](https://t.me/SellSmartKisanBot) ·
FPO dashboard: https://sell-smart.onrender.com/app/kk/ · Price map: https://sell-smart.onrender.com/app/fpo.html ·
Buyer app (Android): [KisaanKhazana.apk](https://sell-smart.onrender.com/app/download/KisaanKhazana.apk)

## What it does

A farmer says *what crop, how much, where* — in Marathi, Hindi or English, by chat, SMS or a keypad call — and gets:

```
🌾 कांदा · 50 क्विंटल
✅ सल्ला: आजच विका
🏪 पिंपळगाव बसवंत बाजार समिती (नाशिक जिल्हा) · 🛣️ 20 किमी · सुमारे 20 मिनिटे
आजचा भाव ₹4,325/क्विंटल × 50 = ₹2,16,250
➖ ट्रक भाडे (20 किमी × ₹25): ₹500   ➖ हमाली/तोलाई: ₹1,000
💰 तुमच्या हातात: ₹2,14,750
📊 आज इतर बाजारात: लासलगाव (19 किमी) ₹2,13,525 · कळवण (71 किमी) ₹2,13,475
🟢 खात्री: जास्त · निर्णय तुमचा आहे 🙏
```

When waiting is better it says *wait 14 days*, shows the expected price band and what happens if prices fall.

- **Forecast:** LightGBM quantile models (P10/P50/P90) for 7, 14 and 21 days ahead, one global model over 3,114
  mandi–crop series. Tested on 2025 data the model never saw: error 15.5 / 18.7 / 21.1 % vs 17.5 / 21.1 / 23.7 % for
  "price stays the same"; real price inside the P10–P90 band 77–78 % (`models/report_v2b.md`). LSTM challenger in
  `models/lstm/` (15.9 / 18.8 / 21.4 %). Every forecast is stored and scored against the real price when it arrives
  (`forecast_scores` view in `sql/schema.sql`).
- **Decision:** ₹ in hand = qty × (1 − spoilage × days) × price − truck (₹25/km × road km via OSRM) − hamali − interest.
  Hold only if it beats selling today with ≥ 70 % probability and the mandi is open; perishables are never held;
  a far mandi must beat a near one by ₹0.5/qtl per extra km (`advice.py`, `transport.py`).
- **Channels:** Telegram bot with list menus, Marathi/Hindi voice notes (Sarvam, Groq fallback), a stock-photo
  "Spoilage Clock" (Gemini vision) and truck sharing between nearby farmers (`api.py`, `speech.py`, `spoilage.py`,
  `market.py`); SMS for feature phones via an Android phone + SIM (`sms_flow.py`); Exotel keypad IVR with spoken advice
  (`ivr.py`). Onboarding videos in all three languages (`web/video/`).
- **Kisaan Khazana:** farmers hand stock to their FPO on Telegram → the FPO bundles it into lots on the dashboard
  (`fpo_api.py`, `web/kk/`) → wholesale buyers bid in the Android app (`mobile/`) → the FPO accepts in one locked
  database transaction, so a lot can never be oversold → the buyer gets the FPO's contact. Buyers never see farmers.
  Fee 1 % from each side.
- **FPO price map:** CesiumJS 3D map of forecast prices per mandi, live farmer queries, carpools and member stock
  (`web/fpo.html`).

## Data

| Source | Used for |
|---|---|
| Agmarknet daily mandi prices 2010–2025 (data.gov.in mirror) | 39.2 lakh clean rows, 129 crops, 339 mandis (`fetch_history.py`, `clean.py`) |
| MSAMB live prices (APMC, private markets, direct buyers) | daily refresh via GitHub Actions (`msamb.py`) |
| ERA5-Land + Open-Meteo weather per district | rain, heat, soil moisture features (`weather.py`) |
| 99 hand-verified policy events (export bans, MEP, duties, subsidies) | `data/ext/events.csv`, `sources/` |
| WPI, exports, world prices, USD/INR, diesel, MSP, festivals | `features_ext.py` |

**Key findings** (details and the full demo script in `docs/DEMO_SCRIPT.md`): onion prices run from an index of 59 in
April–May to 185 in November, tomato peaks in July (170); price spikes mean-revert in grains (wheat 91 %, soybean 82 %)
but not in onion (46 %), which is why onion confidence is capped; export bans moved onion +87 % and +178 % (2019, 2020)
but −60 % (2023); the best and median onion mandi differ by 34 % on the same day (Manchar +21 %, Karjat −29 %).

## Repo map

| Path | What |
|---|---|
| `train.py`, `lstm.py`, `predict.py`, `features_ext.py` | model training, challenger, daily forecasts |
| `advice.py`, `transport.py` | decision engine, truck cost |
| `api.py` | FastAPI server: Telegram, SMS, buyer and FPO APIs |
| `ivr.py`, `sms_flow.py`, `speech.py`, `nlu.py`, `spoilage.py` | calling agent, SMS flow, voice, parsing, photo check |
| `market.py`, `fpo_api.py`, `web/kk/`, `mobile/` | FPO marketplace, dashboard, Android buyer app |
| `web/fpo.html` | public 3D price map |
| `sql/` | Supabase schema (v1–v4) |
| `.github/workflows/daily-data.yml` | daily data refresh |
| `test_kisaan_api.py`, `test_fpo_dashboard.py`, `test_spoilage.py` | end-to-end tests against the real database |
| `docs/` | demo script, IVR setup, screenshots, QR codes |
| `video/` | onboarding videos (mr/hi/en) and the pitch video |

Setup details: `README_KISAAN_KHAZANA.md` (buyer app + API), `README_FPO_DASHBOARD.md` (dashboard),
`docs/IVR_SETUP.md` (calls), `MANUAL_TASKS.md` (accounts and keys — all secrets live in environment variables; none
are in the repo).

## Run locally

```bash
pip install -r requirements.txt
# create .env with: SUPABASE_URL, SUPABASE_SERVICE_KEY, TELEGRAM_BOT_TOKEN, SARVAM_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, PUBLIC_URL
uvicorn api:app --reload
python predict.py                # refresh forecasts (needs the price history in data/)
```