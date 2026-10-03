"""Kisaan Khazana FPO dashboard: API (fpo_api.py + api.py FPO routes) against the real Supabase, plus screenshots.

Telegram is captured (api.tg monkeypatched). Test rows: FPOs "KKTEST *", farmers tg:9990009xx, buyers "KKTEST *".
Every test row is deleted at the end.  Run: python test_fpo_dashboard.py [--screens]
--screens also serves the SPA locally and saves Playwright screenshots to docs/screens/kk/ (1366 / 820 / 390 px).
"""
import json, os, sys, threading, time

from fastapi.testclient import TestClient

import api, db, fpo_api

if not any(getattr(r, "path", "") == "/api/fpos/dashboard" for r in api.app.routes):
    api.app.include_router(fpo_api.router)  # until api.py mounts it
SENT = []
api.tg = lambda method, data=None, files=None: SENT.append((method, data or {})) or {"ok": True, "result": {}}
api.TG_TOKEN = "test-token"
c = TestClient(api.app)
H = lambda tok: {"Authorization": f"Bearer {tok}"}
cb = lambda chat, data: api.tg_callback({"id": "cb", "message": {"chat": {"id": 999000000 + chat}, "message_id": 1}, "data": data})
BUYER_SEEN = []
FARMERS = {901: ("KKTEST Ramu", 20.08, 74.11, 25), 902: ("KKTEST Shamu", 20.10, 74.05, 25), 903: ("KKTEST Bhau", 18.52, 73.85, 30)}
OUT = {}  # tokens / ids handed to the screenshot run


def g(tok, path, **params):
    r = c.get(path, headers=H(tok), params=params)
    assert r.status_code == 200, (path, r.status_code, r.text)
    return r.json()


def bget(tok, path, **params):
    r = c.get(path, headers=H(tok), params=params)
    BUYER_SEEN.append(r.text)
    return r


def cleanup():
    fpos = db.select("fpos", "select=id&name=like.KKTEST*")
    fids = ",".join(str(f["id"]) for f in fpos)
    if fids:
        lots = ",".join(str(l["id"]) for l in db.select("fpo_lots", f"select=id&fpo_id=in.({fids})"))
        if lots:
            db._req("DELETE", f"offers?fpo_lot_id=in.({lots})")
            db._req("DELETE", f"fpo_lot_items?lot_id=in.({lots})")
            db._req("DELETE", f"fpo_lots?id=in.({lots})")
        db._req("DELETE", f"listings?fpo_id=in.({fids})")
        db._req("DELETE", f"fpo_members?fpo_id=in.({fids})")
        db._req("DELETE", f"fpos?id=in.({fids})")
    db._req("DELETE", "listings?farmer=like.tg:9990009*")
    for b in db.select("buyers", "select=id&name=like.KKTEST*"):
        db._req("DELETE", f"offers?buyer_id=eq.{b['id']}")
        db._req("DELETE", f"buyers?id=eq.{b['id']}")
    db._req("DELETE", "farmers?phone=like.tg:9990009*")
    db._req("DELETE", "queries?phone=like.tg:9990009*")
    db._req("DELETE", "live_events?channel=eq.kktest")


def main():
    # --- two FPOs ---
    A = c.post("/api/fpos", json={"name": "KKTEST Niphad Shetkari FPO", "phone": "9876590001", "password": "kk-test-passw0rd-A",
                                  "address": "APMC road, Niphad", "lat": 20.08, "lon": 74.10}).json()["fpo_token"]
    B = c.post("/api/fpos", json={"name": "KKTEST Pune FPO", "phone": "9876590002", "password": "kk-test-passw0rd-B",
                                  "address": "Market yard, Pune", "lat": 18.53, "lon": 73.86}).json()["fpo_token"]
    OUT.update(A=A, B=B)
    assert c.get("/api/fpos/dashboard").status_code == 401 and c.get("/api/fpos/dashboard", headers=H("nope")).status_code == 401

    # --- fresh FPO: every page has an empty state ---
    d = g(A, "/api/fpos/dashboard")
    assert d["metrics"] == {"available_qty_qtl": 0, "in_lot_qty_qtl": 0, "open_lots": 0, "draft_lots": 0, "pending_offers": 0,
                            "sold_qty_month": 0, "sold_value_month": 0, "farmers": 0}, d["metrics"]
    assert d["inventory_by_crop"] == [] and d["recent_offers"] == [] and d["active_lots"] == []
    assert g(A, "/api/fpos/inventory/by-crop") == [] and g(A, "/api/fpos/inventory/items")["total"] == 0
    assert g(A, "/api/fpos/farmers")["total"] == 0 and g(A, "/api/fpos/lots/search")["total"] == 0
    assert g(A, "/api/fpos/offers/search")["total"] == 0 and g(A, "/api/fpos/transactions")["total"] == 0
    assert g(A, "/api/fpos/reports")["enough"] is False and g(A, "/api/fpos/notifications")["items"] == []

    # --- farmers give stock on Telegram ("Give to FPO") ---
    for n, (name, lat, lon, q) in FARMERS.items():
        api.save_farmer(f"tg:{999000000 + n}", name=name, lang="mr", lat=lat, lon=lon, last_crop="Onion", last_qty=q,
                        last_mandi_price=2000, last_net=1850, contact_phone="+919876590901" if n == 901 else None)
        cb(n, "L")
    cb(901, "L")  # double tap: same stock row, not doubled
    by = g(A, "/api/fpos/inventory/by-crop")
    assert by == [{"crop": "Onion", "available_qty_qtl": 50, "in_lot_qty_qtl": 0, "sold_qty_qtl": 0, "updated_at": by[0]["updated_at"],
                   "farmers_n": 2, "total_qty_qtl": 50, "status": "available"}], by
    items = g(A, "/api/fpos/inventory/items", crop="Onion", status="open", limit=1)
    assert items["total"] == 2 and len(items["items"]) == 1 and items["has_more"]
    assert g(A, "/api/fpos/inventory/items", q="shamu")["items"][0]["farmer_name"] == "KKTEST Shamu"
    it = g(A, f"/api/fpos/inventory/{items['items'][0]['id']}")
    assert it["farmer"]["farmer_id"].startswith("tg:9990009") and it["lots"] == [] and it["channel"] == "tg"
    assert c.get(f"/api/fpos/inventory/{it['id']}", headers=H(B)).status_code == 404  # FPO B can't read A's stock
    fs = g(A, "/api/fpos/farmers")
    assert fs["total"] == 2 and {f["name"] for f in fs["items"]} == {"KKTEST Ramu", "KKTEST Shamu"}
    ramu = next(f for f in fs["items"] if f["name"] == "KKTEST Ramu")
    assert ramu["phone"] == "+919876590901" and ramu["district"] == "Nashik" and ramu["primary_crop"] == "Onion"
    assert ramu["available_qty_qtl"] == 25 and ramu["channel"] == "tg"
    assert next(f for f in fs["items"] if f["name"] == "KKTEST Shamu")["phone"] is None  # "via Telegram" in the UI
    assert g(A, "/api/fpos/farmers", q="ramu")["total"] == 1 and g(A, "/api/fpos/farmers", crop="Tomato")["total"] == 0
    assert g(A, f"/api/fpos/farmers/{ramu['farmer_id']}")["items"][0]["qty_qtl"] == 25
    assert c.get(f"/api/fpos/farmers/{ramu['farmer_id']}", headers=H(B)).status_code == 404
    assert g(A, "/api/fpos/dashboard")["metrics"]["farmers"] == 2
    assert [n["type"] for n in g(A, "/api/fpos/notifications")["items"]] == ["inventory", "inventory"]
    OUT["ramu"] = ramu["farmer_id"]

    # --- lot: 50 qtl from two farmers, draft -> publish -> unpublish -> publish ---
    ids = [i["id"] for i in g(A, "/api/fpos/inventory/items")["items"]]
    ref = g(A, "/api/fpos/reference-price", crop="Onion")
    lot = c.post("/api/fpos/lots", headers=H(A), json={"inventory_ids": ids, "asking_price_rs_qtl": 2100, "quality": "Grade A",
                                                        "location": "FPO shed, Niphad", "notes": "Dry, 55 mm+", "publish": False}).json()
    assert lot["status"] == "draft" and float(lot["total_qty_qtl"]) == 50, lot
    if ref:
        assert float(lot["market_reference_price"]) == ref["price"]
    L = lot["id"]
    OUT["lot"] = L
    assert g(A, "/api/fpos/inventory/by-crop")[0]["status"] == "in_lot"
    assert g(A, "/api/fpos/lots/search", status="draft")["items"][0]["code"] == f"ON-{L:03d}"
    assert g(A, "/api/fpos/lots/search", q="grade a")["total"] == 1 and g(A, "/api/fpos/lots/search", q="कांदा")["total"] == 1
    det = g(A, f"/api/fpos/lots/{L}")
    assert len(det["items"]) == 2 and {x["farmer_name"] for x in det["contributors"]} == {"KKTEST Ramu", "KKTEST Shamu"} and det["offers"] == []
    assert c.get(f"/api/fpos/lots/{L}", headers=H(B)).status_code == 404
    assert c.post(f"/api/fpos/lots/{L}/publish", headers=H(B)).status_code == 404
    assert c.patch(f"/api/fpos/lots/{L}", headers=H(A), json={"asking_price_rs_qtl": 2150}).json()["asking_price_rs_qtl"] == 2150
    assert c.patch(f"/api/fpos/lots/{L}", headers=H(A), json={"asking_price_rs_qtl": -5}).json()["detail"] == "bad_price"
    assert c.post(f"/api/fpos/lots/{L}/unpublish", headers=H(A)).json()["detail"] == "bad_status"  # draft can't be unpublished

    # --- buyer (trade only) ---
    T1 = c.post("/api/buyers", json={"name": "KKTEST Buyer One", "company": "KKTEST Agro Traders", "type": "wholesale",
                                     "phone": "9876590011", "pin": "4321", "lat": 20.0, "lon": 74.0, "location_text": "Nashik"}).json()["buyer_token"]
    T2 = c.post("/api/buyers", json={"name": "KKTEST Buyer Two", "type": "processor", "phone": "9876590012", "pin": "4321",
                                     "lat": 18.55, "lon": 73.9}).json()["buyer_token"]
    seen = lambda tok: [x["id"] for x in bget(tok, "/api/fpo-lots", radius_km=1000).json()["items"]]
    assert L not in seen(T1)  # draft: hidden
    assert c.post(f"/api/fpos/lots/{L}/publish", headers=H(A)).json()["status"] == "open"
    assert L in seen(T1)
    assert c.post(f"/api/fpos/lots/{L}/unpublish", headers=H(A)).json()["status"] == "draft"
    assert L not in seen(T1)
    assert c.post(f"/api/fpos/lots/{L}/publish", headers=H(A)).json()["status"] == "open"
    assert g(A, "/api/fpos/dashboard")["active_lots"][0]["id"] == L

    # --- offer 20 @ 4000 ---
    off = lambda tok, qty, price: c.post("/api/offers", headers=H(tok), json={"fpo_lot_id": L, "qty_qtl": qty, "price_rs_qtl": price})
    o1 = off(T1, 20, 4000).json()
    BUYER_SEEN.append(json.dumps(o1))
    d = g(A, "/api/fpos/dashboard")
    assert d["metrics"]["pending_offers"] == 1 and d["recent_offers"][0]["offer_id"] == o1["offer_id"]
    assert d["recent_offers"][0]["buyer"] == {"id": d["recent_offers"][0]["buyer"]["id"], "name": "KKTEST Buyer One", "company": "KKTEST Agro Traders",
                                              "type": "wholesale", "location": "Nashik", "phone": None}
    assert g(A, "/api/fpos/offers/search", status="new")["total"] == 1 and g(A, "/api/fpos/offers/search", status="accepted")["total"] == 0
    assert g(A, "/api/fpos/offers/search", q="agro")["total"] == 1 and g(A, "/api/fpos/offers/search", crop="Tomato")["total"] == 0
    od = g(A, f"/api/fpos/offers/{o1['offer_id']}")
    assert od["total_value"] == 80000 and od["buyer_fee"] == 800 and od["code"] == f"ON-{L:03d}" and od["lot"]["available_qty_qtl"] == 50
    assert c.get(f"/api/fpos/offers/{o1['offer_id']}", headers=H(B)).status_code == 404
    assert g(A, "/api/fpos/notifications")["items"][0]["type"] == "offer"
    assert c.post(f"/api/fpos/lots/{L}/unpublish", headers=H(A)).json()["detail"] == "pending_offers"

    # --- accept: lot 30 left, transaction, buyer sees FPO contact ---
    r = c.post(f"/api/fpos/offers/{o1['offer_id']}/accept", headers=H(A))
    assert r.status_code == 200 and float(r.json()["available"]) == 30, r.text
    assert float(g(A, f"/api/fpos/lots/{L}")["available_qty_qtl"]) == 30
    tx = g(A, "/api/fpos/transactions")
    assert tx["total"] == 1 and tx["items"][0]["buyer"]["phone"] == "+919876590011" and tx["items"][0]["total_value"] == 80000
    td = g(A, f"/api/fpos/transactions/{o1['offer_id']}")
    assert {x["farmer_name"] for x in td["contributors"]} == {"KKTEST Ramu", "KKTEST Shamu"} and td["date"]
    assert c.get(f"/api/fpos/transactions/{o1['offer_id']}", headers=H(B)).status_code == 404
    w = bget(T1, f"/api/offers/{o1['offer_id']}").json()
    assert w["status"] == "accepted" and w["fpo_contact"]["phone"] == "+919876590001" and w["fpo_contact"]["pickup"] == "FPO shed, Niphad"
    rep = g(A, "/api/fpos/reports")
    assert rep["enough"] and rep["totals"]["qty_qtl"] == 20 and rep["totals"]["value"] == 80000 and rep["totals"]["avg_price_rs_qtl"] == 4000
    assert rep["by_crop"][0]["crop"] == "Onion" and rep["by_month"][0]["deals"] == 1 and rep["by_buyer"][0]["name"] == "KKTEST Buyer One"
    assert {f["farmer_name"]: f["in_sold_lots_qty_qtl"] for f in rep["farmers"]} == {"KKTEST Ramu": 25, "KKTEST Shamu": 25}
    assert g(A, "/api/fpos/dashboard")["metrics"]["sold_qty_month"] == 20
    assert g(B, "/api/fpos/transactions")["total"] == 0 and g(B, "/api/fpos/offers/search")["total"] == 0

    # --- reject path ---
    o2 = off(T2, 5, 3900).json()
    assert c.post(f"/api/fpos/offers/{o2['offer_id']}/reject", headers=H(A)).json()["ok"] is True
    assert g(A, "/api/fpos/offers/search", status="rejected")["items"][0]["offer_id"] == o2["offer_id"]
    assert bget(T2, f"/api/offers/{o2['offer_id']}").json()["status"] == "rejected"

    # --- oversell: 30 left, two offers of 20 ---
    o3, o4 = off(T1, 20, 4100).json(), off(T2, 20, 4050).json()
    assert c.post(f"/api/fpos/offers/{o3['offer_id']}/accept", headers=H(A)).status_code == 200
    r = c.post(f"/api/fpos/offers/{o4['offer_id']}/accept", headers=H(A))
    assert r.status_code == 409 and r.json()["detail"] == "insufficient_qty", r.text
    assert float(g(A, f"/api/fpos/lots/{L}")["available_qty_qtl"]) == 10 and g(A, "/api/fpos/transactions")["total"] == 2
    OUT.update(offer_pending=o4["offer_id"], offer_done=o1["offer_id"])

    # --- FPO B: draft lot from Bhau's stock, close it -> stock back ---
    bid = [i["id"] for i in g(B, "/api/fpos/inventory/items")["items"]]
    lb = c.post("/api/fpos/lots", headers=H(B), json={"inventory_ids": bid, "asking_price_rs_qtl": 1900, "publish": True}).json()
    assert c.post(f"/api/fpos/lots/{lb['id']}/close", headers=H(B)).json()["status"] == "closed"
    assert g(B, "/api/fpos/inventory/by-crop")[0]["status"] == "available"
    assert c.post(f"/api/fpos/lots/{lb['id']}/publish", headers=H(B)).json()["detail"] == "bad_status"
    assert c.post(f"/api/fpos/lots/{lb['id']}/close", headers=H(A)).status_code == 404
    assert g(B, "/api/fpos/lots/search", status="closed")["total"] == 1 and g(A, "/api/fpos/lots/search", status="closed")["total"] == 0

    # --- settings ---
    me = c.patch("/api/fpos/me", headers=H(A), json={"address": "Shed 4, APMC road, Niphad"}).json()
    assert me["address"] == "Shed 4, APMC road, Niphad" and "token" not in me and "password_hash" not in me

    # --- buyer responses never carry farmer data ---
    blob = "\n".join(BUYER_SEEN)
    for bad in ("KKTEST Ramu", "KKTEST Shamu", "9990009", "farmer_id", "farmer_name", "contributors", "tg:"):
        assert bad not in blob, bad
    print("FPO dashboard API checks passed")


def screens():
    """Serve api.app (with the router) on a local port and photograph every page at 3 widths."""
    import uvicorn
    from playwright.sync_api import sync_playwright
    port, out = 8765, "docs/screens/kk"
    os.makedirs(out, exist_ok=True)
    srv = uvicorn.Server(uvicorn.Config(api.app, port=port, log_level="warning"))
    threading.Thread(target=srv.run, daemon=True).start()
    while not srv.started:
        time.sleep(0.1)
    base = f"http://{srv.config.host}:{port}/app/kk/"  # the uvicorn test server above
    pages = [("login", "#/login", None), ("overview", "#/overview", "A"), ("inventory", "#/inventory", "A"),
             ("farmers", "#/farmers", "A"), ("lots", "#/lots", "A"), ("create-lot", "#/lots/new", "B"),
             ("lot-detail", f"#/lots/{OUT['lot']}", "A"), ("offers", "#/offers", "A"),
             ("offer-detail", f"#/offers/{OUT['offer_pending']}", "A"), ("transactions", "#/transactions", "A"),
             ("reports", "#/reports", "A"), ("settings", "#/settings", "A"), ("overview-mr", "#/overview", "A")]
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in (1366, 820, 390):
            shots = [p for p in pages if w == 1366 or not p[0].endswith("-mr")]
            pg = br.new_page(viewport={"width": w, "height": 900 if w > 400 else 844}, device_scale_factor=1)
            pg.on("pageerror", lambda e: print("PAGE ERROR", w, e))
            pg.on("console", lambda m: print("CONSOLE", w, m.type, m.text) if m.type in ("error", "warning") else None)
            for name, hash_, who in shots:
                pg.goto(base)
                pg.evaluate(f"localStorage.setItem('kk_lang','{'mr' if name.endswith('-mr') else 'en'}'); " + (f"localStorage.setItem('kk_token', {json.dumps(OUT[who])})" if who else "localStorage.removeItem('kk_token')"))
                pg.goto("about:blank")  # a hash-only change would not reload the app with the new token
                pg.goto(base + hash_)
                pg.wait_for_function("!document.querySelector('.skeleton') && document.querySelector('main, .auth')", timeout=20000)
                pg.wait_for_timeout(700)
                if name == "create-lot":  # walk the wizard to the price step (crop chip -> stock -> price)
                    pg.click(".chip"); pg.click("#next"); pg.wait_for_selector("input[type=checkbox]"); pg.click("#next")
                    pg.wait_for_selector("#price"); pg.wait_for_timeout(500)
                pg.screenshot(path=f"{out}/{name}_{w}.png", full_page=w > 400)
            pg.close()
        br.close()
    srv.should_exit = True
    print("screens saved to", out)


if __name__ == "__main__":
    try:
        main()
        if "--screens" in sys.argv:
            screens()
    finally:
        cleanup()
        left = (db.select("farmers", "select=phone&phone=like.tg:9990009*") + db.select("buyers", "select=id&name=like.KKTEST*")
                + db.select("fpos", "select=id&name=like.KKTEST*") + db.select("listings", "select=id&farmer=like.tg:9990009*"))
        print("cleanup:", "clean" if not left else f"LEFTOVER {json.dumps(left)}")
