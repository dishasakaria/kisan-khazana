"""India Drought Monitor (IIT Gandhinagar, WCL) weekly district drought history for Maharashtra
-> data/ext/drought_district.csv.

The site only publishes per-district stats for the latest week (data/districts/district-stats.json), but it
keeps every weekly 0.25-deg Combined Drought Index grid (data/Drough_TS/CDI_YYYYMMDD.txt, list in
assets/interactive/cdi-manifest.js, from 2021-07-14). We rebuild per-district class shares exactly the way
the site does (idm-ai.js): each 1/16-deg cell of data/districts/grid_21.csv takes the nearest CDI value
(same +-0.0625/0.125 search), classed None/D0..D4 by thresholds -0.5/-0.8/-1.3/-1.6/-2.0.
d*_pct are EXCLUSIVE class shares (not cumulative); drought_pct = 100 - none_pct.
source=rebuilt: our rebuild from the weekly grid. source=official: the site's own district-stats.json rows
(finer native grid, so numbers differ from the rebuild by ~8 pts mean abs on none_pct; Mumbai has too few cells to rebuild); only the latest week is
published, so each run keeps previously saved official rows -> official history accumulates going forward.
Usage: python sources/drought.py      (cached grids in data/ext/.cache/idm/, only new weeks downloaded)
"""
import csv, json, os, re, time

from districts import EXT, canon, http

BASE = "https://indiadroughtmonitor.in/"
CACHE = os.path.join(EXT, ".cache", "idm")
OUT = os.path.join(EXT, "drought_district.csv")
CLASSES = ["None", "D0", "D1", "D2", "D3", "D4"]


def classify(v):
    for cls, thr in zip(CLASSES, (-0.5, -0.8, -1.3, -1.6, -2.0)):
        if v > thr:
            return cls
    return "D4"


def cached(path, refresh=False):
    f = os.path.join(CACHE, path.replace("/", "_"))
    if refresh or not os.path.exists(f):
        data = http(BASE + path)
        open(f, "wb").write(data)
        time.sleep(0.5)
    return open(f, encoding="utf-8").read()


def week_stats(cdi_text, cells):
    idx = {}
    for line in cdi_text.split("\n"):
        p = line.split()
        if len(p) == 3:
            try:
                v = float(p[2])
            except ValueError:
                continue
            if v == v:  # skip NaN
                idx[(round(float(p[0]), 3), round(float(p[1]), 3))] = v
    deltas = (0, 0.0625, -0.0625, 0.125, -0.125)
    tally = {}
    for lat, lng, did in cells:
        v = next((idx[k] for a in deltas for b in deltas if (k := (round(lat + a, 3), round(lng + b, 3))) in idx), None)
        if v is None:
            continue
        t = tally.setdefault(did, {c: 0 for c in CLASSES} | {"n": 0, "sum": 0.0})
        t[classify(v)] += 1
        t["n"] += 1
        t["sum"] += v
    return tally


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    manifest = cached("assets/interactive/cdi-manifest.js", refresh=True)
    weeks = re.findall(r'"(\d{4}-\d{2}-\d{2})"', manifest)
    names = {d["id"]: d["name"] for d in json.loads(cached("data/districts/state_21.json", refresh=True))["districts"]}
    rows = list(csv.DictReader(cached("data/districts/grid_21.csv", refresh=True).splitlines()))
    cells = [(float(r["lat"]), float(r["lng"]), int(r["district_id"])) for r in rows]
    out = []
    for wk in weeks:
        try:
            txt = cached(f"data/Drough_TS/CDI_{wk.replace('-', '')}.txt")
        except Exception as e:
            print("missing", wk, e)
            continue
        for did, t in sorted(week_stats(txt, cells).items()):
            if names.get(did, "Unknown") == "Unknown" or t["n"] < 8:  # site drops tiny/unassigned areas too
                continue
            pc = {c: round(100 * t[c] / t["n"], 1) for c in CLASSES}
            out.append([wk, canon(names[did]), names[did], round(t["sum"] / t["n"], 4), t["n"], pc["None"],
                        pc["D0"], pc["D1"], pc["D2"], pc["D3"], pc["D4"], round(100 - pc["None"], 1)])
    site = json.loads(http(BASE + "data/districts/district-stats.json"))
    official = {}
    if os.path.exists(OUT):
        official = {(r["week_end"], r["idm_district"]): r for r in csv.DictReader(open(OUT)) if r.get("source") == "official"}
    for d in site["districts"]:
        if d["state"] == "Maharashtra" and d["district"] != "Unknown":
            official[(site["week_ending"], d["district"])] = {
                "week_end": site["week_ending"], "district": canon(d["district"]), "idm_district": d["district"],
                "cdi_mean": "", "n_cells": "", **{k: d[k] for k in ("none_pct", "d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct", "drought_pct")}}
    cols = ["week_end", "district", "idm_district", "cdi_mean", "n_cells", "none_pct",
            "d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct", "drought_pct", "source"]
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(r + ["rebuilt"] for r in out)
        w.writerows([r[c] for c in cols[:-1]] + ["official"] for r in sorted(official.values(), key=lambda r: (r["week_end"], r["idm_district"])))
    print(len(out), "rebuilt rows,", len(weeks), "weeks;", len(official), "official rows ->", OUT)
    mine = {r[2]: r for r in out if r[0] == site["week_ending"]}
    diffs = [abs(float(d["none_pct"]) - mine[d["idm_district"]][5]) for d in official.values()
             if d["week_end"] == site["week_ending"] and d["idm_district"] in mine]
    print("rebuilt vs official none_pct, mean abs diff:", round(sum(diffs) / max(len(diffs), 1), 1), "pts")
