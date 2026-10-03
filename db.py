"""Tiny Supabase (PostgREST) client: upsert rows and log job runs. Service key only on the server/CI, never in the browser."""
import json, os, urllib.request
from pathlib import Path


def _env():
    f = Path(__file__).with_name(".env")
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_env()
URL, KEY = os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]


def _req(method, path, body=None, prefer=None):
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(f"{URL}/rest/v1/{path}", data, h, method=method), timeout=120) as r:
        txt = r.read()
        return json.loads(txt) if txt else None


def upsert(table, rows, chunk=5000):
    """Insert or update by primary key, in chunks (PostgREST body limit)."""
    for i in range(0, len(rows), chunk):
        _req("POST", table, rows[i:i + chunk], prefer="resolution=merge-duplicates,return=minimal")
    return len(rows)


def select(table, query=""):
    return _req("GET", f"{table}?{query}")


def _req_count(table, filt=""):
    """Exact row count via PostgREST's Content-Range header."""
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Prefer": "count=exact", "Range": "0-0"}
    req = urllib.request.Request(f"{URL}/rest/v1/{table}?select=date{filt}", headers=h, method="GET")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.headers["Content-Range"].split("/")[1]


def log_run(job, status, rows=0, detail=""):
    _req("POST", "job_runs", [{"job": job, "status": status, "rows": rows, "detail": detail[:500]}], prefer="return=minimal")
