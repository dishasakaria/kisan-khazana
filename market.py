"""Carpool matching + Kisaan Khazana FPO marketplace.

Carpool: farmers advised the same mandi for the same day, within POOL_KM of each other -> one shared truck.
  saving = sum(each farmer's cheapest own trip) - shared trip (longest route + PICKUP_KM per extra stop), split by qty.
Marketplace: farmer (Telegram "Give to FPO") -> nearest FPO's inventory -> FPO aggregates lots (web dashboard)
  -> buyers (Kisaan Khazana app) offer on lots -> FPO accepts/rejects (SQL functions, no overselling).
  Buyers never see farmers. Fee: FEE_BUYER of the deal value, computed server-side.
"""
import csv, datetime as dt, hashlib, hmac, math, secrets, urllib.error
from functools import lru_cache
from pathlib import Path

import db
from advice import CROP_NAME, haversine, mandi_name, mandis
from transport import best_transport, diesel_price

POOL_KM, PICKUP_KM, POOL_DAYS = 10, 3, 3
FEE_BUYER = 0.01


def _q(s):
    import urllib.request
    return urllib.request.quote(str(s), safe="")


# ---------------- carpool ----------------
def recent_trips(days=POOL_DAYS):
    """Advised trips from the last few days: who, where to, which day, qty, location."""
    since = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat()
    qs = db.select("queries", f"select=phone,commodity,qty_qtl,advice,created_at&created_at=gte.{since}&advice=not.is.null&limit=2000")
    farms = {f["phone"]: f for f in db.select("farmers", "select=phone,lat,lon,name&lat=not.is.null&limit=5000")}
    trips = {}
    for q in qs:
        f, a = farms.get(q["phone"]), q["advice"] or {}
        if not f or not a.get("mandi"):
            continue
        day = (dt.date.fromisoformat(q["created_at"][:10]) + dt.timedelta(days=a.get("days") or 0)).isoformat()
        trips[(q["phone"], a["mandi"], day)] = {"farmer": q["phone"], "name": f.get("name"), "mandi": a["mandi"], "date": day,
                                                "crop": q["commodity"], "qty": float(q["qty_qtl"] or 0), "km": float(a.get("km") or 0),
                                                "lat": float(f["lat"]), "lon": float(f["lon"])}
    return list(trips.values())  # latest advice per farmer/mandi/day


def pools(trips, diesel=None):
    """Greedy clustering: seed = biggest load, add farmers within POOL_KM of the seed going to the same mandi/day."""
    diesel = diesel or diesel_price("pune")[0]
    out, left = [], sorted(trips, key=lambda t: -t["qty"])
    while left:
        seed = left.pop(0)
        group = [seed] + [t for t in left if t["mandi"] == seed["mandi"] and t["date"] == seed["date"]
                          and haversine((t["lat"], t["lon"]), (seed["lat"], seed["lon"])) <= POOL_KM]
        left = [t for t in left if t not in group]
        if len(group) < 2:
            continue
        alone = sum(best_transport(t["qty"], t["km"], diesel)["total"] for t in group)
        qty = sum(t["qty"] for t in group)
        shared = best_transport(qty, max(t["km"] for t in group) + PICKUP_KM * (len(group) - 1), diesel)
        saving = alone - shared["total"]
        if saving <= 0:
            continue
        span = max(haversine((a["lat"], a["lon"]), (b["lat"], b["lon"])) for a in group for b in group)
        out.append({"mandi": seed["mandi"], "date": seed["date"], "farmers": len(group), "total_qty_qtl": round(qty, 1),
                    "km_span": round(span, 1), "saving_rs": round(saving), "vehicle": shared["vehicle"], "trips": shared["trips"],
                    "members": [{"farmer": t["farmer"], "name": t["name"], "qty": t["qty"],
                                 "saving_rs": round(saving * t["qty"] / qty)} for t in group]})
    return sorted(out, key=lambda p: -p["saving_rs"])


def pool_for(farmer):
    """The pool this farmer belongs to (if any) — used to nudge them on Telegram after advice."""
    for p in pools(recent_trips()):
        if any(m["farmer"] == farmer for m in p["members"]):
            return p
    return None


# ---------------- Kisaan Khazana: farmer -> FPO inventory -> FPO lot -> buyer offer -> FPO accepts ----------------
# Buyers deal only with FPOs: no farmer id, name, phone or per-farmer quantity ever leaves through a buyer endpoint.
BUYER_TYPES = ("wholesale", "processor", "exporter", "fpo")  # trade buyers only (no individuals)
FPO_KM = 60          # a farmer joins the nearest active FPO within this distance
MAX_PRICE = 100000   # ₹/qtl sanity cap
SORTS = ("nearest", "newest", "price_asc", "price_desc", "qty_desc")


class Conflict(ValueError):
    """-> HTTP 409 (duplicate, sold out, already decided)."""


@lru_cache(maxsize=1)
def _pins():
    with open(Path(__file__).with_name("static") / "pincodes_mh.csv") as fh:
        return [(float(r["lat"]), float(r["lon"]), DISTRICT_FIX.get(r["district"], r["district"])) for r in csv.DictReader(fh)]


DISTRICT_FIX = {"Ahmed Nagar": "Ahilyanagar", "Ahmednagar": "Ahilyanagar", "Raigarh(MH)": "Raigad",
                "Aurangabad": "Chhatrapati Sambhajinagar", "Osmanabad": "Dharashiv"}


@lru_cache(maxsize=4096)
def district_of(lat, lon):
    """District of the nearest PIN centroid."""
    k = math.cos(math.radians(lat)) ** 2
    return min(_pins(), key=lambda p: (p[0] - lat) ** 2 + k * (p[1] - lon) ** 2)[2]


def place(lat, lon):
    """District + nearest mandi town if within 30 km (names in mr/hi/en)."""
    if lat is None or lon is None:
        return {"district": None, "town": None}
    lat, lon = float(lat), float(lon)
    m = min(mandis(), key=lambda k: haversine((lat, lon), mandis()[k][:2]))
    near = haversine((lat, lon), mandis()[m][:2]) <= 30
    return {"district": district_of(round(lat, 2), round(lon, 2)),
            "town": {"en": m, "mr": mandi_name(m, "mr"), "hi": mandi_name(m, "hi")} if near else None}


def _clean_phone(phone):
    d = "".join(ch for ch in str(phone or "") if ch.isdigit())[-10:]
    if len(d) != 10 or d[0] not in "6789":
        raise ValueError("bad_phone")
    return "+91" + d


def _latlon(b):
    try:
        lat, lon = float(b.get("lat")), float(b.get("lon"))
    except (TypeError, ValueError):
        raise ValueError("bad_location")
    if not (6 <= lat <= 37 and 68 <= lon <= 98):  # India
        raise ValueError("bad_location")
    return round(lat, 4), round(lon, 4)


def _text(b, k, n):
    return str(b.get(k) or "").strip()[:n] or None


def hash_secret(s):
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${hashlib.scrypt(s.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32).hex()}"


def check_secret(s, stored):
    try:
        _, salt, h = (stored or "").split("$")
        got = hashlib.scrypt(str(s).encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32).hex()
    except ValueError:
        return False
    return hmac.compare_digest(got, h)


def _insert(table, row):
    try:
        return db._req("POST", table, [row], prefer="return=representation")[0]
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="ignore")
        if e.code == 409 or "23505" in msg:
            raise Conflict("duplicate")
        if "23514" in msg:
            raise ValueError("bad_input")
        raise


def _in(ids):
    return ",".join(str(int(i)) for i in ids)


# ---- farmers (Telegram "Give to FPO") ----
def nearest_fpo(lat, lon):
    fpos = db.select("fpos", "select=id,name,district,lat,lon&status=eq.active&lat=not.is.null&limit=2000")
    best = min(((haversine((lat, lon), (float(f["lat"]), float(f["lon"]))), f) for f in fpos), key=lambda x: x[0], default=None)
    return (best[1], round(best[0])) if best and best[0] <= FPO_KM else (None, None)


def give_to_fpo(farmer, f):
    """The farmer's last advised crop + qty go into the nearest FPO's inventory; the farmer becomes a member.
    Returns (status, fpo, km): status ok / no_last / no_fpo."""
    if not f.get("last_crop") or not f.get("last_qty") or f.get("lat") is None:
        return "no_last", None, None
    lat, lon = float(f["lat"]), float(f["lon"])
    fpo, km = nearest_fpo(lat, lon)
    if not fpo:
        return "no_fpo", None, None
    db.upsert("fpo_members", [{"fpo_id": fpo["id"], "farmer_id": farmer}])
    row = {"crop": f["last_crop"], "qty_qtl": f["last_qty"], "ask_rs_qtl": f.get("last_mandi_price"), "fair_rs_qtl": f.get("last_net"),
           "ready_date": dt.date.today().isoformat(), "condition": f.get("stock_condition") or "unknown"}
    same = db.select("listings", f"select=id&farmer=eq.{_q(farmer)}&fpo_id=eq.{fpo['id']}&crop=eq.{_q(f['last_crop'])}&status=eq.open&limit=1")
    if same:  # tapping twice updates the same stock instead of doubling it
        db._req("PATCH", f"listings?id=eq.{same[0]['id']}", row, prefer="return=minimal")
    else:
        db._req("POST", "listings", [{**row, "farmer": farmer, "fpo_id": fpo["id"], "status": "open", "lat": round(lat, 2),
                                      "lon": round(lon, 2), "district": district_of(round(lat, 2), round(lon, 2))}], prefer="return=minimal")
    return "ok", fpo, km


# ---- FPOs (web dashboard) ----
def _fpo_fields(b, partial=False):
    out = {}
    if "name" in b or not partial:
        name = str(b.get("name") or "").strip()
        if not 2 <= len(name) <= 120:
            raise ValueError("bad_name")
        out["name"] = name
    if "phone" in b or not partial:
        out["phone"] = _clean_phone(b.get("phone"))
    if "email" in b:
        email = (b.get("email") or "").strip().lower() or None
        if email and ("@" not in email or len(email) > 120):
            raise ValueError("bad_email")
        out["email"] = email
    for k, n in (("address", 200), ("district", 60)):
        if k in b:
            out[k] = _text(b, k, n)
    if "lat" in b or "lon" in b or not partial:
        out["lat"], out["lon"] = _latlon(b)
        out.setdefault("district", None)
        out["district"] = out["district"] or district_of(round(out["lat"], 2), round(out["lon"], 2))
    return out


def register_fpo(b):
    if len(str(b.get("password") or "")) < 8:
        raise ValueError("bad_password")
    row = _fpo_fields(b)
    token = secrets.token_urlsafe(32)
    _insert("fpos", {**row, "password_hash": hash_secret(str(b["password"])), "token": token, "status": "active"})
    return token


def login_fpo(login, password):
    login = str(login or "").strip().lower()
    if "@" in login:
        rows = db.select("fpos", f"select=*&email=eq.{_q(login)}&limit=1")
    else:
        try:
            rows = db.select("fpos", f"select=*&phone=eq.{_q(_clean_phone(login))}&limit=1")
        except ValueError:
            rows = []
    f = rows[0] if rows else None
    if not f or not check_secret(password, f["password_hash"]) or f["status"] != "active":
        return None
    return f["token"]


def fpo_by_token(token):
    r = db.select("fpos", f"select=*&token=eq.{_q(token)}&status=eq.active&limit=1") if token else []
    return r[0] if r else None


def fpo_me(f):
    return {k: f.get(k) for k in ("id", "name", "phone", "email", "address", "district", "lat", "lon", "status", "created_at")}


def update_fpo(f, b):
    row = _fpo_fields({k: b[k] for k in ("name", "phone", "email", "address", "district", "lat", "lon") if k in b}, partial=True)
    if b.get("password"):
        if len(str(b["password"])) < 8:
            raise ValueError("bad_password")
        row["password_hash"] = hash_secret(str(b["password"]))
    if row:
        try:
            db._req("PATCH", f"fpos?id=eq.{int(f['id'])}", {**row, "updated_at": dt.datetime.utcnow().isoformat()}, prefer="return=minimal")
        except urllib.error.HTTPError as e:
            if e.code == 409 or "23505" in e.read().decode(errors="ignore"):
                raise Conflict("duplicate")
            raise
    return fpo_by_token(f["token"])


def fpo_inventory(f):
    rows = db.select("listings", f"select=id,farmer,crop,qty_qtl,condition,ready_date,status,created_at&fpo_id=eq.{int(f['id'])}"
                                 "&order=created_at.desc&limit=500")
    ids = ",".join(_q(x) for x in {r["farmer"] for r in rows})
    names = {r["phone"]: r.get("name") for r in db.select("farmers", f"select=phone,name&phone=in.({ids})")} if ids else {}
    return [{**{k: r[k] for k in ("id", "crop", "qty_qtl", "condition", "ready_date", "status", "created_at")},
             "farmer_name": names.get(r["farmer"]) or "—",
             "channel": r["farmer"].split(":", 1)[0]} for r in rows]


def reference_price(crop, lat=None, lon=None):
    """Today's model price (P50, horizon 0) at the nearest forecast mandi for this crop, or None."""
    day = db.select("forecasts", f"select=made_on&commodity=eq.{_q(crop)}&order=made_on.desc&limit=1")
    if not day:
        return None
    rows = db.select("forecasts", f"select=market,p50&commodity=eq.{_q(crop)}&made_on=eq.{day[0]['made_on']}&horizon_days=eq.0&limit=500")
    known = [r for r in rows if r["market"] in mandis()]
    if not known:
        return None
    r = min(known, key=lambda r: haversine((lat, lon), mandis()[r["market"]][:2])) if lat is not None else known[0]
    return {"price": round(float(r["p50"])), "market": r["market"], "date": day[0]["made_on"]}


def create_lot(f, b):
    try:
        ids = sorted({int(i) for i in b.get("inventory_ids") or []})
        price = float(b.get("asking_price_rs_qtl"))
    except (TypeError, ValueError):
        raise ValueError("bad_input")
    if not 1 <= len(ids) <= 200:
        raise ValueError("bad_items")
    if not (math.isfinite(price) and 0 < price <= MAX_PRICE):
        raise ValueError("bad_price")
    items = db.select("listings", f"select=id,farmer,crop,qty_qtl&id=in.({_in(ids)})&fpo_id=eq.{int(f['id'])}&status=eq.open")
    if len(items) != len(ids) or any(float(i["qty_qtl"] or 0) <= 0 for i in items):
        raise ValueError("bad_items")
    if len({i["crop"] for i in items}) != 1:
        raise ValueError("mixed_crops")
    # claim the items first (only still-open ones change), so one stock can't land in two lots
    got = db._req("PATCH", f"listings?id=in.({_in(ids)})&fpo_id=eq.{int(f['id'])}&status=eq.open", {"status": "in_lot"},
                  prefer="return=representation")
    release = lambda: db._req("PATCH", f"listings?id=in.({_in([g['id'] for g in got])})", {"status": "open"}, prefer="return=minimal")
    if len(got) != len(ids):
        if got:
            release()
        raise Conflict("items_taken")
    crop, total = items[0]["crop"], round(sum(float(i["qty_qtl"]) for i in items), 2)
    ref = b.get("market_reference_price")
    if ref in (None, ""):
        ref = (reference_price(crop, f.get("lat") and float(f["lat"]), f.get("lon") and float(f["lon"])) or {}).get("price")
    try:
        lot = _insert("fpo_lots", {"fpo_id": f["id"], "crop": crop, "total_qty_qtl": total, "available_qty_qtl": total,
                                   "asking_price_rs_qtl": round(price, 2), "market_reference_price": float(ref) if ref else None,
                                   "quality": _text(b, "quality", 40), "notes": _text(b, "notes", 500),
                                   "location": _text(b, "location", 200) or f.get("address") or f.get("district"),
                                   "lat": f.get("lat"), "lon": f.get("lon"), "status": "open" if b.get("publish") else "draft"})
        db._req("POST", "fpo_lot_items", [{"lot_id": lot["id"], "inventory_id": i["id"], "farmer_id": i["farmer"],
                                           "qty_qtl": i["qty_qtl"]} for i in items], prefer="return=minimal")
    except Exception:
        release()
        raise
    return lot


def _own_lot(f, lot_id):
    r = db.select("fpo_lots", f"select=*&id=eq.{int(lot_id)}&fpo_id=eq.{int(f['id'])}&limit=1")
    if not r:
        raise LookupError("not_found")
    return r[0]


def update_lot(f, lot_id, b):
    lot = _own_lot(f, lot_id)
    row = {}
    if "asking_price_rs_qtl" in b:
        try:
            price = float(b["asking_price_rs_qtl"])
        except (TypeError, ValueError):
            raise ValueError("bad_price")
        if not (math.isfinite(price) and 0 < price <= MAX_PRICE):
            raise ValueError("bad_price")
        row["asking_price_rs_qtl"] = round(price, 2)
    for k, n in (("quality", 40), ("notes", 500), ("location", 200)):
        if k in b:
            row[k] = _text(b, k, n)
    st = b.get("status")
    if st and st != lot["status"]:
        if (lot["status"], st) not in (("draft", "open"), ("draft", "closed"), ("open", "closed")):
            raise Conflict("bad_status")
        row["status"] = st
    if lot["status"] in ("sold", "closed") and row:
        raise Conflict("lot_closed")
    if row:
        db._req("PATCH", f"fpo_lots?id=eq.{lot['id']}", {**row, "updated_at": dt.datetime.utcnow().isoformat()}, prefer="return=minimal")
    if row.get("status") == "closed":
        now = dt.datetime.utcnow().isoformat()
        db._req("PATCH", f"offers?fpo_lot_id=eq.{lot['id']}&status=eq.sent", {"status": "rejected", "rejected_at": now, "decided_at": now},
                prefer="return=minimal")
        if float(lot["available_qty_qtl"]) >= float(lot["total_qty_qtl"]):  # nothing sold: stock goes back to inventory
            items = db.select("fpo_lot_items", f"select=inventory_id&lot_id=eq.{lot['id']}")
            if items:
                db._req("PATCH", f"listings?id=in.({_in(i['inventory_id'] for i in items)})", {"status": "open"}, prefer="return=minimal")
    return _own_lot(f, lot_id)


def fpo_lots_of(f):
    lots = db.select("fpo_lots", f"select=*&fpo_id=eq.{int(f['id'])}&order=created_at.desc&limit=500")
    ids = _in(l["id"] for l in lots)
    pend = {}
    for o in db.select("offers", f"select=fpo_lot_id&fpo_lot_id=in.({ids})&status=eq.sent") if ids else []:
        pend[o["fpo_lot_id"]] = pend.get(o["fpo_lot_id"], 0) + 1
    return [{**{k: v for k, v in l.items() if k not in ("lat", "lon")}, "pending_offers": pend.get(l["id"], 0)} for l in lots]


def fpo_offers(f):
    lots = {l["id"]: l for l in db.select("fpo_lots", f"select=id,crop,status,available_qty_qtl&fpo_id=eq.{int(f['id'])}&limit=1000")}
    if not lots:
        return []
    rows = db.select("offers", f"select=*&fpo_lot_id=in.({_in(lots)})&order=created_at.desc&limit=500")
    bids = _in({o["buyer_id"] for o in rows})
    buyers = {b["id"]: b for b in db.select("buyers", f"select=id,name,company,type,phone,location_text&id=in.({bids})")} if bids else {}
    out = []
    for o in rows:
        b = buyers.get(o["buyer_id"], {})
        out.append({"offer_id": o["id"], "lot_id": o["fpo_lot_id"], "crop": lots[o["fpo_lot_id"]]["crop"],
                    "lot_available_qty_qtl": lots[o["fpo_lot_id"]]["available_qty_qtl"], "qty_qtl": o["qty_qtl"],
                    "price_rs_qtl": o["price_rs_qtl"], "total_value": o.get("total_value"), "status": o["status"],
                    "created_at": o["created_at"], "accepted_at": o.get("accepted_at"), "rejected_at": o.get("rejected_at"),
                    "buyer": {"name": b.get("name"), "company": b.get("company"), "type": b.get("type"),
                              "location": b.get("location_text"),
                              "phone": b.get("phone") if o["status"] == "accepted" else None}})  # buyer phone once accepted
    return out


def decide(f, offer_id, accept):
    """accept_offer / reject_offer SQL functions: lot row locked, all in one transaction (no overselling)."""
    r = db._req("POST", f"rpc/{'accept_offer' if accept else 'reject_offer'}", {"p_offer": int(offer_id), "p_fpo": int(f["id"])})
    if not r.get("ok"):
        if r.get("error") == "not_found":
            raise LookupError("not_found")
        raise Conflict(r.get("error") or "conflict")
    return r


# ---- buyers (Kisaan Khazana app) ----
def _buyer_fields(b, partial=False):
    out = {}
    if "name" in b or not partial:
        name = str(b.get("name") or "").strip()
        if not 2 <= len(name) <= 80:
            raise ValueError("bad_name")
        out["name"] = name
    if "company" in b:
        out["company"] = _text(b, "company", 120)
    if "location_text" in b:
        out["location_text"] = _text(b, "location_text", 120)
    if "type" in b or not partial:
        if b.get("type") not in BUYER_TYPES:
            raise ValueError("bad_type")
        out["type"] = b["type"]
    if "phone" in b or not partial:
        out["phone"] = _clean_phone(b.get("phone"))
    if "lat" in b or "lon" in b or not partial:
        out["lat"], out["lon"] = _latlon(b)
    if "pin" in b or not partial:
        pin = str(b.get("pin") or "")
        if not (pin.isdigit() and 4 <= len(pin) <= 6):
            raise ValueError("bad_pin")
        out["pin_hash"] = hash_secret(pin)
    return out


def register_buyer(b):
    row = _buyer_fields(b)
    if db.select("buyers", f"select=id&phone=eq.{_q(row['phone'])}&pin_hash=not.is.null&limit=1"):
        raise Conflict("phone_taken")
    token = secrets.token_urlsafe(32)
    _insert("buyers", {"token": token, **row})
    return token


def login_buyer(phone, pin):
    try:
        rows = db.select("buyers", f"select=token,pin_hash&phone=eq.{_q(_clean_phone(phone))}&pin_hash=not.is.null&limit=1")
    except ValueError:
        return None
    return rows[0]["token"] if rows and check_secret(pin, rows[0]["pin_hash"]) else None


def update_buyer(b, fields):
    row = _buyer_fields(fields, partial=True)
    if row.get("phone") and row["phone"] != b.get("phone") and \
            db.select("buyers", f"select=id&phone=eq.{_q(row['phone'])}&pin_hash=not.is.null&id=neq.{int(b['id'])}&limit=1"):
        raise Conflict("phone_taken")
    if row:
        db._req("PATCH", f"buyers?id=eq.{int(b['id'])}", {**row, "updated_at": dt.datetime.utcnow().isoformat()}, prefer="return=minimal")
    return buyer_by_token(b["token"])


def buyer_by_token(token):
    r = db.select("buyers", f"select=*&token=eq.{_q(token)}&limit=1") if token else []
    return r[0] if r else None


def buyer_me(b):
    return {**{k: b.get(k) for k in ("id", "name", "company", "type", "phone", "lat", "lon", "location_text", "created_at")},
            "place": place(b.get("lat"), b.get("lon"))}


LOT_FIELDS = ("id", "crop", "total_qty_qtl", "available_qty_qtl", "asking_price_rs_qtl", "market_reference_price", "quality",
              "location", "status", "notes", "created_at", "updated_at")


def lot_public(l, fpo, lat=None, lon=None):
    """A lot as a buyer sees it: FPO name + district only (FPO phone/address only after an accepted offer)."""
    km = None
    if lat is not None and lon is not None and l.get("lat") is not None:
        km = round(haversine((float(lat), float(lon)), (float(l["lat"]), float(l["lon"]))))
    district = (fpo or {}).get("district") or (district_of(round(float(l["lat"]), 2), round(float(l["lon"]), 2)) if l.get("lat") else None)
    return {**{k: l.get(k) for k in LOT_FIELDS}, "km": km, "district": district,
            "fpo": {"id": fpo["id"], "name": fpo["name"], "district": fpo.get("district")} if fpo else None}


def _fpos(ids):
    ids = _in(set(ids))
    return {f["id"]: f for f in db.select("fpos", f"select=id,name,district,phone,address,status&id=in.({ids})")} if ids else {}


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("bad_input")


def search_lots(b, p):
    """Open lots with stock left, filtered + sorted + paged in Python over the newest 500.
    ponytail: in-memory over 500 rows; move filters into SQL when there are thousands of lots."""
    lat, lon = (float(b["lat"]), float(b["lon"])) if b and b.get("lat") is not None else (None, None)
    lots = db.select("fpo_lots", "select=*&status=eq.open&available_qty_qtl=gt.0&order=created_at.desc&limit=500")
    fpos = _fpos(l["fpo_id"] for l in lots)
    rows = [lot_public(l, fpos[l["fpo_id"]], lat, lon) for l in lots if fpos.get(l["fpo_id"], {}).get("status") == "active"]
    radius, lo, hi, min_qty = _num(p.get("radius_km")), _num(p.get("min_price")), _num(p.get("max_price")), _num(p.get("min_qty"))
    q = str(p.get("q") or "").strip().lower()
    if radius and lat is not None:
        rows = [r for r in rows if r["km"] is not None and r["km"] <= radius]
    if lo is not None:
        rows = [r for r in rows if float(r["asking_price_rs_qtl"]) >= lo]
    if hi is not None:
        rows = [r for r in rows if float(r["asking_price_rs_qtl"]) <= hi]
    if min_qty is not None:
        rows = [r for r in rows if float(r["available_qty_qtl"]) >= min_qty]
    if q:
        names = lambda c: [c] + [CROP_NAME[lg].get(c, "") for lg in CROP_NAME]
        rows = [r for r in rows if q in " ".join(names(r["crop"]) + [r["fpo"]["name"], r["location"] or "", r["district"] or ""]).lower()]
    crops = {}
    for r in rows:
        crops[r["crop"]] = crops.get(r["crop"], 0) + 1
    if p.get("crop"):
        rows = [r for r in rows if r["crop"] == p["crop"]]
    sort = p.get("sort") if p.get("sort") in SORTS else "nearest"
    key = {"nearest": lambda r: r["km"] if r["km"] is not None else 1e9, "newest": None,
           "price_asc": lambda r: float(r["asking_price_rs_qtl"]), "price_desc": lambda r: -float(r["asking_price_rs_qtl"]),
           "qty_desc": lambda r: -float(r["available_qty_qtl"])}[sort]
    if key:
        rows.sort(key=key)  # stable: newest first among equals
    limit = max(1, min(int(_num(p.get("limit")) or 20), 50))
    page = max(1, int(_num(p.get("page")) or 1))
    return {"items": rows[(page - 1) * limit: page * limit], "total": len(rows), "page": page, "limit": limit,
            "has_more": page * limit < len(rows), "crops": [{"crop": c, "lots": n} for c, n in sorted(crops.items(), key=lambda x: -x[1])]}


def lot_detail(lot_id, b=None):
    r = db.select("fpo_lots", f"select=*&id=eq.{int(lot_id)}&status=in.(open,sold,closed)&limit=1")
    if not r:
        return None
    l = r[0]
    f = _fpos([l["fpo_id"]]).get(l["fpo_id"])
    out = lot_public(l, f, b.get("lat") if b else None, b.get("lon") if b else None)
    out["farmers_n"] = len({i["farmer_id"] for i in db.select("fpo_lot_items", f"select=farmer_id&lot_id=eq.{l['id']}")})
    if b:
        mine = db.select("offers", f"select=id,status,qty_qtl,price_rs_qtl&fpo_lot_id=eq.{l['id']}&buyer_id=eq.{int(b['id'])}"
                                   "&order=created_at.desc&limit=1")
        out["my_offer"] = mine[0] if mine else None
    return out


def make_offer(b, lot_id, qty, price):
    """Buyer offers on an open FPO lot. Total and the 1% buyer fee are computed here, never trusted from the client."""
    try:
        lot_id, qty, price = int(lot_id), float(qty), float(price)
    except (TypeError, ValueError):
        raise ValueError("bad_input")
    r = db.select("fpo_lots", f"select=*&id=eq.{lot_id}&limit=1")
    if not r or r[0]["status"] != "open" or float(r[0]["available_qty_qtl"]) <= 0:
        raise Conflict("lot_closed")
    lot = r[0]
    if not (math.isfinite(qty) and 0 < qty <= float(lot["available_qty_qtl"]) + 1e-9):
        raise ValueError("bad_qty")
    if not (math.isfinite(price) and 0 < price <= MAX_PRICE):
        raise ValueError("bad_price")
    if db.select("offers", f"select=id&fpo_lot_id=eq.{lot_id}&buyer_id=eq.{int(b['id'])}&status=eq.sent&limit=1"):
        raise Conflict("duplicate_offer")
    qty, price = round(qty, 2), round(price, 2)
    value = round(qty * price, 2)
    fee = round(value * FEE_BUYER)
    try:
        o = _insert("offers", {"fpo_lot_id": lot_id, "buyer_id": b["id"], "qty_qtl": qty, "price_rs_qtl": price,
                               "total_value": value, "buyer_fee": fee, "fee_buyer_rs": fee})
    except Conflict:
        raise Conflict("duplicate_offer")  # unique pending-offer index caught a double tap
    return o


def buyer_offers(b, offer_id=None):
    filt = f"&id=eq.{int(offer_id)}" if offer_id is not None else ""
    rows = db.select("offers", f"select=*&buyer_id=eq.{int(b['id'])}&fpo_lot_id=not.is.null{filt}&order=created_at.desc&limit=200")
    ids = _in({o["fpo_lot_id"] for o in rows})
    lots = {l["id"]: l for l in db.select("fpo_lots", f"select=*&id=in.({ids})")} if ids else {}
    fpos = _fpos(l["fpo_id"] for l in lots.values())
    out = []
    for o in rows:
        l = lots.get(o["fpo_lot_id"])
        f = fpos.get(l["fpo_id"]) if l else None
        contact = None
        if o["status"] == "accepted" and f:  # FPO contact only for this buyer's accepted offer
            d = "".join(ch for ch in f.get("phone") or "" if ch.isdigit())
            contact = {"name": f["name"], "phone": f.get("phone"), "whatsapp": f"https://wa.me/{d}" if d else None,
                       "address": f.get("address"), "district": f.get("district"), "pickup": (l or {}).get("location")}
        out.append({"offer_id": o["id"], "lot_id": o["fpo_lot_id"], "crop": l["crop"] if l else None, "qty_qtl": o["qty_qtl"],
                    "price_rs_qtl": o["price_rs_qtl"], "total_value": o.get("total_value"), "buyer_fee": o.get("buyer_fee"),
                    "status": o["status"], "created_at": o["created_at"], "accepted_at": o.get("accepted_at"),
                    "rejected_at": o.get("rejected_at"), "lot": lot_public(l, f, b.get("lat"), b.get("lon")) if l else None,
                    "fpo_contact": contact})
    return out


if __name__ == "__main__":
    # self-check of the pooling maths on synthetic trips (no network except the cached diesel price)
    base = {"mandi": "Lasalgaon", "date": "2026-10-03", "crop": "Onion", "name": None}
    trips = [dict(base, farmer="a", qty=20, km=30, lat=20.00, lon=74.10), dict(base, farmer="b", qty=15, km=32, lat=20.03, lon=74.12),
             dict(base, farmer="c", qty=10, km=28, lat=20.02, lon=74.08), dict(base, farmer="far", qty=30, km=90, lat=20.6, lon=74.6)]
    p = pools(trips, diesel=100.0)
    assert len(p) == 1 and p[0]["farmers"] == 3, p
    assert p[0]["saving_rs"] > 0 and sum(m["saving_rs"] for m in p[0]["members"]) <= p[0]["saving_rs"] + 2
    assert not pools([trips[0], trips[3]], diesel=100.0), "too far apart -> no pool"
    print("pool:", {k: v for k, v in p[0].items() if k != "members"})
    print("market self-checks ok")
