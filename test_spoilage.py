"""Checks for spoilage.py. `python test_spoilage.py` runs offline.
SPOILAGE_LIVE=1 python test_spoilage.py  also calls Gemini on data/samples/ (>=6 s apart for the free tier).

Sample images (Wikimedia Commons, all CC BY-SA 4.0), saved in data/samples/ (gitignored):
  onion_sacks.jpg      https://commons.wikimedia.org/wiki/File:Sacks_of_onions.jpg
  onion_sprouting.jpg  https://commons.wikimedia.org/wiki/File:Red_onion_bulb_soft_and_sprouting_after_being_stored_in_light._Norway,_September_2017.jpg
  onion_rotten.jpg     https://commons.wikimedia.org/wiki/File:Rotten_onion.jpg
  tomato_crate.jpg     https://commons.wikimedia.org/wiki/File:Tomato_crate_in_farm,_Punjab.jpg
  grain_sacks.jpg      https://commons.wikimedia.org/wiki/File:Peruvian_Market_Grain_Sacks.jpg
"""
import os, time
from pathlib import Path
from spoilage import (MAX_RATE, MIN_RATE, _finalize, adjust_for_humidity, assess, farmer_message,
                      spoil_rate, weekly_loss_pct)

# rate table: research baselines and multipliers
assert spoil_rate("Onion", "good") == 0.003
assert spoil_rate("Tomato", "good") == 0.015
assert spoil_rate("Soyabean", "good") == 0.0003
assert spoil_rate("Potato", "good") == 0.002
assert spoil_rate("Onion", "early_sprouting") == 0.006
assert spoil_rate("Onion", "some_rot") == 0.009
assert spoil_rate("Onion", "damp_mould") == 0.012
assert spoil_rate("Onion", "heavy_rot") == 0.015
assert spoil_rate("Onion", "good", sprouting=True) == 0.006  # sprout flag never lowers the rate
assert spoil_rate("Onion", "unclear") == 0.003
assert spoil_rate("Tomato", "heavy_rot") == MAX_RATE  # 7.5% capped at 5%
assert spoil_rate("Banana?", "good") == 0.005  # unknown crop -> "other"
for c in ["Onion", "Tomato", "Soyabean", "Grapes", "other"]:
    for cond in ["good", "early_sprouting", "some_rot", "heavy_rot", "damp_mould", "unclear", "junk"]:
        assert MIN_RATE <= spoil_rate(c, cond) <= MAX_RATE

# humidity: onion/potato only, capped
assert adjust_for_humidity(0.004, 85) == 0.006
assert adjust_for_humidity(0.004, 75) == 0.005
assert adjust_for_humidity(0.004, 60) == 0.004
assert adjust_for_humidity(0.004, 90, "Potato") == 0.006
assert adjust_for_humidity(0.004, 90, "Soyabean") == 0.004
assert adjust_for_humidity(0.04, 90) == MAX_RATE
assert adjust_for_humidity(0.004, None) == 0.004

assert weekly_loss_pct(0.003) == 2.1

# model output -> validated result
r = _finalize({"crop": "Onion", "storage": "bags", "condition": "early_sprouting", "rot_pct_est": 140,
               "sprouting": True, "moisture_signs": False, "bags_visible": 12, "heap_qty_qtl": None,
               "confidence": "medium", "message": "कोंब येत आहेत"})
assert r["est_qty_qtl"] == 6.0 and r["rot_pct_est"] == 100 and r["spoil_rate_per_day"] == 0.006
r2 = _finalize({"crop": "Tomato", "storage": "crates", "condition": "good", "bags_visible": 4})
assert r2["est_qty_qtl"] == 1.0  # 4 crates x 25 kg
r3 = _finalize({"crop": "Onion", "storage": "heap", "condition": "good", "bags_visible": None, "heap_qty_qtl": 80})
assert r3["est_qty_qtl"] == 80.0
u = _finalize({"crop": "nonsense", "condition": "unclear", "bags_visible": 30, "confidence": "high"}, crop_hint="Onion")
assert u["crop"] == "Onion" and u["est_qty_qtl"] is None and u["bags_visible"] is None and u["confidence"] == "low"
assert _finalize({"condition": "made_up"})["condition"] == "unclear"

# farmer message: approximate qty + confirm, weekly loss, language
m = farmer_message(r, "mr")
assert "अंदाजे ६ क्विंटल (१२ पोती)" in m and "बरोबर आहे का" in m and "४.१%" in m and len(m.splitlines()) == 3, m
assert "Roughly 1 quintals (4 crates)" in farmer_message(r2, "en")
assert "अंदाज़न" in farmer_message(r, "hi")
mu = farmer_message(u, "mr")
assert "टाइप" in mu and "%" not in mu and len(mu.splitlines()) == 2
assert farmer_message(r, "xx") == m  # unknown lang -> Marathi
assert assess(b"") is None
print("offline checks ok")

if os.environ.get("SPOILAGE_LIVE"):
    hints = {"onion_sacks": "Onion", "tomato_crate": "Tomato"}
    print(f"{'image':18} {'crop':10} {'storage':8} {'condition':16} {'bags':>4} {'qtl':>6} {'rate/day':>8} {'conf':6} {'s':>4}")
    for i, f in enumerate(sorted(Path(__file__).with_name("data").joinpath("samples").glob("*.jpg"))):
        if i:
            time.sleep(6)
        res = assess(f.read_bytes(), crop_hint=hints.get(f.stem), lang="mr")
        assert res is None or 0 < res["spoil_rate_per_day"] <= MAX_RATE
        if res is None:
            print(f"{f.stem:18} FAILED (None)"); continue
        print(f"{f.stem:18} {res['crop'][:10]:10} {res['storage']:8} {res['condition']:16} {str(res['bags_visible']):>4} "
              f"{str(res['est_qty_qtl']):>6} {res['spoil_rate_per_day']:>8} {res['confidence']:6} {res['latency_s']:>4}")
        print("   model:", res["message"])
        print("   reply:", farmer_message(res, "mr").replace("\n", " | "))
