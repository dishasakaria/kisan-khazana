"""LSTM challenger to train.py (LightGBM quantile). Same targets, split, metrics — honest head-to-head.

Input per row (mandi x crop x observed day): last 60 days of log-price relative to today (ffill limit 7, like
train.py), scaled per series by its training-period 7-day volatility, plus a "price known" mask channel;
static: market/crop/day-of-week embeddings, season sin/cos, log(scale).
Output: one network, 9 numbers = log(price_{t+h}/price_t) for h in 7/14/21 x quantiles 0.1/0.5/0.9 (pinball loss).
Split: train date+h < 2024, validate 2024 (early stopping), TEST date >= 2025 (pilot area = all rows here).
Usage: python lstm.py [--gpu] [--stride=3] [--epochs=30] [--seed=0]   -> models/lstm/{report.md, meta.json, lstm.pt}
"""
import json, re, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from train import HORIZONS, QUANTILES, SPLIT_VALID, SPLIT_TEST, mape

SEQ = 60
KEY = ["Onion", "Tomato", "Soyabean", "Wheat", "Bengal Gram (Gram)(Whole)", "Potato", "Maize", "Pomegranate"]
OUT = Path("models/lstm")
arg = lambda k, d: type(d)(next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{k}=")), d))


def build(prices):
    """One row per observed (market, crop, day): window, mask, targets. Mirrors train.build()'s series logic."""
    prices = prices.assign(date=pd.to_datetime(prices.date), lp=np.log(prices.modal.astype(float)))
    W, M, Y, D, MK, CR, SC = [], [], [], [], [], [], []
    for (mkt, crop), s in prices.groupby(["market", "commodity"]):
        s = s.set_index("date").lp.sort_index()
        s = s[~s.index.duplicated()]
        day = s.asfreq("D").ffill(limit=7)
        obs = day.index.isin(s.index)
        ys = np.stack([(s.asfreq("D").ffill(limit=3).reindex(day.index).shift(-h) - day).values for h in HORIZONS], 1)
        # per-series scale from TRAINING dates only (7-day log-change std)
        sc = day.diff(7)[day.index < SPLIT_VALID].std()
        v = day.values
        win = np.lib.stride_tricks.sliding_window_view(np.r_[np.full(SEQ - 1, np.nan), v], SEQ)[obs]
        rel = win - v[obs, None]
        W.append(rel.astype(np.float32)); M.append(~np.isnan(rel)); Y.append(ys[obs].astype(np.float32))
        D.append(day.index[obs].values); MK += [mkt] * obs.sum(); CR += [crop] * obs.sum(); SC += [sc] * obs.sum()
    df = pd.DataFrame({"date": np.concatenate(D), "market": MK, "commodity": CR, "scale": SC})
    # series with no training history: borrow the crop's median scale, then the global one
    df["scale"] = df.scale.fillna(df.groupby("commodity").scale.transform("median")).fillna(df.scale.median()).clip(0.01)
    return df, np.concatenate(W), np.concatenate(M), np.concatenate(Y)


class Net(nn.Module):
    def __init__(self, n_mkt, n_crop, hidden=64, layers=1):
        super().__init__()
        self.em, self.ec, self.ed = nn.Embedding(n_mkt, 8), nn.Embedding(n_crop, 16), nn.Embedding(7, 3)
        self.lstm = nn.LSTM(2, hidden, layers, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden + 8 + 16 + 3 + 3, 64), nn.ReLU(), nn.Linear(64, 9))

    def forward(self, x, m, mkt, crop, dow, stat):
        _, (h, _) = self.lstm(torch.stack([x, m], -1))
        z = torch.cat([h[-1], self.em(mkt), self.ec(crop), self.ed(dow), stat], 1)
        return self.head(z).view(-1, 3, 3) * stat[:, 2:3, None].exp()  # back to raw log-ratio units


def pinball(pred, y):  # pred (B,3h,3q), y (B,3h) with NaN = no target for that horizon in this split
    ok = ~torch.isnan(y)
    e = torch.nan_to_num(y)[..., None] - pred
    q = torch.tensor(QUANTILES, device=pred.device)
    return (torch.maximum(q * e, (q - 1) * e).mean(-1) * ok).sum() / ok.sum().clamp(min=1)


def lgb_tables(path):
    """Overall + key-crop model % per horizon from a train.py report (only source of v1/v2b crop numbers)."""
    out, h = {}, None
    for line in Path(path).read_text().splitlines():
        if m := re.match(r"## (\d+) days ahead", line):
            h = int(m[1]); out[h] = {}
        elif h and (m := re.match(r"\| \*\*Our model\*\* \| \*\*([\d.]+)", line)):
            out[h]["Overall"] = float(m[1])
        elif h and (m := re.match(r"Real price inside our P10–P90 range: \*\*(\d+)%", line)):
            out[h]["coverage"] = float(m[1])
        elif h and (m := re.match(r"\| (.+?)\s+\|\s+([\d.]+)\s+\|", line)) and m[1].strip() in KEY:
            out[h][m[1].strip()] = float(m[2])
    return out


if __name__ == "__main__":
    t0 = time.time()
    dev = torch.device("cuda" if "--gpu" in sys.argv and torch.cuda.is_available() else "cpu")
    if dev.type == "cpu":
        torch.set_num_threads(4)
    stride, epochs = arg("stride", 3), arg("epochs", 30)
    seed = arg("seed", 0); torch.manual_seed(seed); np.random.seed(seed)
    df, X, Mk, Y = build(pd.read_csv("data/clean_prices.csv"))
    print(f"built {len(df):,} rows on {dev} in {time.time() - t0:.0f}s")

    mkts, crops = sorted(df.market.unique()), sorted(df.commodity.unique())
    doy = df.date.dt.dayofyear.values
    T = lambda a, dt=torch.float32: torch.as_tensor(a, dtype=dt)
    tens = {"x": T(np.nan_to_num(X) / df.scale.values[:, None].astype(np.float32)), "m": T(Mk.astype(np.float32)),
            "mkt": T(df.market.map({k: i for i, k in enumerate(mkts)}).values, torch.long),
            "crop": T(df.commodity.map({k: i for i, k in enumerate(crops)}).values, torch.long),
            "dow": T(df.date.dt.dayofweek.values, torch.long),
            "stat": T(np.c_[np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25), np.log(df.scale.values)])}
    del X, Mk

    # per-horizon split masks, exactly train.py: train date+h < 2024, valid 2024 with date+h < 2025, test date >= 2025
    end = np.stack([(df.date + pd.Timedelta(days=h)).values for h in HORIZONS], 1)
    Ytr = np.where(end < np.datetime64(SPLIT_VALID), Y, np.nan)
    Yva = np.where((df.date.values[:, None] >= np.datetime64(SPLIT_VALID)) & (end < np.datetime64(SPLIT_TEST)), Y, np.nan)
    # ponytail: sample every `stride`-th calendar day for training (3 is coprime with 7, so all weekdays seen)
    day_no = (df.date - pd.Timestamp("2019-01-01")).dt.days.values
    tr = np.where(~np.isnan(Ytr).all(1) & (day_no % stride == 0))[0]
    va = np.where(~np.isnan(Yva).all(1))[0]
    te = np.where(df.date.values >= np.datetime64(SPLIT_TEST))[0]
    print(f"train windows {len(tr):,} (every {stride} days), valid {len(va):,}, test {len(te):,}")

    net = Net(len(mkts), len(crops)).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=2e-3)
    batch = lambda idx: {k: v[idx].to(dev) for k, v in tens.items()}

    def predict(idx, bs=8192):
        net.eval()
        with torch.no_grad():
            out = torch.cat([net(**batch(idx[i:i + bs])).cpu() for i in range(0, len(idx), bs)])
        net.train()
        return out.sort(-1).values  # no quantile crossing

    Ytr_t, Yva_t = T(Ytr), T(Yva)
    best, best_state, bad, t1 = 1e9, None, 0, time.time()
    for ep in range(epochs):
        perm = tr[np.random.permutation(len(tr))]
        for i in range(0, len(perm), 1024):
            idx = perm[i:i + 1024]
            loss = pinball(net(**batch(idx)), Ytr_t[idx].to(dev))
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        vl = pinball(predict(va), Yva_t[va]).item()
        print(f"epoch {ep + 1}: train {loss.item():.4f} valid {vl:.4f}  ({time.time() - t1:.0f}s)")
        if vl < best - 1e-5:
            best, best_state, bad = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        elif (bad := bad + 1) >= 4:
            break
    train_s = time.time() - t1
    net.load_state_dict(best_state)

    P = predict(te).numpy()
    v1, v2b = lgb_tables("models/report_v1.md"), lgb_tables("models/report_v2b.md")
    results, lines = {}, []
    for j, h in enumerate(HORIZONS):
        ok = ~np.isnan(Y[te, j])
        y, p, crop = Y[te, j][ok], P[ok, j], df.commodity.values[te][ok]
        r = {"lstm": mape(y, p[:, 1]), "same_price": mape(y, np.zeros_like(y)),
             "coverage_10_90": float(np.mean((y >= p[:, 0]) & (y <= p[:, 2])) * 100), "test_rows": int(ok.sum())}
        bc = pd.DataFrame({"c": crop, "l": np.abs(np.exp(p[:, 1] - y) - 1) * 100, "b": np.abs(np.exp(-y) - 1) * 100}).groupby("c").mean()
        r["by_crop"] = {c: {"lstm": round(float(bc.l[c]), 1), "same_price": round(float(bc.b[c]), 1)} for c in KEY if c in bc.index}
        results[h] = r
        rows = [("**Overall**", r["lstm"], v1[h]["Overall"], v2b[h]["Overall"], r["same_price"])] + \
               [(c, bc.l[c], v1[h].get(c, np.nan), v2b[h].get(c, np.nan), bc.b[c]) for c in KEY if c in bc.index]
        lines += [f"\n### {h} days ahead (MAPE %, lower is better)\n",
                  "| | LSTM | LightGBM v1 | LightGBM v2b (live) | Price stays same |", "|---|---|---|---|---|"]
        lines += [f"| {n} | {a:.1f} | {b:.1f} | {c:.1f} | {d:.1f} |" for n, a, b, c, d in rows]
        lines.append(f"| P10–P90 coverage (target 80) | {r['coverage_10_90']:.0f}% | {v1[h]['coverage']:.0f}% | {v2b[h]['coverage']:.0f}% | – |")
        print(f"h={h}: LSTM {r['lstm']:.1f}% vs same-price {r['same_price']:.1f}% vs v1 {v1[h]['Overall']} / v2b {v2b[h]['Overall']}, "
              f"coverage {r['coverage_10_90']:.0f}%, {r['test_rows']:,} rows")

    OUT.mkdir(parents=True, exist_ok=True)
    torch.save({"state": best_state, "markets": mkts, "crops": crops,
                "scale": df.drop_duplicates(["market", "commodity"]).set_index(["market", "commodity"]).scale.to_dict()},
               OUT / "lstm.pt")
    cfg = {"seq_len": SEQ, "hidden": 64, "layers": 1, "stride": stride, "seed": seed, "batch": 1024, "lr": 2e-3, "patience": 4,
           "epochs_run": ep + 1, "train_windows": len(tr), "device": str(dev), "train_seconds": round(train_s),
           "total_seconds": round(time.time() - t0), "best_valid_pinball": best}
    (OUT / "meta.json").write_text(json.dumps({"horizons": HORIZONS, "quantiles": QUANTILES, "config": cfg,
                                               "results": results}, indent=1))
    (OUT / "report.md").write_text("# LSTM vs LightGBM — test 2025\n" + "\n".join(lines))
    print(f"done in {time.time() - t0:.0f}s (training {train_s:.0f}s) -> {OUT}")
