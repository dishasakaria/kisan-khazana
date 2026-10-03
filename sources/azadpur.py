"""Delhi Azadpur APMC wholesale rates -> data/ext/azadpur.csv
Columns: date,commodity,variety,state,pack,arrivals_t,min_rs_qtl,max_rs_qtl,modal_rs_qtl,source
 source=bulletin   : full Market Information Bulletin (per-package prices, converted to Rs/qtl via pack weight in KG/QTL);
                     2019-2025 from yearly .rar archives, later days via the site's date-range bulletin search.
 source=bazar_rates: 'Current Bazar Rates' summary PDF (Rs/kg x100), only ~last 400 days are listed.
Needs pdftotext (poppler-utils) and bsdtar (apt-get install libarchive-tools) for the .rar archives.
Downloads are cached in data/ext/.cache/azadpur so re-runs only fetch new days."""
import datetime as dt, re, subprocess, sys, tempfile, time
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ext/azadpur.csv"
CACHE = ROOT / "data/ext/.cache/azadpur"
SITE = "https://apmcazadpurdelhi.com"
YEARS = range(2019, 2026)  # yearly bulletin archives
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (sell-smart research)"

NUM = r"(\d+(?:\.\d+)?)"
ROW = re.compile(rf"^(?P<left>.*?)\s{NUM}\s*(?P<unit>K\.?G|QTL|QUINTAL|PC|PCS|DOZ|DOZEN|NOS|GM|BUNDLE)\b\.?(?P<pack>.*?)\s+{NUM}\s+{NUM}\s+{NUM}\s*$")
HEAD = re.compile(rf"^\s*(\d{{1,3}})\s*\.?\s+([A-Z][A-Z .&/()'-]*?[A-Z.)])(?:\s+{NUM})?\s*$")
KG_PER = {"KG": 1, "QTL": 100, "QUINTAL": 100}


def get(url, **kw):
    time.sleep(1.5)
    r = (s.post if "data" in kw or "files" in kw else s.get)(url, timeout=180, **kw)
    r.raise_for_status()
    return r


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout


def bulletin_date(text, name):
    for pat in (r"(\d{2})/(\d{2})/(\d{4})", r"DATE\s+(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", r"(\d{2})[.\-]?(\d{2})[.\-]?(\d{4})"):
        m = re.search(pat, text[:3000]) or (re.search(pat, name) if pat.endswith("(\\d{4})") else None)
        if m:
            try:
                return dt.date(int(m[3]), int(m[2]), int(m[1]))
            except ValueError:
                pass
    return None


def parse_bulletin(text, date):
    rows, comm, arr, state, variety, varcol = [], None, None, "", "", 40
    for line in text.splitlines():
        if "VARIETY" in line:
            varcol = line.index("VARIETY"); continue
        if (h := HEAD.match(line)) and not ROW.match(line) and len(h[2]) <= 40:  # long = footnote
            comm, arr, state, variety = h[2].strip(), float(h[3]) if h[3] else None, "", ""; continue
        if comm is None or not (r := ROW.match(line)):
            continue
        left = r["left"]
        if hm := re.match(r"\s*\d{1,3}\.?\s+([A-Z]\S*(?: \S+)*)", left):  # item header and first row on one line
            comm, arr, state, variety = hm[1], None, "", ""
            left = " " * hm.end() + left[hm.end():]
        toks = [(m.start(), m.group()) for m in re.finditer(r"\S+(?: \S+)*", left)]
        st = [t for p, t in toks if p < varcol - 6]
        va = [t for p, t in toks if p >= varcol - 6]
        if st and state.endswith("/"):  # wrapped state list ("HP/KINNAUR(CS)/" + "SHIMLA/KULLU"): keep variety
            state += " ".join(st)
        elif st:
            state, variety = " ".join(st), ""
        if va:
            variety = " ".join(va)
        lo, hi, mo, w = float(r[5]), float(r[6]), float(r[7]), float(r[2])
        k = KG_PER.get(r["unit"].replace(".", ""))
        if not k or not w or not lo <= mo <= hi:  # per-piece prices / misaligned columns  # per-piece/dozen prices have no weight -> skip
            continue
        f = 100 / (w * k)
        rows.append((date.isoformat(), comm, variety, state, " ".join(f"{r[2]} {r['unit'].replace('.', '')} {r['pack'].lstrip('.')}".split()), arr,
                     round(lo * f, 2), round(hi * f, 2), round(mo * f, 2), "bulletin"))
    return rows


def parse_bazar(text):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    date = dt.date(int(m[3]), int(m[2]), int(m[1])).isoformat()
    out = []
    for r in re.finditer(r"^\s*\d+\s+([A-Z][A-Z .&/()-]*?[A-Z.)])((?:\s+\d+(?:\.\d+)?){3,5})\s*$", text, re.M):
        n = [float(x) for x in r[2].split()]  # [arrival_t] min max modal [vehicles]
        arr, (lo, hi, mo) = (n[0], n[1:4]) if len(n) >= 4 else (None, n)
        out.append((date, r[1].strip(), "ALL", "", "Rs/kg", arr, round(lo * 100, 2), round(hi * 100, 2), round(mo * 100, 2), "bazar_rates"))
    return out


def cached(name, fetch):
    p = CACHE / name
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(fetch().content)
    return p


def main():
    rows, last = [], None
    # 1) yearly archives
    page = get(f"{SITE}/Home/market_bulletins").text
    for y in YEARS:
        href = re.search(rf'href="([^"]*Bulletin ZIP Files/{y}\.rar)"', page)
        if not href:
            print(f"{y}: archive not listed"); continue
        rar = cached(f"{y}.rar", lambda: get(SITE + href[1].replace(" ", "%20")))
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["bsdtar", "-xf", str(rar), "-C", td], check=True)
            n0, files = len(rows), sorted(Path(td).rglob("*.pdf"))
            for f in files:
                t = pdf_text(f)
                d = bulletin_date(t, f.name)
                if d and d.year == y:
                    rows += parse_bulletin(t, d)
                    last = max(last or d, d)
        print(f"{y}.rar: {len(files)} pdfs, {len(rows) - n0} rows", flush=True)
    # 2) bulletins after the last archived day, via the date-range search (FileId listing)
    start = (last or dt.date(2019, 1, 1)) + dt.timedelta(days=1)
    lst = get(f"{SITE}/Home/market_bulletins", files={"FromeDate": (None, start.isoformat()), "ToDate": (None, dt.date.today().isoformat())}).text
    ids = re.findall(r"<td>(\d{2}/\d{2}/\d{4})</td>\s*<td>[^<]*</td>\s*<td><a[^>]*DownloadFile\((\d+)\)", lst)
    n0 = len(rows)
    for ds, fid in ids:
        p = cached(f"bulletin_{fid}.pdf", lambda: get(f"{SITE}/Home/DownloadFile", data={"FileId": fid}))
        d = dt.datetime.strptime(ds, "%d/%m/%Y").date()
        rows += parse_bulletin(pdf_text(p), d)
    print(f"bulletins {start}..: {len(ids)} pdfs, {len(rows) - n0} rows", flush=True)
    # 3) Current Bazar Rates summary PDFs (Rs/kg)
    ids = re.findall(r"DownloadFile\((\d+)\)", get(f"{SITE}/Home/current_bazar_rates").text)
    n0 = len(rows)
    for fid in ids:
        p = cached(f"bazar_{fid}.pdf", lambda: get(f"{SITE}/Home/DownloadFile1", data={"FileId": fid}))
        try:
            rows += parse_bazar(pdf_text(p))
        except (TypeError, ValueError):
            print(f"  bazar {fid}: no date found, skipped")
    print(f"bazar_rates: {len(ids)} pdfs, {len(rows) - n0} rows", flush=True)

    cols = ["date", "commodity", "variety", "state", "pack", "arrivals_t", "min_rs_qtl", "max_rs_qtl", "modal_rs_qtl", "source"]
    df = pd.DataFrame(rows, columns=cols).drop_duplicates().sort_values(["date", "source", "commodity"])
    assert len(df) > 1000, "too few rows parsed"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"azadpur: {len(df)} rows, {df.date.nunique()} days {df.date.min()}..{df.date.max()} -> {OUT}")


if __name__ == "__main__":
    main()
