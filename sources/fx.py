"""USD/INR daily reference rates (ECB via api.frankfurter.dev), 2019-01-01..today -> data/ext/usd_inr_daily.csv"""
import datetime as dt, json, time, urllib.request
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data/ext/usd_inr_daily.csv"
rows = []
for y in range(2019, dt.date.today().year + 1):  # one request per year, polite
    url = f"https://api.frankfurter.dev/v1/{y}-01-01..{y}-12-31?base=USD&symbols=INR"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "sell-smart/1.0"}), timeout=60) as r:
        rates = json.load(r)["rates"]
    rows += [(d, v["INR"]) for d, v in rates.items() if d >= "2019-01-01"]
    time.sleep(1)
df = pd.DataFrame(rows, columns=["date", "usd_inr"]).drop_duplicates("date").sort_values("date")
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"usd_inr_daily: {len(df)} rows {df.date.min()}..{df.date.max()} -> {OUT}")
