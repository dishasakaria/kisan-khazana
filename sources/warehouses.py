"""MSWC (Maharashtra State Warehousing Corp.) warehouse centres -> data/ext/warehouses_mswc.csv.

Directory: https://mswarehousing.com/Mar-mswc/all-districts-list/ (Marathi table: centre no, district, centre,
address+phone, email, manager+mobile, godowns, capacity MT, tariff, grade).
Occupancy: newest "occupancy" PDF found through the site's WordPress media API. MSWC only publishes centres
BELOW 50% utilisation, so occ_* is blank for every centre not in that list (blank != full).
Matched to the directory by English centre name vs the centre's e-mail stub (difflib, >=0.75).
Geocode: Marathi centre name -> e-mail stub -> PIN, within 90 km of district HQ (Nominatim/Photon,
1 req/s, cached); else district HQ. Usage: python sources/warehouses.py   (needs poppler `pdftotext`)
"""
import csv, difflib, html, json, os, re, subprocess, tempfile

from districts import EXT, HQ, geocode, http

SITE = "https://mswarehousing.com/Mar-mswc/"
OUT = os.path.join(EXT, "warehouses_mswc.csv")
MR_DIST = {
    "अकोला": "Akola", "अमरावती": "Amarawati", "अहमदनगर": "Ahmednagar", "उस्मानाबाद": "Dharashiv (Usmanabad)",
    "औरंगाबाद": "Chattrapati Sambhajinagar", "कोल्हापुर": "Kolhapur", "गडचिरोली": "Gadchiroli", "गोंदिया": "Gondiya",
    "चंद्रपुर": "Chandrapur", "चंद्रपूर": "Chandrapur", "जळगांव": "Jalgaon", "जळगाव": "Jalgaon", "जालना": "Jalana",
    "ठाणे": "Thane", "धुळे": "Dhule", "नंदुरबार": "Nandurbar", "नांदेड": "Nanded", "नागपुर": "Nagpur", "नागपूर": "Nagpur",
    "नाशिक": "Nashik", "परभणी": "Parbhani", "पुणे": "Pune", "बीड": "Beed", "बुलढाणा": "Buldhana", "भंडारा": "Bhandara",
    "यवतमाळ": "Yavatmal", "रत्नागिरी": "Ratnagiri", "रायगड": "Raigad", "लातुर": "Latur", "लातूर": "Latur", "वर्धा": "Wardha",
    "वाशिम": "Vashim", "सांगली": "Sangli", "सातारा": "Satara", "सिंधुदुर्ग": "Sindhudurg", "सोलापुर": "Sholapur",
    "सोलापूर": "Sholapur", "हिंगोली": "Hingoli", "पालघर": "Palghar", "मुंबई": "Mumbai",
}
DEV = str.maketrans("०१२३४५६७८९", "0123456789")


def text(td):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", td)).split())


def directory():
    page = http(SITE + "all-districts-list/").decode("utf-8")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        c = [text(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(c) < 11 or not c[0].isdigit():
            continue
        addr = c[4].translate(DEV)
        pin = re.findall(r"\b(4\d{5})\b", addr)
        phone = addr.split("दूरध्वनी")[-1].strip(" :-") if "दूरध्वनी" in addr else ""
        mob = re.findall(r"\b\d{10}\b", c[6].translate(DEV))
        rows.append({
            "centre_no": c[1], "district": MR_DIST.get(c[2], c[2]), "district_mr": c[2], "centre_mr": c[3],
            "centre_en_stub": re.sub(r"\.wh@.*|@.*", "", c[5]), "address_mr": addr.split("कार्या")[0].strip(" ,"),
            "pin": pin[-1] if pin else "", "phone": phone, "email": c[5],
            "manager": re.sub(r"मोबाईल.*", "", c[6]).strip() if c[6] != "#N/A" else "", "manager_mobile": mob[0] if mob else "",
            "godowns": c[7], "capacity_t": c[8], "grade": c[10]})
    return rows


def occupancy():
    """(source_url, [{name, godowns, capacity_t, used_t, pct}]) from the newest occupancy PDF."""
    media = json.loads(http(SITE + "wp-json/wp/v2/media?search=occupancy&per_page=20&orderby=date&order=desc"))
    pdfs = [m for m in media if m["source_url"].lower().endswith(".pdf")]
    if not pdfs:
        return "", []
    url = pdfs[0]["source_url"]
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(http(url)); f.flush()
        txt = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout
    out = []
    for line in txt.splitlines():
        m = re.match(r"\s*(\d+)\s+(.+?)\s+((?:-?\d+\s+){11}-?\d+)\s*$", line)
        if m:
            n = [int(x) for x in m.group(3).split()]
            out.append({"name": m.group(2).strip(), "godowns": n[2], "capacity_t": n[5], "used_t": n[8], "pct": n[11]})
    return url, out


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower().replace("midc", ""))


if __name__ == "__main__":
    rows = directory()
    url, occ = occupancy()
    month = re.search(r"([A-Za-z]+-20\d\d)", url.split("/")[-1])
    used = set()
    for o in occ:
        best = max(rows, key=lambda r: difflib.SequenceMatcher(None, norm(o["name"]), norm(r["centre_en_stub"])).ratio())
        score = difflib.SequenceMatcher(None, norm(o["name"]), norm(best["centre_en_stub"])).ratio()
        if score >= 0.75 and best["centre_no"] not in used:
            used.add(best["centre_no"])
            best.update(occ_name_en=o["name"], occ_month=month.group(1) if month else "", occ_capacity_t=o["capacity_t"],
                        occ_used_t=o["used_t"], occ_pct=o["pct"], occ_source=url)
        else:
            print("occupancy row not matched:", o["name"], "best:", best["centre_en_stub"], round(score, 2))
    for r in rows:
        hq = HQ.get(r["district"])
        stub = re.sub(r"\d+$", "", r["centre_en_stub"])
        lat, lon, q = geocode([r["centre_mr"].split("(")[0].strip(" ,"), stub],
                              pin=r["pin"], near=hq, max_km=90)
        if lat is None and hq:
            lat, lon, q = *hq, "district_hq"
        r.update(lat=lat or "", lon=lon or "", geo_quality=q or "")
    cols = ["centre_no", "district", "district_mr", "centre_mr", "centre_en_stub", "address_mr", "pin", "phone", "email",
            "manager", "manager_mobile", "godowns", "capacity_t", "grade", "occ_name_en", "occ_month", "occ_capacity_t",
            "occ_used_t", "occ_pct", "occ_source", "lat", "lon", "geo_quality"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, cols, restval="")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "centres,", len(used), "/", len(occ), "occupancy rows matched ->", OUT)
