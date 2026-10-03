"""MSAMB (Maharashtra State Agricultural Marketing Board) live rates -> Supabase `prices` (source='msamb').

MSAMB only serves the last ~8 days and has no date parameter (checked its page code), so a daily job
accumulates history from here on. Same-day data, with arrivals, for all 291 APMC yards, all crops.
Usage: python msamb.py
"""
import http.cookiejar, re, time, urllib.request
from datetime import datetime

import db

BASE = "https://www.msamb.com"
HEAD = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE}/ApmcDetail/ArrivalPriceInfo"}  # grid returns empty without these

jar = http.cookiejar.CookieJar()
web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(path, data=None):
    req = urllib.request.Request(BASE + path, data=data, headers=HEAD)
    with web.open(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")


def cells(tr):
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", td)).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]


def num(s):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def parse(html, market, kind="apmc"):
    """kind: apmc (7 cols, date header rows) | private (6 cols, date header rows) | direct (5 cols, date first, one rate)."""
    rows, day = [], None
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        c = cells(tr)
        if len(c) == 1:
            day = datetime.strptime(c[0].replace("Arrival Date:", "").strip(), "%d/%m/%Y").date().isoformat()
            continue
        if kind == "direct" and len(c) == 5:  # date, crop, unit, qty, single purchase rate
            day = datetime.strptime(c[0], "%d/%m/%Y").date().isoformat()
            c = [c[1], "", c[2], c[3], c[4], c[4], c[4]]
        elif kind == "private" and len(c) == 6:
            c = [c[0], ""] + c[1:]
        if len(c) == 7 and day:
            commodity, variety, unit, arr, lo, hi, modal = c
            # ponytail: keep ₹/quintal rows only; fruit sold per NOS/dozen/crate needs a unit column first
            if unit.upper() != "QUINTAL" or not num(modal):
                continue
            rows.append({"date": day, "market": market, "commodity": commodity.title(),
                         "variety": "" if variety.startswith("--") else variety.title(),
                         "min": num(lo), "max": num(hi), "modal": num(modal),
                         "arrivals_t": (num(arr) or 0) / 10, "source": "msamb" if kind == "apmc" else f"msamb_{kind}"})
    return rows


if __name__ == "__main__":
    fetch("/ApmcDetail/ArrivalPriceInfo")              # session cookie
    fetch("/Home/ChangeLanguage", data=b"")             # toggle Marathi -> English names
    import json
    apmcs = json.loads(fetch("/ApmcDetail/GetApmcForArrivalPriceInfo"))
    out = []
    for a in apmcs:
        try:
            out += parse(fetch(f"/ApmcDetail/DataGridBind?commodityCode=null&apmcCode={a['ApmcCode']}"), a["ApmcNameE"].title())
        except Exception as e:
            print(a["ApmcNameE"], "failed:", e)
        time.sleep(0.3)  # polite
    # other ways to sell: licensed private markets and direct-purchase companies (same 8-day window)
    for kind, lst, grid in [("private", "GetCommoditiesForPrivatePriceInfo", "GetArrivalPriceInfoByPrivateMarketWise"),
                            ("direct", "GetCommoditiesForDirectPriceInfo", "GetArrivalPriceInfoByDirectMarketWise")]:
        for m in json.loads(fetch(f"/ApmcDetail/{lst}")):
            try:
                out += parse(fetch(f"/ApmcDetail/{grid}?commodityCode=null&apmcCode={m['MarketCode']}"), m["MarketNameE"], kind)
            except Exception as e:
                print(m["MarketNameE"], "failed:", e)
            time.sleep(0.3)
    out = list({(r["date"], r["market"], r["commodity"], r["variety"], r["source"]): r for r in out}.values())
    n = db.upsert("prices", out)
    db.log_run("msamb", "ok", n, f"{len(apmcs)} APMCs")
    import collections
    print(collections.Counter(r["source"] for r in out))
    print(f"msamb: {n} rows, {len({r['market'] for r in out})} markets, {len({r['commodity'] for r in out})} crops,",
          min(r["date"] for r in out), "->", max(r["date"] for r in out))
