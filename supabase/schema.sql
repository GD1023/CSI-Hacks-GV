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

-- ---------------------------------------------------------------------------
-- Expanded profile fields: course recommendations, majors, and competitions.
-- Grouped below to match the three input categories from product planning.
-- List-type answers (course lists, extracurriculars, etc.) are stored as
-- Postgres text[] arrays -- the profile form collects them as "one per line"
-- textareas and profile.js splits/joins on newlines, so no separate child
-- tables are needed for a form this size.
-- ---------------------------------------------------------------------------

-- General / cross-cutting
alter table public.profiles add column if not exists graduation_year integer;
alter table public.profiles add column if not exists school_type text;
alter table public.profiles add column if not exists time_commitments text;
alter table public.profiles add column if not exists college_list text[];
alter table public.profiles add column if not exists personal_narrative text;
alter table public.profiles add column if not exists additional_notes text;

-- Course recommendations
alter table public.profiles add column if not exists current_courses text[];
alter table public.profiles add column if not exists completed_courses text[];
alter table public.profiles add column if not exists ap_courses text[];
alter table public.profiles add column if not exists school_profile_link text;
alter table public.profiles add column if not exists schedule_type text;
alter table public.profiles add column if not exists max_courses_per_term smallint;
alter table public.profiles add column if not exists academic_strengths text[];
alter table public.profiles add column if not exists academic_weaknesses text[];
alter table public.profiles add column if not exists remaining_requirements text[];
alter table public.profiles add column if not exists sat_score smallint;
alter table public.profiles add column if not exists act_score smallint;
alter table public.profiles add column if not exists psat_score smallint;

-- Majors
alter table public.profiles add column if not exists extracurriculars text[];
alter table public.profiles add column if not exists clubs text[];
alter table public.profiles add column if not exists leadership_roles text[];
alter table public.profiles add column if not exists honors_awards text[];
alter table public.profiles add column if not exists interest_areas text[];
alter table public.profiles add column if not exists work_experience text[];
alter table public.profiles add column if not exists volunteer_experience text[];
alter table public.profiles add column if not exists intended_majors text[];

-- Competitions
alter table public.profiles add column if not exists competition_history text[];
alter table public.profiles add column if not exists competition_hours_per_week smallint;
alter table public.profiles add column if not exists competition_team_preference text;
alter table public.profiles add column if not exists travel_constraints text;
alter table public.profiles add column if not exists budget_constraints text;

do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'profiles_sat_score_check') then
        alter table public.profiles
            add constraint profiles_sat_score_check check (sat_score is null or (sat_score between 400 and 1600));
    end if;
    if not exists (select 1 from pg_constraint where conname = 'profiles_act_score_check') then
        alter table public.profiles
            add constraint profiles_act_score_check check (act_score is null or (act_score between 1 and 36));
    end if;
    if not exists (select 1 from pg_constraint where conname = 'profiles_psat_score_check') then
        alter table public.profiles
            add constraint profiles_psat_score_check check (psat_score is null or (psat_score between 320 and 1520));
    end if;
    if not exists (select 1 from pg_constraint where conname = 'profiles_school_type_check') then
        alter table public.profiles
            add constraint profiles_school_type_check
            check (school_type is null or school_type in ('public', 'private', 'charter', 'homeschool', 'other'));
    end if;
    if not exists (select 1 from pg_constraint where conname = 'profiles_schedule_type_check') then
        alter table public.profiles
            add constraint profiles_schedule_type_check
            check (schedule_type is null or schedule_type in ('traditional', 'block', 'other'));
    end if;
    if not exists (select 1 from pg_constraint where conname = 'profiles_competition_team_pref_check') then
        alter table public.profiles
            add constraint profiles_competition_team_pref_check
            check (competition_team_preference is null or competition_team_preference in ('team', 'solo', 'no preference'));
    end if;
end $$;

-- Additional fields, added after reviewing what would help the RAG model
-- guide students beyond the original input list:
--  - college_preferences: size/setting/region/public-private fit, feeds the
--    "develop a college list" senior-year milestone alongside college_list.
--  - portfolio_link: creative/technical majors are often better judged by a
--    work sample than by course list or GPA alone.
--  - counselor_name: lets generated guidance say "ask <name> about X" instead
--    of a generic "talk to your counselor."
--  - working_style: a lightweight, self-reported stand-in for a full
--    strengths/interest inventory (e.g. Holland Code) without building an
--    actual quiz -- still gives the model a personality/fit signal.

alter table public.profiles add column if not exists college_preferences text;
alter table public.profiles add column if not exists portfolio_link text;
alter table public.profiles add column if not exists counselor_name text;
alter table public.profiles add column if not exists working_style text;

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

insert into public.profiles (id, name, grade)
select u.id, u.raw_user_meta_data ->> 'name', u.raw_user_meta_data ->> 'grade'
from auth.users u
where not exists (
    select 1 from public.profiles p where p.id = u.id
);
insert into storage.buckets (id, name, public)
values ('profile-documents', 'profile-documents', false)
on conflict (id) do nothing;

drop policy if exists "Users can upload their own documents" on storage.objects;
create policy "Users can upload their own documents"
    on storage.objects for insert
    with check (
        bucket_id = 'profile-documents'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can update their own documents" on storage.objects;
create policy "Users can update their own documents"
    on storage.objects for update
    using (
        bucket_id = 'profile-documents'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can view their own documents" on storage.objects;
create policy "Users can view their own documents"
    on storage.objects for select
    using (
        bucket_id = 'profile-documents'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can delete their own documents" on storage.objects;
create policy "Users can delete their own documents"
    on storage.objects for delete
    using (
        bucket_id = 'profile-documents'
        and (storage.foldername(name))[1] = auth.uid()::text
    );
