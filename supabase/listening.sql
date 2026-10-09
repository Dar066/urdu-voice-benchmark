-- Urdu Voice Lab: blind listening test setup
-- Run once in: Supabase dashboard -> SQL Editor -> New query -> paste -> Run

-- 1) Listeners: one secret link code each
create table if not exists public.listeners (
  listener_id text primary key check (listener_id ~ '^L[0-9]{2}$'),       -- L01..L99
  token       text not null unique default replace(gen_random_uuid()::text, '-', ''),
  status      text not null default 'active' check (status in ('active','completed')),
  created_at  timestamptz not null default now()
);

-- 2) Ratings: one row per listener per clip (a listener can change an answer)
create table if not exists public.ratings (
  id          bigint generated always as identity primary key,
  listener_id text not null references public.listeners (listener_id),
  clip_id     text not null,
  naturalness int  not null check (naturalness between 1 and 5),        -- 1 = very unnatural, 5 = fully natural
  accent      text not null check (accent in ('pk','in','unsure')),     -- Pakistani / Indian / can't tell
  wrong_word  boolean not null,                                         -- any word sounded wrong?
  plays       int,                                                      -- how many times the clip was played
  created_at  timestamptz not null default now(),
  unique (listener_id, clip_id)
);

-- 3) Lock both tables: no browser access (the listen function uses the server key)
alter table public.listeners enable row level security;
alter table public.ratings   enable row level security;

-- 4) Create 15 listener links
insert into public.listeners (listener_id)
select 'L' || lpad(g::text, 2, '0') from generate_series(1, 15) g
on conflict do nothing;

-- 5) List all listener links (run any time)
select listener_id, status,
       'https://YOUR-SITE.vercel.app/tools/listen/?t=' || token as link
from public.listeners
order by listener_id;

-- Close a listener's link when they are done:
-- update public.listeners set status = 'completed' where listener_id = 'LXX';
