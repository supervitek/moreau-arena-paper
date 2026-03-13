# Supabase Phase 6C — Scar Garden (Breeding & Genetic Inheritance)

## Eggs Table

```sql
CREATE TABLE public.eggs (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id),
    parent_pet_id uuid REFERENCES public.pets(id),
    donor_pet_id uuid REFERENCES public.pets(id),
    species text NOT NULL,
    inherited_stats jsonb NOT NULL DEFAULT '{}',
    inherited_mutations jsonb NOT NULL DEFAULT '{}',
    incubation_start timestamptz DEFAULT now(),
    incubation_end timestamptz,
    hatched boolean DEFAULT false,
    hatched_pet_id uuid REFERENCES public.pets(id),
    created_at timestamptz DEFAULT now()
);

ALTER TABLE public.eggs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own eggs"
    ON public.eggs
    FOR ALL
    USING (auth.uid() = user_id);

CREATE INDEX idx_eggs_user_id ON public.eggs(user_id);
CREATE INDEX idx_eggs_hatched ON public.eggs(hatched);
```

## Pets Table Additions

```sql
-- Add breeding fields to existing pets table
ALTER TABLE public.pets ADD COLUMN IF NOT EXISTS breed_count integer DEFAULT 0;
ALTER TABLE public.pets ADD COLUMN IF NOT EXISTS parent_id uuid REFERENCES public.pets(id);
ALTER TABLE public.pets ADD COLUMN IF NOT EXISTS donor_id uuid REFERENCES public.pets(id);
ALTER TABLE public.pets ADD COLUMN IF NOT EXISTS generation integer DEFAULT 0;
```

## Notes

- `parent_pet_id`: the living pet that breeds (gets a scar)
- `donor_pet_id`: the dead pet whose genetic memory is used
- `incubation_end`: set to `incubation_start + interval '12 hours'`
- `inherited_stats`: computed average of parent + donor base_stats with variance
- `inherited_mutations`: subset of donor's lab_mutations that passed inheritance roll
- `hatched_pet_id`: filled when egg hatches and new pet is created
- `breed_count` on pets: tracks how many times a pet has bred (max 5)
- `parent_id` / `donor_id` on pets: for lineage tracking on hatched pets
- `generation`: 0 for original pets, parent.generation + 1 for bred pets
