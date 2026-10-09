-- Urdu Voice Lab: Supabase setup
-- Run once in: Supabase dashboard -> SQL Editor -> New query -> paste -> Run

-- 1) Speakers: one secret link code per speaker + condition
create table if not exists public.speakers (
  speaker_id  text not null check (speaker_id ~ '^S[0-9]{2}$'),          -- S01..S99
  condition   text not null default 'spk' check (condition in ('spk','cln')),
  token       text not null unique default replace(gen_random_uuid()::text, '-', ''),  -- 32-char secret code
  status      text not null default 'active' check (status in ('active','completed')),
  created_at  timestamptz not null default now(),
  primary key (speaker_id, condition)
);

-- 2) Recordings: one row per saved take (takes are never overwritten)
create table if not exists public.recordings (
  id          bigint generated always as identity primary key,
  speaker_id  text not null,
  condition   text not null,
  row_id      text not null,                 -- corpus ID, CONSENT, or FREE01-03
  take        int  not null,                 -- 1, 2, 3... per sentence
  file_path   text not null unique,          -- path inside the storage bucket
  category    text,
  text_read   text,
  entity      text,
  duration_s  numeric,
  retakes     int,                           -- discarded attempts before saving
  clipped     boolean,
  is_final    boolean not null default true, -- only the latest take is final
  created_at  timestamptz not null default now(),
  unique (speaker_id, condition, row_id, take)
);

-- 3) Lock both tables: no browser access at all (the upload function uses the server key)
alter table public.speakers   enable row level security;
alter table public.recordings enable row level security;

-- 4) Private storage bucket: audio only, max 3 MB per file
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('recordings', 'recordings', false, 3145728, array['audio/webm','audio/ogg','audio/mp4'])
on conflict (id) do nothing;

-- 5) Create speaker links S01-S12 (speakerphone)
insert into public.speakers (speaker_id, condition)
select 'S' || lpad(g::text, 2, '0'), 'spk' from generate_series(1, 12) g
on conflict do nothing;

-- Close-mic links: run later for your 2 chosen speakers, e.g.
-- insert into public.speakers (speaker_id, condition) values ('S01','cln'), ('S02','cln');

-- 6) List all links (run any time; copy each link to its speaker)
select speaker_id, condition, status,
       'https://YOUR-SITE.vercel.app/tools/recorder.html?t=' || token as link
from public.speakers
order by speaker_id, condition;

-- Lock a speaker's link when they are done (link stops working):
-- update public.speakers set status = 'completed' where speaker_id = 'S04' and condition = 'spk';
