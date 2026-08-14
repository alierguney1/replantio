-- Replantio feedback table (run once in the Supabase SQL editor).
-- RLS stays ON with no policies: only the service key (used by
-- api/feedback.js on Vercel) can write; nothing can read from the client.
create table if not exists public.replantio_feedback (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  message text not null check (char_length(message) between 1 and 2000),
  rating smallint check (rating between 1 and 5),
  cc text, city text, ha numeric, lang text, hash text
);
alter table public.replantio_feedback enable row level security;
