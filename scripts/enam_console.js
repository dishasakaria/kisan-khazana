// eNAM trade/price downloader — runs in YOUR browser (eNAM's backend refuses cloud servers).
// 1. Open  https://enam.gov.in/dashboard/live_price   (note: NO "/web/" in the address)
// 2. F12 -> Console. If Chrome blocks pasting, type:  allow pasting   and press Enter.
// 3. Paste this whole file, press Enter. It downloads enam_maharashtra_<from>_<to>.csv at the end.
// It replays the page's own calls: Liveprice_ctrl/trade_data_list (live prices) and, if empty,
// Ajax_ctrl/trade_data_list (trading details). Both found in the page source.
(async () => {
  const FROM = "2026-09-01", TO = "2026-10-02", STATE = "MAHARASHTRA";
  const base = "https://enam.gov.in/";
  const post = async (path, body) => {
    const r = await fetch(base + path, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest" },
      body: new URLSearchParams(body).toString(),
    });
    const t = await r.text();
    try { return JSON.parse(t); } catch { return { status: r.status, raw: t.slice(0, 150) }; }
  };
  const fmts = [d => d, d => d.split("-").reverse().join("-")]; // yyyy-mm-dd, then dd-mm-yyyy
  const calls = [
    ["Liveprice_ctrl/trade_data_list", day => ({ language: "en", stateName: STATE, fromDate: day, toDate: day })],
    ["Ajax_ctrl/trade_data_list", day => ({ language: "en", stateName: STATE, apmcName: "-- All --", commodityName: "-- All --", fromDate: day, toDate: day })],
  ];
  // find which call + date format works, using the first day
  let pick = null;
  for (const [path, mk] of calls) for (const f of fmts) {
    const res = await post(path, mk(f(FROM)));
    const n = res && res.data ? Object.keys(res.data).length : 0;
    console.log("probe", path, f(FROM), "->", res && res.status, n, "rows", res && res.raw ? res.raw : "");
    if (n && !pick) pick = [path, mk, f];
  }
  if (!pick) { console.error("No call returned data. Copy everything above and share it with the team."); return; }
  console.log("Using", pick[0]);
  const rows = [], keys = new Set(["query_date"]);
  for (let d = new Date(FROM); d <= new Date(TO); d.setDate(d.getDate() + 1)) {
    const day = d.toISOString().slice(0, 10);
    const res = await post(pick[0], pick[1](pick[2](day)));
    const data = res && res.data ? Object.values(res.data) : [];
    data.forEach(r => { Object.keys(r).forEach(k => keys.add(k)); rows.push({ query_date: day, ...r }); });
    console.log(day, "->", data.length, "rows");
    await new Promise(ok => setTimeout(ok, 800)); // polite to the server
  }
  const cols = [...keys], esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = [cols.join(","), ...rows.map(r => cols.map(c => esc(r[c])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = `enam_maharashtra_${FROM}_${TO}.csv`;
  a.click();
  console.log("Done:", rows.length, "rows. Columns:", cols.join(", "));
})();
