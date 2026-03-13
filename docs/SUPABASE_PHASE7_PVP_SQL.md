# Supabase Phase 7 — Global PvP & Auto-Arena SQL

Run these in the Supabase SQL Editor (Dashboard > SQL Editor > New Query).

## Arena Registry

```sql
-- Arena registration: pets that are "in the arena" for matchmaking
CREATE TABLE public.arena_registry (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    pet_id uuid REFERENCES public.pets(id) ON DELETE CASCADE UNIQUE,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    registered_at timestamptz DEFAULT now(),
    last_fought_at timestamptz,
    arena_wins int DEFAULT 0,
    arena_losses int DEFAULT 0,
    arena_rating int DEFAULT 1000  -- ELO-like rating
);

-- Index for matchmaking queries
CREATE INDEX idx_arena_registry_rating ON public.arena_registry(arena_rating);
CREATE INDEX idx_arena_registry_user ON public.arena_registry(user_id);
CREATE INDEX idx_arena_registry_last_fought ON public.arena_registry(last_fought_at);
```

## Arena Fights

```sql
-- Arena fight log
CREATE TABLE public.arena_fights (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    pet1_id uuid REFERENCES public.pets(id) ON DELETE SET NULL,
    pet2_id uuid REFERENCES public.pets(id) ON DELETE SET NULL,
    pet1_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
    pet2_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
    winner_id uuid REFERENCES public.pets(id) ON DELETE SET NULL,
    ticks int,
    rating_change int,  -- for winner (loser gets negative)
    fight_type text DEFAULT 'async',  -- 'async', 'auto'
    created_at timestamptz DEFAULT now()
);

-- Index for fight history queries
CREATE INDEX idx_arena_fights_pet1 ON public.arena_fights(pet1_user_id);
CREATE INDEX idx_arena_fights_pet2 ON public.arena_fights(pet2_user_id);
CREATE INDEX idx_arena_fights_created ON public.arena_fights(created_at DESC);
```

## Row Level Security

```sql
ALTER TABLE public.arena_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.arena_fights ENABLE ROW LEVEL SECURITY;

-- Anyone can read the registry (for matchmaking)
CREATE POLICY "Anyone can read registry"
    ON public.arena_registry FOR SELECT USING (true);

-- Users can manage their own registry entries
CREATE POLICY "Users manage own registry"
    ON public.arena_registry FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users update own registry"
    ON public.arena_registry FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users delete own registry"
    ON public.arena_registry FOR DELETE USING (auth.uid() = user_id);

-- Anyone can read arena fights
CREATE POLICY "Anyone can read arena fights"
    ON public.arena_fights FOR SELECT USING (true);

-- Authenticated users can insert arena fights
CREATE POLICY "Authenticated users insert arena fights"
    ON public.arena_fights FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
```

## Notes

- `arena_rating` starts at 1000 (standard ELO baseline)
- Rating change: base +/-25, adjusted by rating difference
- `fight_type`: `'async'` = player-initiated, `'auto'` = auto-arena system
- `last_fought_at` used for auto-arena cooldown (6 hours)
- Pets must be alive and level 3+ to register
