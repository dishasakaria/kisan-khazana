"""India monthly exports by 8-digit HS (DGCI&S via tradestat.commerce.gov.in), Jan 2019..latest
-> data/ext/exports_monthly.csv (month,hs_code,description,quantity,unit,value_usd_mn). Keeps HS chapters 01-24 (agri/food).
Incremental: months already in the CSV are skipped except the last REFRESH months (revisions). ~8 MB per request."""
import datetime as dt, io, re, time
from pathlib import Path
import pandas as pd, requests

OUT = Path(__file__).resolve().parents[1] / "data/ext/exports_monthly.csv"
URL = "https://tradestat.commerce.gov.in/meidb/commoditywise_export"
REFRESH = 3
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (sell-smart research)"


def fetch(y, m, report):  # report: 2=quantity, 1=US$ million
    for attempt in range(3):
        try:  # CSRF token rotates after every POST (419 otherwise), so fetch a fresh one each time
            token = re.search(r'name="_token" value="([^"]+)"', s.get(URL, timeout=60).text).group(1)
            time.sleep(2)
            r = s.post(URL, data={"_token": token, "ddMonth": m, "ddYear": y, "comlev": "all", "ddCommodityLevel": 8,
                                  "ddReportVal": report, "ddReportYear": 2}, timeout=180)
            r.raise_for_status()
            break
        except (requests.RequestException, AttributeError) as e:
            print(f"  retry {y}-{m:02d} r{report}: {e}"); time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError(f"failed {y}-{m}")
    time.sleep(3)
    d = pd.read_html(io.StringIO(r.text), converters={"HS Code": str})[0]
    col = next(c for c in d.columns if re.match(rf"{dt.date(y, m, 1):%b}-{y}\b", str(c)))  # this month's column, not last year's
    d = d.rename(columns={"HS Code": "hs_code", "Commodity": "description", "Unit": "unit", col: "v"})
    d["v"] = pd.to_numeric(d["v"], errors="coerce")
    return d[d.hs_code.str.fullmatch(r"\d{8}") & (d.hs_code.str[:2] <= "24")], col


old = pd.read_csv(OUT, dtype={"hs_code": str}) if OUT.exists() else pd.DataFrame(columns=["month"])
done = sorted(old.month.unique())[:-REFRESH] if len(old) else []
today = dt.date.today()
months = [(y, m) for y in range(2019, today.year + 1) for m in range(1, 13) if (y, m) < (today.year, today.month)]
new = []


def save():
    df = pd.concat([old[~old.month.isin([n.month.iat[0] for n in new])], *new]) if new else old
    df = df[["month", "hs_code", "description", "quantity", "unit", "value_usd_mn"]].sort_values(["month", "hs_code"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    return df


for y, m in months:
    key = f"{y}-{m:02d}"
    if key in done:
        continue
    q, col = fetch(y, m, 2)
    if q.v.fillna(0).sum() == 0:
        print(f"{key}: not published yet ({col})"); continue
    v, _ = fetch(y, m, 1)
    d = q.rename(columns={"v": "quantity"})[["hs_code", "description", "unit", "quantity"]].merge(
        v.rename(columns={"v": "value_usd_mn"})[["hs_code", "value_usd_mn"]], on="hs_code", how="outer")
    d.insert(0, "month", key)
    new.append(d)
    print(f"{key}: {len(d)} rows ({col})", flush=True)
    save()

df = save()
print(f"exports_monthly: {len(df)} rows, {df.month.nunique()} months {df.month.min()}..{df.month.max()} -> {OUT}")
