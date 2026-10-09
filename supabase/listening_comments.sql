-- Urdu Voice Lab: optional listener comments (run once in Supabase -> SQL Editor)
create table if not exists public.listener_comments (
  id          bigint generated always as identity primary key,
  listener_id text not null references public.listeners (listener_id),
  comment     text not null check (char_length(comment) between 1 and 2000),
  created_at  timestamptz not null default now()
);
alter table public.listener_comments enable row level security;   -- no browser access; the listen function saves comments
