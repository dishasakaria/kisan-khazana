"""Bulk price history (2001-2025) from the Kaggle mirror of data.gov.in's Agmarknet feed (GODL-India licence).

Streams each yearly all-India CSV (~300-400 MB) and keeps only one state, so nothing big touches disk.
No arrivals column in this source: arrivals come from MSAMB / Agmarknet for recent data.
Usage: python fetch_history.py 2019 2025
"""
import csv, io, sys, urllib.request
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/khandelwalmanas/daily-commodity-prices-india/csv%2F{year}.csv"
STATE = "Maharashtra"
OUT = Path(__file__).with_name("data") / "history_mh.csv"
COLS = ["date", "district", "market", "commodity", "variety", "grade", "min", "max", "modal"]

if __name__ == "__main__":
    y0, y1 = int(sys.argv[1]), int(sys.argv[2])
    OUT.parent.mkdir(exist_ok=True)
    new = not OUT.exists()
    with OUT.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(COLS)
        for year in range(y0, y1 + 1):
            req = urllib.request.Request(URL.format(year=year), headers={"User-Agent": "sell-smart-hackathon/0.1"})
            kept = 0
            with urllib.request.urlopen(req, timeout=120) as r:
                for row in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", errors="replace")):
                    if row["State"] == STATE:
                        w.writerow([row["Arrival_Date"], row["District"], row["Market"], row["Commodity"],
                                    row["Variety"], row["Grade"], row["Min_Price"], row["Max_Price"], row["Modal_Price"]])
                        kept += 1
            f.flush()
            print(f"{year}: kept {kept} Maharashtra rows", flush=True)
