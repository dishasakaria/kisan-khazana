"""Maharashtra holidays / festivals / observed mandi closures 2019-2027 -> data/ext/holidays.csv.

public    : python `holidays` India(subdiv='MH') public category + Google "Holidays in India" ICS 'Public holiday'.
festival  : holidays-lib optional/government categories (MH) + ICS observances, minus festivals that are not
            Maharashtrian (Onam, Bihu, Pongal, Chhath ...). ICS only spans ~2021..2031.
mandi_closure : OBSERVED, not scheduled. From data/history_mh.csv (Agmarknet, to 2025-12): days when the number of
            reporting MH markets fell below 35% of the same-weekday median of the surrounding 8 weeks AND a
            public holiday/festival lies within +-2 days (filters out pure Agmarknet ingestion gaps).
            name = the nearby holiday(s). No closure rows after history ends.
One row per (date, type); names/sources joined with '; '.
Usage: python sources/holidays.py   (needs: pip install holidays)
"""
import csv, datetime as dt, os, re, sys

sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import holidays as hlib  # this file is named holidays.py too: import the library, not ourselves
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from districts import EXT, ROOT, http

ICS = "https://calendar.google.com/calendar/ical/en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics"
YEARS = range(2019, 2028)
NOT_MH = re.compile(r"onam|bihu|pongal|vishu|mesadi|lohri|vaisakh|chhat|durga puja|rath yatra|dolyatra|rabindranath|"
                    r"cheti chand|ugadi|karaka|chaitra suk|ravi ?das|dayanand|tegh bahadur|hazarat ali|ramadan start|meshadi|"
                    r"shri panchami|easter|guru gobind|guru govind|"
                    r"jamat|christmas eve|maha saptami|first day of durga", re.I)
OUT = os.path.join(EXT, "holidays.csv")


def ics_events():
    txt = http(ICS).decode("utf-8").replace("\r\n ", "").replace("\n ", "")
    for ev in txt.split("BEGIN:VEVENT")[1:]:
        f = dict(re.findall(r"^([A-Z-]+)(?:;[^:]*)?:(.*?)\r?$", ev, re.M))
        d = dt.datetime.strptime(f["DTSTART"][:8], "%Y%m%d").date()
        yield d, f["SUMMARY"].strip(), "Public holiday" in f.get("DESCRIPTION", "")


def observed_closures(hol_dates):
    h = pd.read_csv(os.path.join(ROOT, "data", "history_mh.csv"), usecols=["date", "market"])
    c = h.groupby("date").market.nunique()
    c.index = pd.to_datetime(c.index)
    c = c.reindex(pd.date_range("2018-11-01", c.index.max()), fill_value=0)
    base = c.groupby(c.index.dayofweek).transform(lambda s: s.rolling(9, center=True, min_periods=4).median())
    low = c[(c < 0.35 * base) & (c.index >= "2019-01-01")]
    for d in low.index.date:
        near = [n for k in range(-2, 3) for n in hol_dates.get(d + dt.timedelta(k), [])]
        if near:
            yield d, "closure near " + " / ".join(dict.fromkeys(near)), f"history_mh: {int(c[pd.Timestamp(d)])} mkts vs ~{int(base[pd.Timestamp(d)])}"


if __name__ == "__main__":
    rows = []  # (date, name, type, source)
    for cat, typ in (("public", "public"), ("optional", "festival"), ("government", "festival")):
        for d, n in hlib.India(subdiv="MH", years=YEARS, categories=(cat,)).items():
            rows += [(d, x.strip(), typ, "holidays-lib") for x in n.split(";") if typ == "public" or not NOT_MH.search(x)]
    for d, n, pub in ics_events():
        if d.year in YEARS and not NOT_MH.search(n):
            rows.append((d, n, "public" if pub else "festival", "google-ics"))
    hol_dates = {}
    for d, n, _, _ in rows:
        hol_dates.setdefault(d, []).append(n)
    rows += [(d, n, "mandi_closure", s) for d, n, s in observed_closures(hol_dates)]

    merged = {}
    for d, n, t, s in rows:
        m = merged.setdefault((d, t), [{}, {}])
        m[0][n] = 1; m[1][s] = 1
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "name", "type", "source"])
        for (d, t), (names, srcs) in sorted(merged.items()):
            w.writerow([d.isoformat(), "; ".join(names), t, "; ".join(srcs)])
    print(len(merged), "rows ->", OUT)
