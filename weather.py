"""Daily weather per pilot district -> Supabase `weather`.

History: ERA5-Land reanalysis (ECMWF/Copernicus, 0.1° grid, ~5-day lag) served free by Open-Meteo's archive API.
Recent days + next 16 days: Open-Meteo forecast API (so the model sees rain coming).
Usage: python weather.py history 2019-01-01   |   python weather.py recent
"""
import datetime as dt, json, sys, time, urllib.request

import db

DISTRICTS = {"Pune": (18.5204, 73.8567), "Nashik": (19.9975, 73.7898), "Ahmednagar": (19.0948, 74.7480)}
DAILY = "precipitation_sum,temperature_2m_max,temperature_2m_min"


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "sell-smart/0.1"}), timeout=120) as r:
                return json.load(r)
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def rows(js, district, source):
    d = js["daily"]
    return [{"date": t, "district": district, "rain_mm": r, "tmax": hi, "tmin": lo, "source": source}
            for t, r, hi, lo in zip(d["time"], d["precipitation_sum"], d["temperature_2m_max"], d["temperature_2m_min"])
            if r is not None or hi is not None]


if __name__ == "__main__":
    mode, out = sys.argv[1], []
    for name, (lat, lon) in DISTRICTS.items():
        if mode == "history":
            end = (dt.date.today() - dt.timedelta(days=6)).isoformat()
            js = get(f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
                     f"&start_date={sys.argv[2]}&end_date={end}&daily={DAILY}&models=era5_land&timezone=Asia%2FKolkata")
            out += rows(js, name, "era5_land")
        else:
            js = get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                     f"&daily={DAILY}&past_days=14&forecast_days=16&timezone=Asia%2FKolkata")
            out += rows(js, name, "forecast")
    n = db.upsert("weather", out)
    db.log_run(f"weather_{mode}", "ok", n)
    print(f"weather {mode}: {n} rows ->", sorted({r['source'] for r in out}), out[0]["date"], "...", out[-1]["date"])
