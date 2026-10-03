# Model report (LightGBM CPU)

Train < 2024-01-01, tune 2024, TEST 2025 (unseen). Error = MAPE of price.


## 7 days ahead

| | MAPE % |
|---|---|
| **Our model** | **15.6** |
| Baseline: price stays same | 17.5 |
| Baseline: same week past years | 22.0 |

Real price inside our P10–P90 range: **79%** of 95,551 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       4.1 |            5.2 |
| Maize                     |       4   |            4.5 |
| Onion                     |      11.5 |           11.7 |
| Pomegranate               |      15   |           16.9 |
| Potato                    |       9.4 |           10.4 |
| Soyabean                  |       2.5 |            2.8 |
| Tomato                    |      22.3 |           23.8 |
| Wheat                     |       3.2 |            3.8 |

## 14 days ahead

| | MAPE % |
|---|---|
| **Our model** | **18.9** |
| Baseline: price stays same | 21.1 |
| Baseline: same week past years | 26.4 |

Real price inside our P10–P90 range: **78%** of 93,202 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       4.4 |            5.6 |
| Maize                     |       4.5 |            5.3 |
| Onion                     |      16.1 |           15.1 |
| Pomegranate               |      16.4 |           17.9 |
| Potato                    |      10.5 |           11.8 |
| Soyabean                  |       3.1 |            3.6 |
| Tomato                    |      27.9 |           28.8 |
| Wheat                     |       3.7 |            4.4 |

## 21 days ahead

| | MAPE % |
|---|---|
| **Our model** | **20.9** |
| Baseline: price stays same | 23.7 |
| Baseline: same week past years | 29.1 |

Real price inside our P10–P90 range: **78%** of 90,360 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |
|:--------------------------|----------:|---------------:|
| Bengal Gram (Gram)(Whole) |       4.8 |            5.8 |
| Maize                     |       4.8 |            5.4 |
| Onion                     |      21.5 |           18.2 |
| Pomegranate               |      18.4 |           19.7 |
| Potato                    |      11.3 |           12.6 |
| Soyabean                  |       3.6 |            4.2 |
| Tomato                    |      31.4 |           32.6 |
| Wheat                     |       4   |            4.7 |

## What drives the forecast (21-day model, importance)

|            |    0 |
|:-----------|-----:|
| commodity  | 24.8 |
| market     | 20.9 |
| season_sin |  8.7 |
| gap_crop   |  8.4 |
| season_cos |  7.3 |
| yoy        |  6.8 |
| dev_ma7    |  5.5 |
| crop_ret_7 |  4.9 |
| dev_ma30   |  2.5 |
| ret_1      |  2   |
| vol_30     |  2   |
| ret_28     |  2   |