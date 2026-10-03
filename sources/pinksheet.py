"""World Bank Pink Sheet monthly prices (2010+) -> data/ext/pinksheet_monthly.csv (month,series,usd_per_unit,unit)"""
import io, re, urllib.request
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data/ext/pinksheet_monthly.csv"
UA = {"User-Agent": "Mozilla/5.0 (sell-smart research)"}
KEEP = ["Soybeans", "Soybean oil", "Soybean meal", "Palm oil", "Maize", "Wheat, US SRW", "Wheat, US HRW",
        "Rice, Thai 5%", "Rice, Viet Namese 5%", "Sugar, world", "DAP", "Urea", "Crude oil, Brent"]

get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
page = get("https://www.worldbank.org/en/research/commodity-markets").decode("utf-8", "ignore")
link = re.search(r'href="([^"]*CMO-Historical-Data-Monthly\.xlsx)"', page).group(1)  # URL changes each release
raw = pd.read_excel(io.BytesIO(get(link)), sheet_name="Monthly Prices", header=None)
names = raw.iloc[4].astype(str).str.replace("*", "", regex=False).str.strip()
units = raw.iloc[5].astype(str).str.strip("() ")
body = raw.iloc[6:]
rows = []
for c in range(1, raw.shape[1]):
    if names[c] not in KEEP:
        continue
    s = pd.DataFrame({"month": body[0].str.replace("M", "-"), "series": names[c],
                      "usd_per_unit": pd.to_numeric(body[c], errors="coerce"), "unit": units[c]})
    rows.append(s)
df = pd.concat(rows).dropna(subset=["usd_per_unit"])
df = df[df.month >= "2010-01"].sort_values(["series", "month"])
missing = set(KEEP) - set(df.series)
assert not missing, f"series not found: {missing}"
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"pinksheet_monthly: {len(df)} rows, {df.series.nunique()} series, {df.month.min()}..{df.month.max()} (src {link})")
