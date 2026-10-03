"""External features for model v2b, joined only with information PUBLISHED by each date (no peeking).

Sources (data/ext/, built by sources/*.py):
  policy events + MSP (PIB/DGFT/news, each row has a source_url) · NASA POWER weather & soil (all districts)
  India Drought Monitor (weekly) · Tradestat exports (monthly, ~2-month lag) · WPI (monthly, ~1-month lag)
  World Bank Pink Sheet (monthly, ~1-month lag) · USD/INR (daily) · PPAC diesel Mumbai (daily) · holidays/festivals
"""
import numpy as np
import pandas as pd

EXT = "data/ext/"
WPI_ITEM = {"Onion": "onion", "Tomato": "tomato", "Potato": "potato", "Soyabean": "soyabean", "Wheat": "wheat",
            "Bengal Gram (Gram)(Whole)": "gram", "Arhar (Tur/Red Gram)(Whole)": "arhar", "Jowar (Sorghum)": "jowar",
            "Bajra (Pearl Millet/Cumbu)": "bajra", "Maize": "maize", "Grapes": "grapes", "Pomegranate": "pomegranate"}
HS_PREFIX = {"Onion": "0703", "Garlic": "070320", "Tomato": "0702", "Potato": "0701", "Grapes": "080610",
             "Pomegranate": "08109010", "Soyabean": "230400", "Wheat": "1001", "Rice": "1006", "Dry Chillies": "0904",
             "Maize": "1005", "Banana": "0803"}
PINK = {"Soyabean": ["Soybeans", "Soybean oil", "Soybean meal", "Palm oil"], "Maize": ["Maize"],
        "Wheat": ["Wheat, US HRW"], "Rice": ["Rice, Thai 5%"]}
EVENT_VALUE = ["export_duty_pct", "min_export_price_usd_t", "import_duty_pct", "state_subsidy_rs_qtl"]
EVENT_FLAG = ["export_ban", "stock_limit", "buffer_procurement", "buffer_release", "procurement_window", "apmc_strike_closure"]


def _monthly_asof(df, key_cols, lag_months):
    """month M's value becomes usable on the 1st of month M+lag+1 (conservative publication lag)."""
    df = df.copy()
    df["avail"] = pd.to_datetime(df.month + "-01") + pd.DateOffset(months=lag_months + 1)
    return df.sort_values("avail")


def _asof(left, right, by, cols):
    """For each row in left, latest right row with avail <= date (same `by` key)."""
    left = left.sort_values("date").assign(**{by: lambda d: d[by].astype(str)})
    right = right.assign(**{by: right[by].astype(str)})
    out = pd.merge_asof(left.reset_index(), right[[by, "avail"] + cols].rename(columns={"avail": "date"}).sort_values("date"),
                        on="date", by=by, direction="backward")
    return out.set_index("index").reindex(left.index)[cols]


def add_external(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df.date)
    crop = df.commodity.astype(str)

    # --- policy events: active on the date? (ALL applies to every crop)
    ev = pd.read_csv(EXT + "events.csv", parse_dates=["date_start", "date_end"])
    ev["date_end"] = ev.date_end.fillna(pd.Timestamp("2030-01-01"))
    for t in EVENT_FLAG + EVENT_VALUE:
        df[f"ev_{t}"] = 0.0
    for r in ev.itertuples():
        mask = (df.date >= r.date_start) & (df.date <= r.date_end)
        if r.commodity != "ALL":
            mask &= crop == r.commodity
        if not mask.any():
            continue
        col = f"ev_{r.event_type}"
        if r.event_type in EVENT_VALUE:
            df.loc[mask, col] = pd.to_numeric(r.value, errors="coerce")
        elif r.event_type in EVENT_FLAG:
            df.loc[mask, col] = 1.0

    # --- MSP: price relative to the MSP in force (kharif year starts Oct, rabi year starts Apr)
    msp = pd.read_csv(EXT + "msp.csv")
    y0 = msp.marketing_year.str[:4].astype(int)
    msp["avail"] = pd.to_datetime(np.where(msp.season.str.lower().str.startswith("k"), y0.astype(str) + "-10-01",
                                           y0.astype(str) + "-04-01"))
    msp = msp.rename(columns={"commodity": "crop_key"}).sort_values("avail")
    df["crop_key"] = crop
    m = _asof(df[["date", "crop_key"]], msp, "crop_key", ["msp_rs_qtl"])
    df["price_vs_msp"] = df.lp - np.log(m.msp_rs_qtl.astype(float))

    # --- weather & soil, all districts (NASA POWER)
    w = pd.read_csv(EXT + "weather_districts.csv", parse_dates=["date"]).sort_values(["district", "date"])
    g = w.groupby("district")
    wf = pd.DataFrame({"date": w.date, "district": w.district,
                       "p_rain_7": g.rain_mm.transform(lambda s: s.rolling(7, 1).sum()),
                       "p_rain_30": g.rain_mm.transform(lambda s: s.rolling(30, 1).sum()),
                       "p_rain_next_7": g.rain_mm.transform(lambda s: s[::-1].rolling(7, 1).sum()[::-1].shift(-1)),
                       "p_tmax_7": g.tmax.transform(lambda s: s.rolling(7, 1).mean()),
                       "p_rh_7": g.rh.transform(lambda s: s.rolling(7, 1).mean()),
                       "p_soil_root": w.soil_root, "p_et_30": g.evapotrans.transform(lambda s: s.rolling(30, 1).sum())})
    df = df.merge(wf, on=["district", "date"], how="left")

    # --- drought (weekly, published at week end)
    dr = pd.read_csv(EXT + "drought_district.csv", parse_dates=["week_end"]).rename(columns={"week_end": "avail"})
    df["drought_pct"] = _asof(df[["date", "district"]], dr.sort_values("avail"), "district", ["drought_pct"]).drought_pct.values

    # --- monthly national signals per crop
    wpi = pd.read_csv(EXT + "wpi_monthly.csv").sort_values(["base", "item", "month"])
    # yoy within one index base (2011-12 vs 2022-23 levels aren't comparable), newer base wins on overlap
    wpi["wpi_yoy"] = wpi.groupby(["base", "item"])["index"].transform(lambda s: np.log(s / s.shift(12)))
    wpi = wpi.dropna(subset=["wpi_yoy"]).sort_values("base").drop_duplicates(["month", "item"], keep="last")
    wpi = _monthly_asof(wpi, ["item"], 1).rename(columns={"item": "crop_key"})
    df["crop_key"] = crop.map(WPI_ITEM)
    df["wpi_yoy"] = _asof(df[["date", "crop_key"]], wpi, "crop_key", ["wpi_yoy"]).wpi_yoy.values

    ex = pd.read_csv(EXT + "exports_monthly.csv", dtype={"hs_code": str})
    rows = []
    for c, pre in HS_PREFIX.items():
        s = ex[ex.hs_code.str.zfill(8).str.startswith(pre)].groupby("month").quantity.sum().sort_index()
        rows.append(pd.DataFrame({"month": s.index, "crop_key": c, "export_yoy": np.log1p(s) - np.log1p(s.shift(12)),
                                  "export_qty_log": np.log1p(s)}))
    ex = _monthly_asof(pd.concat(rows), ["crop_key"], 2)
    df["crop_key"] = crop
    e = _asof(df[["date", "crop_key"]], ex, "crop_key", ["export_yoy", "export_qty_log"])
    df["export_yoy"], df["export_qty_log"] = e.export_yoy.values, e.export_qty_log.values

    pk = pd.read_csv(EXT + "pinksheet_monthly.csv").sort_values("month")
    pk["world_12m"] = pk.groupby("series").usd_per_unit.transform(lambda s: np.log(s / s.shift(12)))
    pk["world_1m"] = pk.groupby("series").usd_per_unit.transform(lambda s: np.log(s / s.shift(1)))
    rows = [pk[pk.series.isin(v)].groupby("month")[["world_12m", "world_1m"]].mean().reset_index().assign(crop_key=k)
            for k, v in PINK.items()]
    pk = _monthly_asof(pd.concat(rows), ["crop_key"], 1)
    p = _asof(df[["date", "crop_key"]], pk, "crop_key", ["world_12m", "world_1m"])
    df["world_12m"], df["world_1m"] = p.world_12m.values, p.world_1m.values

    # --- daily macro: USD/INR, Mumbai diesel (transport cost)
    fx = pd.read_csv(EXT + "usd_inr_daily.csv", parse_dates=["date"]).sort_values("date")
    fx["fx_30"] = np.log(fx.usd_inr / fx.usd_inr.shift(21))
    dz = pd.read_csv(EXT + "diesel_daily.csv", parse_dates=["date"])
    dz = dz[dz.city == "Mumbai"].sort_values("date")
    df = df.sort_values("date")
    df = pd.merge_asof(df, fx[["date", "fx_30"]], on="date")
    df = pd.merge_asof(df, dz[["date", "diesel_rs_l"]], on="date")

    # --- festivals / mandi closures in the coming week
    h = pd.read_csv(EXT + "holidays.csv", parse_dates=["date"])
    days = df.date.values.astype("datetime64[D]")
    for typ, col in [("festival", "festivals_next_7"), ("mandi_closure", "closures_next_7")]:
        hd = np.sort(h[h.type == typ].date.values.astype("datetime64[D]"))
        df[col] = np.searchsorted(hd, days + 8) - np.searchsorted(hd, days + 1)

    return df.drop(columns="crop_key")


EXT_FEATURES = ([f"ev_{t}" for t in EVENT_FLAG + EVENT_VALUE] +
                ["price_vs_msp", "p_rain_7", "p_rain_30", "p_rain_next_7", "p_tmax_7", "p_rh_7", "p_soil_root", "p_et_30",
                 "drought_pct", "wpi_yoy", "export_yoy", "export_qty_log", "world_12m", "world_1m", "fx_30", "diesel_rs_l",
                 "festivals_next_7", "closures_next_7"])
