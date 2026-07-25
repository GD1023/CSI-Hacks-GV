-- Run this once in the Supabase dashboard: Project -> SQL Editor -> New query -> paste -> Run.

create table public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    name text,
    grade text,
    school text,
    interests text,
    updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
    on public.profiles for select
    using (auth.uid() = id);

create policy "Users can insert their own profile"
    on public.profiles for insert
    with check (auth.uid() = id);

create policy "Users can update their own profile"
    on public.profiles for update
    using (auth.uid() = id);

-- Auto-create a profile row for every new signup, seeded with the "name"
-- passed in supabase.auth.signUp()'s options.data (see signup/signup.js).
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, name)
    values (new.id, new.raw_user_meta_data ->> 'name');
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();
