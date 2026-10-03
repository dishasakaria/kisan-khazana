# Model report (LightGBM CPU)

Train < 2024-01-01, tune 2024, TEST 2025 (unseen). Error = MAPE of price.


## 7 days ahead

| | MAPE % |
|---|---|
| **Our model** | **15.9** |
| **Model + safety rule (final)** | **15.9** |
| Baseline: price stays same | 17.4 |
| Baseline: same week past years | 21.9 |

Real price inside our P10–P90 range: **79%** of 90,762 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       4.3 |            5.1 |       4.3 |
| Maize                     |       4.2 |            4.7 |       4.2 |
| Onion                     |      13.5 |           11.5 |      13.5 |
| Pomegranate               |      14.2 |           15.8 |      14.2 |
| Potato                    |       9.4 |           10.4 |       9.4 |
| Soyabean                  |       2.3 |            2.6 |       2.3 |
| Tomato                    |      21.8 |           23.8 |      21.8 |
| Wheat                     |       3.3 |            3.8 |       3.3 |

Safety rule used simple forecast for 6 crops (chosen on 2024): Banana, Castor Seed, Jack Fruit, Karbuja (Musk Melon), Lentil (Masur)(Whole), Mango

## 14 days ahead

| | MAPE % |
|---|---|
| **Our model** | **19.5** |
| **Model + safety rule (final)** | **19.5** |
| Baseline: price stays same | 21.0 |
| Baseline: same week past years | 26.4 |

Real price inside our P10–P90 range: **79%** of 88,749 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       4.7 |            5.7 |       4.7 |
| Maize                     |       4.8 |            5.4 |       4.8 |
| Onion                     |      20.4 |           15   |      20.4 |
| Pomegranate               |      14.6 |           15.8 |      14.6 |
| Potato                    |      10.5 |           11.8 |      10.5 |
| Soyabean                  |       2.9 |            3.4 |       2.9 |
| Tomato                    |      26.2 |           28.8 |      26.2 |
| Wheat                     |       3.7 |            4.4 |       3.7 |

Safety rule used simple forecast for 8 crops (chosen on 2024): Castor Seed, Chikoos (Sapota), Green Gram (Moong)(Whole), Jack Fruit, Karbuja (Musk Melon), Lentil (Masur)(Whole), Tamarind Seed, Water Melon

## 21 days ahead

| | MAPE % |
|---|---|
| **Our model** | **21.7** |
| **Model + safety rule (final)** | **21.8** |
| Baseline: price stays same | 23.7 |
| Baseline: same week past years | 29.1 |

Real price inside our P10–P90 range: **78%** of 86,279 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       5.2 |            5.8 |       5.2 |
| Maize                     |       5.2 |            5.5 |       5.2 |
| Onion                     |      25.7 |           18   |      25.7 |
| Pomegranate               |      17   |           18.4 |      18.4 |
| Potato                    |      11.1 |           12.6 |      11.1 |
| Soyabean                  |       3.5 |            4   |       4   |
| Tomato                    |      29.9 |           32.6 |      29.9 |
| Wheat                     |       4.1 |            4.7 |       4.1 |

Safety rule used simple forecast for 10 crops (chosen on 2024): Amla (Nelli Kai), Chikoos (Sapota), Grapes, Green Gram (Moong)(Whole), Guava, Karbuja (Musk Melon), Papaya, Pomegranate, Soyabean, Tender Coconut

## What drives the forecast (21-day model, importance)

|            |    0 |
|:-----------|-----:|
| commodity  | 30.1 |
| season_sin |  9.6 |
| market     |  9.5 |
| yoy        |  8.5 |
| season_cos |  8.2 |
| tmax_7     |  6.7 |
| gap_crop   |  6.5 |
| dev_ma7    |  4.9 |
| crop_ret_7 |  3.6 |
| dev_ma30   |  2.8 |
| ret_28     |  2.5 |
| ret_1      |  2.3 |