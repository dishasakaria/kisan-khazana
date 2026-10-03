"""Agmarknet 2.0 -> Supabase `prices` (source='agmarknet'), all crops, pilot districts, with ARRIVALS.

One call per day returns every commodity x market for the state (daily-report-state), so a backfill is ~1 call/day.
Usage: python agmarknet.py check                 -> exit 0 if the API is up
       python agmarknet.py 2026-01-01 2026-10-02 -> backfill/refresh that range
"""
import datetime as dt, json, sys, time, urllib.request

API = "https://api.agmarknet.gov.in/v1"
STATE = 20  # Maharashtra
PILOT = {"Pune", "Ahilyanagar", "Ahmednagar", "Nashik"}
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/141.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://agmarknet.gov.in", "Referer": "https://agmarknet.gov.in/"}  # what the site itself sends


def get(path, timeout=90):
    with urllib.request.urlopen(urllib.request.Request(f"{API}/{path}", headers=HEAD), timeout=timeout) as r:
        return json.load(r)


def pilot_markets():
    f = get("daily-price-arrival/filters")["data"]
    dist = {d["id"]: d["district_name"] for d in f["district_data"]}
    return {m["mkt_name"].strip(): dist.get(m["district_id"]) for m in f["market_data"]
            if m.get("state_id") == STATE and dist.get(m["district_id"]) in PILOT}


def day_rows(day, markets):
    js = get(f"prices-and-arrivals/commodity-market/daily-report-state?date={day}&state={STATE}")
    out = []
    for g in js.get("commodityGroups") or []:
        for c in g["commodities"]:
            for m in c["markets"]:
                name = m["marketCenter"].strip()
                if name not in markets:
                    continue
                for x in m["data"]:
                    unit = (x.get("unitOfArrivals") or "").lower()
                    arr = x.get("arrivals")
                    if arr is not None and "quintal" in unit:
                        arr = arr / 10  # store tonnes everywhere
                    if not x.get("modalPrice"):
                        continue
                    out.append({"date": day, "market": name, "commodity": c["commodityName"].strip(),
                                "variety": (x.get("variety") or "").strip(), "min": x.get("minimumPrice"),
                                "max": x.get("maximumPrice"), "modal": x["modalPrice"], "arrivals_t": arr,
                                "source": "agmarknet"})
    return out


if __name__ == "__main__":
    if sys.argv[1] == "check":
        try:
            get("daily-price-arrival/filters", timeout=30)
            print("agmarknet UP")
        except Exception as e:
            print("agmarknet DOWN:", e)
            sys.exit(1)
        sys.exit(0)
    import db
    d0, d1 = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])
    markets = pilot_markets()
    total = 0
    while d0 <= d1:
        try:
            rows = day_rows(d0.isoformat(), markets)
            # duplicate keys inside one batch break the upsert: keep the last
            rows = list({(r["date"], r["market"], r["commodity"], r["variety"]): r for r in rows}.values())
            total += db.upsert("prices", rows)
            print(d0, len(rows), "rows", flush=True)
        except Exception as e:
            print(d0, "failed:", e, flush=True)
        d0 += dt.timedelta(days=1)
        time.sleep(1)
    db.log_run("agmarknet", "ok", total, f"{sys.argv[1]}..{sys.argv[2]}")
