# LSTM vs LightGBM — test 2025

### 7 days ahead (MAPE %, lower is better)

| | LSTM | LightGBM v1 | LightGBM v2b (live) | Price stays same |
|---|---|---|---|---|
| **Overall** | 15.9 | 15.9 | 15.5 | 17.4 |
| Onion | 12.3 | 13.5 | 12.3 | 11.5 |
| Tomato | 22.4 | 21.8 | 21.3 | 23.8 |
| Soyabean | 2.5 | 2.3 | 2.5 | 2.6 |
| Wheat | 3.4 | 3.3 | 3.3 | 3.8 |
| Bengal Gram (Gram)(Whole) | 4.5 | 4.3 | 4.1 | 5.1 |
| Potato | 9.5 | 9.4 | 9.4 | 10.4 |
| Maize | 4.3 | 4.2 | 4.0 | 4.7 |
| Pomegranate | 14.4 | 14.2 | 15.1 | 15.8 |
| P10–P90 coverage (target 80) | 80% | 79% | 78% | – |

### 14 days ahead (MAPE %, lower is better)

| | LSTM | LightGBM v1 | LightGBM v2b (live) | Price stays same |
|---|---|---|---|---|
| **Overall** | 18.8 | 19.5 | 18.7 | 21.0 |
| Onion | 16.5 | 20.4 | 16.4 | 15.0 |
| Tomato | 26.8 | 26.2 | 26.4 | 28.8 |
| Soyabean | 3.4 | 2.9 | 3.3 | 3.4 |
| Wheat | 3.8 | 3.7 | 3.7 | 4.4 |
| Bengal Gram (Gram)(Whole) | 4.9 | 4.7 | 4.4 | 5.7 |
| Potato | 10.9 | 10.5 | 10.4 | 11.8 |
| Maize | 4.9 | 4.8 | 4.7 | 5.4 |
| Pomegranate | 14.8 | 14.6 | 16.3 | 15.8 |
| P10–P90 coverage (target 80) | 81% | 79% | 78% | – |

### 21 days ahead (MAPE %, lower is better)

| | LSTM | LightGBM v1 | LightGBM v2b (live) | Price stays same |
|---|---|---|---|---|
| **Overall** | 21.4 | 21.7 | 21.1 | 23.7 |
| Onion | 20.1 | 25.7 | 20.8 | 18.0 |
| Tomato | 29.5 | 29.9 | 26.7 | 32.6 |
| Soyabean | 4.0 | 3.5 | 4.1 | 4.0 |
| Wheat | 4.0 | 4.1 | 4.1 | 4.7 |
| Bengal Gram (Gram)(Whole) | 5.3 | 5.2 | 4.8 | 5.8 |
| Potato | 11.7 | 11.1 | 11.3 | 12.6 |
| Maize | 5.3 | 5.2 | 4.8 | 5.5 |
| Pomegranate | 17.7 | 17.0 | 18.0 | 18.4 |
| P10–P90 coverage (target 80) | 81% | 78% | 77% | – |

## Setup (`python lstm.py`, add `--gpu` for CUDA)

Same targets, split and metric as `train.py`: log(price_{t+h}/price_t), P10/P50/P90 via pinball loss; train where date+h < 2024, early-stop on 2024, test = 2025 pilot rows. Test set is identical to v1 (90,762 / 88,749 / 86,279 rows; "price stays same" matches 17.4 / 21.0 / 23.7). v2b was scored on slightly more rows (95,551 at 7d) from refreshed data, so read its numbers within ±0.1-0.2.

Model: one multi-output net (9 outputs). 1-layer LSTM (hidden 64) over the last 60 days of log price relative to today (ffill ≤ 7 days, plus a "price known" mask), scaled per series by its 7-day volatility measured on pre-2024 data only. A head adds market/crop/weekday embeddings, season sin/cos and the series scale. Outputs are sorted, so quantiles can't cross. To fit the CPU budget it trains on every 3rd calendar day (153k windows): batch 1024, Adam 2e-3, patience 4. **Training: 20 epochs, about 4-7 min on 4 shared CPU cores**, about 26k parameters (128 KB). A second seed gave 16.1 / 19.1 / 21.4, so differences under about 0.3 points are noise.

## Verdict

- **The LSTM beats "price stays same" at every horizon** (−1.5 / −2.2 / −2.3 points) and **ties or beats LightGBM v1** (15.9 vs 15.9, 18.8 vs 19.5, 21.4 vs 21.7). Its biggest gain is Onion at 14-21 days, where v1 did badly.
- **The live LightGBM v2b still wins overall** by 0.1-0.4 points, which is about seed noise. It clearly wins on Tomato at 21 days (26.7 vs 29.5), Bengal Gram and Maize. LightGBM also wins most staple crops (Soyabean, Wheat, Potato) by a small margin.
- **The LSTM's ranges are better calibrated**: 80-81% of real prices fall inside P10-P90, against 77-79% for LightGBM.
- The comparison is not fully even. The LSTM sees only its own price history and the calendar. LightGBM also gets cross-mandi gaps, year-on-year change, weather and (in v2b) external data such as diesel and MSP. Even so, the LSTM matches v1. **Keep v2b live.** The LSTM is a credible challenger, not a replacement.
- Neither model beats "price stays same" on Onion (11.5 / 15.0 / 18.0).

## What would improve the LSTM

1. Feed in LightGBM's extra signals: the crop's price across all mandis that day, year-ago price, weather and external data.
2. Use a longer lookback (365+ days, or a dilated or attention layer) so it can see seasonality.
3. Train on every day (stride 1) and on the whole-state 2010-2025 data, on a GPU.
4. Average LSTM and LightGBM forecasts (their errors differ by crop), and reuse v2b's 2024 fallback rule for crops where the model loses to "price stays same".
