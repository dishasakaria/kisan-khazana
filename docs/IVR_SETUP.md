# Calling agent (IVR) — setup

Farmers with any phone call our ExoPhone and press keys:
language (1 मराठी · 2 हिंदी · 3 English) → crop (1 कांदा · 2 टोमॅटो · 3 सोयाबीन · 4 कापूस · 5 तूर · 6 हरभरा · 7 गहू · 8 बटाटा · 9 डाळिंब)
→ quintals then `#` → 6-digit pincode (skipped when the caller is already in `farmers` with a location)
→ advice is spoken (Sarvam TTS, 8 kHz MP3). Code: `ivr.py` (`app.include_router(ivr.router)` in `api.py`).

## 1. Exotel flow (laptop, ~10 min)

1. Exotel dashboard → **App Bazaar** → **Create** a new flow, name it `Sell Smart IVR`.
2. Add the applets in this order. Every Gather, Passthru and Greeting points at the **same** URL; the server knows
   from the call's state (by `CallSid`) what to ask next, and repeats a question if a key was wrong or missing.

   | # | Applet | Setting |
   |---|--------|---------|
   | 1 | **Gather** | choose *dynamic URL / "Use URL"*: `https://sell-smart.onrender.com/ivr/exotel/gather` |
   | 2 | **Passthru** | URL `https://sell-smart.onrender.com/ivr/exotel/passthru`, **Make Passthru Async: off**. *If 200 OK* → next Gather; *if 302* → the Greeting (row 11) |
   | 3–10 | repeat Gather + Passthru 4 more times (5 pairs: 4 questions + 1 retry) | last Passthru: both outcomes → Greeting |
   | 11 | **Greeting** | *Read text like a robot* → put only the URL `https://sell-smart.onrender.com/ivr/exotel/advice` |
   | 12 | **Hangup** | |

3. Save. Assign the flow to your ExoPhone (**ExoPhones** → number → *Connect to flow*). Note the flow's **app id**
   (the number in the flow's URL in App Bazaar) for step 3.

## 2. Trial limits

- A trial account only calls/receives **verified numbers** — add each demo phone under the dashboard's
  number verification / whitelist page first. Going live needs KYC.
- Calls cost trial credits; keep test calls short.
- Render's free plan sleeps: open `https://sell-smart.onrender.com/health` a minute before a live call.

## 3. Missed-call callback (optional)

Farmer gives a missed call → we ring back into the IVR (free for the farmer). Set on Render:
`EXOTEL_FLOW_ID=<app id of the IVR flow>`, `EXOTEL_CALLER_ID=<your ExoPhone>`, and if your account is on the
Mumbai cluster `EXOTEL_SUBDOMAIN=api.in.exotel.com` (default `api.exotel.com`). `EXOTEL_SID/API_KEY/API_TOKEN`
are already set. Then make a second flow on another ExoPhone: **Passthru** → `https://sell-smart.onrender.com/ivr/exotel/missed`
→ **Hangup**. One callback per number per 10 minutes. (Not tested end-to-end: needs a KYC'd account.)

## 4. Demo without Exotel: browser call simulator

Open **https://sell-smart.onrender.com/app/call.html** (works on a phone too). Press the green 📞, then the keys
(or the computer keyboard: digits, `#`, Enter to call, Esc to hang up). It plays the same prompts and the same
spoken advice through `POST /ivr/sim`; calls are logged in `queries` with channel `call` and appear in the live feed.
Try: `2` (हिंदी) → `1` (onion) → `50#` → `422001` (Nashik).

## Endpoints

| Route | Used by |
|-------|---------|
| `GET /ivr/exotel/gather` | Gather applet → JSON `{gather_prompt, max_input_digits, finish_on_key, input_timeout, repeat_menu, repeat_gather_prompt}` |
| `GET /ivr/exotel/passthru` | Passthru applet; reads `digits` (sent with quotes, e.g. `"2"`); 200 = ask next, 302 = done |
| `GET /ivr/exotel/advice` | Greeting applet → `text/plain`: MP3 URL (or the advice text if TTS failed) |
| `GET /ivr/exotel/missed` | missed-call flow → Exotel Connect API call-back |
| `GET /ivr/prompt/{lang}/{key}.mp3` | cached prompts (8 kHz; `?hq=1` 22 kHz for the browser) |
| `GET /ivr/say/{id}.mp3` | spoken advice (kept 1 hour) |
| `POST /ivr/sim` | `web/call.html` |

## What was verified in Exotel's docs (Oct 2026)

- Gather dynamic URL: GET with `CallSid`, `CallFrom`, `CallTo`, `digits`…; reply `application/json` with
  `gather_prompt` (`{"text": …}` or `{"audio_url": …}`), `max_input_digits` (default 255), `finish_on_key`
  (default `#`, `""` allowed), `input_timeout` (default 5 s), `repeat_menu`, `repeat_gather_prompt`; gathered
  digits reach the next applet as `digits` wrapped in double quotes —
  [Working with Gather Applet](https://support.exotel.com/support/solutions/articles/3000084635-working-with-gather-applet).
- Passthru: GET with `CallSid`, `From`, `To`, `digits`; sync mode branches on **200 OK** vs **302 Found** —
  [Working with Passthru Applet](https://support.exotel.com/support/solutions/articles/48283-working-with-passthru-applet).
- Greeting dynamic URL: GET with `CallSid`, `From`, `To`…; must reply `Content-Type: text/plain` (and answer HEAD
  with the same headers); body = text, or audio URLs one per line; audio **.wav/.mp3, 8 kHz mono, 16-bit**;
  Exotel caches audio by file name —
  [Greeting using dynamic text or audio from URL](https://support.exotel.com/support/solutions/articles/48285-greeting-using-dynamic-text-or-audio-from-url).
- Connect to flow: `POST https://api.exotel.com/v1/Accounts/<sid>/Calls/connect` with basic auth `api_key:api_token`,
  `From`, `CallerId`, `Url=http://my.exotel.com/<sid>/exoml/start_voice/<app_id>`, `CallType=trans` —
  [Connect Number to Call Flow](https://developer.exotel.com/docs/voice-v1/api-reference/connect-to-flow).

Not verified (no live account): whether Exotel follows a 302 without a `Location` header (we send none, as the
docs only ask for the status code), and how long Exotel waits for a dynamic URL — the advice is started in the
Passthru and the Greeting waits up to 25 s for it.
