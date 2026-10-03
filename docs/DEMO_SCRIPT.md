# Sell Smart + Kisaan Khazana — demo script (≈10 minutes)

Every number below comes from our own data and model reports (`models/report_v2b.md`, `models/lstm/report.md`,
`data/quality_report_state.txt`, and a trend analysis run on `data/clean_prices_state.csv`). Nothing is invented.
**SAY** = what to say. **SHOW** = what is on screen.

---

## 0. Hook (30 s)

**SHOW:** the advice card from Telegram (onion, 50 quintal, Pimpalgaon).

**SAY:** "A farmer in Niphad has 50 quintals of onion. Lasalgaon is 19 km away, Pimpalgaon is 20 km.
Same day, same onion — the difference in money in hand is ₹1,200. Across our pilot area the gap between the
best and the median onion mandi on the same day is typically **34%**. For this farmer that is ₹70,000.
Farmers lose this money not because they lack effort, but because they lack information at the moment of selling.
Sell Smart answers two questions in their own language: *where* to sell, and *when* — in rupees in hand, after
truck rent and hamali, with the uncertainty stated honestly."

---

## 1. Play the video (90 s)

**SHOW:** `video/pitch/sell_smart_pitch.mp4` (Ramu & Shamu).

**SAY (after):** "Everything in that video exists and works today. Let me show it live."

---

## 2. Telegram — the main farmer channel (2 min, live)

**SHOW:** phone screen mirrored. Clear chat → `/start`.

**SAY while tapping:**
- "Language first — मराठी, हिंदी, English." (tap मराठी) "A one-minute how-to video arrives in that language."
- "Name. Then location — one tap, or a pincode."
- "Crop is a list, quantity is a list. Bank-style menus: four taps, no typing. A farmer can also just **speak** —
  a Marathi voice note is transcribed by Sarvam and understood."
- (advice arrives) "Here is the card. Mandi name and district. Distance and travel time. The date to sell.
  Today's price × quantity, **minus truck rent at ₹25/km, minus hamali** — this is the line farmers care about:
  **हातात — in hand**. Below, the same calculation for the other mandis, so the farmer can see why.
  Then a map pin with directions, and the same advice as a voice note for farmers who do not read."
- "When waiting is better, the card says *wait 14 days*, shows the expected band, **and what happens if prices fall**.
  And always: निर्णय तुमचा — the decision is yours."
- Tap **📸 साठवण फोटो**: "Spoilage Clock — a photo of the stored onion. Gemini vision grades sprouting and rot,
  the engine converts that into a daily spoilage rate, and the *wait* advice becomes shorter for stock that will not keep."
- Tap **🤝 ट्रक शेअर**: "Farmers nearby going to the same mandi on the same day are matched to share one rented truck.
  In our test two farmers 3 km apart saved ₹425 on one trip."
- Tap **🏢 FPO ला द्या**: "Or hand the stock to the nearest FPO — I will come back to this."

---

## 3. SMS — feature phones (45 s, live if the gateway phone is on)

**SHOW:** send `START` from a basic phone to the SIM number.

**SAY:** "No smartphone, no internet — the same brain over SMS. START → language → name → pincode →
a numbered crop list → quintals → the advice in one message. The reply is sent by an ordinary Android phone with a
SIM, so it costs nothing to run. Every number here is the same engine; only the wording is shorter."

---

## 4. Phone call — IVR (45 s, live or recorded)

**SHOW:** call 09513886363 on speaker → press 1 → 2 → 50# → 422001.

**SAY:** "For a farmer who cannot read at all: a call. Keys, not speech — on a field with wind and a ₹1,000 handset a
pressed key is never misheard. The advice is spoken back in Marathi by Sarvam's voice model."

---

## 5. FPO + buyers — Kisaan Khazana (1.5 min)

**SHOW:** FPO dashboard (`/app/kk/`) on the laptop, buyer app on a phone.

**SAY:** "A single farmer with 50 quintals has no bargaining power. An FPO with 1,000 does.
Farmers tap *Give to FPO* on Telegram; the stock appears in the FPO's inventory here. The FPO bundles it into a lot —
the market reference price is pre-filled from our forecast — and publishes it.
Wholesale buyers, processors and exporters see the lot in the **Kisaan Khazana** app, filter by crop and distance,
and make an offer. The FPO sees *3 offers need your response*, accepts one — the database locks the lot during
acceptance so two buyers can never be sold the same quintal — and only then does the buyer get the FPO's phone.
Buyers never see an individual farmer. Our fee is 1% from each side, against 6–8% traditional commission."

---

## 6. The model — data, features, trends, results (3.5 min) ← most important

### 6a. Data (SHOW: the data table)

| Source | What | Size |
|---|---|---|
| Agmarknet daily mandi prices (via data.gov.in mirror) | min / max / modal per mandi × crop × variety | 48.5 lakh rows, Maharashtra, 2010–2025 |
| After cleaning | 406 mandis merged by name, duplicates/grades merged, 11k unit errors and 2.25 lakh stale copied values dropped | **39.2 lakh rows, 3,114 mandi–crop series, 129 crops, 339 mandis** |
| MSAMB (live, daily) | APMC + private markets + direct buyers | refreshed every evening by GitHub Actions |
| ERA5-Land weather per district | rain, max temp, humidity, soil moisture, evapotranspiration | 1.05 lakh district-days |
| Policy events (hand-verified) | export bans, MEP, duties, stock limits, buffer buying/release, APMC strikes, state subsidies | 99 dated events with source links |
| Macro | WPI, monthly exports (HS codes), World Bank food prices, USD/INR, diesel, MSP | monthly / daily |
| Calendar | Diwali, festivals, mandi closures | holidays table |

**SAY:** "Each row we train on is one mandi, one crop, one day. The target is **the log change in price 7, 14 and
21 days later** — not the price itself. Predicting a change forces the model to learn *drivers*, not just copy today's
price."

### 6b. Features (48) — what the model sees for each row

- **Momentum:** price change over 1, 7, 14, 28 days.
- **Mean reversion:** distance from the 7-day and 30-day average (`dev_ma7`, `dev_ma30`), 30-day volatility, year-on-year.
- **Cross-mandi:** `gap_crop` = this mandi vs the state-wide median for the crop that day; `crop_ret_7` = how the whole
  crop moved this week.
- **Season:** day-of-year as sine/cosine, weekday, days to Diwali (capped at 30).
- **Weather:** rain last 7/30 days, rain forecast next 7, max temp, humidity, soil moisture, drought index.
- **Policy:** export ban, export duty %, minimum export price, stock limit, buffer procurement/release, APMC strike,
  state subsidy; price vs MSP.
- **Macro:** WPI, export volumes, world prices, rupee, diesel.
- **Identity:** mandi and crop as categories (one global model learns all 3,114 series at once).

### 6c. Trends we found in 15 years of Maharashtra prices (SHOW: one slide per bullet if possible)

1. **Season is the biggest "when" signal — and it is crop-specific.**
   Onion index by month (100 = typical): Apr–May **59**, Oct **161**, Nov **185**. Tomato: Feb–Apr **72**, Jul **170**.
   Potato: Feb–Mar **76**, Jun–Nov **103**. Wheat, soybean, tur, gram: flat within ±6% — storage timing hardly matters.
   → The model's season features (`season_sin/cos`) are 10–13% of its decisions.

2. **Spikes mean-revert in grains, but NOT in onion.**
   When wheat is 20% above its 30-day average it falls over the next 21 days **91%** of the time (median −22%);
   soybean **82%** (−8.5%); potato 62%. **Onion: 46% — a coin toss.** Tomato: 50%.
   → This is why our model beats "price stays the same" on grains and tomato but **loses on onion** (20.8% vs 18.2%
   at 21 days). Onion in Maharashtra behaves like a random walk at the 3-week horizon: it is driven by news
   (export policy, rain on the kharif crop) rather than by its own past. We do not hide this: for onion the system
   caps confidence at *medium* and the safety rule falls back to "price stays the same" wherever that was better in 2024.

3. **Export policy is the onion shock.** Around the three export bans in our data:
   2019 ban: ₹2,350 → ₹4,400 (+87%); 2020 ban: ₹1,150 → ₹3,200 (+178%) — the bans *followed* price spikes.
   Dec-2023 ban: ₹3,500 → ₹1,400 (**−60%**) — the ban *crashed* prices. Same event type, opposite effect, which is
   exactly why a plain "ban = price down" rule is wrong and why we feed the flag to the model with the rest of the context.

4. **Diwali demand is real for tomato and pomegranate, not for onion.**
   Median price in the 30 days before Diwali vs after: tomato **+14%**, pomegranate +5%, onion **−14%**
   (kharif onion arrives then). → `days_to_diwali` is capped at 30 days; uncapped it acted as a hidden date counter
   and over-fitted (found in model v1).

5. **Where matters more than when for onion.** 2023–25, onion vs the state median on the same day:
   Manchar **+21%**, Junnar (Otur) +13%, Dindori (Vani) +13%, Pimpalgaon +11%, Lasalgaon +10% …
   Sangamner −21%, Rahuri −28%, Karjat −29%. Typical gap between the best and the median mandi: **34%**.
   But the best mandi today is still in the top 3 a week later only **45%** of the time — the ranking churns.
   → So "where" uses today's real prices at every mandi within 200 km, minus the real road distance and ₹25/km truck,
   and a far mandi must beat a near one by ₹0.5/quintal per extra km. Two of our top mandis, Manchar and Alephata,
   are in Pune district, not Nashik — that is a non-obvious finding for Nashik farmers.

6. **Weekday effects are negligible** (onion Tuesday −4%, soybean Sunday −5% on thin trading). We keep the
   feature; the model gives it almost no weight. Honest finding: no "sell on Monday" trick exists.

7. **Volatility ladder = confidence ladder.** Typical 21-day move: cotton 4%, soybean 5.5%, wheat 6%, gram 9%,
   potato 14%, pomegranate 25%, onion 35%, **tomato 50%**. Perishables are never advised to wait; the band shown to
   the farmer (P10–P90) is wide for tomato and narrow for wheat because the data says so.

8. **What the trained model actually leans on** (share of decisions, 21-day model): crop identity 23%, mandi identity
   14%, gap vs state median 10%, deviation from 7-day average 7%, season 13%, year-on-year 5%, diesel 5%,
   crop-wide weekly move 5%, price vs MSP 2%, rain forecast 1.3%. Weather in total ≈ 6%; policy flags < 1%
   (they are rare events, but they matter when they fire). Cross-mandi information — knowing what every other mandi
   did today — is the single biggest learned signal after identity.

### 6d. The model (SHOW: the results table)

**SAY:** "One global **LightGBM** model per horizon, trained as **quantile regression** — three models each for 7, 14 and
21 days: P10, P50, P90. So the farmer gets a *range*, not a false single number. We trained on everything before 2024,
tuned on 2024, and tested on **2025, which the model never saw** — 95,551 test cases at 7 days."

| Horizon | Our model | "Price stays the same" | "Same week in past years" | Real price inside our P10–P90 |
|---|---|---|---|---|
| 7 days | **15.5%** | 17.5% | 22.0% | 78% |
| 14 days | **18.7%** | 21.1% | 26.4% | 78% |
| 21 days | **21.1%** | 23.7% | 29.1% | 77% |

(Error = mean absolute percentage error of price.)

Per crop at 21 days, model vs "stays the same": tomato **26.7% vs 32.6%**, gram 4.8 vs 5.8, potato 11.3 vs 12.6,
wheat 4.1 vs 4.7, maize 4.8 vs 5.4, pomegranate 18.0 vs 19.7, soybean 4.1 vs 4.2, **onion 20.8 vs 18.2 (we lose)**.

**SAY:** "We also trained an **LSTM** on the same split as a challenger: 15.9 / 18.8 / 21.4% — LightGBM is slightly
better and 100× cheaper to run, but the LSTM's ranges were better calibrated (80–81% inside), so an ensemble is the
next step. A **safety rule**, chosen on 2024 data only, hands 24–26 thinly traded crops back to the simple forecast."

### 6e. From forecast to decision (SHOW: the formula)

```
₹ in hand(mandi, day) = qty × (1 − spoilage × days) × price(mandi, day)
                        − truck (₹25/km × road km, OSRM) − hamali (₹20/qtl) − interest on waiting
Hold only if:  P(hold beats selling today) ≥ 70%   AND   gain ≥ ₹50/qtl   AND   mandi open that day
Perishables: never hold.  Photo spoilage rate overrides the crop default.  Onion: confidence capped at medium.
```

**SAY:** "The probability comes from the three quantiles. The 70% bar is deliberate: a farmer who is told to wait and
loses, stops trusting you. We would rather say *sell today* too often than *wait* wrongly."

### 6f. Validated in real time, not just in backtest

**SAY:** "Every forecast is stored with its date. When the real mandi price arrives 7, 14, 21 days later, a database view
scores it. The FPO dashboard shows the live error per crop. Judges can check our record next month."

---

## 7. Close (30 s)

**SAY:** "Three channels — Telegram, SMS, a phone call — one honest brain. FPOs aggregate, buyers bid, nobody sells
the same quintal twice. We lose to the simple baseline on one crop and we say so on the card. Trust is the product.
निर्णय तुमचा."

---

## Q&A cheat sheet

- **Why Maharashtra?** Largest onion/tomato/pomegranate volumes, 339 active mandis, best data depth (15 years).
- **Why LightGBM over deep learning?** Equal or better on 2025 (15.5 vs 15.9%), trains in minutes on CPU, runs on a free
  server; LSTM kept as challenger with better-calibrated ranges.
- **Why predict the change, not the price?** Removes the trivial "copy today" solution; forces learning of drivers.
- **Why does onion lose?** 3-week onion moves are news-driven (export policy, kharif rain); 46% mean-reversion = coin toss.
  We cap confidence and fall back to persistence where 2024 showed it was better.
- **Data leakage?** Time split (train <2024, tune 2024, test 2025); monthly macro joined with a 1–2 month publication lag;
  live features use the Open-Meteo *forecast* for next-7-day rain, same as in training.
- **Transport cost?** ₹25/km rented truck (farmer input), real road km from OSRM, 100 qtl per truck.
- **Spoilage rates?** ICAR-CIPHET / DOGR ranges: perishables 1.5%/day, onion/potato 0.3%/day, grains 0.03%/day; photo can only raise it.
- **Privacy?** Farmer IDs only in private tables; public feed rounds locations to 0.1°; buyers never see farmers; FPO
  phone revealed only on an accepted offer; accept/reject runs as one locked database transaction.
- **Cost to run?** ₹0: Render free tier, Supabase free tier, GitHub Actions, Sarvam/Gemini/Groq free quotas, a SIM for SMS.
- **What we would do with more time?** Ensemble LSTM + LightGBM; add Azadpur (Delhi) prices and NDVI as leading
  indicators; per-mandi arrivals; a proper ₹-impact backtest of the hold rule over 2025.
