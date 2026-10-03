# Manual tasks — laptop only (no calls, no emails)

Upload every file to GitHub: open the repo → folder → **Add file → Upload files → Commit changes**.
🔴 do first · 🟡 if time · 🟢 nice to have

## A. Settings (5 minutes)
| ✔ | Prio | Where | Do this |
|---|---|---|---|
| [ ] | 🔴 | Render → sell-smart → Environment | Add `SARVAM_API_KEY` (your Sarvam key) and check `PUBLIC_URL` = `https://sell-smart.onrender.com` → Save → Manual Deploy |
| [ ] | 🔴 | Telegram app → search **@BotFather** → `/newbot` → name `Sell Smart` → username e.g. `SellSmartKisanBot` → copy the token | Put it in Render → Environment as `TELEGRAM_BOT_TOKEN` → Save → Deploy (the bot connects itself) |
| [ ] | 🔴 | RapidAPI dashboard → the mandi API → **Endpoints** tab | Copy the endpoint names (not the key) and note them for the team |
| [ ] | 🔴 | Render → Environment | Add `GEMINI_API_KEY` (for the Spoilage Clock photo feature) and `GROQ_API_KEY` if missing → Save → Deploy |
| [ ] | 🔴 | Supabase → SQL Editor → New query → paste `sql/schema_v2.sql` → Run | Turns on marketplace, buyers, offers, carpool |
| [ ] | 🟡 | GitHub repo → Settings → Secrets and variables → Actions → New repository secret | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` → then Actions → "Daily data refresh" → Run workflow |

## A2. Real phone calls (Exotel trial, ~15 min) — see docs/IVR_SETUP.md
| ✔ | Prio | Do this |
|---|---|---|
| [ ] | 🔴 | Verify your phone: give a missed call to 09513885656 from your registered number |
| [ ] | 🔴 | Exotel → Settings → Whitelist Numbers: add each demo phone (OTP) — max 10 on trial |
| [ ] | 🔴 | App Bazaar → Create flow "Sell Smart IVR" exactly as docs/IVR_SETUP.md §1 → Save → connect it to the trial number |
| [ ] | 🔴 | Test: call 09513886363 from your registered phone (others type the PIN = your registered mobile number) |

## A3. SMS agent (Android phone + SIM + MacroDroid, ~10 min)
| ✔ | Prio | Do this |
|---|---|---|
| [ ] | 🔴 | Render → Environment: add `SMS_PHONE_KEY` = any long random word you make up → Save → Deploy |
| [ ] | 🔴 | On the SIM phone: install **MacroDroid** (Play Store) → Add Macro |
| [ ] | 🔴 | Trigger: **SMS Received** → Any number → Any content |
| [ ] | 🔴 | Action 1: **HTTP Request** → POST `https://sell-smart.onrender.com/sms/phone` · Header `X-Key: <your SMS_PHONE_KEY>` · Body (application/json): `{"from":"[sms_number]","text":"[sms_message]"}` · Save response to new string variable `reply` |
| [ ] | 🔴 | Action 2: **Send SMS** → To: `[sms_number]` · Message: `{v=reply}` · Constraint: variable `reply` is not empty |
| [ ] | 🔴 | Battery → Unrestricted for MacroDroid; test from another phone: `कांदा 50 422001` |

## B. data.gov.in (blocked from the cloud server; works in your browser)
On each dataset page: **Download → CSV** (name/email/purpose "academic research" if asked). Upload to `uploads/datagov/`.
| ✔ | Prio | Type this in the data.gov.in search box | Why |
|---|---|---|---|
| [ ] | 🔴 | `Variety-wise Daily Market Prices Data of Commodity` (Maharashtra, Jan–Oct 2026) | Fills the 2026 price gap (Agmarknet is down) |
| [ ] | 🔴 | `Current Daily Price of Various Commodities from Various Markets` | Today's prices cross-check |
| [ ] | 🔴 | `District wise Season wise Crop Production Statistics` | Supply per district & crop |
| [ ] | 🟡 | `Kisan Call Centre` (query data, Maharashtra) | Real farmer questions to test the bot |
| [ ] | 🟡 | `Live storage of reservoirs` | Dam levels (drought / rabi onion) |
| [ ] | 🟡 | `Cold storage` | Hold advice: where storage exists |
| [ ] | 🟢 | `Minimum Support Price` · `Agricultural Produce Market Committee` | Cross-checks |

## C. Websites to open in your browser
| ✔ | Prio | Do this | Upload to |
|---|---|---|---|
| [ ] | 🔴 | eNAM: open https://enam.gov.in/dashboard/live_price → F12 → Console → paste `scripts/enam_console.js` → Enter (retry if it says error 500) | `uploads/enam/` |
| [ ] | 🟡 | Dam storage: https://wrd.maharashtra.gov.in → reservoir/dam storage report (latest PDF) | `uploads/dams/` |
| [ ] | 🟡 | MSWC warehouse map: https://www.google.com/maps/d/viewer?mid=1CbrbZaMccrpZppivV24E2s3-VFtw3bhw → ⋮ menu → Download KML | `uploads/warehouses/` |
| [ ] | 🟡 | Maharashtra GRs: https://gr.maharashtra.gov.in → search `कांदा अनुदान` (onion subsidy 2026) → download PDFs | `uploads/policy/` |
| [ ] | 🟢 | Old export-policy PDFs: https://www.dgft.gov.in/CP/?opt=notification → filter 2019–2022 → notifications 31/2015-20, 06/2015-20, 39/2015-20 | `uploads/policy/` |
| [ ] | 🟢 | Transport rates: open https://porter.in or https://www.vahak.in and note the price for 5 routes (e.g. Niphad→Lasalgaon, Narayangaon→Pune) for Tata Ace / pickup / truck → note the numbers for the team | — |

## D. For the demo
| ✔ | Prio | Task |
|---|---|---|
| [ ] | 🟡 | Record the 60-second onboarding video on your phone (script in docs/DEMO_SCRIPT.md) and upload it to `uploads/video/` |
| [ ] | 🔒 | After the hackathon: regenerate ALL API keys that were pasted in chat (Supabase, Groq, Gemini, Twilio, Exotel, Sarvam, RapidAPI) |
