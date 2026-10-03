// Typed client for the Kisaan Khazana API (Sell Smart FastAPI backend). Auth: `Authorization: Bearer <buyer token>`.
export const API_BASE = (process.env.EXPO_PUBLIC_API_BASE_URL || "https://sell-smart.onrender.com").replace(/\/+$/, "");

export type BuyerType = "wholesale" | "processor" | "exporter" | "fpo";
export const BUYER_TYPES: BuyerType[] = ["wholesale", "processor", "exporter", "fpo"];
export type Place = { district: string | null; town: { en: string; mr: string; hi: string } | null };
export type OfferStatus = "sent" | "accepted" | "rejected";
export type Sort = "nearest" | "newest" | "price_asc" | "price_desc" | "qty_desc";

/** An FPO lot as a buyer sees it: never farmer details, never the FPO's phone (that comes with an accepted offer). */
export type Lot = {
  id: number;
  crop: string;
  total_qty_qtl: number;
  available_qty_qtl: number;
  asking_price_rs_qtl: number;
  market_reference_price: number | null;
  quality: string | null;
  location: string | null;
  status: "open" | "sold" | "closed";
  notes: string | null;
  created_at: string;
  updated_at: string;
  km: number | null;
  district: string | null;
  fpo: { id: number; name: string; district: string | null } | null;
  farmers_n?: number;
  my_offer?: { id: number; status: OfferStatus; qty_qtl: number; price_rs_qtl: number } | null;
};

export type LotPage = { items: Lot[]; total: number; page: number; limit: number; has_more: boolean; crops: { crop: string; lots: number }[] };
export type LotQuery = {
  q?: string;
  crop?: string;
  radius_km?: number;
  min_price?: number;
  max_price?: number;
  min_qty?: number;
  sort: Sort;
  page: number;
  limit: number;
};

export type FpoContact = { name: string; phone: string | null; whatsapp: string | null; address: string | null; district: string | null; pickup: string | null };

export type Offer = {
  offer_id: number;
  lot_id: number;
  crop: string | null;
  qty_qtl: number;
  price_rs_qtl: number;
  total_value: number;
  buyer_fee: number;
  status: OfferStatus;
  created_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  lot: Lot | null;
  fpo_contact: FpoContact | null;
};

export type Buyer = {
  id: number;
  name: string;
  company: string | null;
  type: BuyerType;
  phone: string | null;
  lat: number | null;
  lon: number | null;
  location_text: string | null;
  created_at: string;
  place: Place;
};

export type BuyerInput = { name: string; company?: string; type: BuyerType; phone: string; lat: number; lon: number; location_text?: string; pin?: string };

/** status 0 = network/timeout. code = the API's `detail` (e.g. "duplicate_offer") or "http_<status>". */
export class ApiError extends Error {
  constructor(public status: number, public code: string) {
    super(code);
  }
}

let token: string | null = null;
let onUnauthorized: () => void = () => {};
export const setApiToken = (t: string | null, on401?: () => void) => {
  token = t;
  if (on401) onUnauthorized = on401;
};

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 60000); // Render free tier can take ~50 s to wake up
  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      method,
      signal: ctrl.signal,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network");
  } finally {
    clearTimeout(timer);
  }
  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized(); // registration gone: back to sign-up
    const detail = (data as { detail?: unknown } | null)?.detail;
    throw new ApiError(res.status, typeof detail === "string" ? detail : `http_${res.status}`);
  }
  return data as T;
}

const qs = (p: Record<string, string | number | undefined | null>) =>
  Object.entries(p)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");

type Session = { buyer_token: string; buyer: Buyer };
export const api = {
  register: (b: BuyerInput) => req<Session>("POST", "/api/buyers", b),
  login: (phone: string, pin: string) => req<Session>("POST", "/api/buyers/login", { phone, pin }),
  me: () => req<Buyer>("GET", "/api/buyers/me"),
  updateMe: (b: Partial<BuyerInput>) => req<Buyer>("PATCH", "/api/buyers/me", b),
  lots: (p: LotQuery) => req<LotPage>("GET", `/api/fpo-lots?${qs(p)}`),
  lot: (id: number) => req<Lot>("GET", `/api/fpo-lots/${id}`),
  makeOffer: (fpo_lot_id: number, qty_qtl: number, price_rs_qtl: number) =>
    req<{ offer_id: number; status: OfferStatus; offer: Offer }>("POST", "/api/offers", { fpo_lot_id, qty_qtl, price_rs_qtl }),
  offers: () => req<Offer[]>("GET", "/api/offers"),
  offer: (id: number) => req<Offer>("GET", `/api/offers/${id}`),
};
