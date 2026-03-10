# TODO: Forbidden Laboratory Major Upgrade

## Creative Brief
Transform the Forbidden Laboratory from a basic gacha roller into a full immersive experience with visual mutation trees, experiment history, death risk, and atmospheric storytelling.

## Phase 1: Core Mechanics

### 1.1 Death Risk System (INSTABILITY)
- [ ] Track `pet.instability` (0-100%) — increases with each experiment
- [ ] Base instability gain per roll: Stable +5%, Volatile +15%, Forbidden +25%
- [ ] Existing mutations add to instability: each filled slot adds +10% baseline
- [ ] At roll time: if `Math.random() * 100 < instability`, experiment "fails catastrophically"
- [ ] On death: pet gets `status: "deceased"` flag, can't fight/train anymore
- [ ] BUT: deceased pets remain in The Kennels as a memorial (greyed out, "In Memoriam")
- [ ] "Stabilize" button — costs nothing but reduces instability by 20% and requires waiting (cooldown)
- [ ] Visual: instability meter below pet info, color shifts green→yellow→orange→red as it rises

### 1.2 Experiment Log
- [ ] Track `pet.lab_log` — array of all experiments attempted
- [ ] Each entry: `{timestamp, tier, mutation_name, success, side_effect, instability_at_time}`
- [ ] Display as scrollable "Research Notes" styled like handwritten lab journal entries
- [ ] Failed experiments (discarded) show as crossed-out entries
- [ ] Deaths show as final entry with red "SUBJECT LOST" stamp

### 1.3 Visual Mutation Map
- [ ] SVG/CSS tree visualization of ALL 49 mutations
- [ ] Three branches (Stable/Volatile/Forbidden), spreading like a neural network
- [ ] Discovered mutations: fully lit, clickable for details
- [ ] Undiscovered: dark silhouette with "???" — shows only tier color glow
- [ ] Currently equipped: pulsing gold border
- [ ] Connections between mutations that form synergies: dotted lines

## Phase 2: Atmosphere & UX

### 2.1 Enhanced Entry Sequence
- [ ] Add ambient sound description (no actual audio — just visual "sound" effects)
- [ ] Flickering fluorescent light CSS effect on the whole lab
- [ ] Warning messages that escalate with instability level

### 2.2 Instability Visual Effects
- [ ] Screen shake on high instability rolls
- [ ] Glitch/static overlay when instability > 60%
- [ ] Pet emoji distortion (CSS filter) at high instability
- [ ] "DANGER" warnings that flash before high-instability rolls

### 2.3 Death Sequence
- [ ] Full-screen dramatic death animation
- [ ] Flatline EKG line across screen
- [ ] "Dr. Moreau's notes: Subject [name] did not survive procedure..."
- [ ] Auto-save to memorial state
- [ ] "Return to The Kennels" button (not "try again" — they're gone)

## Phase 3: Discovery & Collection

### 3.1 Improved Codex
- [ ] Replace current grid with visual mutation map (Phase 1.3)
- [ ] Add filtering: by tier, by discovered/undiscovered, by equipped
- [ ] Show synergy hints for mutations that have been discovered
- [ ] Track total experiments performed, total successes, total deaths

### 3.2 Statistics Dashboard
- [ ] "Dr. Moreau's Research Summary" panel
- [ ] Total experiments across all pets
- [ ] Rarest mutations discovered
- [ ] Death count (with a grim counter)
- [ ] "Near-miss" counter (instability was >80% but survived)

## Implementation Notes
- All data stored in localStorage, extending existing pet schema
- No backend changes needed
- Must work with multi-pet system (each pet has own instability/log)
- Don't touch: config.json, tournament data, run files, analysis code
