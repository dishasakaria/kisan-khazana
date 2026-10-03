"""Step 1 — clean mandi price history for the pilot districts and upload it to Supabase (source='kaggle').

Rules (each one counted in the quality report):
  1. pilot districts only (Pune, Ahilyanagar/Ahmednagar, Nashik)
  2. one name per mandi: the late-2025 rename added "APMC" ("Pune" -> "Pune APMC"); spacing differs across sources
  3. duplicates (same day/mandi/crop/variety, several grades) -> one row (median)
  4. one variety per mandi+crop: the dominant one, so quality mixes don't fake price jumps
  5. unit errors: price >5x or <1/5 of that series' recent median -> dropped
  6. stale copies: identical min/max/modal for 5+ reports in a row -> keep the first only
  7. series kept only with >=300 days of data and still reporting in 2025
Usage: python clean.py            (pilot: data/clean_prices.csv + quality report, uploads to Supabase)
       python clean.py --state    (whole Maharashtra for training: data/clean_prices_state.csv, local only)
"""
import re, sys
import numpy as np
import pandas as pd

PILOT = {"Pune", "Ahmednagar", "Ahilyanagar", "Nashik"}


def canon(name):
    """'APMC Lasalgaon(Vinchur) ' / 'Lasalgaon (Vinchur) APMC' / 'LASALGAON (VINCHUR)' -> 'Lasalgaon (Vinchur)'."""
    s = re.sub(r"\bapmc\b", " ", str(name), flags=re.I)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ") ", s)
    return re.sub(r"\s+", " ", s).strip().title()


def clean(df, report, state=False, min_days=300):
    n0 = len(df)
    if not state:
        df = df[df.district.isin(PILOT)].copy()
    report.append(f"1. {'whole state' if state else 'pilot districts'}: {n0:,} -> {len(df):,} rows")
    district_of = df.drop_duplicates("market").set_index("market").district

    df["district"] = df.market.map(district_of).replace({"Ahilyanagar": "Ahmednagar"})
    df["market"] = df.market.map(canon)
    report.append(f"2. mandi names merged to {df.market.nunique()} mandis")

    df = (df.groupby(["date", "market", "commodity", "variety"], as_index=False)
            .agg(district=("district", "first"), min=("min", "median"), max=("max", "median"), modal=("modal", "median")))
    report.append(f"3. after merging duplicates/grades: {len(df):,}")

    share = df.groupby(["market", "commodity", "variety"]).size()
    top = share.groupby(level=[0, 1]).idxmax().values
    df = df.set_index(["market", "commodity", "variety"]).loc[list(top)].reset_index()
    report.append(f"4. dominant variety only: {len(df):,}")

    df = df.sort_values(["market", "commodity", "date"]).reset_index(drop=True)
    g = df.groupby(["market", "commodity"]).modal
    med = g.transform(lambda s: s.rolling(15, min_periods=5).median().shift(1)).fillna(g.transform("median"))
    ratio = df.modal / med
    bad = (ratio > 5) | (ratio < 0.2)
    report.append(f"5. unit-error / impossible jumps dropped: {int(bad.sum()):,}")
    df = df[~bad]

    key = df[["min", "max", "modal"]].astype(str).agg("|".join, axis=1)
    same = key.eq(key.groupby([df.market, df.commodity]).shift(1))
    run = same.groupby((~same).cumsum()).cumsum()
    stale = run >= 4  # 5th identical report in a row onwards
    report.append(f"6. stale copied values dropped: {int(stale.sum()):,}")
    df = df[~stale]

    s = df.groupby(["market", "commodity"]).agg(n=("modal", "size"), last=("date", "max"))
    keep = s[(s.n >= min_days) & (s["last"] >= "2025-01-01")].index
    df = df.set_index(["market", "commodity"]).loc[keep].reset_index()
    df["pilot"] = df.district.isin(PILOT)
    report.append(f"7. series with >={min_days} days and active in 2025: {len(keep)} series, {len(df):,} rows")
    report.append(f"   crops: {df.commodity.nunique()}  mandis: {df.market.nunique()}  dates {df.date.min()} .. {df.date.max()}")
    return df


if __name__ == "__main__":
    report, state = [], "--state" in sys.argv
    raw = pd.read_csv("data/history_mh.csv")
    df = clean(raw, report, state=state, min_days=100 if state else 300)
    out = "data/clean_prices_state.csv" if state else "data/clean_prices.csv"
    df.to_csv(out, index=False)
    top = df.groupby("commodity").size().sort_values(ascending=False)
    report.append("rows per crop (top 25):\n" + top.head(25).to_string())
    open(out.replace("clean_prices", "quality_report").replace(".csv", ".txt"), "w").write("\n".join(report))
    print("\n".join(report[:9]))
    if "--no-upload" not in sys.argv and not state:  # Supabase free tier: store the pilot area only
        import db
        rows = df.drop(columns=["district", "pilot"]).assign(arrivals_t=None, source="kaggle").replace({np.nan: None}).to_dict("records")
        n = db.upsert("prices", rows)
        db.log_run("clean_history", "ok", n, "; ".join(report[:7])[:500])
        print("uploaded", n, "rows to Supabase")
