"""Transport cost from a farmer's village to a mandi, priced off today's real diesel rate.

Farmers rent trucks: cost = ₹25/km (average rent) x road km x trucks needed. Diesel price is still fetched for display/model.
"""
import json, math, re, time, urllib.request
from pathlib import Path

CACHE = Path(__file__).with_name("diesel_cache.json")
UA = {"User-Agent": "sell-smart-hackathon/0.1 (mandi advisory prototype)"}
DEFAULT_DIESEL = 99.70  # Indore, goodreturns.in, 2 Oct 2026 — used only if fetch and cache both fail

# Farmers hire a truck: average rent ₹25 per km of road distance (farmer survey input, Oct 2026; the calibration knob).
RENT_PER_KM = 25.0
TRUCK_QTL = 100  # one rented 10 T truck carries ~100 quintals


def diesel_price(city="indore", max_age_h=12):
    """Today's retail diesel ₹/L for a city. Returns (price, source, fetched_at). Falls back to cache, then default."""
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    hit = cache.get(city)
    if hit and time.time() - hit["ts"] < max_age_h * 3600:
        return hit["price"], hit["source"], hit["ts"]
    url = f"https://www.goodreturns.in/diesel-price-in-{city}.html"
    try:
        html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "ignore")
        m = re.search(r"Diesel Price in [^<]*?Rs\.\s*([0-9]{2,3}\.[0-9]{2})/Ltr", html)
        price = float(m.group(1))
        if not 60 < price < 150:  # sanity bound: reject parse garbage
            raise ValueError(price)
        cache[city] = {"price": price, "source": url, "ts": time.time()}
        CACHE.write_text(json.dumps(cache, indent=1))
        return price, url, cache[city]["ts"]
    except Exception:
        if hit:  # stale but real beats made up
            return hit["price"], hit["source"] + " (stale cache)", hit["ts"]
        return DEFAULT_DIESEL, "default constant", None


def road_route(frm, to):
    """(km, hours) by road via the public OSRM demo server (1 req/s, non-commercial). frm/to = (lat, lon)."""
    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{frm[1]},{frm[0]};{to[1]},{to[0]}?overview=false")
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20))
    leg = r["routes"][0]
    return leg["distance"] / 1000, leg["duration"] / 3600


def best_transport(qty_qtl, km, diesel=None):
    """Rented truck to the mandi: ₹/km x road km x trucks needed. diesel kept for callers (shown, not used)."""
    trips = max(1, math.ceil(qty_qtl / TRUCK_QTL))
    total = trips * RENT_PER_KM * km
    return {"vehicle": "Truck", "trips": trips, "rate": RENT_PER_KM, "total": round(total), "per_qtl": total / qty_qtl}


if __name__ == "__main__":
    assert best_transport(40, 100)["total"] == 2500 and best_transport(150, 10)["trips"] == 2
    assert best_transport(10, 50)["total"] < best_transport(10, 150)["total"], "farther must cost more"
    print("self-checks ok")

