"""WPI monthly item indices, base 2011-12 and 2022-23 (OEA, eaindustry.nic.in) -> data/ext/wpi_monthly.csv
(month,item,index,base,code). Both bases kept where they overlap; filenames scraped from the download pages."""
import io, re, time, urllib.request
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data/ext/wpi_monthly.csv"
SITE = "https://eaindustry.nic.in/"
UA = {"User-Agent": "Mozilla/5.0 (sell-smart research)"}
ITEMS = {"all commodities": "all_commodities", "food articles": "food_articles", "food grains (cereals+pulses)": "food_grains",
         "cereals": "cereals", "pulses": "pulses", "fruits & vegetables": "fruits_vegetables", "vegetables": "vegetables",
         "fruits": "fruits", "onion": "onion", "tomato": "tomato", "potato": "potato", "soyabean": "soyabean",
         "wheat": "wheat", "gram": "gram", "arhar": "arhar", "jowar": "jowar", "bajra": "bajra", "maize": "maize",
         "grapes": "grapes", "pomegranate": "pomegranate", "hsd": "hsd_diesel", "high speed diesel (hsd)": "hsd_diesel"}


def get(u):
    time.sleep(1)
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()


def link(page, pat):
    return SITE + re.search(pat, get(SITE + page).decode("latin-1")).group(1).replace(" ", "%20")


def norm(s):  # "(A).  FOOD ARTICLES" / "a1. Cereals" -> "food articles" / "cereals"
    return re.sub(r"^\(?[a-z]?[a-z0-9]{0,2}\)?\.\s*", "", str(s).strip().lower()).strip()


def tidy(df, name_col, code_col, month_cols, to_month, base):
    df = df.copy().assign(item=df[name_col].map(lambda s: ITEMS.get(norm(s))), code=df[code_col]).dropna(subset=["item"])
    df = df[df.code.astype(str).str.startswith(("10", "11", "12"))]  # skip manufactured-product namesakes
    long = df.melt(id_vars=["item", "code"], value_vars=month_cols, var_name="m", value_name="index")
    long["month"] = long.m.map(to_month)
    long["index"] = pd.to_numeric(long["index"], errors="coerce")
    return long.dropna(subset=["index"]).astype({"code": "int64"}).assign(base=base)[["month", "item", "index", "base", "code"]]


# 2011-12 base: columns COMM_NAME, COMM_CODE, COMM_WT, INDXmmYYYY...
u = link("download_data_1112.asp", r'href="(indx_download_1112/monthly_index_\d{6}\.xls)"')
a = pd.read_excel(io.BytesIO(get(u)))
cols = [c for c in a.columns if str(c).startswith("INDX")]
a = tidy(a, "COMM_NAME", "COMM_CODE", cols, lambda c: f"{c[6:10]}-{c[4:6]}", "2011-12")
# 2022-23 base: Level, Commodity Name, Commodity Code, Commodity Weight, Apr-23...
u2 = link("download_data_2223.asp", r'href="(indx_download_2223/wpi_monthly_index_\d{6}\.xlsx)"')
b = pd.read_excel(io.BytesIO(get(u2)))
cols = [c for c in b.columns if re.fullmatch(r"[A-Z][a-z]{2}-\d\d", str(c))]
b = tidy(b, "Commodity Name", "Commodity Code", cols, lambda c: pd.to_datetime(c, format="%b-%y").strftime("%Y-%m"), "2022-23")

df = pd.concat([a, b])
df = df[df.month >= "2019-01"].drop_duplicates(["month", "item", "base"]).sort_values(["base", "item", "month"])
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
for base, g in df.groupby("base"):
    print(f"wpi base {base}: {len(g)} rows, {g.item.nunique()} items, {g.month.min()}..{g.month.max()}; missing: {sorted(set(ITEMS.values()) - set(g.item))}")
print(f"wpi_monthly: {len(df)} rows -> {OUT}")
