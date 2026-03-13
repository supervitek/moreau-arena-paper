# Supabase Phase 6B — Arena Oaths

Paste this SQL into the Supabase SQL Editor.

```sql
-- ═══════════════════════════════════════════════
--  Phase 6B: Arena Oaths — Social Rivalry Covenants
-- ═══════════════════════════════════════════════

CREATE TABLE public.oaths (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    challenger_pet_id uuid REFERENCES public.pets(id),
    target_pet_id uuid REFERENCES public.pets(id),
    challenger_user_id uuid REFERENCES auth.users(id),
    target_user_id uuid REFERENCES auth.users(id),
    oath_level int DEFAULT 1,          -- 1-5
    challenger_wins int DEFAULT 0,
    target_wins int DEFAULT 0,
    total_fights int DEFAULT 0,
    last_fight_at timestamptz,
    status text DEFAULT 'active',      -- active, broken, completed
    winner_pet_id uuid REFERENCES public.pets(id),
    created_at timestamptz DEFAULT now()
);

-- Index for fast lookups
CREATE INDEX idx_oaths_challenger ON public.oaths(challenger_user_id);
CREATE INDEX idx_oaths_target ON public.oaths(target_user_id);
CREATE INDEX idx_oaths_status ON public.oaths(status);
CREATE INDEX idx_oaths_created ON public.oaths(created_at DESC);

-- RLS
ALTER TABLE public.oaths ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read oaths"
    ON public.oaths FOR SELECT USING (true);

CREATE POLICY "Users can create oaths"
    ON public.oaths FOR INSERT
    WITH CHECK (auth.uid() = challenger_user_id);

CREATE POLICY "Participants can update oaths"
    ON public.oaths FOR UPDATE
    USING (auth.uid() IN (challenger_user_id, target_user_id));
```
