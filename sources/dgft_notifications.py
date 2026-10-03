"""Pull the current DGFT notification list -> data/ext/dgft_notifications.csv.

Source: https://www.dgft.gov.in/CP/?opt=notification (server-rendered table #metaTable).
Run: python3 sources/dgft_notifications.py
"""
import csv, html, re, sys, urllib.request
from pathlib import Path

URL = "https://www.dgft.gov.in/CP/?opt=notification"
OUT = Path(__file__).resolve().parents[1] / "data" / "ext" / "dgft_notifications.csv"
AGRI = re.compile(r"\b(wheat|rice|onions?|sugar|pulses?|tur|gram|chana|soy\w*|edible|oils?|maize|potato|garlic|flour|atta|cotton|de-oiled|millets?|lentils?|peas|honey)\b", re.I)


def _txt(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse(page):
    body = page[page.find('id="metaTable"'):]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 7:
            continue
        link = re.search(r'href="([^"]+)"', tds[6])
        rows.append({
            "number": _txt(tds[1]), "year": _txt(tds[2]), "subject": _txt(tds[3]),
            "date": _txt(tds[4]),  # dd/mm/yyyy
            "pdf_url": link.group(1).replace(" ", "%20") if link else "",
            "agri_related": bool(AGRI.search(_txt(tds[3]))),
        })
    return rows


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 sell-smart"})
    page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    rows = parse(page)
    if not rows:
        sys.exit("DGFT: no rows parsed - page layout changed?")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows ({sum(r['agri_related'] for r in rows)} agri) -> {OUT}")


if __name__ == "__main__":
    main()
