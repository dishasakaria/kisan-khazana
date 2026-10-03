"""One name per mandi and per crop across sources (Kaggle/Agmarknet, MSAMB, Agmarknet 2.0)."""
import difflib, re

from clean import canon

# MSAMB crop name -> Agmarknet/Kaggle name (only where they differ)
CROP = {
    "Gram": "Bengal Gram (Gram)(Whole)", "Pigeon Pea (Tur)": "Arhar (Tur/Red Gram)(Whole)", "Pigeon Pea": "Arhar (Tur/Red Gram)(Whole)",
    "Tur": "Arhar (Tur/Red Gram)(Whole)", "Bajri": "Bajra (Pearl Millet/Cumbu)", "Bazara": "Bajra (Pearl Millet/Cumbu)",
    "Sorgum(Jawar)": "Jowar (Sorghum)", "Jawar": "Jowar (Sorghum)", "Jowar": "Jowar (Sorghum)",
    "Wheat(Husked)": "Wheat", "Wheat (Husked)": "Wheat", "Black Gram (Udid)": "Black Gram (Urd Beans)(Whole)",
    "Green Gram (Mug)": "Green Gram (Moong)(Whole)", "Green Gram ( Mug)": "Green Gram (Moong)(Whole)",
    "Coriander": "Coriander (Leaves)", "Coriandar": "Coriander (Leaves)", "Fenugreek": "Methi (Leaves)",
    "Cucumber": "Cucumbar (Kheera)", "Bitter Gourd": "Bitter gourd", "Bottle Gourd": "Bottle gourd",
    "Green Chili": "Green Chilli", "Capsicum": "Chilly Capsicum", "Ladies Finger": "Bhindi (Ladies Finger)",
    "Bhendi": "Bhindi (Ladies Finger)", "Cluster Bean": "Guar", "Gavar": "Guar", "Ridgegourd": "Ridgeguard (Tori)",
    "Dodka": "Ridgeguard (Tori)", "Spinach": "Spinach", "Raw Cotton (Kapus)": "Cotton", "Maize": "Maize",
    "Soyabean": "Soyabean", "Onion": "Onion", "Tomato": "Tomato", "Potato": "Potato", "Pomegranate": "Pomegranate",
    "Grapes": "Grapes", "Garlic": "Garlic", "Ginger (Fresh)": "Ginger (Green)", "Carrot": "Carrot", "Cabbage": "Cabbage",
    "Cauliflower": "Cauliflower", "Brinjal": "Brinjal", "French Bean": "French Beans (Frasbean)", "Banana": "Banana",
}


ALIAS = {"ahilyanagar": "ahmednagar", "pimpalgaonbaswant": "pimpalgaon",  # official renames / main-yard names
         "chhatrapatisambhajinagar": "chattrapatisambhajinagar"}


# fuzzy pairs checked by hand and rejected: different towns / separate sub-yards
NOT_SAME = {"koregaon", "sengaon", "baramatisupe"}


def key(s):
    k = re.sub(r"[^a-z]", "", str(s).lower().replace("apmc", ""))
    return ALIAS.get(k, k)


def crop(name):
    n = str(name).strip()
    return CROP.get(n) or CROP.get(n.title()) or n


def market_matcher(known):
    """Returns f(raw) -> known canonical mandi name or None. Exact punctuation-free key first, then close spelling."""
    by_key = {key(k): k for k in known}
    keys = list(by_key)

    def match(raw):
        k = key(canon(raw))
        if k in by_key:
            return by_key[k]
        if k in NOT_SAME:
            return None
        hit = difflib.get_close_matches(k, keys, n=1, cutoff=0.80)  # "sinnar"~"sinner" (0.83) yes; "dound"~"doundkedgaon" (0.59) no
        return by_key[hit[0]] if hit else None
    return match


if __name__ == "__main__":
    m = market_matcher(["Khed (Chakan)", "Sinner", "Pune (Moshi)", "Lasalgaon (Vinchur)", "Dound"])
    assert m("KHED-CHAKAN") == "Khed (Chakan)"
    assert m("Sinnar") == "Sinner"
    assert m("APMC Lasalgaon(Vinchur) ") == "Lasalgaon (Vinchur)"
    assert m("PUNE-MOSHI") == "Pune (Moshi)"
    assert m("Dound-Kedgaon") is None, "different yard must not merge"
    assert market_matcher(["Ahmednagar", "Himalyatnagar"])("Ahilyanagar") == "Ahmednagar", "renamed city"
    assert market_matcher(["Kopargaon", "Shegaon"])("Koregaon") is None, "different town"
    assert crop("Gram") == "Bengal Gram (Gram)(Whole)" and crop("Onion") == "Onion"
    print("names self-checks ok")
