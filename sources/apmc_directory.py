"""MSAMB APMC directory (all Maharashtra APMCs + sub-yards) -> data/ext/apmc_directory.csv.

Source: https://msamb.com/ApmcDetail/Profile (same JSON the page's Profile.js loads):
  /ApmcDetail/GetDistrictForAPMCProfile  -> districts + APMC codes
  /ApmcDetail/ProfileDetail?apmcId=CODE  -> address, PIN, phone, yards, commodities, arrivals, facilities ...
One row per yard: kind=apmc (main market, all details) or sub_yard (name, area, est. date; APMC fields repeated).
arrivals_* are as published (quintals per MSAMB convention), value_* in Rs; FY labels in arrivals_years.
Geocoded via Nominatim/Photon (1 req/s, cached); geo_quality = name | pin | district_hq (fallback) .
Usage: python sources/apmc_directory.py
"""
import csv, http.cookiejar, json, os, time, urllib.request

from districts import EXT, HQ, UA, canon, geocode

BASE = "https://msamb.com"
OUT = os.path.join(EXT, "apmc_directory.csv")
CACHE = os.path.join(EXT, ".cache", "msamb")  # raw profiles, reused for 20 days
jar = http.cookiejar.CookieJar()
web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(path, xhr=True):
    h = {"User-Agent": UA, "Referer": BASE + "/ApmcDetail/Profile"}
    if xhr:
        h["X-Requested-With"] = "XMLHttpRequest"
    for i in range(4):
        try:
            with web.open(urllib.request.Request(BASE + path, headers=h), timeout=60) as r:
                body = r.read().decode("utf-8", "ignore")
            return json.loads(body) if xhr else body
        except Exception:
            if i == 3:
                raise
            time.sleep(5 * (i + 1))


def clean(s):
    return " ".join(str(s or "").split()).strip(" ,")


COLS = ["kind", "apmc_code", "apmc_name", "apmc_name_mr", "yard_name", "district", "msamb_district", "address",
        "address_mr", "pin", "phone", "secretary", "secretary_mobile", "established", "yard_area_ha", "yard_since",
        "n_sub_yards", "sub_yards", "main_commodities", "arrivals_years", "arrivals_y1", "arrivals_y2", "arrivals_y3",
        "value_rs_y1", "value_rs_y2", "value_rs_y3", "facilities", "cold_storage", "warehouses_n", "warehouse_capacity",
        "licenses", "lat", "lon", "geo_quality"]

if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    get("/ApmcDetail/Profile", xhr=False)  # session cookie
    rows = []
    for d in get("/ApmcDetail/GetDistrictForAPMCProfile"):
        dist = canon(d["DistrictNameE"])
        for a in d["ApmcList"]:
            cf = os.path.join(CACHE, a["ApmcCode"] + ".json")
            try:
                if os.path.exists(cf) and time.time() - os.path.getmtime(cf) < 20 * 86400:
                    p = json.load(open(cf))
                else:
                    time.sleep(0.5)
                    p = get(f"/ApmcDetail/ProfileDetail?apmcId={a['ApmcCode']}")[0]
                    json.dump(p, open(cf, "w"), ensure_ascii=False)
            except Exception as e:
                print("profile FAILED (row kept with name/district only)", a["ApmcCode"], a["ApmcNameE"], e)
                p = {}
            yards = p.get("MarketList") or []
            main = [y for y in yards if clean(y.get("MainMarketNameE"))]
            subs = [y for y in yards if not clean(y.get("MainMarketNameE")) and clean(y.get("MarketNameE"))]
            ann = sorted(p.get("AnnualIncomeExpense") or [], key=lambda x: x["FinancialYear"], reverse=True)[:3]
            ann += [{}] * (3 - len(ann))
            fac = [clean(f["FacilityNameE"]) for f in p.get("FacilitiesInMarket") or []]
            wh = p.get("MarketWareHouses") or []
            base = {
                "apmc_code": a["ApmcCode"], "apmc_name": clean(a["ApmcNameE"]), "apmc_name_mr": clean(a["ApmcNameM"]),
                "district": dist, "msamb_district": d["DistrictNameE"], "address": clean(p.get("AddressE")),
                "address_mr": clean(p.get("AddressM")), "pin": clean(p.get("PinCode")),
                "phone": "-".join(x for x in (clean(p.get("STDCode")), clean(p.get("Phone"))) if x),
                "secretary": clean(p.get("SecretaryE")), "secretary_mobile": clean(p.get("SecretaryMobileNo")),
                "established": (p.get("ApmcStartDate") or "")[:10], "n_sub_yards": len(subs),
                "sub_yards": "; ".join(clean(y["MarketNameE"]) for y in subs),
                "main_commodities": "; ".join(clean(c["CommodityNameE"]) for c in p.get("ImpCommodityList") or []),
                "arrivals_years": "; ".join(x.get("FinancialYear", "") for x in ann if x),
                **{f"arrivals_y{i+1}": round(float(x["Arrivals"])) if x.get("Arrivals") else "" for i, x in enumerate(ann)},
                **{f"value_rs_y{i+1}": round(float(x["Price"])) if x.get("Price") else "" for i, x in enumerate(ann)},
                "facilities": "; ".join(fac), "cold_storage": int(any("COLD" in f.upper() for f in fac)),
                "warehouses_n": sum(float(w.get("NoOfWareHouses") or 0) for w in wh) or "",
                "warehouse_capacity": sum(float(w.get("CapacityOfWareHouses") or 0) for w in wh) or "",
                "licenses": "; ".join(f"{clean(l['LicenseNameE'])}={round(float(l['NoOfLicense'] or 0))}" for l in p.get("LicenseList") or []),
            }
            m = main[0] if main else {}
            rows.append({**base, "kind": "apmc", "yard_name": clean(m.get("MainMarketNameE")) or base["apmc_name"],
                         "yard_area_ha": m.get("Area", ""), "yard_since": (m.get("MarketDate") or "")[:10]})
            for y in subs:
                rows.append({**base, "kind": "sub_yard", "yard_name": clean(y["MarketNameE"]),
                             "yard_area_ha": y.get("Area", ""), "yard_since": (y.get("MarketDate") or "")[:10]})
        print(d["DistrictNameE"], len(d["ApmcList"]), "APMCs", flush=True)

    for r in rows:
        hq = HQ.get(r["district"])
        name = r["yard_name"]
        qs = [f"{name}, {r['msamb_district']} district", name] if r["kind"] == "sub_yard" else [name, r["apmc_name"]]
        lat, lon, q = geocode(qs, pin=r["pin"] if r["kind"] == "apmc" else None, near=hq, max_km=90)
        if lat is None and hq:
            lat, lon, q = *hq, "district_hq"
        r.update(lat=lat or "", lon=lon or "", geo_quality=q or "")

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows ->", OUT)
