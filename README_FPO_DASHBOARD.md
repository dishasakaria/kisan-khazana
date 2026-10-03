# Kisaan Khazana — FPO dashboard (`web/kk/`, `fpo_api.py`)

The web dashboard an FPO (Farmer Producer Organisation) uses to turn its members' produce into lots, answer buyer offers
from the Kisaan Khazana Android app, and see what sold. Live at `https://sell-smart.onrender.com/app/kk/`.

```
Farmer (Telegram "Give to FPO")  ──►  listings (fpo_id, status open)        FPO inventory, FPO-private
FPO dashboard: Create lot          ──►  fpo_lots (draft) + fpo_lot_items     listings -> in_lot
FPO dashboard: Publish             ──►  fpo_lots.status = open               visible in the buyer app (/api/fpo-lots)
Buyer app: offer                   ──►  offers (fpo_lot_id, status sent)
FPO dashboard: Accept / Reject     ──►  SQL accept_offer / reject_offer      lot row locked -> no overselling
Buyer app (polls)                  ──►  accepted: sees the FPO's phone / pickup point; farmers get a Telegram note
```

Buyers never see farmers. Farmer names, ids, phones and per-farmer quantities only ever travel through `/api/fpos/*`
routes, which are authenticated with the FPO's bearer token.

## Architecture

| Piece | What | Where |
|---|---|---|
| Backend (shared) | FastAPI app, Supabase via PostgREST with the service key (server only) | `api.py`, `market.py`, `db.py` |
| FPO auth + core routes | register/login (scrypt), `/me`, inventory, reference price, lots create/patch, offers list, accept/reject | `api.py` (`_fpo`, `_call`), `market.py` |
| Dashboard read models + lot actions | `APIRouter(prefix="/api/fpos")`, mounted with `app.include_router(fpo_api.router)` | `fpo_api.py` |
| Frontend | vanilla ES-module SPA, no build step, served as static files at `/app/kk/` | `web/kk/` |
| Tests + screenshots | real Supabase, Telegram captured, Playwright | `test_fpo_dashboard.py`, `docs/screens/kk/` |

`fpo_api.py` imports `api` lazily (inside functions) because `api.py` imports `fpo_api` to mount the router. It adds only
routes `api.py` does not have; nothing is overridden. There are no new tables (`sql/schema_v4.sql` is the current schema):
transactions are accepted offers, notifications are derived from pending offers + stock and lots changed this week.

### Frontend files

| File | Role |
|---|---|
| `index.html` | shell, `<base href="/app/kk/">`, Google Fonts (Inter + Mukta), Chart.js 4.5 from cdnjs |
| `app.js` | hash router (`#/overview`, `#/lots/12`, `#/offers?status=pending` …), sidebar/topbar shell, notifications popover, 30 s pending-offer badge poll |
| `pages.js` | every page: login, register, overview, inventory (+ per-crop drawer), farmers (+ profile), lots (+ detail, 4-step create wizard, edit), offers (+ detail with accept/reject), transactions (+ detail), reports (Chart.js), settings |
| `ui.js` | `api()` fetch wrapper (bearer token, 20 s timeout, error-code mapping, 401 → login), formatting (₹ Indian grouping, dates), status badges (icon + text), table/pager/tabs builders, confirm dialog, toast, skeletons, `busy()` double-submit guard, `poll()` |
| `i18n.js` | every string in मराठी / हिंदी / English (`t(key)`), crop names, language persisted in `localStorage.kk_lang` |
| `icons.js` | inline Lucide SVG subset (the only icon set; no emoji) |
| `kk.css` | design tokens (warm off-white, deep green accent, 8/12/16 px radii), components, responsive rules (sidebar ≥ 1024 px, drawer nav below, stacked tables < 720 px) |
| `favicon.svg` | brand mark |

## FPO workflow in the dashboard

1. **Register / log in** (`#/register`, `#/login`): name, phone, optional email, password (≥ 8), address, lat/lon ("Use my location" asks for GPS only on tap). Token is kept in `localStorage.kk_token`; any 401 logs out.
2. **Overview**: greeting, "N buyer offers need your response" strip, metrics (available produce, open lots, pending offers, sold this month), inventory by crop, active lots, recent offers, quick actions.
3. **Inventory**: one row per crop (total, available, in lots, farmers, status, updated); click → drawer with each farmer's stock entry; entries link to the farmer profile.
4. **Farmers**: members (name, village / nearest town, phone or "via Telegram", primary crop, available qty, last updated), search + crop filter, profile with stock entries and lots.
5. **FPO Lots**: tabs All / Open / Draft / Sold / Closed, search; lot ids like `ON-012` (two letters of the crop + id). **Create lot** wizard: crop → tick stock entries (each goes in whole) → asking price with today's model price for the nearest forecast mandi prefilled (`/api/fpos/reference-price`) → quality / pickup / notes → *Save as draft* or *Create and publish*. Lot page: Publish, Pause (open → draft, refused while offers are pending), Close (rejects pending offers; unsold stock returns to inventory), Edit (price / quality / pickup / notes), contributors, offers.
6. **Buyer Offers**: tabs New (last 24 h) / Pending / Accepted / Rejected / All, search, crop filter. Detail: buyer, lot, qty, price, total, 1 % buyer fee, submitted. **Accept** / **Reject** open a confirmation and then call the SQL functions through the API; `409 insufficient_qty` shows "That lot no longer has enough quantity available." The buyer's phone appears only after acceptance.
7. **Transactions**: accepted offers (date, buyer, lot, crop, qty, price, total); detail with buyer contact (Call / WhatsApp) and the farmers whose stock was in the lot.
8. **Reports**: quantity sold, value, average price, deals; sales by crop and by month (bar charts + tables), farmer contribution (given / in sold lots), top buyers. "Not enough data yet" until the first accepted offer.
9. **Settings**: edit profile (name, phone, email, address, district, lat/lon, new password), language, log out.

Live feel: Overview, Inventory, Lots, Offers and the lot / offer pages refetch on window focus and every 20 s; the sidebar's
pending-offer badge refreshes every 30 s. There is no Supabase Realtime: every table is private (RLS on, no policies), so
only the server reads them.

## Setup / local dev

```bash
pip install -r requirements.txt        # fastapi, uvicorn
# .env (names only): SUPABASE_URL, SUPABASE_SERVICE_KEY  (+ TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, PUBLIC_URL for the bot)
uvicorn api:app --reload               # http://<host>:8000/app/kk/
```

The API is same-origin, so the SPA needs no configuration. Deployment: Render auto-deploys `main`; `api.py` mounts
`web/` with `StaticFiles(html=True)`, so `web/kk/index.html` is served at `/app/kk/`.

## Auth

`Authorization: Bearer <fpo_token>` on every `/api/fpos/*` call (token from `POST /api/fpos` or `POST /api/fpos/login`;
stored on the `fpos` row; passwords are scrypt hashes). The FPO is derived only from the token; ids in the URL are
always filtered by `fpo_id`, so another FPO's lot / offer / farmer / stock entry answers `404 not_found`.

## API contract

Errors are `{"detail": "<code>"}`: `400 bad_input | bad_price | bad_items | mixed_crops | bad_name | bad_phone | bad_email |
bad_password | bad_location`, `401 login_first | bad_login`, `404 not_found`, `409 duplicate | items_taken | lot_closed |
insufficient_qty | not_pending | bad_status | pending_offers`, `429 too_many`. The SPA maps every code (and network / timeout /
5xx) to a sentence in the chosen language (`i18n.js`, keys `e_*`).

Status values: stock entry (`listings.status`) `open | in_lot | sold`; lot `draft | open | sold | closed`; offer
`sent | accepted | rejected`.

### Routes from `api.py` the dashboard uses

| Method | Path | Body / query → returns |
|---|---|---|
| POST | `/api/fpos` | `{name, phone, email?, password, address?, district?, lat, lon}` → `{fpo_token, fpo}` |
| POST | `/api/fpos/login` | `{login: phone or email, password}` → `{fpo_token, fpo}` |
| GET / PATCH | `/api/fpos/me` | profile fields, `password?` → fpo `{id, name, phone, email, address, district, lat, lon, status, created_at}` |
| GET | `/api/fpos/reference-price?crop=` | `{price, market, date}` or `{}` |
| POST | `/api/fpos/lots` | `{inventory_ids[], asking_price_rs_qtl, market_reference_price?, quality?, location?, notes?, publish}` → lot |
| PATCH | `/api/fpos/lots/{id}` | `{asking_price_rs_qtl?, quality?, notes?, location?, status?}` → lot |
| POST | `/api/fpos/offers/{id}/accept` · `/reject` | → `{ok, available, lot_status}` or 409 |

### Routes added in `fpo_api.py`

| Method | Path | Query | Returns |
|---|---|---|---|
| GET | `/api/fpos/dashboard` | | `{fpo, metrics{available_qty_qtl, in_lot_qty_qtl, open_lots, draft_lots, pending_offers, sold_qty_month, sold_value_month, farmers}, inventory_by_crop[], recent_offers[5], active_lots[5], generated_at}` |
| GET | `/api/fpos/notifications` | | `{items[≤30]{type: offer|inventory|sold, at, …}, pending_offers}` |
| GET | `/api/fpos/inventory/by-crop` | | `[{crop, total_qty_qtl, available_qty_qtl, in_lot_qty_qtl, sold_qty_qtl, farmers_n, status: available|in_lot|sold, updated_at}]` |
| GET | `/api/fpos/inventory/items` | `crop, status, q, page, limit≤100` | page of `{id, crop, qty_qtl, condition, ready_date, status, created_at, district, farmer_id, farmer_name, channel}` |
| GET | `/api/fpos/inventory/{id}` | | item + `farmer` + `lots[]` |
| GET | `/api/fpos/farmers` | `q, crop, page, limit` | page of `{farmer_id, name, channel, phone, lang, district, town{en,mr,hi}, primary_crop, available_qty_qtl, in_lot_qty_qtl, sold_qty_qtl, items_n, updated_at}` |
| GET | `/api/fpos/farmers/{farmer_id}` | | farmer + `items[]` + `lots[]` (with `farmer_qty_qtl`) |
| GET | `/api/fpos/lots/search` | `status, crop, q, page, limit` | page of lot + `{code, sold_qty_qtl, pending_offers, accepted_offers}` |
| GET | `/api/fpos/lots/{id}` | | lot + `items[]`, `contributors[]`, `offers[]` |
| POST | `/api/fpos/lots/{id}/publish` | | draft → open (409 `bad_status` otherwise) |
| POST | `/api/fpos/lots/{id}/unpublish` | | open → draft; 409 `pending_offers` while offers are pending |
| POST | `/api/fpos/lots/{id}/close` | | draft/open → closed; pending offers rejected; unsold stock back to `open` |
| GET | `/api/fpos/offers/search` | `status: new|pending|accepted|rejected, crop, q, page, limit` | page of `{offer_id, lot_id, code, crop, lot_status, lot_available_qty_qtl, qty_qtl, price_rs_qtl, total_value, buyer_fee, status, created_at, decided_at, buyer{id, name, company, type, location, phone (accepted only)}}` |
| GET | `/api/fpos/offers/{id}` | | offer + `lot` |
| GET | `/api/fpos/transactions` | `crop, q, page, limit` | page of accepted offers + `{transaction_id, date}` |
| GET | `/api/fpos/transactions/{id}` | | transaction + `lot` + `contributors[]` |
| GET | `/api/fpos/reports` | | `{enough, totals{deals, qty_qtl, value, avg_price_rs_qtl, lots, lots_sold, farmers, inventory_qty_qtl}, by_crop[], by_month[], by_buyer[], farmers[]}` |

Paged responses are `{items, total, page, limit, has_more}`. Filtering and paging happen in Python over the newest 1000
rows per FPO (`ROW_CAP` in `fpo_api.py`); move them into SQL when an FPO has thousands of rows.

## Schema / migrations

Everything lives in `sql/schema_v4.sql` (applied): `fpos`, `fpo_members`, `fpo_lots`, `fpo_lot_items`, `listings.fpo_id`,
offer columns `fpo_lot_id, total_value, buyer_fee, accepted_at, rejected_at`, functions `accept_offer` / `reject_offer`.
The dashboard needed no `schema_v5.sql`. Known limits: a stock entry goes into a lot whole (no partial quantities);
`listings` has no `updated_at`, so "updated" is the entry's creation date.

## Testing

```bash
python test_fpo_dashboard.py            # API against the real Supabase; deletes every test row afterwards
python test_fpo_dashboard.py --screens  # + serves the SPA locally and saves docs/screens/kk/*.png at 1366 / 820 / 390 px
```

Covers: 401 without / with a bad token; every empty state for a fresh FPO; three Telegram farmers ("Give to FPO") into two
FPOs, double tap not doubled; inventory by crop / items paging / search; farmers list, search, crop filter, profile, phone vs
"via Telegram"; lot create (50 qtl from two farmers, draft) with the model reference price, search by quality and Marathi crop
name, detail with contributors, price edit, bad price; publish → visible in the buyer app, unpublish → hidden, publish again;
buyer offer 20 @ 4000 → dashboard strip, offer search (new / crop / company), detail (total 80 000, fee 800), unpublish refused
while pending; accept → lot 30 left, transaction with buyer phone and contributors, buyer sees the FPO contact, reports totals;
reject path; oversell (30 left, two offers of 20 → second accept 409 `insufficient_qty`); FPO B cannot read A's stock entry,
farmer, lot, offer, transaction, nor publish / close A's lot; FPO B closes its own lot → stock back to open; settings PATCH;
every buyer-facing response scanned for farmer names, ids, `farmer_*` fields and `tg:`.
