import { ApiError } from "./api";
import { hasKey, type Key, type Lang } from "./i18n";

/** Indian digit grouping (1,23,456) without relying on Intl support in the JS engine. */
export function inr(n: number, decimals = 0): string {
  const neg = n < 0;
  const [int = "0", frac] = Math.abs(n).toFixed(decimals).split(".");
  let head = int.slice(0, -3);
  let tail = int.slice(-3);
  while (head.length > 2) {
    tail = head.slice(-2) + "," + tail;
    head = head.slice(0, -2);
  }
  return (neg ? "-" : "") + (head ? head + "," + tail : tail) + (frac && Number(frac) ? "." + frac : "");
}

export const rs = (n: number | null | undefined) => (n == null || !isFinite(n) ? "—" : "₹" + inr(Math.round(n)));
export const qtl = (n: number | null | undefined) => (n == null || !isFinite(n) ? "—" : inr(n, n % 1 ? 1 : 0));

const MONTHS: Record<Lang, string[]> = {
  mr: "जाने फेब्रु मार्च एप्रि मे जून जुलै ऑग सप्टें ऑक्टो नोव्हें डिसें".split(" "),
  hi: "जन फ़र मार्च अप्रै मई जून जुला अग सितं अक्टू नवं दिसं".split(" "),
  en: "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" "),
};

export function shortDate(lang: Lang, iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
  if (isNaN(d.getTime())) return "—";
  return `${d.getDate()} ${MONTHS[lang][d.getMonth()]}`;
}

export function ago(t: (k: Key, v?: Record<string, string | number>) => string, iso: string | null | undefined, now = Date.now()) {
  if (!iso) return "";
  const m = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000));
  if (m < 1) return t("just_now");
  if (m < 60) return t("ago_m", { n: m });
  if (m < 48 * 60) return t("ago_h", { n: Math.round(m / 60) });
  return t("ago_d", { n: Math.round(m / 1440) });
}

/** API error -> sentence in the buyer's language. */
export function errText(t: (k: Key) => string, e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 0) return t("err_network");
    const k = "err_" + e.code;
    if (hasKey(k)) return t(k);
    if (e.status === 401) return t("err_session");
  }
  return t("err_generic");
}
