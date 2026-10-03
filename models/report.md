# Model report (LightGBM CPU)

Train < 2024-01-01, tune 2024, TEST 2025 (unseen). Error = MAPE of price.


## 7 days ahead

| | MAPE % |
|---|---|
| **Our model** | **15.9** |
| Baseline: price stays same | 17.4 |
| Baseline: same week past years | 21.9 |

Real price inside our P10–P90 range: **78%** of 90,762 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       4.3 |            5.1 |
| Maize                     |       4.1 |            4.7 |
| Onion                     |      12.6 |           11.5 |
| Pomegranate               |      14.2 |           15.8 |
| Potato                    |       9.5 |           10.4 |
| Soyabean                  |       2.3 |            2.6 |
| Tomato                    |      21.8 |           23.8 |
| Wheat                     |       3.3 |            3.8 |

## 14 days ahead

| | MAPE % |
|---|---|
| **Our model** | **19.4** |
| Baseline: price stays same | 21.0 |
| Baseline: same week past years | 26.4 |

Real price inside our P10–P90 range: **79%** of 88,749 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       4.8 |            5.7 |
| Maize                     |       4.8 |            5.4 |
| Onion                     |      18.7 |           15   |
| Pomegranate               |      14.4 |           15.8 |
| Potato                    |      10.5 |           11.8 |
| Soyabean                  |       2.9 |            3.4 |
| Tomato                    |      26.5 |           28.8 |
| Wheat                     |       3.8 |            4.4 |

## 21 days ahead

| | MAPE % |
|---|---|
| **Our model** | **21.7** |
| Baseline: price stays same | 23.7 |
| Baseline: same week past years | 29.1 |

Real price inside our P10–P90 range: **79%** of 86,279 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       5.1 |            5.8 |
| Maize                     |       5.4 |            5.5 |
| Onion                     |      24   |           18   |
| Pomegranate               |      16.8 |           18.4 |
| Potato                    |      11.4 |           12.6 |
| Soyabean                  |       3.4 |            4   |
| Tomato                    |      30.2 |           32.6 |
| Wheat                     |       4.1 |            4.7 |

## What drives the forecast (21-day model, importance)

|                |    0 |
|:---------------|-----:|
| commodity      | 31.3 |
| days_to_diwali | 10.7 |
| yoy            |  8.6 |
| season_sin     |  7.9 |
| market         |  7.6 |
| gap_crop       |  7.6 |
| dev_ma7        |  6.1 |
| season_cos     |  6.1 |
| crop_ret_7     |  3.6 |
| dev_ma30       |  3.3 |
| ret_1          |  3   |
| ret_28         |  1.8 |