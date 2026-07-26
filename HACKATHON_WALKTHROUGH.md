# High School Compass — Project Walkthrough

A reference doc explaining every component of the site: what it does, how it's wired together, and why it was built that way. Written to prep for explaining the project to hackathon judges.

**One-sentence pitch:** High School Compass is a personalized guidance platform for high schoolers — students fill out one detailed profile, and the site turns it into a visual snapshot (radar chart), organized views across six life-of-a-student categories, and AI-generated, retrieval-grounded advice for each.

---

## 1. Architecture at a glance

Three pieces, cleanly separated:

| Piece | Tech | Hosting | Responsibility |
|---|---|---|---|
| Frontend | Plain HTML/CSS/vanilla JS ES modules (no framework, no build step) | **Vercel** | UI, auth forms, profile CRUD, talks to Supabase directly |
| Database + Auth + File storage | **Supabase** (managed Postgres + Auth + Storage) | Supabase cloud | Source of truth for users, profiles, competitions catalog, uploaded PDFs |
| AI backend | **Flask** (Python) + LangChain + FAISS + Groq | **Render** | One endpoint (`/advice`) that runs a RAG pipeline over the student's profile |

The frontend talks **directly** to Supabase for everything except one thing — generating AI advice — which is the only reason a separate backend server exists at all. This is a deliberate minimalism: no custom REST API for CRUD, because Supabase's client library + Row Level Security already provides one safely.

```
Browser (Vercel static site)
   |
   |-- Supabase JS client -----> Supabase (Postgres + Auth + Storage)
   |                              - auth.users / public.profiles / public.competitions
   |                              - RLS enforces "you only see your own row"
   |
   \-- fetch('/advice', Bearer <jwt>) --> Flask API (Render)
                                            - re-auths as the user via the same JWT
                                            - RAG over public.competitions (FAISS)
                                            - Groq Llama 3.3 70B generates advice
```

---

## 2. Database schema (`supabase/schema.sql`)

This single SQL file is the entire backend data layer. It's written to be **safe to re-run** — paste it into the Supabase SQL editor any number of times without erroring, via `create table if not exists`, `add column if not exists`, and `do $$ ... if not exists (select from pg_constraint) ... $$` guards around constraints (Postgres has no native `add constraint if not exists`).

### 2.1 `public.profiles` — one row per user

```sql
create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    name text,
    grade text,
    school text,
    ...
    updated_at timestamptz not null default now()
);
```

- `id` is both the primary key **and** a foreign key into Supabase's built-in `auth.users` table, with `on delete cascade` — delete the auth user and their profile row disappears too.
- The rest of the table is ~45 columns added incrementally via `alter table ... add column if not exists`, grouped by the six advice categories the app surfaces: general info, courses, clubs, extracurriculars, competitions/awards, testing/college prep.
- **List-type answers** (`current_courses`, `clubs`, `intended_majors`, `honors_awards`, etc.) are stored as native **Postgres `text[]` arrays**, not child tables. The profile form collects each as a "one per line" `<textarea>`, and the frontend just does `value.split('\n')` / `.join('\n')` to move between array and textarea — no join tables needed for a form this size.
- **Check constraints** validate data at the database level, independent of whatever the frontend allows through:
  - `gpa` between 0 and 5.0
  - `sat_score` between 400–1600, `act_score` 1–36, `psat_score` 320–1520
  - enum-style checks on `school_type` (`public/private/charter/homeschool/other`), `schedule_type` (`traditional/block/other`), `competition_team_preference` (`team/solo/no preference`)

### 2.2 Row Level Security (RLS) — the core security concept

```sql
alter table public.profiles enable row level security;

create policy "Users can view their own profile"
    on public.profiles for select using (auth.uid() = id);
create policy "Users can insert their own profile"
    on public.profiles for insert with check (auth.uid() = id);
create policy "Users can update their own profile"
    on public.profiles for update using (auth.uid() = id);
```

`auth.uid()` is a Postgres function Supabase provides that reads the caller's id straight out of their JWT. Once RLS is enabled, **every** query — from any client, with any key — must satisfy a policy or it returns nothing. This is what lets the frontend query `supabase.from('profiles').select(...)` using only the public **anon key**: Postgres itself enforces that a user can only ever see or modify their own row. There is no separate authorization layer to write or get wrong — it's enforced at the database, once, for every access path (frontend, backend, even the Supabase dashboard).

### 2.3 The signup trigger — auto-creating a profile row

```sql
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public
as $$
begin
    insert into public.profiles (id, name, grade)
    values (new.id, new.raw_user_meta_data ->> 'name', new.raw_user_meta_data ->> 'grade')
    on conflict (id) do nothing;
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();
```

When `supabase.auth.signUp()` inserts a row into `auth.users`, this trigger fires automatically and creates the matching `public.profiles` row, pulling `name`/`grade` out of the signup metadata (`options.data` in the JS call — see §4.2). `security definer` means the function executes with the privileges of its owner rather than the calling user, which is necessary because a brand-new user can't yet satisfy the profiles `insert` RLS policy at the exact instant their `auth.users` row is created. A one-time backfill `insert ... where not exists (...)` right after the trigger definition covers any accounts that existed before this trigger was added.

### 2.4 `public.competitions` — the RAG corpus

```sql
create table if not exists public.competitions (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text,
    category text,
    grade_levels text,
    team_or_solo text,
    url text
);

alter table public.competitions enable row level security;
create policy "Anyone can read competitions"
    on public.competitions for select using (true);
```

~300 rows of competition data (science fairs, hackathons, olympiads, etc.) — **shared reference data, not user-owned**. RLS is enabled, but the select policy allows anyone, including anonymous requests, to read it (`using (true)`). There's deliberately no insert policy — this table is populated manually via the Supabase table editor/CSV import, not through the app. This is the retrieval corpus the Flask backend embeds into a FAISS vector index (§6).

### 2.5 Storage — transcript & school-profile PDFs

```sql
insert into storage.buckets (id, name, public)
values ('profile-documents', 'profile-documents', false)
on conflict (id) do nothing;

create policy "Users can upload their own documents" on storage.objects
    for insert with check (
        bucket_id = 'profile-documents'
        and (storage.foldername(name))[1] = auth.uid()::text
    );
-- (mirrored for select / update / delete)
```

One **private** bucket. Files live at `<user_id>/transcript.pdf` and `<user_id>/school-profile.pdf` (upsert on re-upload, so a new file replaces the old one at the same path). `storage.foldername(name)` splits the object path into folder segments, so each policy enforces "you can only touch files inside a folder named after your own user id" — the same RLS pattern as the profiles table, applied to file storage. Because the bucket isn't public, the frontend never links to it directly — it calls `createSignedUrl(path, 60 * 60)` to mint a 1-hour temporary URL on read, since transcripts are sensitive.

---

## 3. Frontend shell (shared across every page)

### 3.1 `supabase-client.js` — one shared client

```js
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
```

Every page imports this single client instance. The key baked in here is the **anon key** — safe to ship to the browser, since it grants no access beyond what RLS policies allow.

### 3.2 `auth-guard.js` — page gating

```js
const { data: { session } } = await supabase.auth.getSession();
if (!session) window.location.href = '/login';
else document.body.classList.remove('gated');
```

Included on pages that require login. Supabase persists the session/JWT in browser storage, so this is just a read — no network auth call needed on every page load. The `gated` class is presumably hidden-by-default CSS, removed once a session is confirmed, to avoid a flash of protected content before the redirect fires.

### 3.3 `script.js` — site-wide chrome, loaded on every page

Four independent init functions, all called at the bottom of the file:

- **`initTermsGate()`** — intercepts the login/signup form's `submit` event and blocks it (`preventDefault` + `stopImmediatePropagation`) until the user checks a terms checkbox and clicks "Accept" in a modal, at which point it calls `form.requestSubmit()` to let the real handler (login.js/signup.js) run. Relies on `script.js` being loaded *before* `login.js`/`signup.js` in the HTML so its listener registers first.
- **`initMobileNav()`** — hamburger menu toggle; also auto-collapses the mobile nav if the viewport crosses the desktop breakpoint via `matchMedia('(min-width: 768px)')`, so it can't get stuck open behind the desktop layout.
- **`initActiveNavLink()`** — normalizes the current pathname (strips `/index.html` and trailing slashes) and adds a `nav-current` class to the matching nav link.
- **`initScrollReveal()`** — `IntersectionObserver`-based fade/slide-in for cards as they scroll into view, with a staggered delay per element (capped at 6 × 60ms). Falls back to making everything visible immediately if `IntersectionObserver` isn't supported.
- **`updateAuthNav()`** — re-renders the nav's auth area based on session state (Login/Sign Up buttons vs. a profile badge + Sign Out), and toggles visibility of every `.nav-restricted` link (the logged-in-only nav items like Courses/Clubs/Careers). Re-runs automatically on `supabase.auth.onAuthStateChange(...)`, so login/logout updates the nav without a page reload.

### 3.4 `tailwind-config.js` — design tokens

Tailwind is loaded via the **Play CDN** (`<script src="https://cdn.tailwindcss.com">`) rather than a build step — appropriate for a no-bundler static site. This file, loaded right after, defines the theme: a "Reading Room" look (near-white background, hairline rules instead of card shadows, one pine-green accent color used only for interactive elements, Archivo for headings/UI, Source Serif 4 for body copy). It also registers reusable component classes (`.btn`, `.btn-primary`, `.nav-link`, `.nav-current`, `.nav-profile-badge`, `.container-page`) via Tailwind's `addComponents` plugin API, so those class names can be used directly in HTML instead of repeating utility class soup on every page.

---

## 4. Auth pages

### 4.1 `login/login.js`

```js
const { error } = await supabase.auth.signInWithPassword({ email, password });
```

Straight passthrough to Supabase Auth. On success, redirects to `/`.

### 4.2 `signup/signup.js`

```js
const { error } = await supabase.auth.signUp({
    email, password,
    options: { data: { name, grade } }
});
```

The `options.data` object becomes `raw_user_meta_data` on the new `auth.users` row — this is exactly what the `handle_new_user()` trigger (§2.3) reads to pre-fill the new profile's `name` and `grade`.

Both forms are gated by `initTermsGate()` from `script.js` (§3.3) before the actual Supabase call fires.

---

## 5. Profile — the data entry point for everything else

### 5.1 `profile/profile.js`

The biggest frontend file. Three field-type arrays drive the whole form generically instead of hand-writing per-field logic:

```js
const LIST_FIELDS = [...];   // text[] columns, "one per line" textareas
const NUMBER_FIELDS = [...]; // numeric columns; empty input -> null, not 0/NaN
const TEXT_FIELDS = [...];   // plain text/select columns, read/written as-is
```

**Load**: fetches the current user's row with `supabase.from('profiles').select(ALL_FIELDS.join(', ')).eq('id', user.id).maybeSingle()`, then populates the form — arrays get joined into textareas, numbers use `??` so `0` isn't treated as empty, everything else is direct.

**Save**: on submit, builds a payload keyed by `{ id: user.id, ...fields }` and calls `supabase.from('profiles').upsert(payload)` — a single upsert whether the row already existed (it does, thanks to the signup trigger) or not.

**File uploads**: transcript and school-profile PDFs are handled separately from the rest of the form, because file inputs can't be pre-filled — an empty file input on submit means "no change," not "clear the file." Only inputs with an actually-selected file get uploaded (10MB cap, `application/pdf`) via `supabase.storage.from('profile-documents').upload(path, file, { upsert: true })`, and the resulting storage path is merged into the same upsert payload. After upload, `showCurrentDocument()` mints a signed URL to render a "View current file" link.

### 5.2 `profile-view.js` — shared read-side helpers

Used by every other page (classes, clubs, extracurriculars, competitions, college-prep, testing, career-advice) to display profile data without repeating boilerplate:

- `fetchProfileFields(userId, columns)` — a scoped `select` for just the columns that page needs (keeps each page's query minimal).
- `renderList(containerId, items, emptyText)` — turns a `text[]` column into a `<ul>`, or an empty-state message.
- `renderText(containerId, value, emptyText)` — plain text with a fallback.
- `renderMaybeLink(containerId, value, emptyText)` — renders as a clickable link only if the value looks like `http(s)://...`, otherwise plain text (used for `portfolio_link`, which is optional and might just be a name).
- `renderDocumentLink(containerId, path, emptyText)` — same signed-URL pattern as profile.js, reused for displaying (not uploading) transcript/school-profile links.

---

## 6. The six "advice" pages

Six pages — `classes/`, `clubs/`, `extracurriculars/`, `competitions/`, `college-prep/`, `testing/`, plus `career-advice/` — all follow the **exact same three-step pattern**:

```js
const profile = await fetchProfileFields(session.user.id, [ /* just this page's columns */ ]);
renderList('pd-...', profile.some_array_field, 'No ... added yet.');
renderText('pd-...', profile.some_field, 'Not set');
renderAdvice('ai-advice', 'clubs'); // <- key matches one of the 6 advice JSON keys
```

1. Pull only the profile columns relevant to that page's topic.
2. Render each one into the page (read-only display of what the user entered on `/profile`).
3. Call `renderAdvice(containerId, key)` to show the AI-generated paragraph for that category.

This consistency is worth highlighting to judges: adding a 7th "advice page" is almost entirely copy-paste-and-adjust-column-list, because the hard parts (fetching, rendering, caching, AI generation) are all centralized in shared modules.

### `advice-client.js` — talking to the AI backend

```js
const API_BASE = ['localhost', '127.0.0.1'].includes(window.location.hostname)
    ? 'http://localhost:5000'
    : 'https://high-school-compass-api.onrender.com';

export async function getAdvice() {
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (cached) return JSON.parse(cached);
    const { data: { session } } = await supabase.auth.getSession();
    const response = await fetch(`${API_BASE}/advice`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${session.access_token}` },
    });
    ...
}
```

Two things worth calling out:

- **Environment-aware API base URL** — automatically points at `localhost:5000` during local dev and the deployed Render URL otherwise, based on `window.location.hostname`. No env var/build step needed for a static site to know which backend to call.
- **Session caching** — the backend's one `/advice` call returns all six advice sections at once (it's a single LLM call over the whole profile, see §7), so the result is cached in `sessionStorage` for the browser tab's lifetime. Navigating between the six advice pages doesn't re-trigger the LLM each time — only a fresh login/session clears it.

`renderAdvice(containerId, key)` wraps this in a try/catch so a failed or logged-out call just displays a friendly message in place instead of breaking the page.

---

## 7. AI backend (`backend/`) — deployed separately on Render

### 7.1 Why a separate server at all

The frontend is a static site with no server-side runtime — fine for talking to Supabase (client-side SDK + RLS), but not for running an embeddings model, a FAISS vector index, and an LLM call. That needs a real, long-lived Python process, hence a second deployment target.

### 7.2 `app.py` — the one route

```python
@app.route("/advice", methods=["POST"])
def advice():
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header[len("Bearer "):].strip()

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)

    result = client.table("profiles").select("*").maybe_single().execute()
    profile = result.data
    ...
    advice_result = get_bot().chat(profile)
    return jsonify(advice_result)
```

The key design decision: **the backend never uses a Supabase service-role key.** It takes the *user's own* JWT (forwarded by `advice-client.js`), authenticates a fresh anon-key Supabase client as that user (`client.postgrest.auth(access_token)`), and queries `profiles` with **no `.eq('id', ...)` filter at all** — RLS does the filtering, because `auth.uid()` now resolves correctly from the forwarded token. This is worth stating plainly to judges: **the backend inherits the exact same row-level security model as the frontend**, so there's no separate authorization logic that could be gotten wrong or fall out of sync.

Other details:
- CORS is locked to an explicit allow-list (`ALLOWED_ORIGINS` env var, defaulting to the deployed Vercel URL + local dev ports) — not a wildcard.
- `get_bot()` is called once at **module import time**, not inside the request handler, so the FAISS index and embedding model are built once at process startup. This matters because Render's free tier spins the service down after inactivity — building the index lazily on the first request after a cold start would eat into that request's response time.

### 7.3 `model.py` — the RAG pipeline

**Step 1 — build the retrieval index (once, at startup):**
```python
competitions = supabase.table("competitions").select("*").execute().data
self.vectorstore = FAISS.from_texts(
    texts=[_competition_to_text(row) for row in competitions],
    embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    metadatas=competitions,
)
```
Every row of `public.competitions` is flattened into one string (`name | category | grade_levels | team_or_solo | description`) and embedded locally with a small HuggingFace sentence-transformer, then indexed in an in-memory **FAISS** vector store. If the query fails (e.g. schema not yet applied to that Supabase project), it degrades gracefully — logs a warning and retrieves nothing, rather than crashing the whole service.

**Step 2 — per-request retrieval + generation (`chat(profile)`):**
```python
profile = clean_profile(profile)  # drop id/updated_at/transcript_link/school_profile_link
retrieval_signal = " ".join(profile.get(f) for f in [
    "interests", "intended_majors", "interest_areas",
    "extracurriculars", "competition_history", "competition_team_preference",
] if profile.get(f))
docs = self.vectorstore.similarity_search(retrieval_signal, k=7)
```
The retrieval query is deliberately narrowed to just the fields that predict a good *competition* match — GPA, travel constraints, etc. are excluded here so they don't dilute the similarity search (they're still shown to the LLM in the full profile, just not used to drive retrieval).

**Step 3 — one prompt, structured output:**
The full profile JSON + the 7 retrieved competitions get combined into a single prompt sent to **Groq's `llama-3.3-70b-versatile`** via `langchain_groq.ChatGroq`. The prompt asks the model to analyze 4 aspects (courses & rigor, clubs & involvement, competitions & awards, testing & college prep) and return strict JSON with exactly 6 keys: `testing, clubs, competitions, courses, career, college_prep`. Two grounding instructions matter here:
- *"Never invent a competition that wasn't retrieved"* — this is the RAG grounding step; the model is explicitly told to only recommend from the retrieved context, not hallucinate competition names.
- *"If part of the student's profile is missing, don't guess"* — handles incomplete profiles gracefully instead of fabricating advice from nothing.

**Step 4 — defensive JSON parsing:**
```python
start, end = raw.find("{"), raw.rfind("}")
candidate = raw[start:end + 1] if start != -1 and end != -1 else raw
try:
    return json.loads(candidate)
except json.JSONDecodeError:
    return {"raw": raw}
```
LLMs often wrap JSON output in a markdown code fence or add a sentence of preamble despite being asked for raw JSON, so the code just slices from the first `{` to the last `}` before parsing, and falls back to returning the raw text under a `raw` key if parsing still fails (which is exactly the fallback `advice-client.js` checks for on the frontend: `advice[key] || advice.raw`).

This is a textbook **RAG (Retrieval-Augmented Generation)** pattern: embed a corpus → vector search per-query → stuff results into an LLM prompt → parse structured output — small in scope (one table, one endpoint) but demonstrates the full pattern end to end.

### 7.4 `context_schema.json`

A sample fully-filled-out student profile (fictional "Jordan Lee"), used only for local smoke testing — running `python model.py` directly loads this file and prints the model's advice JSON, without needing a real Supabase row or a browser session.

---

## 8. Homepage radar chart

### 8.1 `home.js` — scoring logic

Computes a 0–100 score per category from raw profile fields, purely client-side (no AI call — deterministic math, cheap to compute on every homepage load):

```js
function countComponent(count, countForFullScore) {
    return clamp((count / countForFullScore) * 100, 0, 100);
}
```
Each score is a weighted blend of sub-components, each capped via a "how many of these = a full score" divisor (e.g. 5 AP courses maxes out the rigor component). The comment in the code is candid about this: *"There's no canonical formula for this — these divisors were picked to feel reasonable rather than derived from anything."* Worth being upfront about that same point if a judge asks how the scoring works — it's a heuristic, not a validated model.

One category is handled differently on purpose: **testing**. SAT/ACT/PSAT are alternatives to each other (most students only take one or two), so a missing score isn't averaged in as a 0 — the function only averages whichever scores were actually reported:
```js
function testingScore(profile) {
    const normalized = [];
    if (profile.sat_score) normalized.push(...);
    if (profile.act_score) normalized.push(...);
    if (profile.psat_score) normalized.push(...);
    if (!normalized.length) return 0;
    return normalized.reduce((sum, v) => sum + v, 0) / normalized.length;
}
```

### 8.2 `radar-chart.js` — rendering

Hand-rolled SVG radar/spider chart (no charting library) — `renderRadarChart(containerId, categories)` takes exactly 5 `{ label, score }` entries and draws:
- `RING_COUNT` (4) background grid rings + 5 axis lines, computed via `pointOnAxis(index, radius)` which places each axis at `360° / AXIS_COUNT` apart, starting straight up (`-90°` offset).
- One filled polygon connecting the 5 (clamped 0–100) scores, plus a dot at each vertex.
- A label + numeric score text at each axis, positioned just outside the data polygon (`MAX_RADIUS + LABEL_OFFSET`), with `text-anchor` chosen per point (`start`/`end`/`middle`) so labels grow away from the chart center rather than overlapping it.

Only shown to logged-in users — `home.js` checks the session on load and on every `supabase.auth.onAuthStateChange`, showing/hiding the `#profile-radar-section` accordingly.

*(This chart originally had a bug where the "Testing" and "Clubs" labels — positioned near the left/right edges where `text-anchor` is `end`/`start` — got clipped by the SVG's own viewBox boundary. Fixed by widening the canvas (`SIZE`) without changing `MAX_RADIUS`, giving labels more edge padding while keeping the plotted chart the same visual size.)*

---

## 9. Deployment

- **Frontend → Vercel.** Static site, no build step (Tailwind via CDN, native ES modules via `<script type="module">`), so Vercel just serves the files directly. `.vercel/project.json` confirms the project link.
- **Backend → Render** (`render.yaml`):
  ```yaml
  services:
    - type: web
      name: high-school-compass-api
      runtime: python
      rootDir: backend
      buildCommand: pip install -r requirements.txt
      startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
      envVars:
        - key: API_KEY        # Groq API key
          sync: false
        - key: SUPABASE_URL
          sync: false
        - key: SUPABASE_ANON_KEY
          sync: false
        - key: ALLOWED_ORIGINS
          value: https://highschoolcompass.vercel.app
  ```
  Secrets (`sync: false`) are set directly in Render's dashboard rather than committed to the repo. `app.py`'s own `if __name__ == "__main__"` block is explicitly local-dev-only — production always runs via `gunicorn`, which is what actually binds Render's `$PORT`.
- **Local dev** uses a `.env` file + `python-dotenv` for the same three variables (`API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`).

---

## 10. Talking points / likely judge questions

- **"Why Supabase instead of your own API + database?"** — RLS pushes authorization down to the database layer itself, so both the frontend and the Python backend can safely query the same tables with the same low-privilege anon key, with zero custom authorization code. Less surface area for security bugs, less code to write during a hackathon.
- **"Why is the AI backend a separate deployment from the frontend?"** — the frontend is a static site (Vercel) with no long-lived server process; running FAISS + a local embeddings model + an LLM call needs a real Python runtime, so it's a small dedicated Flask service on Render.
- **"How does the backend know which user is asking, without you passing a user ID?"** — it doesn't need to. It forwards the user's own Supabase JWT and re-authenticates a client as that user; Postgres RLS (`auth.uid() = id`) does the scoping automatically, identically to how the frontend already queries its own data.
- **"Why FAISS instead of a hosted vector DB?"** — the corpus is small (~300 rows) and read-mostly, so an in-memory index built once at process startup is simpler and free, versus provisioning a separate vector database service for a hackathon-scale corpus.
- **"How do you keep the LLM from making things up?"** — the prompt explicitly restricts competition recommendations to only what was retrieved from the vector search (RAG grounding), and instructs the model not to guess when profile data is missing.
- **"Why arrays instead of normalized child tables for things like `clubs` or `honors_awards`?"** — the form collects each as a simple "one per line" textarea; a full relational schema with join tables would add real complexity for no benefit at this data scale, so Postgres `text[]` columns were used instead.
