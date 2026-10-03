# Kisaan Khazana — buyer app (Android) + FPO API

**Kisaan Khazana** — *Buy directly from trusted FPOs.* Trade buyers (wholesalers, processors, exporters, FPO
procurement teams) buy **only from FPOs** (Farmer Producer Organisations). They never see or contact individual farmers.
The backend and the farmer channels keep the **Sell Smart** name (FastAPI on Render, Telegram bot, SMS, IVR).

## Flow

```
Farmer (Telegram)  advice -> "🏢 Give to FPO"
   └─► stock lands in the nearest active FPO's inventory (≤ 60 km; table `listings` + fpo_id), farmer becomes a member
FPO dashboard (web/kk/, built separately on the /api/fpos/* contract below)
   └─► pick member stock of one crop -> lot (total, asking price, market reference from our model, quality, pickup point)
Buyer app (Kisaan Khazana, mobile/)
   └─► browse/search/filter open lots -> offer (qty, ₹/quintal) -> total + 1% buyer fee computed on the server
FPO dashboard -> Accept / Reject  ──► SQL function accept_offer(): locks the lot row, checks qty, decrements, marks sold at 0
Buyer app polls (on focus + every 20 s) -> accepted: FPO name, phone, pickup point, Call / WhatsApp
Farmers in the lot get a Telegram note when part of it sells (no buyer details).
```

Privacy rules enforced in the API (not just the UI): buyer endpoints never return farmer ids, names, phones or
per-farmer quantities; an FPO's phone/address appear only inside that buyer's accepted offer; buyers and FPOs are
identified only by their bearer token, never by ids in the request body. `/api/stock` (public dashboard) returns totals per crop and district only.

## Architecture

- **Backend**: `api.py` (routes), `market.py` (marketplace logic), Supabase via PostgREST with the service key (server only).
  Passwords and PINs are hashed with scrypt; tokens are random 32-byte URL-safe strings; login attempts are rate-limited.
- **FPO dashboard**: built separately (`fpo_api.py`, `web/kk/`) on top of the `/api/fpos/*` endpoints below.
- **App** (`mobile/`): Expo SDK 57, React Native 0.86, TypeScript strict, expo-router.
  - `src/app/`: `welcome` (language, Create account / Log in), `(tabs)/index` (Home: lots, search, filter sheet, sort),
    `(tabs)/offers` (All / Pending / Accepted / Rejected), `(tabs)/profile` (edit, location, language, about, how it works,
    support, logout, version), `lot/[id]` (lot + About this FPO), `make-offer/[id]` (live total + fee preview),
    `offer/[id]` (status; `?sent=1` is the success state built from the server's response), `profile-edit`.
  - `src/lib/`: `api.ts` (typed client), `session.tsx` (token in expo-secure-store, cached profile, language; any 401 logs out to the welcome screen),
    `i18n.ts` (every string, mr/hi/en), `format.ts` (₹ Indian grouping, dates, API error code -> text), `theme.ts`, `usePoll.ts`.
  - `src/components/`: `ui.tsx` (text, buttons, chips, cards, sheet, skeletons, status pills with icon + text), `BuyerForm`,
    `LocationPicker` (GPS asked only on tap; offline pincode / district fallback from `src/geo/`), `LotCard`.
  - Fonts Mukta (Devanagari) + Inter; icons Ionicons only; brand mark `assets/logo.svg` (icons rendered from it).
  - `plugins/with-release-signing.js` signs release builds from Gradle properties (keystore never in the repo).

## Environment variables (names only)

| Where | Name | Notes |
|---|---|---|
| app (`mobile/.env`, build time) | `EXPO_PUBLIC_API_BASE_URL` | defaults to `https://sell-smart.onrender.com` |
| app (optional) | `EXPO_PUBLIC_SUPPORT_EMAIL`, `EXPO_PUBLIC_SUPPORT_PHONE` | Support buttons appear only when set |
| backend (Render / `.env`) | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | server only |
| backend | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `PUBLIC_URL` | farmer bot |
| APK signing (Gradle props) | `SS_STORE_FILE`, `SS_STORE_PASSWORD`, `SS_KEY_ALIAS`, `SS_KEY_PASSWORD` | `-P…` or `ORG_GRADLE_PROJECT_…` |

## Database migrations (Supabase → SQL Editor → paste → Run; all safe to re-run)

1. `sql/schema_v3.sql` (contact phone, buyer company, indexes) — already applied.
2. **`sql/schema_v4.sql`** — `fpos`, `fpo_members`, `fpo_lots`, `fpo_lot_items`; `listings.fpo_id` (farmer inventory);
   offers get `fpo_lot_id, total_value, buyer_fee, accepted_at, rejected_at` + qty/price checks + one pending offer per buyer per lot;
   buyers get `location_text, pin_hash` (the DB check also allows `individual`; the API accepts only `wholesale | processor | exporter | fpo`);
   functions `accept_offer(offer, fpo)` / `reject_offer(offer, fpo)` (row lock, one transaction; execute revoked from anon).

## API

Auth header: `Authorization: Bearer <token>`. Errors: `{"detail": "<code>"}` — 400 `bad_*`, 401 `register_first | login_first | bad_login`,
404 `not_found`, 409 `duplicate | phone_taken | duplicate_offer | lot_closed | insufficient_qty | not_pending | items_taken | bad_status`, 429 `too_many`.

Buyers (app)

| Method | Path | Body / query | Returns |
|---|---|---|---|
| POST | `/api/buyers` | `{name, company?, type, phone, lat, lon, location_text?, pin (4–6 digits)}` | `{buyer_token, buyer}` |
| POST | `/api/buyers/login` | `{phone, pin}` | `{buyer_token, buyer}` (10 tries/hour per phone) |
| GET / PATCH | `/api/buyers/me` | profile fields | buyer |
| GET | `/api/fpo-lots` | `q, crop, radius_km, min_price, max_price, min_qty, sort=nearest\|newest\|price_asc\|price_desc\|qty_desc, page, limit` | `{items, total, page, limit, has_more, crops}` |
| GET | `/api/fpo-lots/{id}` | | lot + `fpo {id, name, district}` + `farmers_n` + `my_offer` |
| POST | `/api/offers` | `{fpo_lot_id, qty_qtl, price_rs_qtl}` | `{offer_id, status, offer}` |
| GET | `/api/offers`, `/api/offers/{id}` | | this buyer's offers; `fpo_contact` only when accepted |

FPOs (dashboard contract — identity from the FPO token only)

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/fpos` | `{name, phone, email?, password (≥8), address, lat, lon}` | `{fpo_token, fpo}` |
| POST | `/api/fpos/login` | `{login: phone or email, password}` | `{fpo_token, fpo}` |
| GET / PATCH | `/api/fpos/me` | profile fields, `password` | fpo |
| GET | `/api/fpos/inventory` | | member stock (farmer name, crop, qty, status) |
| GET | `/api/fpos/reference-price?crop=` | | `{price, market, date}` from the latest model run |
| GET / POST | `/api/fpos/lots` | `{inventory_ids[], asking_price_rs_qtl, market_reference_price?, quality?, location?, notes?, publish}` | lots / new lot |
| PATCH | `/api/fpos/lots/{id}` | `{status: open\|closed, asking_price_rs_qtl?, quality?, notes?, location?}` | lot |
| GET | `/api/fpos/offers` | | offers on this FPO's lots (buyer phone only once accepted) |
| POST | `/api/fpos/offers/{id}/accept` · `/reject` | | `{ok, available, lot_status}` or 409 |

## Build the APK

Prerequisites: Node 20+, JDK 17 or 21, Android SDK (platform 36, build-tools 36.0.0, NDK 27.1.12297006, cmake 3.22.1).

```bash
cd mobile
npm ci                                  # .npmrc sets legacy-peer-deps (optional react-dom peer of expo-router)
npx tsc --noEmit
npx expo export -p android              # proves the JS bundles
npx expo prebuild -p android --clean    # android/ is generated and git-ignored
cd android
ANDROID_HOME=/path/to/android-sdk ./gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a,armeabi-v7a \
  -PSS_STORE_FILE=/outside/repo/kisaankhazana-release.p12 -PSS_STORE_PASSWORD=… -PSS_KEY_ALIAS=kisaankhazana -PSS_KEY_PASSWORD=…
# -> android/app/build/outputs/apk/release/app-release.apk
```

Keystore (once; keep it and its password safe outside the repo — every update must be signed with the same key):
`keytool -genkeypair -storetype PKCS12 -keystore kisaankhazana-release.p12 -alias kisaankhazana -keyalg RSA -keysize 2048 -validity 10000`.
Without the `SS_*` properties the release APK is signed with the debug key. Cloud alternative: `npx eas-cli build:configure`
then `npx eas-cli build -p android` (needs an Expo account / `EXPO_TOKEN`).

## Tests

`python test_kisaan_api.py` — real Supabase (needs `.env` and schema_v4), Telegram captured, deletes every test row.
Covers FPO register/login (scrypt hash stored, wrong password), farmers' "Give to FPO" (nearest FPO, none within 60 km,
double tap), inventory per FPO, lot creation rules (other FPO's stock, already-used stock, price), buyer register/login
(PIN rules, duplicate phone), search/filter/sort/pagination, draft lots hidden, offer validation and duplicates,
cross-buyer and cross-FPO authorization, a **concurrent 20 + 30 qtl accept race on a 40 qtl lot** (exactly one wins,
the other gets 409 `insufficient_qty`), contact only after accept, reject path, sell-out, closing an unsold lot, and a scan
of every buyer response for farmer data.

On a phone: register an FPO (FPO dashboard or `POST /api/fpos`); on Telegram as a farmer near it get advice ("कांदा 50 क्विंटल") and tap
**🏢 FPO ला द्या**; make a lot from that stock and publish it; in the app find it on Home, make an offer; accept it
from the FPO side; within ~20 s the app's Offers tab shows Accepted with Call / WhatsApp for the FPO.
