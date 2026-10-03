// Shared runtime: API client, formatting, badges, tables, dialogs, toasts, skeletons, polling.
import { t, cropName, locale } from "./i18n.js";
import { icon } from "./icons.js";

export const state = { token: null, fpo: null, pending: 0, title: "" };
try { state.token = localStorage.getItem("kk_token"); } catch (e) { /* storage blocked */ }

export function setToken(tok) {
  state.token = tok;
  try { tok ? localStorage.setItem("kk_token", tok) : localStorage.removeItem("kk_token"); } catch (e) { /* storage blocked */ }
}
export function logout() { setToken(null); state.fpo = null; state.pending = 0; go("/login"); }
export const go = (path) => { location.hash = "#" + path; };

export class ApiError extends Error {
  constructor(code, status, data) { super(code); this.code = code; this.status = status; this.data = data; }
}

/** fetch wrapper: same origin, bearer token, 20 s timeout, {detail: code} -> ApiError(code, status). 401 with a token -> login. */
export async function api(path, { method = "GET", body, params, timeout = 20000 } = {}) {
  const url = new URL("/api" + path, location.origin);
  for (const k in params || {}) if (params[k] !== "" && params[k] != null) url.searchParams.set(k, params[k]);
  const ctrl = new AbortController(), tm = setTimeout(() => ctrl.abort(), timeout), headers = {};
  if (state.token) headers.Authorization = "Bearer " + state.token;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let r;
  try {
    r = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: ctrl.signal });
  } catch (e) {
    throw new ApiError(e.name === "AbortError" ? "timeout" : "network", 0);
  } finally { clearTimeout(tm); }
  let data = null;
  try { data = await r.json(); } catch (e) { /* empty body */ }
  if (!r.ok) {
    const code = data && typeof data.detail === "string" ? data.detail : String(r.status);
    if (r.status === 401 && state.token) logout();
    throw new ApiError(code, r.status, data);
  }
  return data;
}

export function errText(e) {
  if (!(e instanceof ApiError)) return t("e_generic");
  if (e.code === "network" || e.code === "timeout") return t("e_" + e.code);
  const k = "e_" + e.code;
  if (t(k) !== k) return t(k);
  if (e.status === 401 || e.status === 403 || e.status === 404 || e.status === 422 || e.status === 429) return t("e_" + e.status);
  if (e.status >= 500) return t("e_500");
  if (e.status === 400) return t("e_bad_input");
  return t("e_generic");
}

// ---------- formatting ----------
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const num = (x, d = 1) => (x == null || x === "" || isNaN(+x)) ? "—" : (+x).toLocaleString("en-IN", { maximumFractionDigits: d });
export const rs = (x) => x == null || isNaN(+x) ? "—" : "₹" + num(x, 0);
export const qtl = (x) => `${num(x)} ${t("qtl")}`;
export const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString(locale(), { day: "numeric", month: "short", year: "numeric" }) : "—";
export const fmtDT = (iso) => iso ? new Date(iso).toLocaleString(locale(), { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) : "—";
export function lotCode(l) {
  if (l.code) return l.code;
  const letters = String(l.crop || "").replace(/[^A-Za-z]/g, "").slice(0, 2).toUpperCase() || "LT";
  return `${letters}-${String(l.id).padStart(3, "0")}`;
}
export const typeName = (ty) => (ty && t("t_" + ty) !== "t_" + ty) ? t("t_" + ty) : (ty || "—");
export const channelText = (ch) => t({ tg: "via_telegram", sms: "via_sms", call: "via_call" }[ch] || "via_telegram");
export const initials = (name) => (name || "?").trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
export { cropName, icon, t };

// ---------- badges (icon + text, never colour alone) ----------
const BADGE = {
  open: ["ok", "st_open", "okcircle"], available: ["ok", "st_available", "okcircle"], in_lot: ["info", "st_in_lot", "layers"],
  sold: ["info", "st_sold", "tag"], draft: ["neutral", "st_draft", "file"], lot_open: ["ok", "st_lot_open", "eye"], closed: ["neutral", "st_closed", "xcircle"],
  sent: ["warn", "st_sent", "clock"], accepted: ["ok", "st_accepted", "okcircle"], rejected: ["bad", "st_rejected", "xcircle"],
};
export function badge(status, kind) {
  const key = kind === "lot" && status === "open" ? "lot_open" : status;
  const [cls, label, ic] = BADGE[key] || ["neutral", null, "info"];
  return `<span class="badge ${cls}">${icon(ic, 13)}${label ? t(label) : esc(status)}</span>`;
}

// ---------- building blocks ----------
export const skeleton = (n = 4) => `<div class="card sk-card" aria-busy="true" aria-label="${t("loading")}">${Array.from({ length: n }, (_, i) => `<span class="skeleton" style="width:${[70, 95, 85, 60, 90][i % 5]}%"></span>`).join("")}</div>`;
export const empty = (ic, title, sub, action = "") => `<div class="empty">${icon(ic, 36)}<b>${esc(title)}</b><p>${esc(sub || "")}</p>${action}</div>`;
export const errBox = (e, retryId) => `<div class="alert err" role="alert">${icon("alert", 18)}<div style="flex:1">${esc(errText(e))}</div>${retryId ? `<button class="btn sm" id="${retryId}">${t("retry")}</button>` : ""}</div>`;

/** cols: [{k, l, f(row) -> html, cls}] ; rows ; onRow(row) ; data-l labels make the table stack on phones. */
export function table(cols, rows, { onRow, stack = true, id = "" } = {}) {
  const cls = `tbl${stack ? " stack" : ""}`;
  const head = `<thead><tr>${cols.map((c) => `<th class="${c.cls || ""}">${esc(c.l)}</th>`).join("")}</tr></thead>`;
  const body = rows.map((r, i) => `<tr class="${onRow ? "row" : ""}" data-i="${i}" ${onRow ? 'tabindex="0" role="link"' : ""}>${cols.map((c) =>
    `<td class="${c.cls || ""}" data-l="${esc(c.l)}">${c.f ? c.f(r) : esc(r[c.k])}</td>`).join("")}</tr>`).join("");
  return `<div class="tbl-wrap"><table class="${cls}" ${id ? `id="${id}"` : ""}>${head}<tbody>${body}</tbody></table></div>`;
}
export function bindRows(root, rows, onRow) {
  root.querySelectorAll("tr.row, li.row").forEach((tr) => {
    const open = () => onRow(rows[+tr.dataset.i]);
    tr.addEventListener("click", open);
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
  });
}
export function pager(p) {
  const pages = Math.max(1, Math.ceil(p.total / p.limit));
  return `<div class="pager"><span>${t("results", { n: p.total })} · ${t("page_of", { p: p.page, n: pages })}</span><span class="actions">
    <button class="btn sm" data-pg="${p.page - 1}" ${p.page <= 1 ? "disabled" : ""} aria-label="${t("prev")}">${icon("left", 14)} ${t("prev")}</button>
    <button class="btn sm" data-pg="${p.page + 1}" ${p.has_more ? "" : "disabled"} aria-label="${t("next")}">${t("next")} ${icon("right", 14)}</button></span></div>`;
}
export const tabs = (items, cur) => `<div class="tabs" role="tablist">${items.map(([v, l, n]) =>
  `<button role="tab" data-tab="${v}" aria-selected="${v === cur}">${esc(l)}${n != null ? `<span class="cnt">${n}</span>` : ""}</button>`).join("")}</div>`;
export const kv = (pairs) => `<dl class="kv">${pairs.filter((p) => p).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v ?? "—"}</dd>`).join("")}</dl>`;
export const field = (label, input, hint = "") => `<div class="field"><label class="f">${esc(label)}${input}</label>${hint ? `<div class="hint">${esc(hint)}</div>` : ""}</div>`;

// ---------- toast / confirm ----------
export function toast(msg, type = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.setAttribute("role", type === "err" ? "alert" : "status");
  el.innerHTML = `${icon(type === "err" ? "alert" : "okcircle", 18)}<span>${esc(msg)}</span>`;
  document.getElementById("toasts").appendChild(el);
  setTimeout(() => el.remove(), type === "err" ? 7000 : 4000);
}
export function confirmDialog({ title, body, ok, danger = false }) {
  return new Promise((resolve) => {
    const d = document.createElement("dialog");
    d.innerHTML = `<div class="bd"><h2>${esc(title)}</h2><p>${esc(body)}</p><div class="actions">
      <button class="btn" value="no">${t("cancel")}</button><button class="btn ${danger ? "danger solid" : "primary"}" value="yes">${esc(ok)}</button></div></div>`;
    document.body.appendChild(d);
    d.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { d.close(b.value); }));
    d.addEventListener("close", () => { resolve(d.returnValue === "yes"); d.remove(); });
    d.showModal();
    d.querySelector('[value="yes"]').focus();
  });
}

/** Double-submit guard: disables the button while fn runs. */
export async function busy(btn, fn) {
  if (!btn || btn.disabled) return;
  const html = btn.innerHTML;
  btn.disabled = true; btn.setAttribute("aria-busy", "true"); btn.innerHTML = `${icon("refresh", 16)} ${t("working")}`;
  try { return await fn(); } catch (e) { toast(errText(e), "err"); }
  finally { btn.disabled = false; btn.removeAttribute("aria-busy"); btn.innerHTML = html; }
}
export const formData = (form) => Object.fromEntries(new FormData(form).entries());

/** Refetch on focus/visibility + every `ms`. Returns a stop(). */
export function poll(fn, ms = 20000) {
  let timer = setInterval(() => { if (document.visibilityState === "visible") fn(); }, ms);
  const onVis = () => { if (document.visibilityState === "visible") fn(); };
  document.addEventListener("visibilitychange", onVis);
  window.addEventListener("focus", onVis);
  return () => { clearInterval(timer); document.removeEventListener("visibilitychange", onVis); window.removeEventListener("focus", onVis); };
}
export const debounce = (fn, ms = 300) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };
