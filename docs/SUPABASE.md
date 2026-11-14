# Supabase edit store for the 50-site table

Supabase holds the 50-site reference table so the team can check and correct rows in one place. It is an edit store only.

## Rules
- The deployed site reads exported static JSON (`public/data/sites.json`). It never calls Supabase at runtime.
- No Supabase client code ships in the site bundle. Do not add `@supabase/supabase-js` to `dependencies`; the upsert and export scripts run locally and are not imported by `src/`.
- Writes happen only through the service key, from a local `.env`. The service key is never committed, never pasted in an issue, and never sent in chat or in a public place.
- The anon (public) key is read-only through row level security. Nothing in the repo needs it at build time.
- Keys go in `.env` (ignored by git). `.env.example` lists the variable names with empty values.

## Setup (issue A8)
1. Create a Supabase project.
2. Run the SQL below in the SQL editor.
3. Send Yash the project URL and the service key privately.

## SQL

```sql
create table public.sites (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  body text not null,
  lat double precision not null,
  lon double precision not null,
  kind text,
  analog_of text,
  source_url_1 text not null,
  source_url_2 text,
  v1_used boolean,
  created_at timestamptz default now(),
  unique (name, body)
);
alter table public.sites enable row level security;
create policy "public read" on public.sites for select to anon using (true);
```

## Data flow (issue B13)
- Upsert script: loads the checked rows from `data/reference/sites.csv` into `public.sites` using the service key.
- Export script: reads the table and writes `public/data/sites.json`.
- `make_data` calls the export when the keys are set, and reads `data/reference/sites.csv` otherwise. The build must work without keys.
