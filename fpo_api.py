"""Kisaan Khazana FPO dashboard API (serves web/kk/). Read models + lot actions on top of api.py's FPO routes.

Mount in api.py:  app.include_router(fpo_api.router)
Identity always comes from the bearer token (api._fpo); every query is scoped by fpo_id, another FPO's rows are 404.
Nothing here is buyer-facing: farmer names / ids / quantities only ever go back to the FPO that owns the inventory.
Existing routes reused by the dashboard (api.py): POST /api/fpos, /login, GET+PATCH /me, GET /inventory, GET /reference-price,
GET+POST /lots, PATCH /lots/{id}, GET /offers, POST /offers/{id}/accept|reject.
"""
import datetime as dt, urllib.parse

from fastapi import APIRouter, HTTPException, Request

import db, market
from advice import CROP_NAME

router = APIRouter(prefix="/api/fpos")
PAGE_MAX, ROW_CAP = 100, 1000  # ponytail: filter/page in Python over the newest ROW_CAP rows; push into SQL past a few thousand


def _api():
    import api  # lazy: api.py imports this module to mount the router
    return api


def _fpo(req):
    return _api()._fpo(req)


def _call(fn, *a):
    return _api()._call(fn, *a)


def _q(s):
    return urllib.parse.quote(str(s), safe="")


def _in(ids):
    return ",".join(str(int(i)) for i in ids)


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _page(req, rows):
    p = req.query_params
    try:
        page, limit = max(1, int(p.get("page") or 1)), max(1, min(int(p.get("limit") or 20), PAGE_MAX))
    except ValueError:
        raise HTTPException(400, "bad_input")
    return {"items": rows[(page - 1) * limit: page * limit], "total": len(rows), "page": page, "limit": limit,
            "has_more": page * limit < len(rows)}


def crop_words(crop):
    return " ".join([crop] + [CROP_NAME[lg].get(crop, "") for lg in CROP_NAME]).lower()


def lot_code(lot):
    """Human lot id: two letters of the crop + id, e.g. ON-012."""
    letters = "".join(ch for ch in lot["crop"] if ch.isalpha())[:2].upper() or "LT"
    return f"{letters}-{int(lot['id']):03d}"


# ---------------- scoped fetchers ----------------
def _listings(f, extra=""):
    return db.select("listings", f"select=id,farmer,crop,qty_qtl,condition,ready_date,status,created_at,district"
                                 f"&fpo_id=eq.{int(f['id'])}{extra}&order=created_at.desc&limit={ROW_CAP}")


def _lots(f, extra=""):
    rows = db.select("fpo_lots", f"select=*&fpo_id=eq.{int(f['id'])}{extra}&order=created_at.desc&limit={ROW_CAP}")
    return [{k: v for k, v in l.items() if k not in ("lat", "lon")} for l in rows]


def _offers(lot_ids, extra=""):
    ids = _in(lot_ids)
    return db.select("offers", f"select=*&fpo_lot_id=in.({ids}){extra}&order=created_at.desc&limit={ROW_CAP}") if ids else []


def _farmers(ids):
    ids = ",".join(_q(x) for x in set(ids))
    rows = db.select("farmers", f"select=phone,name,lang,lat,lon,contact_phone,last_crop&phone=in.({ids})") if ids else []
    return {r["phone"]: r for r in rows}


def _buyers(ids):
    ids = _in(set(ids))
    rows = db.select("buyers", f"select=id,name,company,type,phone,location_text&id=in.({ids})") if ids else []
    return {r["id"]: r for r in rows}


def _members(f):
    return [m["farmer_id"] for m in db.select("fpo_members", f"select=farmer_id&fpo_id=eq.{int(f['id'])}&limit={ROW_CAP}")]


# ---------------- views ----------------
def _lot_view(l, offers=None):
    mine = [o for o in offers or [] if o["fpo_lot_id"] == l["id"]]
    return {**l, "code": lot_code(l), "sold_qty_qtl": round(_f(l["total_qty_qtl"]) - _f(l["available_qty_qtl"]), 2),
            "pending_offers": sum(o["status"] == "sent" for o in mine), "accepted_offers": sum(o["status"] == "accepted" for o in mine)}


def _offer_view(o, lot, buyer):
    b, l = buyer or {}, lot or {}
    at = o.get("accepted_at") or o.get("rejected_at") or o.get("decided_at")
    return {"offer_id": o["id"], "lot_id": o["fpo_lot_id"], "code": lot_code(l) if l else None, "crop": l.get("crop"),
            "lot_status": l.get("status"), "lot_available_qty_qtl": l.get("available_qty_qtl"), "qty_qtl": o["qty_qtl"],
            "price_rs_qtl": o["price_rs_qtl"], "total_value": o.get("total_value"), "buyer_fee": o.get("buyer_fee"),
            "status": o["status"], "created_at": o["created_at"], "decided_at": at,
            "accepted_at": o.get("accepted_at"), "rejected_at": o.get("rejected_at"),
            "buyer": {"id": b.get("id"), "name": b.get("name"), "company": b.get("company"), "type": b.get("type"),
                      "location": b.get("location_text"),
                      "phone": b.get("phone") if o["status"] == "accepted" else None}}  # buyer phone only once accepted


def _item_view(i, farmers):
    fr = farmers.get(i["farmer"], {})
    return {**{k: i.get(k) for k in ("id", "crop", "qty_qtl", "condition", "ready_date", "status", "created_at", "district")},
            "farmer_id": i["farmer"], "farmer_name": fr.get("name"), "channel": i["farmer"].split(":", 1)[0]}


def _farmer_view(fid, fr, items):
    fr = fr or {}
    place = market.place(fr.get("lat"), fr.get("lon"))
    by_crop = {}
    for i in items:
        if i["status"] != "sold":
            by_crop[i["crop"]] = by_crop.get(i["crop"], 0) + _f(i["qty_qtl"])
    primary = max(by_crop, key=by_crop.get) if by_crop else fr.get("last_crop")
    tot = lambda st: round(sum(_f(i["qty_qtl"]) for i in items if i["status"] == st), 2)
    return {"farmer_id": fid, "name": fr.get("name"), "channel": fid.split(":", 1)[0], "phone": fr.get("contact_phone"),
            "lang": fr.get("lang"), "district": place["district"], "town": place["town"], "primary_crop": primary,
            "available_qty_qtl": tot("open"), "in_lot_qty_qtl": tot("in_lot"), "sold_qty_qtl": tot("sold"), "items_n": len(items),
            "updated_at": max((i["created_at"] for i in items), default=None)}


def _by_crop(items):
    out = {}
    for i in items:
        c = out.setdefault(i["crop"], {"crop": i["crop"], "available_qty_qtl": 0, "in_lot_qty_qtl": 0, "sold_qty_qtl": 0,
                                       "farmers": set(), "updated_at": None})
        c[{"open": "available_qty_qtl", "in_lot": "in_lot_qty_qtl"}.get(i["status"], "sold_qty_qtl")] += _f(i["qty_qtl"])
        c["farmers"].add(i["farmer"])
        c["updated_at"] = max(c["updated_at"] or "", i["created_at"] or "")
    rows = []
    for c in out.values():
        farmers = c.pop("farmers")
        rows.append({**c, "farmers_n": len(farmers), "total_qty_qtl": round(c["available_qty_qtl"] + c["in_lot_qty_qtl"], 2),
                     "status": "available" if c["available_qty_qtl"] > 0 else "in_lot" if c["in_lot_qty_qtl"] > 0 else "sold"})
        for k in ("available_qty_qtl", "in_lot_qty_qtl", "sold_qty_qtl"):
            rows[-1][k] = round(rows[-1][k], 2)
    return sorted(rows, key=lambda r: -r["total_qty_qtl"])


def _match(q, *parts):
    return q in " ".join(str(p or "") for p in parts).lower()


# ---------------- dashboard ----------------
@router.get("/dashboard")
def dashboard(req: Request):
    f = _fpo(req)
    items, lots = _listings(f), _lots(f)
    offers = _offers(l["id"] for l in lots)
    lot_by = {l["id"]: l for l in lots}
    buyers = _buyers(o["buyer_id"] for o in offers[:5])
    month = _now().date().replace(day=1).isoformat()
    sold = [o for o in offers if o["status"] == "accepted" and (o.get("accepted_at") or o.get("decided_at") or "")[:10] >= month]
    return {"fpo": market.fpo_me(f),
            "metrics": {"available_qty_qtl": round(sum(_f(i["qty_qtl"]) for i in items if i["status"] == "open"), 2),
                        "in_lot_qty_qtl": round(sum(_f(i["qty_qtl"]) for i in items if i["status"] == "in_lot"), 2),
                        "open_lots": sum(l["status"] == "open" for l in lots), "draft_lots": sum(l["status"] == "draft" for l in lots),
                        "pending_offers": sum(o["status"] == "sent" for o in offers),
                        "sold_qty_month": round(sum(_f(o["qty_qtl"]) for o in sold), 2),
                        "sold_value_month": round(sum(_f(o.get("total_value")) for o in sold), 2),
                        "farmers": len({i["farmer"] for i in items} | set(_members(f)))},
            "inventory_by_crop": _by_crop(items),
            "recent_offers": [_offer_view(o, lot_by.get(o["fpo_lot_id"]), buyers.get(o["buyer_id"])) for o in offers[:5]],
            "active_lots": [_lot_view(l, offers) for l in lots if l["status"] == "open"][:5],
            "generated_at": _now().isoformat()}


@router.get("/notifications")
def notifications(req: Request):
    """Derived, no table: pending offers, stock added this week, lots sold out this week. Newest first."""
    f = _fpo(req)
    week = (_now() - dt.timedelta(days=7)).isoformat()
    lots = _lots(f)
    lot_by = {l["id"]: l for l in lots}
    out = [{"type": "offer", "at": o["created_at"], "offer_id": o["id"], "lot_id": o["fpo_lot_id"],
            "code": lot_code(lot_by[o["fpo_lot_id"]]), "crop": lot_by[o["fpo_lot_id"]]["crop"], "qty_qtl": o["qty_qtl"],
            "price_rs_qtl": o["price_rs_qtl"]} for o in _offers(lot_by, "&status=eq.sent") if o["fpo_lot_id"] in lot_by]
    items = _listings(f, f"&created_at=gte.{_q(week)}")
    farmers = _farmers(i["farmer"] for i in items)
    out += [{"type": "inventory", "at": i["created_at"], "inventory_id": i["id"], "crop": i["crop"], "qty_qtl": i["qty_qtl"],
             "farmer_name": farmers.get(i["farmer"], {}).get("name")} for i in items]
    out += [{"type": "sold", "at": l["updated_at"], "lot_id": l["id"], "code": lot_code(l), "crop": l["crop"],
             "qty_qtl": l["total_qty_qtl"]} for l in lots if l["status"] == "sold" and (l.get("updated_at") or "") >= week]
    out.sort(key=lambda n: n["at"] or "", reverse=True)
    return {"items": out[:30], "pending_offers": sum(n["type"] == "offer" for n in out)}


# ---------------- inventory ----------------
@router.get("/inventory/by-crop")
def inventory_by_crop(req: Request):
    return _by_crop(_listings(_fpo(req)))


@router.get("/inventory/items")
def inventory_items(req: Request):
    f, p = _fpo(req), req.query_params
    extra = "".join(f"&{k}=eq.{_q(p[k])}" for k in ("crop", "status") if p.get(k))
    items = _listings(f, extra)
    farmers = _farmers(i["farmer"] for i in items)
    rows = [_item_view(i, farmers) for i in items]
    q = (p.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if _match(q, r["farmer_name"], r["farmer_id"], crop_words(r["crop"]), r["condition"])]
    return _page(req, rows)


@router.get("/inventory/{item_id}")
def inventory_item(req: Request, item_id: int):
    f = _fpo(req)
    rows = _listings(f, f"&id=eq.{item_id}")
    if not rows:
        raise HTTPException(404, "not_found")
    i = rows[0]
    farmers = _farmers([i["farmer"]])
    links = db.select("fpo_lot_items", f"select=lot_id,qty_qtl&inventory_id=eq.{item_id}")
    lots = _lots(f, f"&id=in.({_in(x['lot_id'] for x in links)})") if links else []
    return {**_item_view(i, farmers), "farmer": _farmer_view(i["farmer"], farmers.get(i["farmer"]), _listings(f, f"&farmer=eq.{_q(i['farmer'])}")),
            "lots": [_lot_view(l) for l in lots]}


# ---------------- farmers (members) ----------------
@router.get("/farmers")
def farmers(req: Request):
    f, p = _fpo(req), req.query_params
    items = _listings(f)
    ids = set(_members(f)) | {i["farmer"] for i in items}
    farmers = _farmers(ids)
    rows = [_farmer_view(fid, farmers.get(fid), [i for i in items if i["farmer"] == fid]) for fid in ids]
    q = (p.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if _match(q, r["name"], r["farmer_id"], r["district"], (r["town"] or {}).get("en"),
                                          (r["town"] or {}).get("mr"), (r["town"] or {}).get("hi"), r["phone"])]
    if p.get("crop"):
        has = {i["farmer"] for i in items if i["crop"] == p["crop"]}
        rows = [r for r in rows if r["farmer_id"] in has or r["primary_crop"] == p["crop"]]
    rows.sort(key=lambda r: (r["updated_at"] or "", r["name"] or ""), reverse=True)
    return _page(req, rows)


@router.get("/farmers/{farmer_id}")
def farmer_one(req: Request, farmer_id: str):
    f = _fpo(req)
    items = _listings(f, f"&farmer=eq.{_q(farmer_id)}")
    if not items and farmer_id not in _members(f):
        raise HTTPException(404, "not_found")
    fr = _farmers([farmer_id]).get(farmer_id)
    links = db.select("fpo_lot_items", f"select=lot_id,inventory_id,qty_qtl&farmer_id=eq.{_q(farmer_id)}")
    lots = {l["id"]: l for l in _lots(f, f"&id=in.({_in(x['lot_id'] for x in links)})")} if links else {}
    return {**_farmer_view(farmer_id, fr, items), "items": [_item_view(i, {farmer_id: fr or {}}) for i in items],
            "lots": [{**_lot_view(lots[x["lot_id"]]), "farmer_qty_qtl": x["qty_qtl"]} for x in links if x["lot_id"] in lots]}


# ---------------- lots ----------------
@router.get("/lots/search")
def lots_search(req: Request):
    f, p = _fpo(req), req.query_params
    extra = "".join(f"&{k}=eq.{_q(p[k])}" for k in ("crop", "status") if p.get(k))
    lots = _lots(f, extra)
    offers = _offers(l["id"] for l in lots)
    rows = [_lot_view(l, offers) for l in lots]
    q = (p.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if _match(q, r["code"], crop_words(r["crop"]), r["quality"], r["location"], r["notes"])]
    return _page(req, rows)


@router.get("/lots/{lot_id}")
def lot_one(req: Request, lot_id: int):
    f = _fpo(req)
    lot = _call(market._own_lot, f, lot_id)
    lot = {k: v for k, v in lot.items() if k not in ("lat", "lon")}
    offers = _offers([lot_id])
    buyers = _buyers(o["buyer_id"] for o in offers)
    links = db.select("fpo_lot_items", f"select=inventory_id,farmer_id,qty_qtl&lot_id=eq.{lot_id}")
    farmers = _farmers(x["farmer_id"] for x in links)
    inv = {i["id"]: i for i in _listings(f, f"&id=in.({_in(x['inventory_id'] for x in links)})")} if links else {}
    contrib = {}
    for x in links:
        c = contrib.setdefault(x["farmer_id"], {"farmer_id": x["farmer_id"], "farmer_name": farmers.get(x["farmer_id"], {}).get("name"),
                                                "qty_qtl": 0, "items": 0})
        c["qty_qtl"] = round(c["qty_qtl"] + _f(x["qty_qtl"]), 2)
        c["items"] += 1
    return {**_lot_view(lot, offers),
            "items": [{"inventory_id": x["inventory_id"], "farmer_id": x["farmer_id"], "qty_qtl": x["qty_qtl"],
                       "farmer_name": farmers.get(x["farmer_id"], {}).get("name"),
                       "condition": inv.get(x["inventory_id"], {}).get("condition"),
                       "item_status": inv.get(x["inventory_id"], {}).get("status")} for x in links],
            "contributors": sorted(contrib.values(), key=lambda c: -c["qty_qtl"]),
            "offers": [_offer_view(o, lot, buyers.get(o["buyer_id"])) for o in offers]}


@router.post("/lots/{lot_id}/publish")
def lot_publish(req: Request, lot_id: int):
    return _lot_view(_call(market.update_lot, _fpo(req), lot_id, {"status": "open"}))


@router.post("/lots/{lot_id}/close")
def lot_close(req: Request, lot_id: int):
    return _lot_view(_call(market.update_lot, _fpo(req), lot_id, {"status": "closed"}))


@router.post("/lots/{lot_id}/unpublish")
def lot_unpublish(req: Request, lot_id: int):
    """open -> draft (hidden from buyers). Refused while buyer offers are pending: decide them first."""
    f = _fpo(req)
    lot = _call(market._own_lot, f, lot_id)
    if lot["status"] != "open":
        raise HTTPException(409, "bad_status")
    if _offers([lot_id], "&status=eq.sent"):
        raise HTTPException(409, "pending_offers")
    db._req("PATCH", f"fpo_lots?id=eq.{lot_id}&fpo_id=eq.{int(f['id'])}&status=eq.open",
            {"status": "draft", "updated_at": _now().isoformat()}, prefer="return=minimal")
    return _lot_view(_call(market._own_lot, f, lot_id))


# ---------------- offers ----------------
def _offer_rows(f, extra=""):
    lots = {l["id"]: l for l in _lots(f)}
    offers = [o for o in _offers(lots, extra) if o["fpo_lot_id"] in lots]
    buyers = _buyers(o["buyer_id"] for o in offers)
    return [(o, lots[o["fpo_lot_id"]], buyers.get(o["buyer_id"])) for o in offers]


@router.get("/offers/search")
def offers_search(req: Request):
    f, p = _fpo(req), req.query_params
    st = p.get("status")
    extra = f"&status=eq.{'sent' if st in ('new', 'pending') else _q(st)}" if st else ""
    rows = _offer_rows(f, extra)
    if st == "new":
        day = (_now() - dt.timedelta(hours=24)).isoformat()
        rows = [r for r in rows if r[0]["created_at"] >= day]
    if p.get("crop"):
        rows = [r for r in rows if r[1]["crop"] == p["crop"]]
    out = [_offer_view(*r) for r in rows]
    q = (p.get("q") or "").strip().lower()
    if q:
        out = [r for r in out if _match(q, r["code"], crop_words(r["crop"]), r["buyer"]["name"], r["buyer"]["company"], r["buyer"]["location"])]
    return _page(req, out)


@router.get("/offers/{offer_id}")
def offer_one(req: Request, offer_id: int):
    rows = _offer_rows(_fpo(req), f"&id=eq.{offer_id}")
    if not rows:
        raise HTTPException(404, "not_found")
    o, lot, buyer = rows[0]
    return {**_offer_view(o, lot, buyer), "lot": _lot_view(lot, [o])}


# ---------------- transactions = accepted offers ----------------
def _tx(o, lot, buyer):
    v = _offer_view(o, lot, buyer)
    return {**v, "transaction_id": o["id"], "date": o.get("accepted_at") or o.get("decided_at")}


@router.get("/transactions")
def transactions(req: Request):
    f, p = _fpo(req), req.query_params
    rows = [_tx(*r) for r in _offer_rows(f, "&status=eq.accepted")]
    if p.get("crop"):
        rows = [r for r in rows if r["crop"] == p["crop"]]
    q = (p.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if _match(q, r["code"], crop_words(r["crop"]), r["buyer"]["name"], r["buyer"]["company"])]
    rows.sort(key=lambda r: r["date"] or "", reverse=True)
    return _page(req, rows)


@router.get("/transactions/{offer_id}")
def transaction_one(req: Request, offer_id: int):
    f = _fpo(req)
    rows = _offer_rows(f, f"&id=eq.{offer_id}&status=eq.accepted")
    if not rows:
        raise HTTPException(404, "not_found")
    o, lot, buyer = rows[0]
    links = db.select("fpo_lot_items", f"select=farmer_id,qty_qtl&lot_id=eq.{lot['id']}")
    farmers = _farmers(x["farmer_id"] for x in links)
    return {**_tx(o, lot, buyer), "lot": _lot_view(lot),
            "contributors": [{"farmer_id": x["farmer_id"], "farmer_name": farmers.get(x["farmer_id"], {}).get("name"),
                              "qty_qtl": x["qty_qtl"]} for x in links]}


# ---------------- reports ----------------
@router.get("/reports")
def reports(req: Request):
    f = _fpo(req)
    items, lots = _listings(f), _lots(f)
    lot_by = {l["id"]: l for l in lots}
    deals = [o for o in _offers(lot_by, "&status=eq.accepted") if o["fpo_lot_id"] in lot_by]
    buyers = _buyers(o["buyer_id"] for o in deals)
    qty, value = sum(_f(o["qty_qtl"]) for o in deals), sum(_f(o.get("total_value")) for o in deals)
    by_crop, by_month, by_buyer = {}, {}, {}
    for o in deals:
        for key, d in ((lot_by[o["fpo_lot_id"]]["crop"], by_crop), ((o.get("accepted_at") or o.get("decided_at") or "")[:7], by_month),
                       (o["buyer_id"], by_buyer)):
            c = d.setdefault(key, {"qty_qtl": 0, "value": 0, "deals": 0})
            c["qty_qtl"] += _f(o["qty_qtl"])
            c["value"] += _f(o.get("total_value"))
            c["deals"] += 1
    fin = lambda d, k: [{k: key, **{x: round(v, 2) for x, v in c.items()}, "avg_price_rs_qtl": round(c["value"] / c["qty_qtl"]) if c["qty_qtl"] else None}
                        for key, c in d.items()]
    sold_lots = {l["id"] for l in lots if _f(l["total_qty_qtl"]) > _f(l["available_qty_qtl"])}
    links = db.select("fpo_lot_items", f"select=lot_id,farmer_id,qty_qtl&lot_id=in.({_in(sold_lots)})") if sold_lots else []
    farmers = _farmers({i["farmer"] for i in items} | {x["farmer_id"] for x in links})
    contrib = {}
    for i in items:
        c = contrib.setdefault(i["farmer"], {"farmer_id": i["farmer"], "farmer_name": farmers.get(i["farmer"], {}).get("name"),
                                             "given_qty_qtl": 0, "in_sold_lots_qty_qtl": 0})
        c["given_qty_qtl"] = round(c["given_qty_qtl"] + _f(i["qty_qtl"]), 2)
    for x in links:
        c = contrib.setdefault(x["farmer_id"], {"farmer_id": x["farmer_id"], "farmer_name": farmers.get(x["farmer_id"], {}).get("name"),
                                                "given_qty_qtl": 0, "in_sold_lots_qty_qtl": 0})
        c["in_sold_lots_qty_qtl"] = round(c["in_sold_lots_qty_qtl"] + _f(x["qty_qtl"]), 2)
    return {"enough": len(deals) > 0,
            "totals": {"deals": len(deals), "qty_qtl": round(qty, 2), "value": round(value, 2),
                       "avg_price_rs_qtl": round(value / qty) if qty else None, "lots": len(lots),
                       "lots_sold": sum(l["status"] == "sold" for l in lots), "farmers": len(contrib),
                       "inventory_qty_qtl": round(sum(_f(i["qty_qtl"]) for i in items if i["status"] != "sold"), 2)},
            "by_crop": sorted(fin(by_crop, "crop"), key=lambda r: -r["value"]),
            "by_month": sorted(fin(by_month, "month"), key=lambda r: r["month"]),
            "by_buyer": sorted([{**r, "name": (buyers.get(r["buyer_id"]) or {}).get("name"),
                                 "company": (buyers.get(r["buyer_id"]) or {}).get("company")} for r in fin(by_buyer, "buyer_id")],
                               key=lambda r: -r["value"])[:10],
            "farmers": sorted(contrib.values(), key=lambda c: -c["given_qty_qtl"])[:50]}
