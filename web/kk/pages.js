// Every page of the dashboard. Each export: render(root, params) -> optional cleanup().
import { getLang, setLang, LANGS } from "./i18n.js";
import * as U from "./ui.js";
const { t, icon, esc, num, rs, qtl, fmtDate, fmtDT, badge, cropName, api, state, table, bindRows, pager, tabs, kv, field, skeleton, empty, errBox,
        toast, confirmDialog, busy, go, poll, lotCode, typeName, channelText, initials, formData, debounce } = U;

const card = (title, body, extra = "") => `<section class="card"><div class="hd"><h2>${esc(title)}</h2>${extra}</div>${body}</section>`;
const hdr = (title, sub = "", right = "") => `<div class="page-hd"><div><h1>${esc(title)}</h1>${sub ? `<p>${esc(sub)}</p>` : ""}</div><div class="actions">${right}</div></div>`;
const cropOptions = (crops, cur) => `<option value="">${t("all_crops")}</option>${crops.map((c) => `<option value="${esc(c)}" ${c === cur ? "selected" : ""}>${esc(cropName(c))}</option>`).join("")}`;
const query = () => Object.fromEntries(new URLSearchParams(location.hash.split("?")[1] || ""));
const setQuery = (q) => { const base = location.hash.split("?")[0]; const s = new URLSearchParams(Object.entries(q).filter(([, v]) => v)).toString(); location.hash = base + (s ? "?" + s : ""); };
const CROPS = ["Onion", "Tomato", "Potato", "Soyabean", "Wheat", "Maize", "Bengal Gram (Gram)(Whole)", "Arhar (Tur/Red Gram)(Whole)", "Pomegranate", "Grapes", "Jowar (Sorghum)", "Bajra (Pearl Millet/Cumbu)", "Cotton"];

/** Shared list page: toolbar (search/crop/tabs) + paged table from a server endpoint. */
function listPage(root, { path, cols, onRow, emptyState, tabList, tabKey = "status", crops = true, params = {}, title, sub, right = "", live = false }) {
  let q = query();
  const draw = async () => {
    root.innerHTML = `${hdr(title, sub, right)}
      ${tabList ? tabs(tabList, q[tabKey] || "") : ""}
      <div class="toolbar"><label class="search">${icon("search", 16)}<span class="sr">${t("search")}</span><input id="q" type="search" placeholder="${t("search")}" value="${esc(q.q || "")}"></label>
        ${crops ? `<select id="crop" aria-label="${t("crop")}">${cropOptions(CROPS, q.crop)}</select>` : ""}</div>
      <div id="list">${skeleton(5)}</div>`;
    root.querySelector("#q").addEventListener("input", debounce((e) => { q = { ...q, q: e.target.value, page: "" }; setQuery(q); }));
    root.querySelector("#crop")?.addEventListener("change", (e) => { q = { ...q, crop: e.target.value, page: "" }; setQuery(q); });
    root.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => { q = { ...q, [tabKey]: b.dataset.tab, page: "" }; setQuery(q); }));
    load();
  };
  const load = async () => {
    const box = root.querySelector("#list");
    try {
      const p = await api(path, { params: { ...params, q: q.q, crop: q.crop, [tabKey]: q[tabKey], page: q.page || 1, limit: 20 } });
      if (!p.total) { box.innerHTML = `<div class="card">${q.q || q.crop || q[tabKey] ? empty("filter", t("empty_filter"), "") : emptyState}</div>`; return; }
      box.innerHTML = `<div class="card">${table(cols, p.items, { onRow })}${pager(p)}</div>`;
      bindRows(box, p.items, onRow);
      box.querySelectorAll("[data-pg]").forEach((b) => b.addEventListener("click", () => { q = { ...q, page: b.dataset.pg }; setQuery(q); }));
    } catch (e) {
      box.innerHTML = errBox(e, "retry");
      box.querySelector("#retry")?.addEventListener("click", load);
    }
  };
  draw();
  const stop = live ? poll(load) : null;
  const onHash = () => { q = query(); draw(); };
  return { stop: () => { stop && stop(); }, onQuery: onHash };
}

// ======================= AUTH =======================
const langRow = () => `<div class="lang-row" role="group" aria-label="${t("language")}">${LANGS.map(([v, l]) => `<button type="button" data-lang="${v}" aria-pressed="${v === getLang()}">${l}</button>`).join("")}</div>`;
const bindLang = (root, rerender) => root.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => { setLang(b.dataset.lang); rerender(); }));
const brand = () => `<div class="brand"><span class="mark">${icon("sprout", 20)}</span><div><b>${t("brand")}</b><span>${t("tag")}</span></div></div>`;
const pwField = (name, label, hint, auto) => field(label, `<span class="pw"><input name="${name}" type="password" required minlength="8" autocomplete="${auto}"><button type="button" class="btn ghost sm icon" data-pw aria-label="${t("password")}">${icon("eye", 16)}</button></span>`, hint);
const bindPw = (root) => root.querySelectorAll("[data-pw]").forEach((b) => b.addEventListener("click", () => { const i = b.previousElementSibling; i.type = i.type === "password" ? "text" : "password"; b.innerHTML = icon(i.type === "password" ? "eye" : "eyeoff", 16); }));

export function login(root) {
  const draw = () => {
    root.innerHTML = `<div class="auth"><form class="card" id="f" novalidate>${brand()}<h1>${t("login")}</h1><p class="sub">${t("login_sub")}</p>${langRow()}
      ${field(t("phone_or_email"), `<input name="login" required autocomplete="username" inputmode="email">`)}
      ${pwField("password", t("password"), "", "current-password")}
      <div id="err"></div><button class="btn primary block" id="go">${t("login")}</button>
      <p class="foot">${t("no_account")} <a href="#/register">${t("register")}</a></p></form></div>`;
    bindLang(root, draw); bindPw(root);
    root.querySelector("#f").addEventListener("submit", (e) => {
      e.preventDefault();
      const f = e.target, b = formData(f);
      if (!f.reportValidity()) return;
      busy(root.querySelector("#go"), async () => {
        try {
          const r = await api("/fpos/login", { method: "POST", body: b });
          U.setToken(r.fpo_token); state.fpo = r.fpo; go("/overview");
        } catch (err) { root.querySelector("#err").innerHTML = errBox(err); }
      });
    });
  };
  draw();
}

export function register(root) {
  const draw = () => {
    root.innerHTML = `<div class="auth"><form class="card" id="f" novalidate>${brand()}<h1>${t("register")}</h1><p class="sub">${t("login_sub")}</p>${langRow()}
      ${field(t("fpo_name"), `<input name="name" required minlength="2" maxlength="120" autocomplete="organization">`)}
      <div class="row2">${field(t("phone"), `<input name="phone" required inputmode="tel" autocomplete="tel" placeholder="98765 43210">`)}${field(t("email"), `<input name="email" type="email" autocomplete="email">`)}</div>
      ${pwField("password", t("password"), t("password_hint"), "new-password")}
      ${field(t("address"), `<input name="address" maxlength="200" autocomplete="street-address">`)}
      <div class="row2">${field(t("lat"), `<input name="lat" required inputmode="decimal" step="any" type="number" min="6" max="37">`)}${field(t("lon"), `<input name="lon" required inputmode="decimal" step="any" type="number" min="68" max="98">`)}</div>
      <div class="field"><button type="button" class="btn sm" id="gps">${icon("locate", 16)} ${t("use_gps")}</button> <span class="hint" id="gpsmsg"></span></div>
      <div id="err"></div><button class="btn primary block" id="go">${t("create_account")}</button>
      <p class="foot">${t("have_account")} <a href="#/login">${t("login")}</a></p></form></div>`;
    bindLang(root, draw); bindPw(root);
    root.querySelector("#gps").addEventListener("click", () => {
      const msg = root.querySelector("#gpsmsg");
      if (!navigator.geolocation) { msg.textContent = t("gps_fail"); return; }
      navigator.geolocation.getCurrentPosition((p) => {
        root.querySelector("[name=lat]").value = p.coords.latitude.toFixed(4); root.querySelector("[name=lon]").value = p.coords.longitude.toFixed(4); msg.textContent = "";
      }, () => { msg.textContent = t("gps_fail"); }, { timeout: 10000 });
    });
    root.querySelector("#f").addEventListener("submit", (e) => {
      e.preventDefault();
      const f = e.target;
      if (!f.reportValidity()) return;
      busy(root.querySelector("#go"), async () => {
        try {
          const r = await api("/fpos", { method: "POST", body: formData(f) });
          U.setToken(r.fpo_token); state.fpo = r.fpo; go("/overview");
        } catch (err) { root.querySelector("#err").innerHTML = errBox(err); }
      });
    });
  };
  draw();
}

// ======================= OVERVIEW =======================
const greet = () => { const h = new Date().getHours(); return t(h < 12 ? "good_morning" : h < 17 ? "good_afternoon" : "good_evening"); };
const metric = (lbl, val, unit, sub, ic) => `<div class="card metric"><div class="lbl">${icon(ic, 15)}${esc(lbl)}</div><div class="val">${val}${unit ? `<small>${esc(unit)}</small>` : ""}</div>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>`;
const offerCols = () => [
  { l: t("buyer"), cls: "pri", f: (o) => `${esc(o.buyer.name || "—")}${o.buyer.company ? `<div class="small muted">${esc(o.buyer.company)}</div>` : ""}` },
  { l: t("lot"), f: (o) => `${esc(o.code || "")} · ${esc(cropName(o.crop))}` },
  { l: t("qty"), cls: "num", f: (o) => qtl(o.qty_qtl) },
  { l: t("price"), cls: "num", f: (o) => rs(o.price_rs_qtl) + t("per_qtl") },
  { l: t("total_value"), cls: "num", f: (o) => rs(o.total_value) },
  { l: t("status"), f: (o) => badge(o.status) },
  { l: t("submitted"), f: (o) => `<span class="small muted">${fmtDT(o.created_at)}</span>` },
];
const lotCols = () => [
  { l: t("lot_id"), cls: "pri", f: (l) => lotCode(l) }, { l: t("crop"), f: (l) => esc(cropName(l.crop)) },
  { l: t("available"), cls: "num", f: (l) => `${num(l.available_qty_qtl)} / ${num(l.total_qty_qtl)} ${t("qtl")}` },
  { l: t("asking_price"), cls: "num", f: (l) => rs(l.asking_price_rs_qtl) + t("per_qtl") },
  { l: t("pending_offers_n"), cls: "num", f: (l) => l.pending_offers ? `<span class="badge warn">${l.pending_offers}</span>` : "0" },
  { l: t("status"), f: (l) => badge(l.status, "lot") }, { l: t("created"), f: (l) => `<span class="small muted">${fmtDate(l.created_at)}</span>` },
];
const cropCols = () => [
  { l: t("crop"), cls: "pri", f: (c) => esc(cropName(c.crop)) }, { l: t("total"), cls: "num", f: (c) => qtl(c.total_qty_qtl) },
  { l: t("available"), cls: "num", f: (c) => qtl(c.available_qty_qtl) }, { l: t("in_lots"), cls: "num", f: (c) => qtl(c.in_lot_qty_qtl) },
  { l: t("farmers_n"), cls: "num", f: (c) => c.farmers_n }, { l: t("status"), f: (c) => badge(c.status) },
  { l: t("updated_at"), f: (c) => `<span class="small muted">${fmtDate(c.updated_at)}</span>` },
];

export function overview(root) {
  const load = async () => {
    try {
      const d = await api("/fpos/dashboard");
      state.fpo = d.fpo; state.pending = d.metrics.pending_offers; document.dispatchEvent(new Event("kk:pending"));
      const m = d.metrics;
      root.innerHTML = `${hdr(`${greet()}, ${d.fpo.name}`, `${d.fpo.district || ""} · ${t("updated")} ${fmtDT(d.generated_at)}`)}
        ${m.pending_offers ? `<div class="strip">${icon("inbox", 20)}<b>${m.pending_offers === 1 ? t("action_required_1") : t("action_required", { n: m.pending_offers })}</b><a class="btn sm primary" href="#/offers?status=pending">${t("review_offers")} ${icon("arrow", 14)}</a></div>` : ""}
        <div class="grid metrics" style="margin-bottom:16px">
          ${metric(t("m_available"), num(m.available_qty_qtl), t("qtl"), `${num(m.in_lot_qty_qtl)} ${t("qtl")} ${t("in_lots")}`, "package")}
          ${metric(t("m_open_lots"), m.open_lots, "", `${m.draft_lots} ${t("drafts")}`, "layers")}
          ${metric(t("m_pending"), m.pending_offers, "", "", "inbox")}
          ${metric(t("m_sold_month"), num(m.sold_qty_month), t("qtl"), rs(m.sold_value_month), "trend")}
        </div>
        <section class="card" style="margin-bottom:16px"><div class="hd"><h2>${t("quick_actions")}</h2></div><div class="bd quick">
          <a href="#/lots/new">${icon("plus", 18)}${t("create_lot")}</a><a href="#/offers">${icon("inbox", 18)}${t("view_offers")}</a>
          <a href="#/inventory">${icon("package", 18)}${t("inventory")}</a><a href="#/farmers">${icon("users", 18)}${t("farmers")}</a></div></section>
        <div class="grid two">
          ${card(t("current_inventory"), d.inventory_by_crop.length ? table(cropCols().filter((c, i) => [0, 1, 2, 5].includes(i)), d.inventory_by_crop) : empty("package", t("empty_inventory"), t("empty_inventory_sub")), `<a class="small" href="#/inventory">${t("view_all")}</a>`)}
          ${card(t("active_lots"), d.active_lots.length ? table(lotCols().filter((c, i) => [0, 1, 2, 4].includes(i)), d.active_lots, { onRow: true }) : empty("layers", t("empty_lots"), t("empty_lots_sub"), `<a class="btn primary sm" href="#/lots/new">${icon("plus", 14)} ${t("create_lot")}</a>`), `<a class="small" href="#/lots">${t("view_all")}</a>`)}
        </div>
        <div style="margin-top:16px" id="recent">${card(t("recent_offers"), d.recent_offers.length ? table(offerCols().filter((c, i) => i !== 6), d.recent_offers, { onRow: true }) : empty("inbox", t("empty_offers"), t("empty_offers_sub")), `<a class="small" href="#/offers">${t("view_all")}</a>`)}</div>`;
      bindRows(root.querySelectorAll(".grid.two > .card")[1], d.active_lots, (l) => go(`/lots/${l.id}`));
      bindRows(root.querySelector("#recent"), d.recent_offers, (o) => go(`/offers/${o.offer_id}`));
    } catch (e) { root.innerHTML = hdr(t("overview")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  root.innerHTML = hdr(t("overview")) + skeleton(6);
  load();
  return poll(load);
}

// ======================= INVENTORY =======================
export function inventory(root) {
  let drawerCrop = null;
  const load = async () => {
    try {
      const rows = await api("/fpos/inventory/by-crop");
      root.innerHTML = `${hdr(t("inventory"), "", `<a class="btn primary" href="#/lots/new">${icon("plus", 16)} ${t("create_lot")}</a>`)}
        <div class="card">${rows.length ? table(cropCols(), rows, { onRow: true }) : empty("package", t("empty_inventory"), t("empty_inventory_sub"))}</div>
        <div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="${t("details")}"></div>`;
      bindRows(root, rows, (r) => openDrawer(r.crop));
      if (drawerCrop) openDrawer(drawerCrop);
    } catch (e) { root.innerHTML = hdr(t("inventory")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  const openDrawer = async (crop) => {
    drawerCrop = crop;
    const d = root.querySelector("#drawer");
    d.classList.add("open");
    d.innerHTML = `<div class="hd"><h2>${esc(cropName(crop))}</h2><button class="btn ghost icon" id="x" aria-label="${t("close")}">${icon("x", 18)}</button></div><div class="bd">${skeleton(4)}</div>`;
    d.querySelector("#x").addEventListener("click", () => { drawerCrop = null; d.classList.remove("open"); });
    try {
      const p = await api("/fpos/inventory/items", { params: { crop, limit: 100 } });
      d.querySelector(".bd").innerHTML = `<p class="muted small" style="margin-bottom:12px">${t("contributors")} · ${t("results", { n: p.total })}</p>
        ${table([{ l: t("farmer"), cls: "pri", f: (i) => `${esc(i.farmer_name || "—")}<div class="small muted">${channelText(i.channel)}</div>` },
                 { l: t("qty"), cls: "num", f: (i) => qtl(i.qty_qtl) }, { l: t("condition"), f: (i) => esc(i.condition || "—") },
                 { l: t("status"), f: (i) => badge(i.status) }, { l: t("ready"), f: (i) => `<span class="small muted">${fmtDate(i.ready_date)}</span>` }], p.items, { onRow: true })}`;
      bindRows(d, p.items, (i) => go(`/farmers/${encodeURIComponent(i.farmer_id)}`));
    } catch (e) { d.querySelector(".bd").innerHTML = errBox(e); }
  };
  root.innerHTML = hdr(t("inventory")) + skeleton(5);
  load();
  return poll(load);
}

// ======================= FARMERS =======================
export function farmers(root) {
  const town = (f) => (f.town && (f.town[getLang()] || f.town.en)) || f.district || "—";
  return listPage(root, {
    path: "/fpos/farmers", title: t("farmers"), live: false,
    emptyState: empty("users", t("empty_farmers"), t("empty_farmers_sub")),
    cols: [{ l: t("name"), cls: "pri", f: (f) => `${esc(f.name || f.farmer_id)}` }, { l: t("village"), f: (f) => esc(town(f)) },
           { l: t("phone"), f: (f) => f.phone ? esc(f.phone) : `<span class="muted">${channelText(f.channel)}</span>` },
           { l: t("primary_crop"), f: (f) => esc(cropName(f.primary_crop)) }, { l: t("available"), cls: "num", f: (f) => qtl(f.available_qty_qtl) },
           { l: t("updated_at"), f: (f) => `<span class="small muted">${fmtDate(f.updated_at)}</span>` }],
    onRow: (f) => go(`/farmers/${encodeURIComponent(f.farmer_id)}`),
  });
}

export function farmer(root, { id }) {
  const fid = decodeURIComponent(id);
  const load = async () => {
    try {
      const f = await api(`/fpos/farmers/${encodeURIComponent(fid)}`);
      const town = (f.town && (f.town[getLang()] || f.town.en)) || "";
      root.innerHTML = `<a class="small" href="#/farmers">${icon("left", 14)} ${t("farmers")}</a>
        <div class="page-hd" style="margin-top:8px"><div style="display:flex;gap:14px;align-items:center"><span class="avatar">${esc(initials(f.name))}</span><div><h1>${esc(f.name || fid)}</h1><p>${esc([town, f.district].filter(Boolean).join(", ") || "—")} · ${channelText(f.channel)}</p></div></div>
          <div class="actions">${f.phone ? `<a class="btn" href="tel:${esc(f.phone)}">${icon("phone", 16)} ${esc(f.phone)}</a>` : ""}</div></div>
        <div class="grid metrics" style="margin-bottom:16px">${metric(t("available"), num(f.available_qty_qtl), t("qtl"), "", "package")}${metric(t("in_lots"), num(f.in_lot_qty_qtl), t("qtl"), "", "layers")}${metric(t("sold"), num(f.sold_qty_qtl), t("qtl"), "", "tag")}${metric(t("primary_crop"), esc(cropName(f.primary_crop)), "", "", "sprout")}</div>
        <div class="grid two">
          ${card(t("items"), f.items.length ? table([{ l: t("crop"), cls: "pri", f: (i) => esc(cropName(i.crop)) }, { l: t("qty"), cls: "num", f: (i) => qtl(i.qty_qtl) }, { l: t("condition"), f: (i) => esc(i.condition || "—") }, { l: t("status"), f: (i) => badge(i.status) }, { l: t("date"), f: (i) => `<span class="small muted">${fmtDate(i.created_at)}</span>` }], f.items) : empty("package", t("empty_inventory"), ""))}
          ${card(t("lots"), f.lots.length ? table([{ l: t("lot_id"), cls: "pri", f: (l) => lotCode(l) }, { l: t("crop"), f: (l) => esc(cropName(l.crop)) }, { l: t("qty"), cls: "num", f: (l) => qtl(l.farmer_qty_qtl) }, { l: t("status"), f: (l) => badge(l.status, "lot") }], f.lots, { onRow: true }) : empty("layers", t("empty_lots"), ""))}
        </div>`;
      bindRows(root.querySelectorAll(".grid.two > .card")[1], f.lots, (l) => go(`/lots/${l.id}`));
    } catch (e) { root.innerHTML = hdr(t("farmer")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  root.innerHTML = hdr(t("farmer")) + skeleton(5);
  load();
}

// ======================= LOTS =======================
export function lots(root) {
  return listPage(root, {
    path: "/fpos/lots/search", title: t("lots"), right: `<a class="btn primary" href="#/lots/new">${icon("plus", 16)} ${t("create_lot")}</a>`,
    tabList: [["", t("all")], ["open", t("open")], ["draft", t("draft")], ["sold", t("sold")], ["closed", t("closed")]],
    emptyState: empty("layers", t("empty_lots"), t("empty_lots_sub"), `<a class="btn primary sm" href="#/lots/new">${icon("plus", 14)} ${t("create_lot")}</a>`),
    cols: lotCols(), onRow: (l) => go(`/lots/${l.id}`), live: true,
  });
}

export function lot(root, { id }) {
  let editing = false;
  const act = async (btn, path, confirmKey, doneKey) => {
    const l = root._lot;
    if (!(await confirmDialog({ title: t("confirm_" + confirmKey), body: t("confirm_" + confirmKey + "_body"), ok: t(confirmKey === "close" ? "close_lot" : confirmKey), danger: confirmKey === "close" }))) return;
    await busy(btn, async () => { await api(`/fpos/lots/${l.id}/${path}`, { method: "POST" }); toast(t(doneKey)); load(); });
  };
  const load = async () => {
    try {
      const l = await api(`/fpos/lots/${id}`);
      root._lot = l;
      const pct = l.total_qty_qtl ? Math.round(100 * l.sold_qty_qtl / l.total_qty_qtl) : 0;
      const canEdit = l.status === "draft" || l.status === "open";
      root.innerHTML = `<a class="small" href="#/lots">${icon("left", 14)} ${t("lots")}</a>
        <div class="page-hd" style="margin-top:8px"><div><h1>${lotCode(l)} · ${esc(cropName(l.crop))} ${badge(l.status, "lot")}</h1><p>${t("created")} ${fmtDate(l.created_at)} · ${l.pending_offers} ${t("pending_offers_n").toLowerCase()}</p></div>
          <div class="actions">
            ${l.status === "draft" ? `<button class="btn primary" id="publish">${icon("eye", 16)} ${t("publish")}</button>` : ""}
            ${l.status === "open" ? `<button class="btn" id="unpublish">${icon("pause", 16)} ${t("unpublish")}</button>` : ""}
            ${canEdit ? `<button class="btn" id="edit">${icon("pencil", 16)} ${t("edit")}</button><button class="btn danger" id="close">${icon("xcircle", 16)} ${t("close_lot")}</button>` : ""}
          </div></div>
        <div class="grid two" style="margin-bottom:16px">
          <section class="card"><div class="hd"><h2>${t("details")}</h2></div><div class="bd" id="det">${editing ? editForm(l) : kv([
            [t("total"), qtl(l.total_qty_qtl)], [t("available"), `${qtl(l.available_qty_qtl)} <span class="muted small">(${t("sold")} ${num(l.sold_qty_qtl)})</span><div class="bar" style="margin-top:6px;max-width:220px"><i style="width:${pct}%"></i></div>`],
            [t("asking_price"), rs(l.asking_price_rs_qtl) + t("per_qtl")], [t("market_ref"), l.market_reference_price ? rs(l.market_reference_price) + t("per_qtl") : "—"],
            [t("lot_value"), rs(l.available_qty_qtl * l.asking_price_rs_qtl)], [t("quality"), esc(l.quality || "—")], [t("pickup"), esc(l.location || "—")], [t("notes"), esc(l.notes || "—")]])}</div></section>
          ${card(t("contributors"), l.contributors.length ? `<ul class="list">${l.contributors.map((c) => `<li><span class="avatar">${esc(initials(c.farmer_name))}</span><div class="t"><b>${esc(c.farmer_name || c.farmer_id)}</b><span>${c.items} ${t("items").toLowerCase()}</span></div><b class="mono">${qtl(c.qty_qtl)}</b></li>`).join("")}</ul>` : empty("users", t("empty_farmers"), ""))}
        </div>
        <div id="loffers">${card(t("offers"), l.offers.length ? table(offerCols(), l.offers, { onRow: true }) : empty("inbox", t("empty_offers"), t("empty_offers_sub")))}</div>`;
      bindRows(root.querySelector("#loffers"), l.offers, (o) => go(`/offers/${o.offer_id}`));
      root.querySelector("#publish")?.addEventListener("click", (e) => act(e.currentTarget, "publish", "publish", "done_publish"));
      root.querySelector("#unpublish")?.addEventListener("click", (e) => act(e.currentTarget, "unpublish", "unpublish", "done_unpublish"));
      root.querySelector("#close")?.addEventListener("click", (e) => act(e.currentTarget, "close", "close", "done_close"));
      root.querySelector("#edit")?.addEventListener("click", () => { editing = true; load(); });
      root.querySelector("#ef")?.addEventListener("submit", (e) => {
        e.preventDefault();
        const f = e.target;
        if (!f.reportValidity()) return;
        busy(f.querySelector("#save"), async () => { await api(`/fpos/lots/${l.id}`, { method: "PATCH", body: formData(f) }); editing = false; toast(t("done_saved")); load(); });
      });
      root.querySelector("#cancel")?.addEventListener("click", () => { editing = false; load(); });
    } catch (e) { root.innerHTML = hdr(t("lot")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  const editForm = (l) => `<form id="ef" novalidate>${field(t("asking_price") + " (₹/" + t("quintal") + ")", `<input name="asking_price_rs_qtl" type="number" min="1" max="100000" step="1" required value="${esc(l.asking_price_rs_qtl)}">`)}
    ${field(t("quality"), `<input name="quality" maxlength="40" value="${esc(l.quality || "")}" placeholder="${t("quality_ph")}">`)}
    ${field(t("pickup"), `<input name="location" maxlength="200" value="${esc(l.location || "")}">`)}
    ${field(t("notes"), `<textarea name="notes" maxlength="500">${esc(l.notes || "")}</textarea>`)}
    <div class="actions"><button class="btn primary" id="save">${t("save")}</button><button type="button" class="btn" id="cancel">${t("cancel")}</button></div></form>`;
  root.innerHTML = hdr(t("lot")) + skeleton(6);
  load();
  return poll(() => { if (!editing) load(); });
}

export function lotNew(root) {
  const w = { step: 0, crop: query().crop || "", items: [], picked: new Set(), price: "", ref: null, quality: "", location: "", notes: "" };
  const steps = ["step_crop", "step_items", "step_price", "step_details"];
  const selQty = () => w.items.filter((i) => w.picked.has(i.id)).reduce((s, i) => s + +i.qty_qtl, 0);
  const draw = async () => {
    root.innerHTML = `<a class="small" href="#/lots">${icon("left", 14)} ${t("lots")}</a>${hdr(t("new_lot"))}
      <div class="steps">${steps.map((s, i) => `<span class="${i === w.step ? "on" : i < w.step ? "done" : ""}">${i + 1}. ${t(s)}</span>`).join("")}</div>
      <div class="card"><div class="bd" id="body">${skeleton(4)}</div></div>`;
    const body = root.querySelector("#body");
    try {
      if (w.step === 0) {
        const rows = await api("/fpos/inventory/by-crop");
        const avail = rows.filter((r) => r.available_qty_qtl > 0);
        if (!avail.length) { body.innerHTML = empty("package", t("empty_inventory"), t("no_stock_for_lot"), `<a class="btn" href="#/inventory">${t("inventory")}</a>`); return; }
        body.innerHTML = `<h2 style="margin-bottom:12px">${t("choose_crop")}</h2><div class="chips">${avail.map((r) => `<button class="chip" data-crop="${esc(r.crop)}" aria-pressed="${r.crop === w.crop}">${esc(cropName(r.crop))} · ${qtl(r.available_qty_qtl)} · ${r.farmers_n} ${t("farmers_n").toLowerCase()}</button>`).join("")}</div>
          <div class="actions" style="margin-top:18px"><button class="btn primary" id="next" ${w.crop ? "" : "disabled"}>${t("next")} ${icon("arrow", 16)}</button></div>`;
        body.querySelectorAll("[data-crop]").forEach((b) => b.addEventListener("click", () => { w.crop = b.dataset.crop; w.picked.clear(); draw(); }));
        body.querySelector("#next").addEventListener("click", () => { w.step = 1; draw(); });
      } else if (w.step === 1) {
        const p = await api("/fpos/inventory/items", { params: { crop: w.crop, status: "open", limit: 100 } });
        w.items = p.items;
        if (!w.picked.size) w.items.forEach((i) => w.picked.add(i.id));
        const list = () => `<div class="grid" style="gap:8px">${w.items.map((i) => `<label class="chk ${w.picked.has(i.id) ? "on" : ""}"><input type="checkbox" data-id="${i.id}" ${w.picked.has(i.id) ? "checked" : ""}><span class="t"><b>${esc(i.farmer_name || i.farmer_id)}</b><span>${esc(i.condition || "")} · ${fmtDate(i.ready_date)} · ${channelText(i.channel)}</span></span><b class="mono">${qtl(i.qty_qtl)}</b></label>`).join("")}</div>`;
        body.innerHTML = `<h2>${t("pick_items")} — ${esc(cropName(w.crop))}</h2><p class="muted small" style="margin:4px 0 14px">${t("pick_items_hint")}</p>${list()}
          <p id="sum" style="margin-top:14px;font-weight:600"></p>
          <div class="actions" style="margin-top:12px"><button class="btn" id="back">${icon("left", 16)} ${t("back")}</button><button class="btn primary" id="next">${t("next")} ${icon("arrow", 16)}</button></div>`;
        const sum = () => { body.querySelector("#sum").textContent = t("selected_total", { n: w.picked.size, q: num(selQty()) }); body.querySelector("#next").disabled = !w.picked.size; };
        body.querySelectorAll("input[type=checkbox]").forEach((c) => c.addEventListener("change", () => { c.checked ? w.picked.add(+c.dataset.id) : w.picked.delete(+c.dataset.id); c.closest(".chk").classList.toggle("on", c.checked); sum(); }));
        sum();
        body.querySelector("#back").addEventListener("click", () => { w.step = 0; draw(); });
        body.querySelector("#next").addEventListener("click", () => { w.step = 2; draw(); });
      } else if (w.step === 2) {
        if (w.ref === null) { try { w.ref = (await api("/fpos/reference-price", { params: { crop: w.crop } })) || {}; } catch (e) { w.ref = {}; } }
        if (!w.price && w.ref.price) w.price = w.ref.price;
        body.innerHTML = `<h2 style="margin-bottom:12px">${t("set_price")}</h2>
          <div class="alert info" style="margin-bottom:14px">${icon("trend", 18)}<div>${w.ref.price ? esc(t("ref_from", { m: w.ref.market, d: fmtDate(w.ref.date), p: num(w.ref.price, 0) })) : t("ref_none")}
            ${w.ref.price ? ` <button type="button" class="btn sm" id="useref">${t("use_ref")}</button>` : ""}</div></div>
          ${field(t("asking_price") + " (₹/" + t("quintal") + ")", `<input id="price" type="number" min="1" max="100000" step="1" required value="${esc(w.price)}" inputmode="numeric">`)}
          <p class="muted">${t("lot_value")}: <b id="val"></b> <span class="small">(${num(selQty())} ${t("qtl")})</span></p>
          <div class="actions" style="margin-top:16px"><button class="btn" id="back">${icon("left", 16)} ${t("back")}</button><button class="btn primary" id="next">${t("next")} ${icon("arrow", 16)}</button></div>`;
        const inp = body.querySelector("#price"), val = () => { w.price = inp.value; body.querySelector("#val").textContent = rs(selQty() * +inp.value); body.querySelector("#next").disabled = !(+inp.value > 0); };
        inp.addEventListener("input", val); val();
        body.querySelector("#useref")?.addEventListener("click", () => { inp.value = w.ref.price; val(); });
        body.querySelector("#back").addEventListener("click", () => { w.step = 1; draw(); });
        body.querySelector("#next").addEventListener("click", () => { if (+inp.value > 0) { w.step = 3; draw(); } });
      } else {
        body.innerHTML = `<h2 style="margin-bottom:12px">${t("step_details")}</h2><form id="f" novalidate>
          ${field(t("quality"), `<input name="quality" maxlength="40" value="${esc(w.quality)}" placeholder="${t("quality_ph")}">`)}
          ${field(t("pickup"), `<input name="location" maxlength="200" value="${esc(w.location)}" placeholder="${t("pickup_ph")}">`)}
          ${field(t("notes"), `<textarea name="notes" maxlength="500" placeholder="${t("notes_ph")}">${esc(w.notes)}</textarea>`)}
          ${kv([[t("crop"), esc(cropName(w.crop))], [t("qty"), `${qtl(selQty())} · ${w.picked.size} ${t("items").toLowerCase()}`], [t("asking_price"), rs(w.price) + t("per_qtl")], [t("lot_value"), rs(selQty() * +w.price)]])}
          <div class="actions" style="margin-top:18px"><button type="button" class="btn" id="back">${icon("left", 16)} ${t("back")}</button><button type="button" class="btn" id="draft">${t("save_draft")}</button><button type="button" class="btn primary" id="pub">${icon("eye", 16)} ${t("create_publish")}</button></div></form>`;
        const create = (btn, publish) => busy(btn, async () => {
          const f = formData(body.querySelector("#f"));
          const lot = await api("/fpos/lots", { method: "POST", body: { inventory_ids: [...w.picked], asking_price_rs_qtl: +w.price, market_reference_price: w.ref.price || null, ...f, publish } });
          toast(t("lot_created", { c: lotCode(lot) })); go(`/lots/${lot.id}`);
        });
        body.querySelector("#back").addEventListener("click", () => { Object.assign(w, formData(body.querySelector("#f"))); w.step = 2; draw(); });
        body.querySelector("#draft").addEventListener("click", (e) => create(e.currentTarget, false));
        body.querySelector("#pub").addEventListener("click", (e) => create(e.currentTarget, true));
      }
    } catch (e) { body.innerHTML = errBox(e, "retry"); body.querySelector("#retry")?.addEventListener("click", draw); }
  };
  draw();
}

// ======================= OFFERS =======================
export function offers(root) {
  return listPage(root, {
    path: "/fpos/offers/search", title: t("offers"), live: true,
    tabList: [["new", t("new")], ["pending", t("pending")], ["accepted", t("accepted")], ["rejected", t("rejected")], ["", t("all")]],
    emptyState: empty("inbox", t("empty_offers"), t("empty_offers_sub")), cols: offerCols(), onRow: (o) => go(`/offers/${o.offer_id}`),
  });
}

const buyerCard = (b, showPhone) => card(t("buyer"), `<div class="bd">${kv([[t("name"), esc(b.name || "—")], [t("company"), esc(b.company || "—")], [t("type"), esc(typeName(b.type))], [t("location"), esc(b.location || "—")],
  showPhone && b.phone ? [t("phone"), `<a href="tel:${esc(b.phone)}">${esc(b.phone)}</a>`] : null])}
  ${showPhone && b.phone ? `<div class="actions" style="margin-top:14px"><a class="btn" href="tel:${esc(b.phone)}">${icon("phone", 16)} ${t("call")}</a><a class="btn" target="_blank" rel="noopener" href="https://wa.me/${esc(b.phone.replace(/\D/g, ""))}">${icon("message", 16)} ${t("whatsapp")}</a></div>` : ""}</div>`);
const offerKv = (o) => kv([[t("lot"), `<a href="#/lots/${o.lot_id}">${esc(o.code)}</a> · ${esc(cropName(o.crop))} ${badge(o.lot_status, "lot")}`], [t("qty"), qtl(o.qty_qtl)], [t("price"), rs(o.price_rs_qtl) + t("per_qtl")],
  [t("total_value"), `<b>${rs(o.total_value)}</b>`], [t("buyer_fee"), rs(o.buyer_fee)], [t("submitted"), fmtDT(o.created_at)], o.decided_at ? [t("decided"), fmtDT(o.decided_at)] : null]);

export function offer(root, { id }) {
  const decide = async (btn, accept) => {
    const o = root._o, b = o.buyer.company || o.buyer.name || "—";
    const ok = await confirmDialog({ title: t(accept ? "confirm_accept" : "confirm_reject"), ok: t(accept ? "accept" : "reject"), danger: !accept,
      body: accept ? t("confirm_accept_body", { q: num(o.qty_qtl), c: cropName(o.crop), p: num(o.price_rs_qtl, 0), b, t: rs(o.total_value) }) : t("confirm_reject_body", { b, q: num(o.qty_qtl) }) });
    if (!ok) return;
    await busy(btn, async () => {
      const r = await api(`/fpos/offers/${o.offer_id}/${accept ? "accept" : "reject"}`, { method: "POST" });
      toast(accept ? t("done_accept", { a: num(r.available) }) : t("done_reject")); load();
    });
  };
  const load = async () => {
    try {
      const o = await api(`/fpos/offers/${id}`);
      root._o = o;
      const pending = o.status === "sent";
      root.innerHTML = `<a class="small" href="#/offers">${icon("left", 14)} ${t("offers")}</a>
        <div class="page-hd" style="margin-top:8px"><div><h1>${esc(o.buyer.company || o.buyer.name || "—")} · ${qtl(o.qty_qtl)} ${esc(cropName(o.crop))} ${badge(o.status)}</h1><p>${rs(o.price_rs_qtl)}${t("per_qtl")} · ${t("total_value")} ${rs(o.total_value)}</p></div>
          ${pending ? `<div class="actions"><button class="btn danger" id="rej">${icon("xcircle", 16)} ${t("reject")}</button><button class="btn primary" id="acc">${icon("check", 16)} ${t("accept")}</button></div>` : ""}</div>
        ${pending && +o.qty_qtl > +o.lot.available_qty_qtl ? `<div class="alert err" style="margin-bottom:16px">${icon("alert", 18)}<div>${t("e_insufficient_qty")} (${t("available")}: ${qtl(o.lot.available_qty_qtl)})</div></div>` : ""}
        <div class="grid two">${card(t("details"), `<div class="bd">${offerKv(o)}</div>`)}${buyerCard(o.buyer, o.status === "accepted")}</div>`;
      root.querySelector("#acc")?.addEventListener("click", (e) => decide(e.currentTarget, true));
      root.querySelector("#rej")?.addEventListener("click", (e) => decide(e.currentTarget, false));
    } catch (e) { root.innerHTML = hdr(t("offers")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  root.innerHTML = hdr(t("offers")) + skeleton(5);
  load();
  return poll(load);
}

// ======================= TRANSACTIONS =======================
const txCols = () => [
  { l: t("date"), f: (x) => fmtDate(x.date) },
  { l: t("buyer"), cls: "pri", f: (x) => `${esc(x.buyer.company || x.buyer.name || "—")}${x.buyer.company ? `<div class="small muted">${esc(x.buyer.name)}</div>` : ""}` },
  { l: t("lot"), f: (x) => esc(x.code) }, { l: t("crop"), f: (x) => esc(cropName(x.crop)) }, { l: t("qty"), cls: "num", f: (x) => qtl(x.qty_qtl) },
  { l: t("price"), cls: "num", f: (x) => rs(x.price_rs_qtl) + t("per_qtl") }, { l: t("total_value"), cls: "num pri", f: (x) => rs(x.total_value) },
];
export function transactions(root) {
  return listPage(root, { path: "/fpos/transactions", title: t("transactions"), emptyState: empty("receipt", t("empty_tx"), t("empty_tx_sub")), cols: txCols(), onRow: (x) => go(`/transactions/${x.transaction_id}`) });
}
export function transaction(root, { id }) {
  const load = async () => {
    try {
      const x = await api(`/fpos/transactions/${id}`);
      root.innerHTML = `<a class="small" href="#/transactions">${icon("left", 14)} ${t("transactions")}</a>
        <div class="page-hd" style="margin-top:8px"><div><h1>${rs(x.total_value)} · ${qtl(x.qty_qtl)} ${esc(cropName(x.crop))}</h1><p>${fmtDT(x.date)} · ${esc(x.code)}</p></div></div>
        <div class="grid two">${card(t("details"), `<div class="bd">${offerKv(x)}</div>`)}${buyerCard(x.buyer, true)}</div>
        <div style="margin-top:16px">${card(t("contributors"), `<ul class="list">${x.contributors.map((c) => `<li><span class="avatar">${esc(initials(c.farmer_name))}</span><div class="t"><b>${esc(c.farmer_name || c.farmer_id)}</b></div><b class="mono">${qtl(c.qty_qtl)}</b></li>`).join("")}</ul>`)}</div>`;
    } catch (e) { root.innerHTML = hdr(t("transactions")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  root.innerHTML = hdr(t("transactions")) + skeleton(5);
  load();
}

// ======================= REPORTS =======================
export function reports(root) {
  const charts = [];
  const load = async () => {
    try {
      const r = await api("/fpos/reports");
      if (!r.enough) { root.innerHTML = hdr(t("reports")) + `<div class="card">${empty("chart", t("empty_reports"), t("empty_reports_sub"), `<a class="btn sm" href="#/lots">${t("lots")}</a>`)}</div>`; return; }
      const T = r.totals;
      root.innerHTML = `${hdr(t("reports"))}
        <div class="grid metrics" style="margin-bottom:16px">${metric(t("r_qty"), num(T.qty_qtl), t("qtl"), `${T.deals} ${t("r_deals").toLowerCase()}`, "scale")}${metric(t("r_value"), rs(T.value), "", "", "receipt")}${metric(t("r_avg"), rs(T.avg_price_rs_qtl), t("per_qtl"), "", "trend")}${metric(t("farmers_n"), T.farmers, "", `${T.lots_sold}/${T.lots} ${t("lots_sold")}`, "users")}</div>
        <div class="grid two" style="margin-bottom:16px">
          ${card(t("r_by_crop"), `<div class="bd"><div class="chart-box"><canvas id="c1" role="img" aria-label="${t("r_by_crop")}"></canvas></div>${table([{ l: t("crop"), cls: "pri", f: (x) => esc(cropName(x.crop)) }, { l: t("qty"), cls: "num", f: (x) => qtl(x.qty_qtl) }, { l: t("r_value"), cls: "num", f: (x) => rs(x.value) }, { l: t("r_avg"), cls: "num", f: (x) => rs(x.avg_price_rs_qtl) }], r.by_crop)}</div>`)}
          ${card(t("r_by_month"), `<div class="bd"><div class="chart-box"><canvas id="c2" role="img" aria-label="${t("r_by_month")}"></canvas></div>${table([{ l: t("r_by_month"), cls: "pri", f: (x) => esc(x.month) }, { l: t("r_deals"), cls: "num", f: (x) => x.deals }, { l: t("qty"), cls: "num", f: (x) => qtl(x.qty_qtl) }, { l: t("r_value"), cls: "num", f: (x) => rs(x.value) }], r.by_month)}</div>`)}
        </div>
        <div class="grid two">
          ${card(t("r_farmers"), table([{ l: t("farmer"), cls: "pri", f: (x) => esc(x.farmer_name || x.farmer_id) }, { l: t("given"), cls: "num", f: (x) => qtl(x.given_qty_qtl) }, { l: t("in_sold"), cls: "num", f: (x) => qtl(x.in_sold_lots_qty_qtl) }], r.farmers))}
          ${card(t("r_buyers"), table([{ l: t("buyer"), cls: "pri", f: (x) => `${esc(x.company || x.name || "—")}${x.company ? `<div class="small muted">${esc(x.name)}</div>` : ""}` }, { l: t("r_deals"), cls: "num", f: (x) => x.deals }, { l: t("r_value"), cls: "num", f: (x) => rs(x.value) }], r.by_buyer))}
        </div>`;
      if (window.Chart) {
        const base = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${rs(c.parsed.y)}` } } },
                       scales: { x: { grid: { display: false }, ticks: { color: "#6b665c" } }, y: { grid: { color: "#eee9de" }, ticks: { color: "#6b665c", callback: (v) => "₹" + (v >= 100000 ? (v / 100000).toFixed(1) + "L" : v >= 1000 ? (v / 1000).toFixed(0) + "k" : v) } } } };
        Chart.defaults.font.family = "Inter, Mukta, system-ui, sans-serif";
        charts.push(new Chart(root.querySelector("#c1"), { type: "bar", data: { labels: r.by_crop.map((x) => cropName(x.crop)), datasets: [{ data: r.by_crop.map((x) => x.value), backgroundColor: "#1f6f3f", borderRadius: 4, maxBarThickness: 36 }] }, options: base }));
        charts.push(new Chart(root.querySelector("#c2"), { type: "bar", data: { labels: r.by_month.map((x) => x.month), datasets: [{ data: r.by_month.map((x) => x.value), backgroundColor: "#1f6f3f", borderRadius: 4, maxBarThickness: 36 }] }, options: base }));
      }
    } catch (e) { root.innerHTML = hdr(t("reports")) + errBox(e, "retry"); root.querySelector("#retry")?.addEventListener("click", load); }
  };
  root.innerHTML = hdr(t("reports")) + skeleton(6);
  load();
  return () => charts.forEach((c) => c.destroy());
}

// ======================= SETTINGS =======================
export function settings(root) {
  const draw = async () => {
    const f = state.fpo || await api("/fpos/me");
    state.fpo = f;
    root.innerHTML = `${hdr(t("settings"))}<div class="grid two">
      <section class="card"><div class="hd"><h2>${t("profile")}</h2></div><div class="bd"><form id="pf" novalidate>
        ${field(t("fpo_name"), `<input name="name" required minlength="2" maxlength="120" value="${esc(f.name)}">`)}
        <div class="row2">${field(t("phone"), `<input name="phone" required inputmode="tel" value="${esc(f.phone || "")}">`)}${field(t("email"), `<input name="email" type="email" value="${esc(f.email || "")}">`)}</div>
        ${field(t("address"), `<input name="address" maxlength="200" value="${esc(f.address || "")}">`)}
        <div class="row2">${field(t("district"), `<input name="district" maxlength="60" value="${esc(f.district || "")}">`)}<div class="row2">${field(t("lat"), `<input name="lat" type="number" step="any" min="6" max="37" value="${esc(f.lat ?? "")}">`)}${field(t("lon"), `<input name="lon" type="number" step="any" min="68" max="98" value="${esc(f.lon ?? "")}">`)}</div></div>
        ${field(t("new_password"), `<input name="password" type="password" minlength="8" autocomplete="new-password">`, t("password_hint"))}
        <div id="err"></div><div class="actions"><button class="btn primary" id="save">${t("save")}</button></div></form></div></section>
      <div class="grid" style="align-content:start">
        <section class="card"><div class="hd"><h2>${t("language")}</h2></div><div class="bd"><div class="chips">${LANGS.map(([v, l]) => `<button class="chip" data-lang="${v}" aria-pressed="${v === getLang()}">${l}</button>`).join("")}</div></div></section>
        <section class="card"><div class="hd"><h2>${t("account")}</h2></div><div class="bd">${kv([[t("member_since"), fmtDate(f.created_at)], [t("status"), esc(f.status)], [t("district"), esc(f.district || "—")]])}<p class="muted small" style="margin:14px 0">${t("about")}</p>
          <button class="btn danger" id="logout">${icon("logout", 16)} ${t("logout")}</button></div></section>
      </div></div>`;
    root.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => { setLang(b.dataset.lang); document.dispatchEvent(new Event("kk:lang")); }));
    root.querySelector("#logout").addEventListener("click", U.logout);
    root.querySelector("#pf").addEventListener("submit", (e) => {
      e.preventDefault();
      const form = e.target;
      if (!form.reportValidity()) return;
      const b = formData(form);
      if (!b.password) delete b.password;
      if (!b.email) b.email = null;
      busy(root.querySelector("#save"), async () => {
        try { state.fpo = await api("/fpos/me", { method: "PATCH", body: b }); toast(t("done_saved")); document.dispatchEvent(new Event("kk:fpo")); draw(); }
        catch (err) { root.querySelector("#err").innerHTML = errBox(err); }
      });
    });
  };
  root.innerHTML = hdr(t("settings")) + skeleton(6);
  draw().catch((e) => { root.innerHTML = hdr(t("settings")) + errBox(e); });
}
