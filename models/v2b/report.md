# Model report (LightGBM CPU)

Train < 2024-01-01, tune 2024, TEST 2025 (unseen). Error = MAPE of price.


## 7 days ahead

| | MAPE % |
|---|---|
| **Our model** | **15.5** |
| **Model + safety rule (final)** | **15.5** |
| Baseline: price stays same | 17.5 |
| Baseline: same week past years | 22.0 |

Real price inside our P10–P90 range: **78%** of 95,551 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       4.1 |            5.2 |       4.1 |
| Maize                     |       4   |            4.5 |       4   |
| Onion                     |      12.3 |           11.7 |      12.3 |
| Pomegranate               |      15.1 |           16.9 |      15.1 |
| Potato                    |       9.4 |           10.4 |       9.4 |
| Soyabean                  |       2.5 |            2.8 |       2.5 |
| Tomato                    |      21.3 |           23.8 |      21.3 |
| Wheat                     |       3.3 |            3.8 |       3.3 |

Safety rule used simple forecast for 24 crops (chosen on 2024): Ajwan, Almond (Badam), Arecanut (Betelnut/Supari), Arhar Dal (Tur Dal), Bengal Gram Dal (Chana Dal), Black Gram Dal (Urd Dal), Cashewnuts, Castor Seed, Cinamon (Dalchini), Coconut, Cotton, Cummin Seed (Jeera), Ghee, Green Gram Dal (Moong Dal), He Buffalo

## 14 days ahead

| | MAPE % |
|---|---|
| **Our model** | **18.7** |
| **Model + safety rule (final)** | **18.7** |
| Baseline: price stays same | 21.1 |
| Baseline: same week past years | 26.4 |

Real price inside our P10–P90 range: **78%** of 93,202 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       4.4 |            5.6 |       4.4 |
| Maize                     |       4.7 |            5.3 |       4.7 |
| Onion                     |      16.4 |           15.1 |      16.4 |
| Pomegranate               |      16.3 |           17.9 |      16.3 |
| Potato                    |      10.4 |           11.8 |      10.4 |
| Soyabean                  |       3.3 |            3.6 |       3.6 |
| Tomato                    |      26.4 |           28.8 |      26.4 |
| Wheat                     |       3.7 |            4.4 |       3.7 |

Safety rule used simple forecast for 24 crops (chosen on 2024): Amla (Nelli Kai), Arecanut (Betelnut/Supari), Bengal Gram Dal (Chana Dal), Black Gram Dal (Urd Dal), Cardamoms, Cashewnuts, Castor Seed, Cinamon (Dalchini), Cotton, Cummin Seed (Jeera), Ginger (Dry), Goat, Green Gram Dal (Moong Dal), He Buffalo, Hen

## 21 days ahead

| | MAPE % |
|---|---|
| **Our model** | **21.1** |
| **Model + safety rule (final)** | **21.1** |
| Baseline: price stays same | 23.7 |
| Baseline: same week past years | 29.1 |

Real price inside our P10–P90 range: **77%** of 90,360 test cases (target ~80%).

Key crops (model vs 'price stays same'):

| commodity                 |   model % |   same-price % |   final % |
|:--------------------------|----------:|---------------:|----------:|
| Bengal Gram (Gram)(Whole) |       4.8 |            5.8 |       4.8 |
| Maize                     |       4.8 |            5.4 |       4.8 |
| Onion                     |      20.8 |           18.2 |      20.8 |
| Pomegranate               |      18   |           19.7 |      19.7 |
| Potato                    |      11.3 |           12.6 |      11.3 |
| Soyabean                  |       4.1 |            4.2 |       4.2 |
| Tomato                    |      26.7 |           32.6 |      26.7 |
| Wheat                     |       4.1 |            4.7 |       4.1 |

Safety rule used simple forecast for 26 crops (chosen on 2024): Ajwan, Almond (Badam), Amla (Nelli Kai), Arecanut (Betelnut/Supari), Bengal Gram Dal (Chana Dal), Black Gram Dal (Urd Dal), Cardamoms, Castor Seed, Cinamon (Dalchini), Coconut, Cotton, Cummin Seed (Jeera), Green Gram Dal (Moong Dal), Guava, Gur (Jaggery)

## What drives the forecast (21-day model, importance)

|              |    0 |
|:-------------|-----:|
| commodity    | 22.6 |
| market       | 14.2 |
| gap_crop     | 10.3 |
| dev_ma7      |  7.4 |
| season_sin   |  6.8 |
| season_cos   |  6.1 |
| yoy          |  5.2 |
| diesel_rs_l  |  5.2 |
| crop_ret_7   |  4.7 |
| dev_ma30     |  3.1 |
| ret_1        |  2.5 |
| price_vs_msp |  1.9 |