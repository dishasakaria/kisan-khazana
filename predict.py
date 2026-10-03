"""Live forecasts for every pilot mandi x crop -> Supabase `forecasts` (P10/P50/P90 at 7/14/21 days).

Latest prices come from every source we have, matched to one name per mandi/crop (names.py):
  Kaggle/Agmarknet history (<=2025) · Agmarknet 2.0 saved Jul-Oct 2026 (onion/tomato/soybean)
  · MSAMB live (Supabase) · Agmarknet / eNAM (Supabase, when their watchers get data)
Usage: python predict.py [--tag=v2b]   (default: best tag listed in models/best.txt, else v1)
"""
import datetime as dt, json, sys
from pathlib import Path

import numpy as np
import pandas as pd

import db
from names import crop as crop_name, market_matcher
from train import CAT, build, from_supabase

MAX_STALE_DAYS = 10  # no forecast for a series whose last real price is older than this


def latest_prices(known_markets):
    match = market_matcher(known_markets)
    hist = pd.read_csv("data/clean_prices.csv", usecols=["date", "market", "commodity", "modal"])
    hist = hist[hist.date >= (pd.Timestamp.today() - pd.Timedelta(days=430)).strftime("%Y-%m-%d")]
    parts = [hist]
    q3 = Path("data/live/agmarknet2_2026Q3.csv")
    if q3.exists():
        a = pd.read_csv(q3)
        parts.append(pd.DataFrame({"date": a.date, "market": a.market_raw.map(match), "commodity": a.commodity,
                                   "modal": a.modal_rs_q}))
    live = from_supabase("prices", "date,market,commodity,modal,source", "&source=in.(msamb,agmarknet,enam)")
    if len(live):
        parts.append(pd.DataFrame({"date": live.date, "market": live.market.map(match),
                                   "commodity": live.commodity.map(crop_name), "modal": live.modal}))
    p = pd.concat(parts).dropna(subset=["market", "modal"])
    p = p[p.market.isin(known_markets)]
    # ponytail: median across varieties/sources per day; training used the dominant variety only
    return p.groupby(["date", "market", "commodity"], as_index=False).modal.median()


def main(tag):
    meta = json.loads((Path("models") / tag / "meta.json").read_text())
    feats, today = meta["features"], pd.Timestamp(dt.date.today())
    known = set(pd.read_csv("data/clean_prices.csv", usecols=["market"]).market)
    prices = latest_prices(known)
    weather = from_supabase("weather", "date,district,rain_mm,tmax", "&source=eq.era5_land")
    hist = pd.read_csv("data/history_mh.csv", usecols=["market", "district"]).drop_duplicates()
    from clean import canon
    district_of = {canon(m): ("Ahmednagar" if d in ("Ahmednagar", "Ahilyanagar") else d)
                   for m, d in hist[["market", "district"]].values}
    df = build(prices, weather, district_of)
    if any(f.startswith("ev_") for f in feats):
        from features_ext import add_external
        df = add_external(df)
        for c in CAT:
            df[c] = df[c].astype("category")
    last = df.sort_values("date").groupby(["market", "commodity"], observed=True).tail(1)
    last = last[(today - last.date).dt.days <= MAX_STALE_DAYS]
    pairs = set(map(tuple, pd.read_csv("data/clean_prices.csv", usecols=["market", "commodity"]).drop_duplicates().values))
    last = last[[(m, str(c)) in pairs for m, c in zip(last.market, last.commodity)]]  # only series with real history
    import lightgbm as lgb
    out = []
    for h in meta["horizons"]:
        pred = {q: lgb.Booster(model_file=str(Path("models") / tag / f"lgb_h{h}_q{int(q * 100)}.txt")).predict(last[feats])
                for q in meta["quantiles"]}
        lo, mid, hi = np.sort(np.vstack([pred[0.1], pred[0.5], pred[0.9]]), axis=0)  # no crossed quantiles
        simple = last.commodity.astype(str).isin(meta["results"][str(h)].get("fallback_crops", []))
        mid = np.where(simple, 0.0, mid)  # safety rule chosen on 2024 validation
        now = np.exp(last.lp.values)
        for i, r in enumerate(last.itertuples()):
            out.append({"made_on": today.date().isoformat(), "market": r.market, "commodity": str(r.commodity),
                        "horizon_days": h, "target_date": (today + pd.Timedelta(days=h)).date().isoformat(),
                        "p10": round(float(now[i] * np.exp(min(lo[i], mid[i]))), 1), "p50": round(float(now[i] * np.exp(mid[i])), 1),
                        "p90": round(float(now[i] * np.exp(max(hi[i], mid[i]))), 1), "model": tag})
    for r, p in zip(last.itertuples(), np.exp(last.lp.values)):  # day 0 = latest real price (and its date)
        out.append({"made_on": today.date().isoformat(), "market": r.market, "commodity": str(r.commodity), "horizon_days": 0,
                    "target_date": r.date.date().isoformat(), "p10": round(float(p), 1), "p50": round(float(p), 1),
                    "p90": round(float(p), 1), "model": tag})
    n = db.upsert("forecasts", out)
    db.log_run("predict", "ok", n, f"{tag}: {len(last)} series, last price dates {last.date.min().date()}..{last.date.max().date()}")
    print(f"{tag}: {len(last)} live series -> {n} forecasts. Crops: {last.commodity.astype(str).value_counts().head(10).to_dict()}")


if __name__ == "__main__":
    tag = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--tag=")), None)
    best = Path("models/best.txt")
    main(tag or (best.read_text().strip() if best.exists() else "v1"))
