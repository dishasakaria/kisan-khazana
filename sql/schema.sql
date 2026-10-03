-- Sell Smart database. Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Security model: Row Level Security ON for every table. The public (anon) key used by the website can only
-- READ non-personal tables. Farmer phone numbers and messages are readable only with the service key (server).

create table if not exists prices (
  date date not null, market text not null, commodity text not null, variety text not null default '',
  min numeric, max numeric, modal numeric not null, arrivals_t numeric, source text not null,
  primary key (date, market, commodity, variety, source)
);
create index if not exists prices_lookup on prices (commodity, market, date);

create table if not exists weather (
  date date not null, district text not null, rain_mm numeric, tmax numeric, tmin numeric, source text not null,
  primary key (date, district, source)
);

create table if not exists diesel (
  date date not null, city text not null, price numeric not null, source text not null,
  primary key (date, city)
);

-- every forecast we make is stored, then scored automatically when the real price arrives
create table if not exists forecasts (
  made_on date not null, market text not null, commodity text not null, horizon_days int not null,
  target_date date not null, p10 numeric, p50 numeric not null, p90 numeric, model text not null,
  primary key (made_on, market, commodity, horizon_days, model)
);

-- live validation: forecast vs actual, computed by the database itself
create or replace view forecast_scores as
select f.*, a.modal as actual,
       abs(a.modal - f.p50) / nullif(a.modal, 0) as abs_pct_error,
       (a.modal between f.p10 and f.p90) as inside_range
from forecasts f
join lateral (
  select avg(p.modal) as modal from prices p
  where p.market = f.market and p.commodity = f.commodity and p.date = f.target_date
) a on a.modal is not null;

create table if not exists farmers (            -- PRIVATE (personal data)
  phone text primary key, lang text default 'mr', lat numeric, lon numeric,
  created_at timestamptz default now()
);

create table if not exists queries (            -- PRIVATE (personal data)
  id bigserial primary key, phone text, channel text not null, message text,
  commodity text, qty_qtl numeric, advice jsonb, created_at timestamptz default now()
);

-- public, anonymised feed for the live map (no phone, location rounded to ~10 km)
create table if not exists live_events (
  id bigserial primary key, channel text, commodity text, qty_qtl numeric,
  lat numeric, lon numeric, mandi text, action text, created_at timestamptz default now()
);

create table if not exists job_runs (
  id bigserial primary key, job text not null, status text not null, rows int, detail text,
  started_at timestamptz default now()
);

alter table prices enable row level security;
alter table weather enable row level security;
alter table diesel enable row level security;
alter table forecasts enable row level security;
alter table farmers enable row level security;
alter table queries enable row level security;
alter table live_events enable row level security;
alter table job_runs enable row level security;

do $$
declare t text;
begin
  foreach t in array array['prices','weather','diesel','forecasts','live_events','job_runs'] loop
    execute format('drop policy if exists public_read on %I', t);
    execute format('create policy public_read on %I for select to anon, authenticated using (true)', t);
  end loop;
end $$;
-- farmers and queries: no policies => anon gets nothing; service key bypasses RLS.

grant select on forecast_scores to anon, authenticated;
alter view forecast_scores set (security_invoker = true);

-- live map updates instantly when a farmer asks something
do $$ begin
  alter publication supabase_realtime add table live_events;
exception when duplicate_object then null; end $$;
