-- Kisaan Khazana (v4): buyers trade only with FPOs. Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Flow: farmer (Telegram) -> FPO inventory (table listings, now with fpo_id) -> FPO lot -> buyer offer -> FPO accepts.
-- All tables PRIVATE (RLS on, no public policies); only the server (service key) reads/writes them.

create table if not exists fpos (
  id bigserial primary key,
  name text not null,
  phone text not null unique,
  email text unique,
  address text,
  district text,
  lat numeric,
  lon numeric,
  status text not null default 'active' check (status in ('active', 'suspended')),
  password_hash text not null,          -- scrypt, never plaintext
  token text unique,                    -- dashboard session token
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists fpo_members (
  fpo_id bigint not null references fpos(id) on delete cascade,
  farmer_id text not null,              -- tg:<chat> / sms:+91… / call:+91…
  created_at timestamptz default now(),
  primary key (fpo_id, farmer_id)
);

-- farmer inventory = the existing listings table, now owned by an FPO (status: open -> in_lot -> sold)
alter table listings add column if not exists fpo_id bigint references fpos(id);
create index if not exists listings_fpo on listings (fpo_id, status);

create table if not exists fpo_lots (
  id bigserial primary key,
  fpo_id bigint not null references fpos(id),
  crop text not null,
  total_qty_qtl numeric not null check (total_qty_qtl > 0),
  available_qty_qtl numeric not null check (available_qty_qtl >= 0),
  asking_price_rs_qtl numeric not null check (asking_price_rs_qtl > 0),
  market_reference_price numeric,
  quality text,
  location text,
  lat numeric,
  lon numeric,
  status text not null default 'draft' check (status in ('draft', 'open', 'sold', 'closed')),
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  check (available_qty_qtl <= total_qty_qtl)
);
create index if not exists fpo_lots_status on fpo_lots (status, created_at desc);
create index if not exists fpo_lots_fpo on fpo_lots (fpo_id);

create table if not exists fpo_lot_items (
  lot_id bigint not null references fpo_lots(id) on delete cascade,
  inventory_id bigint not null references listings(id),
  farmer_id text not null,
  qty_qtl numeric not null check (qty_qtl > 0),
  primary key (lot_id, inventory_id)
);

-- offers now point at an FPO lot (old listing_id rows stay, unused)
alter table offers add column if not exists fpo_lot_id bigint references fpo_lots(id);
alter table offers add column if not exists total_value numeric;
alter table offers add column if not exists buyer_fee numeric;
alter table offers add column if not exists accepted_at timestamptz;
alter table offers add column if not exists rejected_at timestamptz;
alter table offers drop constraint if exists offers_qty_pos;
alter table offers add constraint offers_qty_pos check (qty_qtl > 0);
alter table offers drop constraint if exists offers_price_pos;
alter table offers add constraint offers_price_pos check (price_rs_qtl > 0);
create unique index if not exists offers_one_pending_lot on offers (fpo_lot_id, buyer_id) where status = 'sent';
create index if not exists offers_fpo_lot on offers (fpo_lot_id);

-- buyers: individuals allowed again; phone + PIN login on a new phone
alter table buyers add column if not exists company text;
alter table buyers add column if not exists updated_at timestamptz default now();
alter table buyers add column if not exists location_text text;
alter table buyers add column if not exists pin_hash text;
alter table buyers drop constraint if exists buyers_type_check;
alter table buyers add constraint buyers_type_check check (type in ('individual', 'wholesale', 'processor', 'exporter', 'fpo'));
create unique index if not exists buyers_phone_login on buyers (phone) where pin_hash is not null;

-- Accept / reject in ONE transaction: the lot row is locked, so two accepts can never oversell it.
create or replace function accept_offer(p_offer bigint, p_fpo bigint) returns jsonb
language plpgsql as $$
declare o offers%rowtype; l fpo_lots%rowtype; left_qty numeric;
begin
  select * into o from offers where id = p_offer for update;
  if not found or o.fpo_lot_id is null then return jsonb_build_object('ok', false, 'error', 'not_found'); end if;
  select * into l from fpo_lots where id = o.fpo_lot_id for update;
  if l.fpo_id <> p_fpo then return jsonb_build_object('ok', false, 'error', 'not_found'); end if;
  if o.status <> 'sent' then return jsonb_build_object('ok', false, 'error', 'not_pending', 'status', o.status); end if;
  if l.status <> 'open' then return jsonb_build_object('ok', false, 'error', 'lot_closed'); end if;
  if o.qty_qtl > l.available_qty_qtl then
    return jsonb_build_object('ok', false, 'error', 'insufficient_qty', 'available', l.available_qty_qtl);
  end if;
  left_qty := l.available_qty_qtl - o.qty_qtl;
  update fpo_lots set available_qty_qtl = left_qty, status = case when left_qty <= 0 then 'sold' else status end,
                      updated_at = now() where id = l.id;
  update offers set status = 'accepted', accepted_at = now(), decided_at = now() where id = o.id;
  if left_qty <= 0 then  -- sold out: close the other pending offers and the farmers' inventory items
    update offers set status = 'rejected', rejected_at = now(), decided_at = now() where fpo_lot_id = l.id and status = 'sent';
    update listings set status = 'sold' where id in (select inventory_id from fpo_lot_items where lot_id = l.id);
  end if;
  return jsonb_build_object('ok', true, 'available', left_qty, 'lot_status', case when left_qty <= 0 then 'sold' else l.status end);
end $$;

create or replace function reject_offer(p_offer bigint, p_fpo bigint) returns jsonb
language plpgsql as $$
declare o offers%rowtype; l fpo_lots%rowtype;
begin
  select * into o from offers where id = p_offer for update;
  if not found or o.fpo_lot_id is null then return jsonb_build_object('ok', false, 'error', 'not_found'); end if;
  select * into l from fpo_lots where id = o.fpo_lot_id;
  if l.fpo_id <> p_fpo then return jsonb_build_object('ok', false, 'error', 'not_found'); end if;
  if o.status <> 'sent' then return jsonb_build_object('ok', false, 'error', 'not_pending', 'status', o.status); end if;
  update offers set status = 'rejected', rejected_at = now(), decided_at = now() where id = o.id;
  return jsonb_build_object('ok', true);
end $$;

-- only the server may call them (PostgREST exposes functions to anon by default)
revoke execute on function accept_offer(bigint, bigint) from public, anon, authenticated;
revoke execute on function reject_offer(bigint, bigint) from public, anon, authenticated;
grant execute on function accept_offer(bigint, bigint) to service_role;
grant execute on function reject_offer(bigint, bigint) to service_role;

alter table fpos enable row level security;
alter table fpo_members enable row level security;
alter table fpo_lots enable row level security;
alter table fpo_lot_items enable row level security;
alter table listings enable row level security;
alter table offers enable row level security;
alter table buyers enable row level security;

notify pgrst, 'reload schema';
