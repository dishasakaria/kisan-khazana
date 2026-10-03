"""NASA POWER daily agro-weather per Maharashtra district HQ -> data/ext/weather_districts.csv.

Source: https://power.larc.nasa.gov (MERRA-2 / GEOS-IT + IMERG-corrected precip, 0.5x0.625 deg grid).
Units: rain_mm mm/day, tmax/tmin degC, rh %, soil_root/soil_top wetness 0-1, evapotrans MJ/m2/day (energy flux).
-999 = missing (dropped; latest ~3 days not yet published). Re-runnable: refetches everything.
Usage: python sources/nasa_power.py [start=2019-01-01] [end=today]
"""
import csv, datetime as dt, os, sys, time

from districts import EXT, HQ, http_json

PARAMS = {"PRECTOTCORR": "rain_mm", "T2M_MAX": "tmax", "T2M_MIN": "tmin", "RH2M": "rh",
          "GWETROOT": "soil_root", "GWETTOP": "soil_top", "EVPTRNS": "evapotrans"}
OUT = os.path.join(EXT, "weather_districts.csv")

if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else "2019-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else dt.date.today().isoformat()
    os.makedirs(EXT, exist_ok=True)
    n = 0
    with open(OUT + ".tmp", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "district", "lat", "lon", *PARAMS.values()])
        for name, (lat, lon) in HQ.items():
            js = http_json("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=" + ",".join(PARAMS)
                           + f"&community=AG&longitude={lon}&latitude={lat}&start={start.replace('-', '')}"
                           f"&end={end.replace('-', '')}&format=JSON", timeout=300)
            p = js["properties"]["parameter"]
            fill = js.get("header", {}).get("fill_value", -999)
            for day in sorted(p["PRECTOTCORR"]):
                vals = [p[k].get(day) for k in PARAMS]
                vals = ["" if v is None or v == fill else v for v in vals]
                if any(v != "" for v in vals):  # drop days that are all-missing (not yet published)
                    w.writerow([f"{day[:4]}-{day[4:6]}-{day[6:]}", name, lat, lon, *vals])
                    n += 1
            print(name, len(p["PRECTOTCORR"]), "days", flush=True)
            time.sleep(1)  # be polite
    os.replace(OUT + ".tmp", OUT)
    print(n, "rows ->", OUT)
