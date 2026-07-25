-- Safe to re-run: paste this whole file into Supabase Dashboard -> SQL Editor -> New query -> Run.
-- It creates/updates the profiles table, RLS policies, and the signup trigger,
-- and backfills a profile row for any existing auth.users that don't have one yet
-- (covers accounts created before this trigger existed).

create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    name text,
    grade text,
    school text,
    interests text,
    gpa numeric(3, 2) check (gpa is null or (gpa >= 0 and gpa <= 5.0)),
    transcript_link text,
    updated_at timestamptz not null default now()
);

alter table public.profiles add column if not exists gpa numeric(3, 2);
alter table public.profiles add column if not exists transcript_link text;

do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'profiles_gpa_check'
    ) then
        alter table public.profiles
            add constraint profiles_gpa_check check (gpa is null or (gpa >= 0 and gpa <= 5.0));
    end if;
end $$;

alter table public.profiles enable row level security;

drop policy if exists "Users can view their own profile" on public.profiles;
create policy "Users can view their own profile"
    on public.profiles for select
    using (auth.uid() = id);

drop policy if exists "Users can insert their own profile" on public.profiles;
create policy "Users can insert their own profile"
    on public.profiles for insert
    with check (auth.uid() = id);

drop policy if exists "Users can update their own profile" on public.profiles;
create policy "Users can update their own profile"
    on public.profiles for update
    using (auth.uid() = id);

-- Auto-create a profile row for every new signup, seeded with the "name" and
-- "grade" passed in supabase.auth.signUp()'s options.data (see signup/signup.js).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, name, grade)
    values (new.id, new.raw_user_meta_data ->> 'name', new.raw_user_meta_data ->> 'grade')
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- Backfill: create a (mostly empty) profile row for any existing auth.users
-- that predate the trigger above, so nobody is stuck without a profiles row.
insert into public.profiles (id, name, grade)
select u.id, u.raw_user_meta_data ->> 'name', u.raw_user_meta_data ->> 'grade'
from auth.users u
where not exists (
    select 1 from public.profiles p where p.id = u.id
);
