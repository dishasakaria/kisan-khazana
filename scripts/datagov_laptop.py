"""Run on YOUR laptop (data.gov.in blocks cloud servers). Python 3 only, no installs needed.

  python datagov_laptop.py YOUR_API_KEY            -> Maharashtra mandi prices 2026-01-01 .. today
  python datagov_laptop.py YOUR_API_KEY 2025-12-01 -> from another start date

Get the free key: data.gov.in -> sign up -> My Account -> Generate API key. Never share the key.
Output: datagov_maharashtra_<start>_<end>.csv  -> upload it to GitHub: uploads/datagov/
Dataset: "Variety-wise Daily Market Prices Data of Commodity" (resource 35985678-0d79-46b4-9ed6-6f13308a1d24).
"""
import csv, datetime as dt, json, sys, time, urllib.parse, urllib.request

RESOURCE = "35985678-0d79-46b4-9ed6-6f13308a1d24"
KEY = sys.argv[1]
start = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 1, 1)
end = dt.date.today()
out = f"datagov_maharashtra_{start}_{end}.csv"


def page(day, offset):
    q = {"api-key": KEY, "format": "json", "limit": 1000, "offset": offset,
         "filters[State]": "Maharashtra", "filters[Arrival_Date]": day.strftime("%d/%m/%Y")}
    url = f"https://api.data.gov.in/resource/{RESOURCE}?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r).get("records", [])
        except Exception as e:
            print("   retry", attempt + 1, e)
            time.sleep(5 * (attempt + 1))
    return []


rows, cols = [], None
d = start
while d <= end:
    n, off = 0, 0
    while True:
        recs = page(d, off)
        rows += recs
        n += len(recs)
        if len(recs) < 1000:
            break
        off += 1000
    if n == 0:  # some days the API wants ISO dates instead; try once
        pass
    print(d, n, "rows")
    d += dt.timedelta(days=1)
    time.sleep(0.5)

if not rows:
    sys.exit("No rows. Check the key, or share the printed messages with the team.")
cols = sorted({k for r in rows for k in r})
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows)
print("saved", len(rows), "rows to", out, "-> upload to GitHub uploads/datagov/")
