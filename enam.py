"""eNAM trade/price data -> Supabase `prices` (source='enam'). Same calls as enam.gov.in's own pages.

As of 2026-10-02 both calls return HTTP 500 for everyone (also from Indian browsers), so this runs as a watcher.
Usage: python enam.py check                    -> exit 0 if a call returns data
       python enam.py 2026-09-01 2026-10-02    -> pull that range for Maharashtra
"""
import datetime as dt, http.cookiejar, json, sys, time, urllib.parse, urllib.request

BASE = "https://enam.gov.in/"
STATE = "MAHARASHTRA"
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/141.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest", "Referer": BASE + "dashboard/live_price", "Origin": "https://enam.gov.in"}
CALLS = [  # (path, body builder) — from the page source of dashboard/live_price and dashboard/trade-data
    ("Liveprice_ctrl/trade_data_list", lambda d: {"language": "en", "stateName": STATE, "fromDate": d, "toDate": d}),
    ("Ajax_ctrl/trade_data_list", lambda d: {"language": "en", "stateName": STATE, "apmcName": "-- All --",
                                             "commodityName": "-- All --", "fromDate": d, "toDate": d}),
]
web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def post(path, body):
    req = urllib.request.Request(BASE + path, urllib.parse.urlencode(body).encode(), HEAD)
    with web.open(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def day_rows(day):
    """Try each call and date format; return (call, raw rows)."""
    for path, mk in CALLS:
        for d in (day, "-".join(reversed(day.split("-")))):
            try:
                js = post(path, mk(d))
            except Exception:
                continue
            data = list((js or {}).get("data") or {})
            if isinstance((js or {}).get("data"), dict):
                data = list(js["data"].values())
            if data:
                return path, data
    return None, []


def to_price(r, day):
    """eNAM field names vary by endpoint; map the common ones, keep raw in variety if unsure."""
    g = lambda *ks: next((r[k] for k in ks if r.get(k) not in (None, "")), None)
    modal = g("modal_price", "modalPrice", "modal")
    if not modal:
        return None
    return {"date": day, "market": str(g("apmc", "apmc_name", "apmcName") or "?").strip(),
            "commodity": str(g("commodity", "commodity_name", "commodityName") or "?").strip().title(),
            "variety": "", "min": g("min_price", "minPrice"), "max": g("max_price", "maxPrice"),
            "modal": float(modal), "arrivals_t": None, "source": "enam"}


if __name__ == "__main__":
    web.open(urllib.request.Request(BASE + "dashboard/live_price", headers=HEAD), timeout=60).read()  # session
    if sys.argv[1] == "check":
        path, rows = day_rows((dt.date.today() - dt.timedelta(days=1)).isoformat())
        print("enam UP via" if rows else "enam DOWN", path or "", len(rows), "rows")
        if rows:
            print("sample fields:", sorted(rows[0].keys()))
        sys.exit(0 if rows else 1)
    import db
    d0, d1, total = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]), 0
    while d0 <= d1:
        _, raw = day_rows(d0.isoformat())
        rows = [p for p in (to_price(r, d0.isoformat()) for r in raw) if p]
        rows = list({(r["date"], r["market"], r["commodity"], r["variety"], r["source"]): r for r in rows}.values())
        total += db.upsert("prices", rows) if rows else 0
        print(d0, len(raw), "raw", len(rows), "saved", flush=True)
        d0 += dt.timedelta(days=1)
        time.sleep(1)
    db.log_run("enam", "ok", total, f"{sys.argv[1]}..{sys.argv[2]}")
