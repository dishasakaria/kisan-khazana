"""PPAC daily RSP of petrol & diesel in 4 metros since 16-Jun-2017 -> data/ext/diesel_daily.csv
(date,city,diesel_rs_l,petrol_rs_l); Mumbai diesel also upserted into Supabase `diesel`. Needs pdftotext (poppler-utils)."""
import re, subprocess, sys, tempfile, urllib.request
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ext/diesel_daily.csv"
PAGE = "https://ppac.gov.in/retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/rsp-of-petrol-and-diesel-in-metro-cities-since-16-6-2017"
UA = {"User-Agent": "Mozilla/5.0 (sell-smart research)"}
CITIES = ["Delhi", "Mumbai", "Chennai", "Kolkata"]
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()

html = get(PAGE).decode("utf-8", "ignore")
pdf_url = re.search(r'href="([^"]*DailyPriceMSHSD_Metro[^"]*\.pdf)"', html).group(1)  # filename carries a timestamp+date
with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
    f.write(get(pdf_url)); f.flush()
    text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout

D, N = r"(\d{1,2}-[A-Za-z]{3}-\d{2})", r"\s+([\d.]+)"
rows = []
for d1, *p, d2, dz1, dz2, dz3, dz4 in re.findall(D + N * 4 + r"\s+" + D + N * 4, text):
    assert d1 == d2, (d1, d2)  # petrol and diesel tables share the row
    iso = datetime.strptime(d1, "%d-%b-%y").date().isoformat()
    rows += [(iso, c, float(dz), float(pt)) for c, dz, pt in zip(CITIES, (dz1, dz2, dz3, dz4), p)]
df = pd.DataFrame(rows, columns=["date", "city", "diesel_rs_l", "petrol_rs_l"]).drop_duplicates(["date", "city"]).sort_values(["date", "city"])
assert len(df) > 4 * 3000 and df.diesel_rs_l.between(40, 200).all(), "parse looks wrong"
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"diesel_daily: {len(df)} rows, {df.date.min()}..{df.date.max()} -> {OUT} (src {pdf_url})")

if "--no-db" not in sys.argv:
    sys.path.insert(0, str(ROOT)); import db
    m = df[df.city == "Mumbai"]
    n = db.upsert("diesel", [{"date": r.date, "city": "Mumbai", "price": r.diesel_rs_l, "source": "PPAC metro RSP (IOC)"} for r in m.itertuples()])
    print(f"supabase diesel: upserted {n} Mumbai rows")
