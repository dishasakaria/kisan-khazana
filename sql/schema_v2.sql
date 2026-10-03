-- Sell Smart v2: direct-sale marketplace, buyers, offers, carpools. Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- All tables are PRIVATE (RLS on, no public policies): the website reads them only through our API, which hides
-- farmer ids/phones and rounds locations.

alter table farmers add column if not exists name text;
alter table farmers add column if not exists last_crop text;
alter table farmers add column if not exists last_qty numeric;
alter table farmers add column if not exists last_mandi text;
alter table farmers add column if not exists last_days int;
alter table farmers add column if not exists last_mandi_price numeric;
alter table farmers add column if not exists last_net numeric;
alter table farmers add column if not exists spoil_rate numeric;      -- from Spoilage Clock photo, per day
alter table farmers add column if not exists stock_condition text;

create table if not exists listings (           -- farmer offers produce directly to buyers (pickup at farm)
  id bigserial primary key, farmer text not null, crop text not null, qty_qtl numeric not null,
  ask_rs_qtl numeric, fair_rs_qtl numeric, lat numeric, lon numeric, district text, ready_date date,
  condition text, status text not null default 'open', created_at timestamptz default now()
);

create table if not exists buyers (
  id bigserial primary key, token text unique not null, name text not null,
  type text not null check (type in ('individual', 'wholesale')), phone text, lat numeric, lon numeric,
  created_at timestamptz default now()
);

create table if not exists offers (
  id bigserial primary key, listing_id bigint references listings(id), buyer_id bigint references buyers(id),
  qty_qtl numeric not null, price_rs_qtl numeric not null, status text not null default 'sent',
  fee_farmer_rs numeric, fee_buyer_rs numeric, created_at timestamptz default now(), decided_at timestamptz
);

create table if not exists carpool_optin (     -- farmers who agreed to share a truck to a mandi on a date
  farmer text not null, mandi text not null, sell_date date not null, crop text, qty_qtl numeric,
  lat numeric, lon numeric, created_at timestamptz default now(), primary key (farmer, mandi, sell_date)
);

alter table listings enable row level security;
alter table buyers enable row level security;
alter table offers enable row level security;
alter table carpool_optin enable row level security;
