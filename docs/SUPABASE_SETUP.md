# Supabase Setup — The Island (Side B)

Complete setup instructions for Supabase auth, database, and client integration.

---

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to your Render deployment (e.g., `us-east-1`)
3. Set a strong database password — save it somewhere secure
4. Once created, go to **Settings > API** and copy:
   - **Project URL** (e.g., `https://xyzcompany.supabase.co`)
   - **anon (public) key** — safe to expose in browser
   - **service_role key** — server-side only, never expose in frontend
5. Add to Render environment variables:
   ```
   SUPABASE_URL=https://xyzcompany.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOi...
   ```

---

## 2. SQL Schema

Copy-paste the entire block below into the **Supabase SQL Editor** (Database > SQL Editor > New query) and run it.

```sql
-- ============================================================
-- THE ISLAND — FULL SCHEMA
-- Run this in Supabase SQL Editor as a single transaction
-- ============================================================

-- ==================== TABLES ====================

-- users: extends Supabase auth.users
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  avatar_url text,
  is_premium boolean not null default false,
  created_at timestamptz not null default now()
);

-- pets: core game entity
create table public.pets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  name text not null check (char_length(name) <= 20),
  animal text not null,
  base_stats jsonb not null default '{"hp":5,"atk":5,"spd":5,"wil":5}'::jsonb,
  level int not null default 1 check (level between 1 and 10),
  xp int not null default 0,
  mutations jsonb not null default '[]'::jsonb,
  lab_mutations jsonb not null default '{}'::jsonb,
  side_effects jsonb not null default '[]'::jsonb,
  instability int not null default 0 check (instability between 0 and 100),
  scars int not null default 0 check (scars between 0 and 5),
  mercy_used boolean not null default false,
  mood text default 'neutral',
  is_alive boolean not null default true,
  fights_won int not null default 0,
  fights_lost int not null default 0,
  created_at timestamptz not null default now(),
  died_at timestamptz
);

-- fights: combat history
create table public.fights (
  id uuid primary key default gen_random_uuid(),
  pet1_id uuid not null references public.pets(id) on delete cascade,
  pet2_id uuid references public.pets(id) on delete set null,
  winner_id uuid references public.pets(id) on delete set null,
  ticks int not null,
  fight_type text not null check (fight_type in ('training', 'sparring', 'ranked', 'auto')),
  xp_gained int not null default 0,
  timestamp timestamptz not null default now()
);

-- mutations_codex: discovered mutations per user
create table public.mutations_codex (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  mutation_id text not null,
  discovered_at timestamptz not null default now(),
  unique (user_id, mutation_id)
);

-- ==================== INDEXES ====================

create index idx_pets_user_id on public.pets(user_id);
create index idx_pets_is_alive on public.pets(is_alive);
create index idx_fights_pet1_id on public.fights(pet1_id);
create index idx_fights_pet2_id on public.fights(pet2_id);
create index idx_fights_winner_id on public.fights(winner_id);
create index idx_fights_timestamp on public.fights(timestamp desc);
create index idx_mutations_codex_user_id on public.mutations_codex(user_id);

-- ==================== ROW LEVEL SECURITY ====================

alter table public.users enable row level security;
alter table public.pets enable row level security;
alter table public.fights enable row level security;
alter table public.mutations_codex enable row level security;

-- users: read own profile, update own profile
create policy "users_select_own"
  on public.users for select
  using (auth.uid() = id);

create policy "users_update_own"
  on public.users for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- pets: anyone can read (public profiles), owner can insert/update/delete
create policy "pets_select_all"
  on public.pets for select
  using (true);

create policy "pets_insert_own"
  on public.pets for insert
  with check (auth.uid() = user_id);

create policy "pets_update_own"
  on public.pets for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "pets_delete_own"
  on public.pets for delete
  using (auth.uid() = user_id);

-- fights: anyone can read, participants can insert
create policy "fights_select_all"
  on public.fights for select
  using (true);

create policy "fights_insert_own"
  on public.fights for insert
  with check (
    auth.uid() = (select user_id from public.pets where id = pet1_id)
  );

-- mutations_codex: read/write own only
create policy "codex_select_own"
  on public.mutations_codex for select
  using (auth.uid() = user_id);

create policy "codex_insert_own"
  on public.mutations_codex for insert
  with check (auth.uid() = user_id);

create policy "codex_delete_own"
  on public.mutations_codex for delete
  using (auth.uid() = user_id);

-- ==================== TRIGGER: AUTO-CREATE USER PROFILE ====================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.users (id, email, display_name, avatar_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data->>'avatar_url', new.raw_user_meta_data->>'picture')
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

---

## 3. Supabase JS Client Setup

Add to any Island HTML page (before your app scripts):

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  // These are safe to expose — RLS protects the data
  const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOi...YOUR_ANON_KEY';
  const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
</script>
```

Usage examples:

```javascript
// Get current user
const { data: { user } } = await sb.auth.getUser();

// Fetch user's pets
const { data: pets } = await sb.from('pets')
  .select('*')
  .eq('user_id', user.id)
  .eq('is_alive', true);

// Insert a new pet
const { data: pet, error } = await sb.from('pets').insert({
  user_id: user.id,
  name: 'Shadow',
  animal: 'fox',
  base_stats: { hp: 5, atk: 7, spd: 5, wil: 3 }
}).select().single();

// Record a fight
await sb.from('fights').insert({
  pet1_id: myPet.id,
  pet2_id: opponentPet.id,
  winner_id: myPet.id,
  ticks: 42,
  fight_type: 'training',
  xp_gained: 30
});
```

---

## 4. Auth Setup

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI:
   ```
   https://YOUR_PROJECT.supabase.co/auth/v1/callback
   ```
4. Copy Client ID and Client Secret
5. In Supabase dashboard: **Authentication > Providers > Google**
   - Enable Google
   - Paste Client ID and Client Secret
   - Save

### Email/Password

1. In Supabase dashboard: **Authentication > Providers > Email**
   - Enable Email provider (enabled by default)
   - Optionally disable "Confirm email" for development
   - Save

### Redirect URLs

In Supabase dashboard: **Authentication > URL Configuration**:
- Site URL: `https://moreau-arena.onrender.com/island/home`
- Redirect URLs (add all):
  ```
  https://moreau-arena.onrender.com/island/**
  http://localhost:8000/island/**
  ```

### Login Code

```javascript
// Google OAuth
async function loginWithGoogle() {
  const { error } = await sb.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin + '/island/home'
    }
  });
  if (error) console.error('Login error:', error.message);
}

// Email/Password sign up
async function signUp(email, password) {
  const { data, error } = await sb.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: window.location.origin + '/island/home'
    }
  });
  if (error) console.error('Signup error:', error.message);
  return data;
}

// Email/Password sign in
async function signIn(email, password) {
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) console.error('Login error:', error.message);
  return data;
}

// Sign out
async function signOut() {
  await sb.auth.signOut();
  window.location.href = '/island';
}

// Auth state listener — put this on every Island page
sb.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT') {
    window.location.href = '/island';
  }
});
```

---

## 5. Migration Script (localStorage to Supabase)

Run this once on first login. Show a prompt: "Import existing pets?"

```javascript
async function migrateLocalStorageToSupabase(userId) {
  // ---- Pets ----
  const localPets = JSON.parse(localStorage.getItem('moreau_pets') || '[]');
  if (localPets.length === 0) {
    console.log('No local pets to migrate.');
    return { pets: 0, codex: 0, fights: 0 };
  }

  const petIdMap = {}; // old index -> new uuid

  for (const pet of localPets) {
    const { data, error } = await sb.from('pets').insert({
      user_id: userId,
      name: pet.name || 'Unnamed',
      animal: pet.animal || 'fox',
      base_stats: pet.base_stats || pet.stats || { hp: 5, atk: 5, spd: 5, wil: 5 },
      level: pet.level || 1,
      xp: pet.xp || 0,
      mutations: pet.mutations || [],
      lab_mutations: pet.lab_mutations || {},
      side_effects: pet.side_effects || [],
      instability: pet.instability || 0,
      scars: pet.scars || 0,
      mercy_used: pet.mercy_used || false,
      mood: pet.mood || 'neutral',
      is_alive: !pet.deceased,
      fights_won: (pet.fights || []).filter(f => f.result === 'win').length,
      fights_lost: (pet.fights || []).filter(f => f.result === 'loss').length,
      died_at: pet.deceased ? (pet.died_at || new Date().toISOString()) : null
    }).select().single();

    if (error) {
      console.error('Failed to migrate pet:', pet.name, error);
      continue;
    }
    petIdMap[localPets.indexOf(pet)] = data.id;
  }

  // ---- Mutations Codex ----
  const localCodex = JSON.parse(localStorage.getItem('moreau_codex') || '[]');
  let codexCount = 0;
  for (const mutationId of localCodex) {
    const { error } = await sb.from('mutations_codex').insert({
      user_id: userId,
      mutation_id: mutationId
    });
    if (!error) codexCount++;
  }

  // ---- Fight History ----
  const localFights = JSON.parse(localStorage.getItem('moreau_pit_history') || '[]');
  let fightCount = 0;
  for (const fight of localFights) {
    // Map local fight records to DB format
    // Local fights may not have proper pet UUIDs, so we do best-effort
    const pet1Id = petIdMap[fight.pet1_index ?? 0];
    if (!pet1Id) continue;

    const { error } = await sb.from('fights').insert({
      pet1_id: pet1Id,
      pet2_id: fight.pet2_index != null ? (petIdMap[fight.pet2_index] || null) : null,
      winner_id: fight.winner_index != null ? (petIdMap[fight.winner_index] || null) : null,
      ticks: fight.ticks || 0,
      fight_type: fight.type || 'training',
      xp_gained: fight.xp || 0
    });
    if (!error) fightCount++;
  }

  // ---- Clear localStorage ----
  localStorage.removeItem('moreau_pets');
  localStorage.removeItem('moreau_active_pet');
  localStorage.removeItem('moreau_pet'); // legacy key
  localStorage.removeItem('moreau_codex');
  localStorage.removeItem('moreau_pit_history');

  const result = { pets: Object.keys(petIdMap).length, codex: codexCount, fights: fightCount };
  console.log('Migration complete:', result);
  return result;
}

// Usage: call after first login
// const user = (await sb.auth.getUser()).data.user;
// const result = await migrateLocalStorageToSupabase(user.id);
// alert(`Imported ${result.pets} pets, ${result.codex} codex entries, ${result.fights} fights!`);
```

---

## 6. Quick Reference

| What | Where |
|------|-------|
| Supabase Dashboard | `https://supabase.com/dashboard/project/YOUR_PROJECT_ID` |
| SQL Editor | Dashboard > Database > SQL Editor |
| Auth settings | Dashboard > Authentication > Providers |
| API keys | Dashboard > Settings > API |
| Table editor | Dashboard > Table Editor |
| Logs | Dashboard > Database > Logs |
| Free tier limits | 50K MAU, 500MB DB, 1GB file storage, 2GB bandwidth |
