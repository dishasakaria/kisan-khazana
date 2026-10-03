"""MODIS MOD13Q1 (250 m, 16-day) NDVI per Maharashtra district -> data/ext/ndvi_district.csv.

ORNL DAAC MODIS web service, 11x11 km box (kmAboveBelow=kmLeftRight=5, 41x41 pixels) around each point.
Point = centroid of the district polygon from India Drought Monitor's state_21.json (cached by drought.py),
i.e. the district's farm belt rather than the HQ city; falls back to HQ (districts.HQ) when no polygon.
NDVI = mean of valid pixels * 0.0001 (fill -3000 and anything outside [-2000, 10000] dropped).
API allows <=10 composites per call; responses cached in data/ext/.cache/ndvi/ so reruns fetch only new chunks.
Usage: python sources/ndvi.py [start_year=2019]
"""
import csv, datetime as dt, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

from districts import EXT, HQ, canon, http_json

API = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
CACHE = os.path.join(EXT, ".cache", "ndvi")
OUT = os.path.join(EXT, "ndvi_district.csv")


def centroid(ring):
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        c = x1 * y2 - x2 * y1
        a += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
    return round(cy / (3 * a), 4), round(cx / (3 * a), 4)


def points():
    pts = dict(HQ)
    f = os.path.join(EXT, ".cache", "idm", "data_districts_state_21.json")
    if os.path.exists(f):
        for d in json.load(open(f))["districts"]:
            if d["name"] != "Unknown":
                pts[canon(d["name"])] = centroid(max(d["rings"], key=len))
    pts.pop("Murum", None)  # town inside Dharashiv; same NDVI belt
    return pts


def chunk(name, lat, lon, dates):
    f = os.path.join(CACHE, f"{name}_{dates[0]}_{dates[-1]}.json".replace(" ", "_"))
    if os.path.exists(f):
        return name, json.load(open(f))
    js = http_json(f"{API}/subset?latitude={lat}&longitude={lon}&band=250m_16_days_NDVI&startDate={dates[0]}"
                   f"&endDate={dates[-1]}&kmAboveBelow=5&kmLeftRight=5", headers={"Accept": "application/json"}, timeout=300)
    if len(js["subset"]) == len(dates):  # only cache complete chunks
        json.dump(js, open(f, "w"))
    time.sleep(1)
    return name, js


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2019
    os.makedirs(CACHE, exist_ok=True)
    pts = points()
    lat0, lon0 = pts["Pune"]
    dates = [d["modis_date"] for d in http_json(f"{API}/dates?latitude={lat0}&longitude={lon0}",
                                                  headers={"Accept": "application/json"})["dates"]
             if int(d["modis_date"][1:5]) >= start]
    chunks = [dates[i:i + 10] for i in range(0, len(dates), 10)]
    jobs = [(n, *ll, c) for n, ll in pts.items() for c in chunks]
    print(len(pts), "points,", len(dates), "composites,", len(jobs), "calls", flush=True)
    rows = []
    with ThreadPoolExecutor(3) as ex:  # ponytail: 3 parallel calls is polite for a 15 s/call service
        for i, fut in enumerate([ex.submit(chunk, *j) for j in jobs]):
            try:
                name, js = fut.result()
            except Exception as e:
                print("FAILED", jobs[i][0], jobs[i][3][0], e, flush=True)
                continue
            lat, lon = pts[name]
            for s in js["subset"]:
                v = [x for x in s["data"] if -2000 <= x <= 10000]
                if v:
                    rows.append([s["calendar_date"], name, lat, lon, round(sum(v) / len(v) * 0.0001, 4), len(v)])
            if i % 50 == 0:
                print(i, "/", len(jobs), flush=True)
    rows.sort(key=lambda r: (r[1], r[0]))
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "district", "lat", "lon", "ndvi_mean", "n_pixels"])
        w.writerows(rows)
    print(len(rows), "rows ->", OUT)
