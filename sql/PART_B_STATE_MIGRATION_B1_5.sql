-- ============================================================
-- PART B STATE MIGRATION — B1.5
-- Minimal server-side persistence for ecological benchmark runs
-- ============================================================

create table if not exists public.part_b_runs (
  id uuid primary key default gen_random_uuid(),
  operator_id uuid references public.users(id) on delete set null,
  season_id text not null,
  run_class text not null check (run_class in ('manual', 'operator-assisted', 'agent-only')),
  status text not null default 'active',
  subject_pet_id text,
  subject_pet_name text,
  subject_pet_animal text,
  active_zone text not null default 'arena',
  priority_profile text not null default 'balanced',
  risk_appetite text not null default 'measured',
  care_threshold int not null default 60,
  combat_bias int not null default 50,
  expedition_bias int not null default 50,
  world_tick int not null default 0,
  state_revision int not null default 0,
  inference_budget_remaining int not null default 4,
  inference_budget_daily int not null default 4,
  billing_mode text not null default 'hybrid',
  world_access_active boolean not null default true,
  house_agent_enabled boolean not null default false,
  house_agent_provider text not null default 'anthropic',
  house_agent_model text not null default 'claude-haiku-4-5-20251001',
  house_agent_last_plan jsonb not null default '{}'::jsonb,
  autopause_reason text,
  observation_version text not null default 'B1',
  action_version text not null default 'B1',
  scoring_version text not null default 'B1',
  conflict_policy text not null default 'operator_wins_before_execution',
  queue_capacity int not null default 6,
  queue_state jsonb not null default '[]'::jsonb,
  state_projection jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  last_event_at timestamptz,
  last_actor_type text,
  last_action_verb text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.part_b_events (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.part_b_runs(id) on delete cascade,
  sequence int not null,
  world_tick int not null default 0,
  actor_type text not null check (actor_type in ('manual', 'operator', 'agent', 'system')),
  event_type text not null,
  action_verb text check (
    action_verb is null or action_verb in (
      'HOLD', 'CARE', 'REST', 'TRAIN',
      'ENTER_ARENA', 'ENTER_CAVE', 'EXTRACT', 'MUTATE'
    )
  ),
  zone text,
  expected_state_revision int,
  applied_state_revision int,
  conflict_status text not null default 'none' check (
    conflict_status in ('none', 'stale_rejected', 'operator_preempted', 'manual_freeze')
  ),
  accepted boolean not null default true,
  observation jsonb not null default '{}'::jsonb,
  outcome jsonb not null default '{}'::jsonb,
  details jsonb not null default '{}'::jsonb,
  state_after jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (run_id, sequence)
);

create index if not exists idx_part_b_runs_operator on public.part_b_runs(operator_id);
create index if not exists idx_part_b_runs_updated_at on public.part_b_runs(updated_at desc);
create index if not exists idx_part_b_events_run_id on public.part_b_events(run_id);
create index if not exists idx_part_b_events_run_sequence on public.part_b_events(run_id, sequence);
create index if not exists idx_part_b_events_created_at on public.part_b_events(created_at desc);

alter table public.part_b_runs enable row level security;
alter table public.part_b_events enable row level security;

drop policy if exists "part_b_runs_select_own" on public.part_b_runs;
create policy "part_b_runs_select_own"
  on public.part_b_runs for select
  using (auth.uid() = operator_id);

drop policy if exists "part_b_runs_insert_own" on public.part_b_runs;
create policy "part_b_runs_insert_own"
  on public.part_b_runs for insert
  with check (auth.uid() = operator_id);

drop policy if exists "part_b_runs_update_own" on public.part_b_runs;
create policy "part_b_runs_update_own"
  on public.part_b_runs for update
  using (auth.uid() = operator_id)
  with check (auth.uid() = operator_id);

drop policy if exists "part_b_events_select_own" on public.part_b_events;
create policy "part_b_events_select_own"
  on public.part_b_events for select
  using (
    exists (
      select 1 from public.part_b_runs r
      where r.id = part_b_events.run_id and r.operator_id = auth.uid()
    )
  );

drop policy if exists "part_b_events_insert_own" on public.part_b_events;
create policy "part_b_events_insert_own"
  on public.part_b_events for insert
  with check (
    exists (
      select 1 from public.part_b_runs r
      where r.id = part_b_events.run_id and r.operator_id = auth.uid()
    )
  );

create or replace function public.touch_part_b_run_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_part_b_runs_updated_at on public.part_b_runs;
create trigger trg_part_b_runs_updated_at
before update on public.part_b_runs
for each row
execute function public.touch_part_b_run_updated_at();
