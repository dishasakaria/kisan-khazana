"""Pilot mandi coordinates -> static/mandis.csv (market, district, lat, lon, query).

Sub-yards "Pune (Moshi)" are located by the place in brackets ("Moshi, Pune"). Nominatim: 1 request/s, proper UA.
ponytail: town-level points (the yard is usually within 2-3 km); replace with MSAMB APMC addresses when needed.
"""
import csv, json, re, time, urllib.parse, urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "sell-smart-hackathon/0.1 (mandi geocoding, one-off)"}
BBOX = (73.2, 17.8, 75.8, 21.1)  # Pune + Nashik + Ahilyanagar: stops same-named towns elsewhere from matching
ALIAS = {"Devala": "Deola", "Kalvan": "Kalwan", "Pimpalgaon": "Pimpalgaon Baswant", "Dound": "Daund", "Sinner": "Sinnar",
         "Nasik": "Nashik", "Bhlhe": "Belhe", "Gogargaon": "Gogargaon Shrigonda", "Vambori": "Vambori"}


# hand-checked fixes where the geocoder picked the wrong spot (coords from Nominatim town lookups)
OVERRIDE = {"Junnar (Alephata)": (19.1714, 74.1166), "Nira (Saswad)": (18.3444, 74.0295), "Lasalgaon (Niphad)": (20.0797, 74.1071)}


def geocode(q):
    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode({"q": q, "limit": 1, "bbox": ",".join(map(str, BBOX))})
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))["features"]
    time.sleep(0.6)
    if not r:
        return None
    lon, lat = r[0]["geometry"]["coordinates"]
    return (lat, lon) if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3] else None


if __name__ == "__main__":
    d = pd.read_csv(ROOT / "data/clean_prices_state.csv", usecols=["market", "district", "pilot"]).drop_duplicates("market")
    d = d[d.pilot]
    out = []
    for m, dist in d[["market", "district"]].values:
        sub = re.search(r"\(([^)]+)\)", m)
        main = ALIAS.get(re.sub(r"\s*\(.*", "", m), re.sub(r"\s*\(.*", "", m))
        sub = re.match(r"(.*)", ALIAS.get(sub.group(1), sub.group(1))) if sub else None
        tries = ([f"{sub.group(1)} {main}", f"{sub.group(1)} {dist}"] if sub else []) + [f"{main} {dist}", main]
        hit, q = OVERRIDE.get(m), "manual override" if m in OVERRIDE else None
        for q in ([] if hit else tries):
            hit = geocode(q)
            if hit:
                break
        out.append({"market": m, "district": dist, "lat": hit[0] if hit else "", "lon": hit[1] if hit else "", "query": q})
        print(m, "->", hit, "via", q, flush=True)
    with open(ROOT / "static/mandis.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["market", "district", "lat", "lon", "query"])
        w.writeheader()
        w.writerows(out)
    print(sum(1 for o in out if o["lat"]), "of", len(out), "geocoded")
