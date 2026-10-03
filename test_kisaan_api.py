"""End-to-end test of Kisaan Khazana (FPO marketplace) against the real Supabase (needs .env + sql/schema_v4.sql).

Telegram is captured (api.tg monkeypatched): nothing is sent, no bot token needed.
Farmers tg:99900010x -> FPO inventory -> FPO lots -> 2 buyers offer -> concurrent accepts (20 + 30 on a 40 qtl lot).
Every test row is deleted at the end. Run: python test_kisaan_api.py
"""
import json, threading

from fastapi.testclient import TestClient

import api, db

FARMERS = {101: (20.08, 74.11, 25), 102: (20.10, 74.05, 15), 103: (18.52, 73.85, 30), 104: (19.80, 80.00, 10)}
SENT = []
api.tg = lambda method, data=None, files=None: SENT.append((method, data or {})) or {"ok": True, "result": {}}
api.TG_TOKEN = "test-token"
c = TestClient(api.app)
H = lambda tok: {"Authorization": f"Bearer {tok}"}
cb = lambda chat, data: api.tg_callback({"id": "cb", "message": {"chat": {"id": 999000000 + chat}, "message_id": 1}, "data": data})
BUYER_SEEN = []  # every buyer-facing response body, scanned for farmer data at the end


def bget(tok, path, **kw):
    r = c.get(path, headers=H(tok), **kw)
    BUYER_SEEN.append(r.text)
    return r


def bpost(tok, path, body):
    r = c.post(path, headers=H(tok), json=body)
    BUYER_SEEN.append(r.text)
    return r


def texts(chat):
    return [d.get("text", "") for m, d in SENT if m == "sendMessage" and str(d.get("chat_id")) == str(999000000 + chat)]


def cleanup():
    fpos = db.select("fpos", "select=id&name=like.SSTEST*")
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
    db._req("DELETE", "listings?farmer=like.tg:9990001*")
    for b in db.select("buyers", "select=id&name=like.SSTEST*"):
        db._req("DELETE", f"offers?buyer_id=eq.{b['id']}")
        db._req("DELETE", f"buyers?id=eq.{b['id']}")
    db._req("DELETE", "farmers?phone=like.tg:9990001*")
    db._req("DELETE", "queries?phone=like.tg:9990001*")


def main():
    # --- FPOs register / login ---
    fpo = lambda **kw: c.post("/api/fpos", json={"name": "SSTEST FPO A", "phone": "9876511111", "password": "kisaan-secret-1",
                                                 "email": "sstest-a@kisaan.test", "address": "APMC road, Niphad", "lat": 20.08, "lon": 74.10, **kw})
    assert fpo(password="short").json()["detail"] == "bad_password"
    assert fpo(lat=None).json()["detail"] == "bad_location"
    ra = fpo()
    assert ra.status_code == 200, ra.text
    A = ra.json()["fpo_token"]
    assert ra.json()["fpo"]["district"] == "Nashik" and "password_hash" not in ra.text and "token" not in ra.json()["fpo"]
    assert fpo().status_code == 409  # same phone/email
    B = c.post("/api/fpos", json={"name": "SSTEST FPO B", "phone": "9876522222", "password": "kisaan-secret-2",
                                  "address": "Market yard, Pune", "lat": 18.53, "lon": 73.86}).json()["fpo_token"]
    assert c.post("/api/fpos/login", json={"login": "9876511111", "password": "wrong-pass"}).status_code == 401
    assert c.post("/api/fpos/login", json={"login": "+91 98765 11111", "password": "kisaan-secret-1"}).json()["fpo_token"] == A
    assert c.post("/api/fpos/login", json={"login": "SSTEST-A@kisaan.test", "password": "kisaan-secret-1"}).json()["fpo_token"] == A
    assert c.get("/api/fpos/me").status_code == 401 and c.get("/api/fpos/me", headers=H(A)).json()["name"] == "SSTEST FPO A"
    stored = db.select("fpos", "select=password_hash&name=eq.SSTEST%20FPO%20A")[0]["password_hash"]
    assert stored.startswith("scrypt$") and "kisaan-secret-1" not in stored

    # --- farmers give stock to the nearest FPO on Telegram ---
    for n, (lat, lon, q) in FARMERS.items():
        api.save_farmer(f"tg:{999000000 + n}", name=f"SSTEST Farmer {n}", lang="en", lat=lat, lon=lon, last_crop="Onion",
                        last_qty=q, last_mandi_price=2000, last_net=1850)
        cb(n, "L")
    cb(101, "L")  # tapping twice updates, doesn't double
    assert any("SSTEST FPO A" in t for t in texts(101)) and any("SSTEST FPO B" in t for t in texts(103)), SENT
    assert any("No FPO is registered within 60 km" in t for t in texts(104))
    inv_a = c.get("/api/fpos/inventory", headers=H(A)).json()
    inv_b = c.get("/api/fpos/inventory", headers=H(B)).json()
    assert sorted(i["qty_qtl"] for i in inv_a) == [15, 25] and len(inv_b) == 1, (inv_a, inv_b)
    assert {i["farmer_name"] for i in inv_a} == {"SSTEST Farmer 101", "SSTEST Farmer 102"}
    assert db.select("fpo_members", "select=farmer_id&farmer_id=like.tg:9990001*&order=farmer_id") == \
        [{"farmer_id": "tg:999000101"}, {"farmer_id": "tg:999000102"}, {"farmer_id": "tg:999000103"}]

    # --- FPO lots ---
    ids_a, ids_b = [i["id"] for i in inv_a], [i["id"] for i in inv_b]
    assert c.post("/api/fpos/lots", headers=H(B), json={"inventory_ids": ids_a, "asking_price_rs_qtl": 2000}).json()["detail"] == "bad_items"
    assert c.post("/api/fpos/lots", headers=H(A), json={"inventory_ids": ids_a, "asking_price_rs_qtl": 0}).json()["detail"] == "bad_price"
    la = c.post("/api/fpos/lots", headers=H(A), json={"inventory_ids": ids_a, "asking_price_rs_qtl": 2100, "quality": "A grade",
                                                      "notes": "Dry, sorted", "location": "FPO shed, Niphad", "publish": True})
    assert la.status_code == 200, la.text
    la = la.json()
    assert la["total_qty_qtl"] == 40 and la["available_qty_qtl"] == 40 and la["status"] == "open"
    assert all(i["status"] == "in_lot" for i in c.get("/api/fpos/inventory", headers=H(A)).json())
    assert c.post("/api/fpos/lots", headers=H(A), json={"inventory_ids": ids_a, "asking_price_rs_qtl": 2100}).json()["detail"] == "bad_items"
    lb = c.post("/api/fpos/lots", headers=H(B), json={"inventory_ids": ids_b, "asking_price_rs_qtl": 1900, "market_reference_price": 2050}).json()
    assert lb["status"] == "draft" and lb["market_reference_price"] == 2050
    print("reference price for Onion near FPO A:", c.get("/api/fpos/reference-price?crop=Onion", headers=H(A)).json())

    # --- buyers register / login ---
    reg = lambda **kw: c.post("/api/buyers", json={"name": "SSTEST Buyer One", "type": "processor", "phone": "9876533333", "pin": "4321",
                                                   "lat": 20.0, "lon": 73.79, "location_text": "Nashik city", **kw})
    assert reg(pin="12").json()["detail"] == "bad_pin" and reg(pin="12ab").json()["detail"] == "bad_pin"
    assert reg(type="retail").json()["detail"] == "bad_type"
    assert reg(type="individual").json()["detail"] == "bad_type"  # trade buyers only
    r1 = reg()
    assert r1.status_code == 200, r1.text
    T1 = r1.json()["buyer_token"]
    assert r1.json()["buyer"]["type"] == "processor" and "pin_hash" not in r1.text
    assert reg().json()["detail"] == "phone_taken"
    T2 = c.post("/api/buyers", json={"name": "SSTEST Buyer Two", "company": "SSTEST Traders", "type": "wholesale", "phone": "9876544444",
                                     "pin": "123456", "lat": 18.55, "lon": 73.9}).json()["buyer_token"]
    assert c.post("/api/buyers/login", json={"phone": "9876533333", "pin": "0000"}).status_code == 401
    assert c.post("/api/buyers/login", json={"phone": "+919876533333", "pin": "4321"}).json()["buyer_token"] == T1
    assert c.get("/api/buyers/me").status_code == 401
    assert c.patch("/api/buyers/me", headers=H(T1), json={"location_text": "Nashik Road"}).json()["location_text"] == "Nashik Road"

    # --- marketplace (draft lot invisible) ---
    q = lambda tok, **p: bget(tok, "/api/fpo-lots", params=p).json()
    ids = lambda res: [x["id"] for x in res["items"]]
    assert la["id"] in ids(q(T1, radius_km=50)) and lb["id"] not in ids(q(T1, radius_km=1000))
    assert bget(T1, f"/api/fpo-lots/{lb['id']}").status_code == 404  # draft lots are invisible to buyers
    assert c.patch(f"/api/fpos/lots/{lb['id']}", headers=H(A), json={"status": "open"}).status_code == 404  # FPO A can't touch B's lot
    assert c.patch(f"/api/fpos/lots/{lb['id']}", headers=H(B), json={"status": "open"}).json()["status"] == "open"
    wide = q(T1, radius_km=300)
    assert {la["id"], lb["id"]} <= set(ids(wide)) and [x["km"] for x in wide["items"]] == sorted(x["km"] for x in wide["items"])
    assert {"crop": "Onion", "lots": wide["total"]} in wide["crops"]
    assert ids(q(T1, radius_km=300, q="sstest fpo b")) == [lb["id"]]
    assert la["id"] in ids(q(T1, radius_km=300, q="कांदा")) and la["id"] in ids(q(T1, radius_km=300, q="niphad"))
    assert lb["id"] not in ids(q(T1, radius_km=300, min_qty=35)) and la["id"] in ids(q(T1, radius_km=300, min_qty=35))
    assert la["id"] not in ids(q(T1, radius_km=300, max_price=2000)) and lb["id"] in ids(q(T1, radius_km=300, max_price=2000))
    pr = [x["asking_price_rs_qtl"] for x in q(T1, radius_km=300, sort="price_desc")["items"]]
    assert pr == sorted(pr, reverse=True)
    p1, p2 = q(T1, radius_km=300, limit=1, page=1), q(T1, radius_km=300, limit=1, page=2)
    assert p1["has_more"] and ids(p1) != ids(p2)
    d = bget(T1, f"/api/fpo-lots/{la['id']}").json()
    assert d["farmers_n"] == 2 and d["fpo"]["name"] == "SSTEST FPO A" and d["my_offer"] is None and "phone" not in d["fpo"]
    assert c.get("/api/fpo-lots").status_code == 401

    # --- offers ---
    off = lambda tok, lot, qty, price, **kw: bpost(tok, "/api/offers", {"fpo_lot_id": lot, "qty_qtl": qty, "price_rs_qtl": price, **kw})
    assert off(T1, la["id"], 0, 2000).json()["detail"] == "bad_qty"
    assert off(T1, la["id"], 41, 2000).json()["detail"] == "bad_qty"
    assert off(T1, la["id"], 10, 0).json()["detail"] == "bad_price"
    assert off(T1, 987654321, 10, 2000).json()["detail"] == "lot_closed"
    o1 = off(T1, la["id"], 20, 2050, buyer_fee=0).json()
    assert o1["offer"]["total_value"] == 41000 and o1["offer"]["buyer_fee"] == 410 and o1["offer"]["fpo_contact"] is None
    assert off(T1, la["id"], 5, 2050).json()["detail"] == "duplicate_offer"
    o2 = off(T2, la["id"], 30, 2000).json()
    o3 = off(T1, lb["id"], 10, 1900).json()  # on B's lot, will be closed by B later
    assert bget(T2, f"/api/offers/{o1['offer_id']}").status_code == 404  # buyer 2 can't read buyer 1's offer
    assert o1["offer_id"] not in [o["offer_id"] for o in bget(T2, "/api/offers").json()]

    # --- FPO side: authorization ---
    assert c.post(f"/api/fpos/offers/{o1['offer_id']}/accept", headers=H(B)).status_code == 404
    assert o1["offer_id"] not in [o["offer_id"] for o in c.get("/api/fpos/offers", headers=H(B)).json()]
    fa = {o["offer_id"]: o for o in c.get("/api/fpos/offers", headers=H(A)).json()}
    assert fa[o1["offer_id"]]["buyer"]["name"] == "SSTEST Buyer One" and fa[o1["offer_id"]]["buyer"]["phone"] is None
    assert fa[o2["offer_id"]]["buyer"]["company"] == "SSTEST Traders" and fa[o2["offer_id"]]["total_value"] == 60000

    # --- race: 20 + 30 on a 40 qtl lot, both accepted at the same moment ---
    res = {}

    def accept(oid):
        res[oid] = TestClient(api.app).post(f"/api/fpos/offers/{oid}/accept", headers=H(A))

    ts = [threading.Thread(target=accept, args=(o["offer_id"],)) for o in (o1, o2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    codes = sorted(r.status_code for r in res.values())
    assert codes == [200, 409], {k: (v.status_code, v.text) for k, v in res.items()}
    win = next(k for k, v in res.items() if v.status_code == 200)
    lose = next(k for k, v in res.items() if v.status_code == 409)
    assert res[lose].json()["detail"] == "insufficient_qty"
    won_qty = 20 if win == o1["offer_id"] else 30
    lot_now = db.select("fpo_lots", f"select=available_qty_qtl,status&id=eq.{la['id']}")[0]
    assert float(lot_now["available_qty_qtl"]) == 40 - won_qty and lot_now["status"] == "open", lot_now
    assert c.post(f"/api/fpos/offers/{lose}/accept", headers=H(A)).json()["detail"] == "insufficient_qty"
    assert c.post(f"/api/fpos/offers/{win}/accept", headers=H(A)).json()["detail"] == "not_pending"
    print(f"race: offer {win} ({won_qty} qtl) accepted, offer {lose} refused with 409 insufficient_qty")

    # --- contact only for the accepted buyer ---
    win_tok, lose_tok = (T1, T2) if win == o1["offer_id"] else (T2, T1)
    w = bget(win_tok, f"/api/offers/{win}").json()
    assert w["status"] == "accepted" and w["accepted_at"] and w["fpo_contact"]["phone"] == "+919876511111"
    assert w["fpo_contact"]["whatsapp"] == "https://wa.me/919876511111" and w["fpo_contact"]["pickup"] == "FPO shed, Niphad"
    assert bget(lose_tok, f"/api/offers/{lose}").json()["fpo_contact"] is None
    assert any("sold from the Onion lot" in t for t in texts(101)) and any("sold from the Onion lot" in t for t in texts(102))
    assert not texts(103) or not any("sold from" in t for t in texts(103))

    # --- reject path ---
    assert c.post(f"/api/fpos/offers/{lose}/reject", headers=H(A)).json()["ok"] is True
    rj = bget(lose_tok, f"/api/offers/{lose}").json()
    assert rj["status"] == "rejected" and rj["rejected_at"] and rj["fpo_contact"] is None
    assert c.post(f"/api/fpos/offers/{lose}/reject", headers=H(A)).json()["detail"] == "not_pending"

    # --- sell out the rest: lot sold, inventory sold, gone from the market ---
    rest = 40 - won_qty
    o4 = off(lose_tok, la["id"], rest, 2080).json()
    assert c.post(f"/api/fpos/offers/{o4['offer_id']}/accept", headers=H(A)).status_code == 200
    assert db.select("fpo_lots", f"select=status&id=eq.{la['id']}")[0]["status"] == "sold"
    assert all(i["status"] == "sold" for i in c.get("/api/fpos/inventory", headers=H(A)).json())
    assert la["id"] not in ids(q(T1, radius_km=1000))
    assert off(T1, la["id"], 1, 2000).json()["detail"] == "lot_closed"

    # --- FPO B closes its lot unsold: pending offer rejected, stock back in inventory ---
    assert c.patch(f"/api/fpos/lots/{lb['id']}", headers=H(B), json={"status": "closed"}).json()["status"] == "closed"
    assert bget(T1, f"/api/offers/{o3['offer_id']}").json()["status"] == "rejected"
    assert [i["status"] for i in c.get("/api/fpos/inventory", headers=H(B)).json()] == ["open"]
    assert c.patch(f"/api/fpos/lots/{lb['id']}", headers=H(B), json={"status": "open"}).status_code == 409

    # --- buyers never received farmer data; public stock is aggregated ---
    blob = "\n".join(BUYER_SEEN)
    for bad in ("999000", "SSTEST Farmer", "farmer_id", "farmer_name", "inventory", "tg:", "tg://"):
        assert bad not in blob, bad
    assert "9876511111" not in "\n".join(b for b in BUYER_SEEN if '"fpo_contact"' not in b)  # lot list/detail never show the FPO phone
    stock = c.get("/api/stock").json()
    assert all(set(s) <= {"crop", "district", "qty_qtl", "lots", "ready_date", "condition", "spoil_rate_per_day"} for s in stock)
    print("all Kisaan Khazana API checks passed")


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
        left = (db.select("farmers", "select=phone&phone=like.tg:9990001*") + db.select("buyers", "select=id&name=like.SSTEST*")
                + db.select("fpos", "select=id&name=like.SSTEST*") + db.select("listings", "select=id&farmer=like.tg:9990001*"))
        print("cleanup:", "clean" if not left else f"LEFTOVER {json.dumps(left)}")
