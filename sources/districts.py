"""Shared bits for sources/*.py: Maharashtra district HQ points + polite HTTP/geocoding helpers.

HQ keys use the history_mh.csv `district` spelling (Amarawati, Jalana, Sholapur, Vashim, Gondiya,
Chattrapati Sambhajinagar = Aurangabad, Dharashiv (Usmanabad) = Osmanabad, Ahmednagar = Ahilyanagar).
Palghar, Sindhudurg, Mumbai Suburban are not in history but are MH districts; "Murum" is a Dharashiv
market town that history files as a district, kept so joins don't drop it.
Coords: Nominatim town points (structured city= query, 2026-10-02), hand-checked; Nanded/Mumbai/Murum fixed by hand.
"""
import difflib, json, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "data", "ext")
UA = "sell-smart/0.1 (mandi price research; parth@insitohealth.com)"

HQ = {
    "Ahmednagar": (19.093, 74.7493), "Akola": (20.7117, 77.0026), "Amarawati": (20.9316, 77.7588),
    "Beed": (18.9904, 75.7542), "Bhandara": (21.1707, 79.6566), "Buldhana": (20.5321, 76.1799),
    "Chandrapur": (19.9508, 79.2987), "Chattrapati Sambhajinagar": (19.8773, 75.339),
    "Dharashiv (Usmanabad)": (18.1854, 76.042), "Dhule": (20.898, 74.7732), "Gadchiroli": (20.1854, 80.0035),
    "Gondiya": (21.4552, 80.1963), "Hingoli": (19.7158, 77.1388), "Jalana": (19.8393, 75.8819),
    "Jalgaon": (21.0101, 75.5696), "Kolhapur": (16.7028, 74.2405), "Latur": (18.3982, 76.5626),
    "Mumbai": (18.9388, 72.8354), "Nagpur": (21.1498, 79.0821), "Nanded": (19.1383, 77.321),
    "Nandurbar": (21.3638, 74.2411), "Nashik": (20.0112, 73.7902), "Parbhani": (19.2625, 76.7718),
    "Pune": (18.5214, 73.8545), "Raigad": (18.6498, 72.8765), "Ratnagiri": (16.9934, 73.2954),
    "Sangli": (16.8503, 74.5949), "Satara": (17.6883, 74.0042), "Sholapur": (17.67, 75.9008),
    "Thane": (19.1943, 72.9702), "Vashim": (20.1029, 77.1354), "Wardha": (20.7465, 78.5998),
    "Yavatmal": (20.3903, 78.1329), "Palghar": (19.6967, 72.7695), "Sindhudurg": (16.1163, 73.7079),
    "Mumbai Suburban": (19.0596, 72.8295), "Murum": (17.787, 76.4761),
}

# Common spellings -> HQ key (for mapping other sources' district names).
ALIAS = {
    "ahilyanagar": "Ahmednagar", "ahmadnagar": "Ahmednagar", "amravati": "Amarawati", "aurangabad": "Chattrapati Sambhajinagar",
    "chhatrapati sambhajinagar": "Chattrapati Sambhajinagar", "sambhajinagar": "Chattrapati Sambhajinagar",
    "osmanabad": "Dharashiv (Usmanabad)", "dharashiv": "Dharashiv (Usmanabad)", "usmanabad": "Dharashiv (Usmanabad)",
    "gondia": "Gondiya", "jalna": "Jalana", "solapur": "Sholapur", "washim": "Vashim", "bid": "Beed",
    "mumbai city": "Mumbai", "greater bombay": "Mumbai", "bombay": "Mumbai", "raigarh": "Raigad",
    "buldana": "Buldhana", "yewatmal": "Yavatmal", "yeotmal": "Yavatmal", "paghar": "Palghar", "nasik": "Nashik", "nashik": "Nashik", "garhchiroli": "Gadchiroli",
}


def canon(name):
    """Map any district spelling to the history_mh.csv name (unknown -> stripped title-case input)."""
    n = " ".join(str(name).replace("(", " (").split()).strip()
    k = n.lower()
    if k in ALIAS:
        return ALIAS[k]
    for h in HQ:
        if h.lower() == k:
            return h
    return n.title()


def http(url, tries=4, timeout=120, headers=None, data=None):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if i == tries - 1 or getattr(e, "code", 0) in (400, 404):
                raise
            time.sleep(5 * (i + 1))


def http_json(url, **kw):
    return json.loads(http(url, **kw))


_last = [0.0]
GEOCACHE = os.path.join(EXT, ".cache", "geocode.json")
_geo = None


def _km(a, b):
    import math
    dy, dx = (a[0] - b[0]) * 111, (a[1] - b[1]) * 111 * math.cos(math.radians(a[0]))
    return (dx * dx + dy * dy) ** 0.5


def _nom(params):
    key = "nom|" + urllib.parse.urlencode(sorted(params.items()))
    if key not in _geo:
        wait = 1.1 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)  # Nominatim policy: max 1 req/s
        _last[0] = time.time()
        js = http_json("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {**params, "format": "json", "limit": 1, "countrycodes": "in"}))
        _geo[key] = [float(js[0]["lat"]), float(js[0]["lon"])] if js else None
    return _geo[key]


def _photon(q):
    key = "photon|" + q
    if key not in _geo:
        time.sleep(1)
        js = http_json("https://photon.komoot.io/api/?" + urllib.parse.urlencode({"q": q, "limit": 1}))
        f = js["features"]
        head = q.split(",")[0].strip().lower()
        name = (f[0]["properties"].get("name") or "").lower() if f else ""
        # photon is fuzzy: "Kannad, Aurangabad" returns Aurangabad city. Require the place name to match the query head.
        same = name and (head in name or name in head or difflib.SequenceMatcher(None, head, name).ratio() >= 0.75)
        _geo[key] = ([f[0]["geometry"]["coordinates"][1], f[0]["geometry"]["coordinates"][0]]
                     if same and f[0]["properties"].get("state") == "Maharashtra" else None)
    return _geo[key]


def geocode(names, pin=None, near=None, max_km=80):
    """(lat, lon, quality). Tries each query in `names` on Nominatim then Photon (quality 'name'), then the PIN
    centroid ('pin'); a hit must be in Maharashtra and, if `near`=(lat, lon) is given, within max_km of it.
    Results cached in data/ext/.cache/geocode.json so reruns don't hit the services again."""
    global _geo
    if _geo is None:
        _geo = json.load(open(GEOCACHE)) if os.path.exists(GEOCACHE) else {}

    def ok(ll):
        return ll and 15.5 < ll[0] < 22.2 and 72.5 < ll[1] < 80.95 and (not near or _km(ll, near) <= max_km)

    try:
        for q in [n for n in names if n]:
            for ll in (_nom({"q": f"{q}, Maharashtra"}),):
                if ok(ll):
                    return round(ll[0], 5), round(ll[1], 5), "name"
            ll = _photon(f"{q}, Maharashtra, India")
            if ok(ll):
                return round(ll[0], 5), round(ll[1], 5), "name"
        if pin and str(pin).strip().isdigit() and len(str(pin).strip()) == 6:
            ll = _nom({"postalcode": str(pin).strip(), "country": "India"})
            if ok(ll):
                return round(ll[0], 5), round(ll[1], 5), "pin"
    finally:  # merge with what's on disk (another script may be geocoding too), write atomically
        os.makedirs(os.path.dirname(GEOCACHE), exist_ok=True)
        disk = json.load(open(GEOCACHE)) if os.path.exists(GEOCACHE) else {}
        _geo = {**disk, **_geo}
        json.dump(_geo, open(GEOCACHE + f".{os.getpid()}", "w"))
        os.replace(GEOCACHE + f".{os.getpid()}", GEOCACHE)
    return None, None, None


if __name__ == "__main__":
    assert canon("Ahilyanagar") == "Ahmednagar" and canon("Aurangabad") == "Chattrapati Sambhajinagar"
    assert canon("SOLAPUR") == "Sholapur" and canon("Pune") == "Pune"
    print(len(HQ), "districts;", geocode(["Lasalgaon"], near=HQ["Nashik"]))
