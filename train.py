"""Step 2+3 — build features, train price-range models, test them honestly.

What it does, in order:
  1. load cleaned prices (Supabase, or local CSV with --csv) + ERA5 weather (Supabase)
  2. build one row per mandi x crop x day with features known ON that day (no peeking)
  3. target = % change of price after h days (log ratio), h in 7/14/21
  4. train LightGBM quantile models (P10, P50, P90) per horizon — or XGBoost on an NVIDIA GPU with --gpu
  5. time split: train <=2023, tune 2024, TEST 2025 (never seen); compare with 2 simple baselines
  6. write models/*.txt and models/report.md
Usage: python train.py [--csv | --state] [--gpu] [--tag=v2a]   (models + report go to models/<tag>/)
"""
import json, math, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HORIZONS = [7, 14, 21]
QUANTILES = [0.1, 0.5, 0.9]
SPLIT_VALID, SPLIT_TEST = "2024-01-01", "2025-01-01"
OUT = Path("models")
DIWALI = pd.to_datetime(["2019-10-27", "2020-11-14", "2021-11-04", "2022-10-24", "2023-11-12",
                         "2024-11-01", "2025-10-21", "2026-11-08", "2027-10-29"])
CAT = ["commodity", "market"]


# ---------- 1. load ----------
def from_supabase(table, select, filt="", page=1000, workers=8):
    import db
    total = int(db._req_count(table, filt))
    def chunk(off):
        return db.select(table, f"select={select}{filt}&order=date&offset={off}&limit={page}")
    with ThreadPoolExecutor(workers) as ex:
        parts = list(ex.map(chunk, range(0, total, page)))
    return pd.DataFrame([r for p in parts for r in p])


def load(use_csv, state=False):
    if state:  # whole Maharashtra 2010-2025, local file (too big for the free Supabase tier)
        prices = pd.read_csv("data/clean_prices_state.csv", usecols=["date", "market", "commodity", "modal", "district", "pilot"])
    elif use_csv:
        prices = pd.read_csv("data/clean_prices.csv")
    else:
        prices = from_supabase("prices", "date,market,commodity,modal", "&source=eq.kaggle")
    weather = from_supabase("weather", "date,district,rain_mm,tmax", "&source=eq.era5_land")
    return prices, weather


# ---------- 2-3. features + targets ----------
def build(prices, weather, district_of):
    prices = prices.assign(date=pd.to_datetime(prices.date), lp=np.log(prices.modal.astype(float)))
    if "district" in prices:
        district_of = prices.drop_duplicates("market").set_index("market").district.to_dict()
    pilot_of = prices.drop_duplicates("market").set_index("market").pilot.to_dict() if "pilot" in prices else {}
    frames = []
    for (mkt, crop), s in prices.groupby(["market", "commodity"]):
        s = s.set_index("date").lp.sort_index()
        s = s[~s.index.duplicated()]
        observed = s.copy()
        day = s.asfreq("D").ffill(limit=7)  # mandi holidays: carry the last price up to a week
        f = pd.DataFrame({"lp": day})
        f["observed"] = observed.reindex(f.index).notna()
        for k in (1, 7, 14, 28):
            f[f"ret_{k}"] = day - day.shift(k)            # momentum over k days
        f["dev_ma7"] = day - day.rolling(7, min_periods=3).mean()
        f["dev_ma30"] = day - day.rolling(30, min_periods=10).mean()
        f["vol_30"] = day.diff().rolling(30, min_periods=10).std()
        f["yoy"] = day - day.shift(365)                    # vs same day last year
        for h in HORIZONS:
            fut = observed.asfreq("D").ffill(limit=3).reindex(f.index).shift(-h)  # real price ~h days later
            f[f"y_{h}"] = fut - day                        # TARGET: log change after h days
            # baseline B: what happened in the same calendar window in previous years (median)
            past = [day.shift(365 * k - h) - day.shift(365 * k) for k in (1, 2, 3)]
            f[f"seasonal_{h}"] = pd.concat(past, axis=1).median(axis=1)
        f["market"], f["commodity"], f["district"] = mkt, crop, district_of.get(mkt)
        f["pilot"] = pilot_of.get(mkt, True)
        frames.append(f[f.observed].drop(columns="observed").reset_index(names="date"))
    df = pd.concat(frames, ignore_index=True)

    # cross-mandi: how far this mandi's price is from the crop's typical price that day
    df["gap_crop"] = df.lp - df.groupby(["commodity", "date"]).lp.transform("median")
    df["crop_ret_7"] = df.groupby(["commodity", "date"]).ret_7.transform("median")

    # calendar: season + festival demand
    doy = df.date.dt.dayofyear
    df["season_sin"], df["season_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    df["dow"] = df.date.dt.dayofweek
    nxt = np.searchsorted(DIWALI.values, df.date.values)
    # capped at 30: only the run-up to Diwali matters; uncapped it acted as a hidden date counter (v1 finding)
    df["days_to_diwali"] = np.minimum((DIWALI.values[np.minimum(nxt, len(DIWALI) - 1)] - df.date.values) / np.timedelta64(1, "D"), 30)

    # weather (ERA5-Land): past rain/heat, and next-7-day rain (live: Open-Meteo forecast)
    w = weather.assign(date=pd.to_datetime(weather.date)).sort_values("date")
    wf = []
    for dist, g in w.groupby("district"):
        g = g.set_index("date").asfreq("D")
        wf.append(pd.DataFrame({"district": dist, "rain_7": g.rain_mm.rolling(7, min_periods=1).sum(),
                                "rain_30": g.rain_mm.rolling(30, min_periods=1).sum(),
                                "rain_next_7": g.rain_mm[::-1].rolling(7, min_periods=1).sum()[::-1].shift(-1),
                                "tmax_7": g.tmax.rolling(7, min_periods=1).mean()}).reset_index())
    df = df.merge(pd.concat(wf), on=["district", "date"], how="left")
    for c in CAT:
        df[c] = df[c].astype("category")
    return df


FEATURES = ["ret_1", "ret_7", "ret_14", "ret_28", "dev_ma7", "dev_ma30", "vol_30", "yoy", "gap_crop", "crop_ret_7",
            "season_sin", "season_cos", "dow", "days_to_diwali", "rain_7", "rain_30", "rain_next_7", "tmax_7"] + CAT


# ---------- 4. models ----------
def fit(Xtr, ytr, Xva, yva, q, gpu):
    if gpu:  # NVIDIA via XGBoost (pip install xgboost); categorical support built in
        import xgboost as xgb
        m = xgb.XGBRegressor(objective="reg:quantileerror", quantile_alpha=q, n_estimators=2000, learning_rate=0.05,
                             max_depth=8, subsample=0.8, colsample_bytree=0.8, tree_method="hist", device="cuda",
                             enable_categorical=True, early_stopping_rounds=100)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
        return m
    import lightgbm as lgb
    big = len(Xtr) > 1_500_000  # whole-state data: faster settings, same model family
    m = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=1500 if big else 2000,
                          learning_rate=0.1 if big else 0.05, num_leaves=127 if big else 63,
                          min_child_samples=200 if big else 50, subsample=0.7 if big else 0.8, subsample_freq=1,
                          colsample_bytree=0.8, max_bin=127 if big else 255, verbose=-1)
    m.fit(Xtr, ytr, eval_set=[(Xva, yva)], callbacks=[lgb.early_stopping(50 if big else 100, verbose=False)])
    return m


def mape(true_lr, pred_lr):  # error in rupees, as % of the real price
    return float(np.mean(np.abs(np.exp(pred_lr - true_lr) - 1)) * 100)


# ---------- 5-6. run ----------
if __name__ == "__main__":
    FEATURES = list(FEATURES)
    t0 = time.time()
    gpu, use_csv, state = "--gpu" in sys.argv, "--csv" in sys.argv, "--state" in sys.argv
    tag = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--tag=")), "v1")
    OUT = Path("models") / tag
    prices, weather = load(use_csv, state)
    hist = pd.read_csv("data/history_mh.csv", usecols=["market", "district"]) if Path("data/history_mh.csv").exists() else None
    from clean import canon
    # explicit columns: usecols keeps FILE order (district, market), so unpacking .values swapped them (bug in v1)
    district_of = {} if hist is None else {canon(m): ("Ahmednagar" if d in ("Ahmednagar", "Ahilyanagar") else d)
                                           for m, d in hist.drop_duplicates()[["market", "district"]].values}
    print(f"loaded {len(prices):,} prices, {len(weather):,} weather rows in {time.time() - t0:.0f}s")
    df = build(prices, weather, district_of)
    if "--ext" in sys.argv:  # v2b: policy, MSP, NASA weather/soil, drought, exports, WPI, world prices, fx, diesel, festivals
        from features_ext import add_external, EXT_FEATURES
        df = add_external(df)
        FEATURES += EXT_FEATURES
        for c in CAT:
            df[c] = df[c].astype("category")
    print(f"built {len(df):,} feature rows, {len(FEATURES)} features in {time.time() - t0:.0f}s")
    OUT.mkdir(exist_ok=True)
    lines, results = [f"# Model report ({'XGBoost GPU' if gpu else 'LightGBM CPU'})\n",
                      f"Train < {SPLIT_VALID}, tune {SPLIT_VALID[:4]}, TEST {SPLIT_TEST[:4]} (unseen). Error = MAPE of price.\n"], {}
    for h in HORIZONS:
        d = df.dropna(subset=[f"y_{h}"])
        horizon_end = d.date + pd.Timedelta(days=h)
        tr = d[horizon_end < SPLIT_VALID]
        va = d[(d.date >= SPLIT_VALID) & (horizon_end < SPLIT_TEST)]
        te = d[(d.date >= SPLIT_TEST) & d.pilot]  # judge on the pilot area: that's where we give advice
        preds, va_mid = {}, None
        for q in QUANTILES:
            m = fit(tr[FEATURES], tr[f"y_{h}"], va[FEATURES], va[f"y_{h}"], q, gpu)
            preds[q] = m.predict(te[FEATURES])
            if q == 0.5:
                va_mid = m.predict(va[FEATURES])
            if gpu:
                m.save_model(OUT / f"xgb_h{h}_q{int(q * 100)}.json")
            else:
                m.booster_.save_model(OUT / f"lgb_h{h}_q{int(q * 100)}.txt")
                if q == 0.5:
                    imp = pd.Series(m.booster_.feature_importance("gain"), index=FEATURES).sort_values(ascending=False)
        y = te[f"y_{h}"].values
        seas = te[f"seasonal_{h}"].fillna(0).values
        r = {"model": mape(y, preds[0.5]), "same_price": mape(y, np.zeros_like(y)), "past_years": mape(y, seas),
             "coverage_10_90": float(np.mean((y >= preds[0.1]) & (y <= preds[0.9])) * 100), "test_rows": len(te)}
        by_crop = (te.assign(err=np.abs(np.exp(preds[0.5] - y) - 1) * 100, base=np.abs(np.exp(-y) - 1) * 100)
                     .groupby("commodity", observed=True)[["err", "base"]].mean().round(1))
        # safety rule, decided on 2024 (validation) only: crops where the model lost to "price stays same"
        # get the simple forecast as their likely price (ranges still from the model)
        vv = va.assign(e_m=np.abs(np.exp(va_mid - va[f"y_{h}"]) - 1), e_0=np.abs(np.exp(-va[f"y_{h}"]) - 1))
        losers = set(vv.groupby("commodity", observed=True)[["e_m", "e_0"]].mean().query("e_m > e_0").index)
        mid = np.where(te.commodity.astype(str).isin(losers), 0.0, preds[0.5])
        r["model_plus_fallback"] = mape(y, mid)
        r["fallback_crops"] = sorted(losers)
        by_crop["final %"] = (te.assign(e=np.abs(np.exp(mid - y) - 1) * 100).groupby("commodity", observed=True).e.mean().round(1))
        results[h] = r
        lines += [f"\n## {h} days ahead\n", f"| | MAPE % |\n|---|---|\n| **Our model** | **{r['model']:.1f}** |",
                  f"| **Model + safety rule (final)** | **{r['model_plus_fallback']:.1f}** |",
                  f"| Baseline: price stays same | {r['same_price']:.1f} |", f"| Baseline: same week past years | {r['past_years']:.1f} |",
                  f"\nReal price inside our P10–P90 range: **{r['coverage_10_90']:.0f}%** of {r['test_rows']:,} test cases (target ~80%).\n",
                  "Key crops (model vs 'price stays same'):\n\n" + by_crop.loc[by_crop.index.intersection(
                      ["Onion", "Tomato", "Soyabean", "Wheat", "Potato", "Bengal Gram (Gram)(Whole)", "Maize", "Pomegranate"])]
                  .rename(columns={"err": "model %", "base": "same-price %"}).to_markdown(),
                  f"\nSafety rule used simple forecast for {len(r['fallback_crops'])} crops (chosen on 2024): {', '.join(r['fallback_crops'][:15])}"]
        print(f"h={h}: final {r['model_plus_fallback']:.1f}% | model {r['model']:.1f}% vs same-price {r['same_price']:.1f}% vs past-years {r['past_years']:.1f}%, "
              f"coverage {r['coverage_10_90']:.0f}%  ({time.time() - t0:.0f}s)")
    if not gpu:
        lines.append("\n## What drives the forecast (21-day model, importance)\n\n" + (imp / imp.sum() * 100).round(1).head(12).to_markdown())
    (OUT / "report.md").write_text("\n".join(lines))
    import shutil; shutil.copy(OUT / "report.md", Path("models") / f"report_{tag}.md")
    (OUT / "meta.json").write_text(json.dumps({"features": FEATURES, "horizons": HORIZONS, "quantiles": QUANTILES,
                                               "results": results, "engine": "xgboost-gpu" if gpu else "lightgbm"}, indent=1))
    print(f"done in {time.time() - t0:.0f}s -> models/report.md")
