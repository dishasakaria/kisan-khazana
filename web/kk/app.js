// Kisaan Khazana FPO dashboard — hash router + shell. Served as static files at /app/kk/ by the FastAPI app.
import { t, getLang, setLang, LANGS, cropName } from "./i18n.js";
import { icon } from "./icons.js";
import { state, api, go, logout, esc, fmtDT, rs, qtl, errText, poll } from "./ui.js";
import * as P from "./pages.js";

const ROUTES = [
  [/^\/login$/, P.login, "login", false], [/^\/register$/, P.register, "register", false],
  [/^\/overview$/, P.overview, "overview"], [/^\/inventory$/, P.inventory, "inventory"],
  [/^\/farmers$/, P.farmers, "farmers"], [/^\/farmers\/([^/]+)$/, P.farmer, "farmers"],
  [/^\/lots$/, P.lots, "lots"], [/^\/lots\/new$/, P.lotNew, "lots"], [/^\/lots\/(\d+)$/, P.lot, "lots"],
  [/^\/offers$/, P.offers, "offers"], [/^\/offers\/(\d+)$/, P.offer, "offers"],
  [/^\/transactions$/, P.transactions, "transactions"], [/^\/transactions\/(\d+)$/, P.transaction, "transactions"],
  [/^\/reports$/, P.reports, "reports"], [/^\/settings$/, P.settings, "settings"],
];
const NAV = [["overview", "dashboard"], ["inventory", "package"], ["farmers", "users"], ["lots", "layers"], ["offers", "inbox"], ["transactions", "receipt"], ["reports", "chart"], ["settings", "settings"]];
const app = document.getElementById("app");
let cur = { path: null, section: null, result: null, shell: false };
document.documentElement.lang = getLang();

function cleanup() {
  const r = cur.result;
  if (typeof r === "function") r(); else if (r && r.stop) r.stop();
  cur.result = null;
}

function shell(section) {
  app.innerHTML = `<div class="shell"><div class="overlay" id="ov"></div>
    <aside class="side" id="side" aria-label="${t("menu")}">
      <div class="brand"><span class="mark">${icon("sprout", 20)}</span><div><b>${t("brand")}</b><span>${t("tag")}</span></div></div>
      <nav class="nav" id="nav">${NAV.map(([k, ic]) => `<a href="#/${k}" data-nav="${k}" ${k === section ? 'aria-current="page"' : ""}>${icon(ic, 18)}${t(k)}${k === "offers" ? `<span class="cnt" id="pend" ${state.pending ? "" : "hidden"}>${state.pending}</span>` : ""}</a>`).join("")}</nav>
      <div class="spacer"></div>
      <div class="fpo"><b id="fponame">${esc(state.fpo?.name || "")}</b><span class="muted">${esc(state.fpo?.district || "")}</span>
        <div class="actions" style="margin-top:8px"><select id="lang" aria-label="${t("language")}" style="min-height:32px;padding:4px 8px;font-size:.8125rem">${LANGS.map(([v, l]) => `<option value="${v}" ${v === getLang() ? "selected" : ""}>${l}</option>`).join("")}</select>
        <button class="btn ghost sm" id="logout">${icon("logout", 15)} ${t("logout")}</button></div></div>
    </aside>
    <div><header class="top"><button class="btn ghost icon burger" id="burger" aria-label="${t("menu")}" aria-controls="side" aria-expanded="false">${icon("menu", 20)}</button>
      <h1 id="ptitle">${t(section)}</h1>
      <button class="btn ghost icon" id="refresh" aria-label="${t("refresh")}">${icon("refresh", 18)}</button>
      <button class="btn ghost icon" id="bell" aria-label="${t("notifications")}" aria-expanded="false">${icon("bell", 18)}</button></header>
      <div id="pop" class="card pop" hidden></div><main id="main"></main></div></div>`;
  const side = app.querySelector("#side"), ov = app.querySelector("#ov"), burger = app.querySelector("#burger");
  const toggle = (open) => { side.classList.toggle("open", open); ov.classList.toggle("open", open); burger.setAttribute("aria-expanded", String(open)); };
  burger.addEventListener("click", () => toggle(!side.classList.contains("open")));
  ov.addEventListener("click", () => toggle(false));
  app.querySelector("#nav").addEventListener("click", () => toggle(false));
  app.querySelector("#logout").addEventListener("click", logout);
  app.querySelector("#lang").addEventListener("change", (e) => { setLang(e.target.value); document.dispatchEvent(new Event("kk:lang")); });
  app.querySelector("#refresh").addEventListener("click", () => { cur.path = null; route(); });
  app.querySelector("#bell").addEventListener("click", bell);
  cur.shell = true;
}

async function bell(e) {
  const pop = app.querySelector("#pop"), btn = e.currentTarget;
  if (!pop.hidden) { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); return; }
  pop.hidden = false; btn.setAttribute("aria-expanded", "true");
  pop.innerHTML = `<div class="hd"><h2>${t("notifications")}</h2></div><div class="bd muted">${t("loading")}</div>`;
  try {
    const n = await api("/fpos/notifications");
    setPending(n.pending_offers);
    const line = (x) => x.type === "offer" ? [`#/offers/${x.offer_id}`, "inbox", `${t("new")} ${t("offers").toLowerCase()} · ${esc(x.code)} ${esc(cropName(x.crop))}`, `${qtl(x.qty_qtl)} @ ${rs(x.price_rs_qtl)}`]
      : x.type === "inventory" ? [`#/inventory`, "package", `${esc(x.farmer_name || t("farmer"))} · ${esc(cropName(x.crop))}`, qtl(x.qty_qtl)]
      : [`#/lots/${x.lot_id}`, "tag", `${esc(x.code)} ${esc(cropName(x.crop))} · ${t("st_sold")}`, qtl(x.qty_qtl)];
    pop.innerHTML = `<div class="hd"><h2>${t("notifications")}</h2><button class="btn ghost icon sm" id="popx" aria-label="${t("close")}">${icon("x", 16)}</button></div>` +
      (n.items.length ? `<ul class="list">${n.items.map((x) => { const [href, ic, a, b] = line(x); return `<li><a href="${href}" style="display:flex;gap:12px;flex:1;color:inherit">${icon(ic, 18)}<span class="t"><b>${a}</b><span>${b} · ${fmtDT(x.at)}</span></span></a></li>`; }).join("")}</ul>` : `<div class="bd muted">${t("no_notifications")}</div>`);
    pop.querySelector("#popx").addEventListener("click", () => { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); });
    pop.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); }));
  } catch (err) { pop.querySelector(".bd").textContent = errText(err); }
}

function setPending(n) {
  state.pending = n;
  const el = app.querySelector("#pend");
  if (el) { el.textContent = n; el.hidden = !n; }
}

async function route() {
  const hash = location.hash.slice(1) || "/overview";
  const path = hash.split("?")[0];
  if (path === cur.path && cur.result && cur.result.onQuery) { cur.result.onQuery(); return; }
  const hit = ROUTES.find((r) => r[0].test(path));
  if (!hit) { go("/overview"); return; }
  const [re, page, section, needsAuth = true] = hit;
  if (needsAuth && !state.token) { go("/login"); return; }
  if (!needsAuth && state.token) { go("/overview"); return; }
  cleanup();
  cur.path = path; cur.section = section;
  if (!needsAuth) {
    cur.shell = false;
    cur.result = page(app) || null;
    document.title = `${t(section)} · ${t("brand")}`;
    return;
  }
  if (!state.fpo) {
    try { state.fpo = await api("/fpos/me"); } catch (e) { if (!state.token) return; }
  }
  if (!cur.shell) shell(section);
  app.querySelectorAll("[data-nav]").forEach((a) => a.dataset.nav === section ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  app.querySelector("#ptitle").textContent = t(section);
  document.title = `${t(section)} · ${t("brand")}`;
  const main = app.querySelector("#main");
  main.innerHTML = "";
  const m = path.match(re);
  cur.result = page(main, { id: m[1] }) || null;
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", route);
document.addEventListener("kk:lang", () => { document.documentElement.lang = getLang(); cur.shell = false; cur.path = null; route(); });
document.addEventListener("kk:fpo", () => { const el = app.querySelector("#fponame"); if (el) el.textContent = state.fpo?.name || ""; });
document.addEventListener("kk:pending", () => setPending(state.pending));
poll(async () => { if (state.token && cur.shell) { try { setPending((await api("/fpos/notifications")).pending_offers); } catch (e) { /* shown on next page load */ } } }, 30000);
route();
