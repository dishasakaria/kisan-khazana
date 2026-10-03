-- Sell Smart v3: buyer mobile app. Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Tables stay PRIVATE (RLS on, no public policies); the app reads them only through our API.

-- Telegram farmers have no phone number: they can share it with the bot after accepting an offer.
alter table farmers add column if not exists contact_phone text;

-- Buyers: wholesale only (trader, processor, exporter, FPO procurement); no individual buyers.
alter table buyers add column if not exists company text;
alter table buyers add column if not exists updated_at timestamptz default now();
update buyers set type = 'wholesale' where type not in ('wholesale', 'processor', 'exporter', 'fpo');
alter table buyers drop constraint if exists buyers_type_check;
alter table buyers add constraint buyers_type_check check (type in ('wholesale', 'processor', 'exporter', 'fpo'));

-- Offers keep using decided_at for accept/reject time. One pending offer per buyer per lot:
-- close older duplicates first, then let the database enforce it.
update offers o set status = 'rejected', decided_at = now()
where o.status = 'sent' and exists (select 1 from offers n where n.listing_id = o.listing_id and n.buyer_id = o.buyer_id
                                     and n.status = 'sent' and n.id > o.id);
create unique index if not exists offers_one_pending on offers (listing_id, buyer_id) where status = 'sent';

create index if not exists listings_status_created on listings (status, created_at desc);
create index if not exists offers_buyer on offers (buyer_id);
create index if not exists offers_listing on offers (listing_id);

alter table farmers enable row level security;
alter table buyers enable row level security;
alter table offers enable row level security;
alter table listings enable row level security;
