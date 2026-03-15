// ══════════════════════════════════════════════════════════════════
//  Caretaker Engine — AI Zoo Manager for Moreau Island
//  Core systems: Needs, Decay, Actions, Diary, Trust, Mercy,
//                Overnight Training, Feeding Ledger (Aleph Lore)
// ══════════════════════════════════════════════════════════════════

(function(window) {
    'use strict';

    // ── Storage keys ──────────────────────────────────────────────

    var PETS_KEY           = 'moreau_pets';
    var ACTIVE_KEY         = 'moreau_active_pet';
    var LOG_KEY            = 'moreau_caretaker_log';
    var DIARY_KEY          = 'moreau_caretaker_diary';
    var TRUST_KEY          = 'moreau_caretaker_trust';
    var OVERNIGHT_KEY      = 'moreau_overnight';
    var PREMIUM_KEY        = 'moreau_caretaker_premium';
    var MERCY_KEY          = 'moreau_mercy_pending';
    var STREAK_KEY         = 'moreau_caretaker_streak';
    var LEDGER_KEY         = 'moreau_feeding_ledger';

    var MAX_LOG            = 100;
    var MAX_DIARY          = 200;
    var MAX_PETS           = 6;
    var NEEDS_CEIL         = 100;
    var NEEDS_FLOOR        = 0;
    var TRUST_MAX          = 10;
    var TRUST_MIN          = 0;
    var TRUST_DEFAULT      = 5;
    var MERCY_WINDOW_MS    = 21600000;   // 6 hours
    var OVERNIGHT_MIN_MS   = 14400000;   // 4 hours
    var REST_DURATION_MS   = 3600000;    // 1 hour
    var LEDGER_TOTAL_PAGES = 12;
    var STREAK_DAYS_PER_PAGE = 7;

    // ── Motivational quotes per animal ────────────────────────────

    var ANIMAL_QUOTES = {
        fox: [
            "Every dodge is a story you get to tell tomorrow.",
            "Cunning isn't cruelty — it's survival with style.",
            "The cleverest fox knows when to rest in the den."
        ],
        bear: [
            "The mountain doesn't hurry. Neither should you.",
            "Strength means knowing when not to use it.",
            "Even the largest bear sleeps through the long winter."
        ],
        tiger: [
            "Rest now. The hunt begins again when you're ready.",
            "A single strike, perfectly timed, beats a hundred wild swings.",
            "The jungle remembers every patient step you've taken."
        ],
        wolf: [
            "The pack is only as strong as its weakest moment of rest.",
            "Howl if you need to. The sky won't judge you.",
            "Lone wolves survive. But wolf packs thrive."
        ],
        eagle: [
            "You don't need to fly highest. Just fly truest.",
            "The storm lifts those who spread their wings into it.",
            "Every descent is just the beginning of the next ascent."
        ],
        shark: [
            "Keep moving. Stillness is for things that have given up.",
            "The deep is dark, but it's yours.",
            "Teeth are only impressive when the will behind them holds."
        ],
        snake: [
            "Shed what doesn't serve you. Growth demands it.",
            "Patience coiled is power stored.",
            "Even venom can be medicine in the right dose."
        ],
        cat: [
            "Nine lives means nine chances to get it right.",
            "Land on your feet. That's not luck — that's practice.",
            "The softest paw hides the sharpest claw."
        ],
        rabbit: [
            "Speed isn't cowardice. It's intelligence in motion.",
            "They underestimate you. Good. Let them.",
            "Quick feet, quicker mind — that's the rabbit way."
        ],
        owl: [
            "See what others miss. That's your gift.",
            "The night is not your enemy. It's your domain.",
            "Wisdom isn't knowing everything. It's knowing what matters."
        ],
        crow: [
            "Collect the shiny things — memories, victories, scars.",
            "Adapt. That's not weakness. That's evolution.",
            "The smartest bird in the arena is the one that remembers."
        ],
        deer: [
            "Grace under pressure is the hardest stat to train.",
            "Your antlers grew back stronger every time. So will you.",
            "Fleet of foot, steady of heart."
        ],
        lizard: [
            "Cold blood, warm heart. Surprise them.",
            "Regeneration isn't a mutation — it's your birthright.",
            "Sun-warmed and ready. That's the lizard creed."
        ],
        monkey: [
            "Chaos is just strategy that hasn't been explained yet.",
            "Swing first, calculate second — wait, no, both at once.",
            "The arena is your playground. Treat it that way."
        ]
    };

    var GENERIC_QUOTES = [
        "One more round. You can do this.",
        "Every champion was once a contender who refused to give up.",
        "Pain is temporary. A good win-rate is forever.",
        "Rest, recover, return. The cycle of all fighters.",
        "Your next fight could be the one that changes everything.",
        "The arena rewards those who show up.",
        "Scars are just experience points the body keeps.",
        "You're not behind. You're building momentum.",
        "Small wins compound. Trust the process.",
        "The Caretaker believes in you. That's gotta count for something."
    ];

    // ── Advice templates (30+) ────────────────────────────────────

    /**
     * Each template: { id, condition(pet), text(pet) }
     * condition returns true if relevant, text returns the advice string.
     */
    var ADVICE_POOL = [
        // Hunger
        { id: 'h1', condition: function(p) { return n(p).hunger < 20; },
          text: function(p) { return 'Feed ' + p.name + ' before the next fight or lose HP permanently.'; } },
        { id: 'h2', condition: function(p) { return n(p).hunger < 50 && n(p).hunger >= 20; },
          text: function(p) { return p.name + "'s hunger is at " + n(p).hunger + '%. A meal would go a long way.'; } },
        { id: 'h3', condition: function(p) { return n(p).hunger >= 80; },
          text: function(p) { return p.name + ' is well-fed. Good time for training.'; } },

        // Energy
        { id: 'e1', condition: function(p) { return n(p).energy < 20; },
          text: function(p) { return 'Energy at ' + n(p).energy + '%. Rest for an hour before training.'; } },
        { id: 'e2', condition: function(p) { return n(p).energy >= 80; },
          text: function(p) { return 'Energy is high (' + n(p).energy + '%). Perfect for a training session.'; } },
        { id: 'e3', condition: function(p) { var r = p.resting_until; return r && r > Date.now(); },
          text: function(p) { var mins = Math.ceil((p.resting_until - Date.now()) / 60000); return p.name + ' is resting. ' + mins + ' minutes left.'; } },

        // Health
        { id: 'hp1', condition: function(p) { return n(p).health < 30; },
          text: function(p) { return 'Health critical at ' + n(p).health + '%. Heal immediately.'; } },
        { id: 'hp2', condition: function(p) { return n(p).health < 60 && n(p).health >= 30; },
          text: function(p) { return 'Health is below 60%. Consider healing before any fights.'; } },

        // Morale
        { id: 'm1', condition: function(p) { return n(p).morale < 30; },
          text: function(p) { return 'Morale dropping. Win a fight or visit the Caretaker to motivate.'; } },
        { id: 'm2', condition: function(p) { return n(p).morale >= 90; },
          text: function(p) { return p.name + ' is in high spirits! Morale bonus in effect.'; } },

        // Level / XP
        { id: 'l1', condition: function(p) { return p.level < 10; },
          text: function(p) { var needed = xpForLevel(p.level + 1) - (p.xp || 0); return 'Close to level ' + (p.level + 1) + '! ' + Math.max(0, needed) + ' XP to go.'; } },
        { id: 'l2', condition: function(p) { return p.level >= 10; },
          text: function() { return 'Max level reached. Focus on mutations and strategy.'; } },

        // Mutations
        { id: 'mut1', condition: function(p) { var lm = p.lab_mutations || {}; return p.level >= 3 && !lm.L3; },
          text: function() { return 'L3 mutation slot is empty. Visit the Lab!'; } },
        { id: 'mut2', condition: function(p) { var lm = p.lab_mutations || {}; return p.level >= 6 && !lm.L6; },
          text: function() { return 'L6 mutation slot is empty. The Lab awaits.'; } },
        { id: 'mut3', condition: function(p) { var lm = p.lab_mutations || {}; return p.level >= 9 && !lm.L9; },
          text: function() { return 'L9 mutation slot is empty. Ultimate mutations are available!'; } },
        { id: 'mut4', condition: function(p) { var lm = p.lab_mutations || {}; var c = 0; if (lm.L3) c++; if (lm.L6) c++; if (lm.L9) c++; return c === 3; },
          text: function() { return 'All mutation slots filled. Consider synergies between them.'; } },

        // Corruption
        { id: 'c1', condition: function(p) { return (p.corruption || 0) > 60; },
          text: function(p) { return 'Corruption at ' + (p.corruption || 0) + '%. One more corrupted mutation = Tainted.'; } },
        { id: 'c2', condition: function(p) { return (p.corruption || 0) > 30 && (p.corruption || 0) <= 60; },
          text: function(p) { return 'Corruption at ' + (p.corruption || 0) + '%. Proceed carefully with the Lab.'; } },

        // Instability
        { id: 'i1', condition: function(p) { return (p.instability || 0) > 70; },
          text: function(p) { return 'Instability at ' + (p.instability || 0) + '%. The Forbidden Lab is risky right now.'; } },
        { id: 'i2', condition: function(p) { return (p.instability || 0) > 40 && (p.instability || 0) <= 70; },
          text: function(p) { return 'Instability at ' + (p.instability || 0) + '%. Side effects more likely in the Lab.'; } },

        // Fights / Win rate
        { id: 'f1', condition: function(p) { return (p.fights || []).length >= 5; },
          text: function(p) { var recent = (p.fights || []).slice(-10); var wins = 0; recent.forEach(function(f) { if (f.result === 'win') wins++; }); var rate = Math.round((wins / recent.length) * 100); return 'Win rate in recent fights: ' + rate + '%. ' + (rate < 50 ? 'Try harder opponents for more XP.' : 'Keep it up!'); } },
        { id: 'f2', condition: function(p) { return (p.fights || []).length === 0; },
          text: function(p) { return p.name + ' has never fought. Time for a first match!'; } },

        // Heal debt
        { id: 'hd1', condition: function(p) { return (p.heal_debt || 0) > 0; },
          text: function(p) { return 'Heal debt: ' + p.heal_debt + ' fights with reduced stats. Fight carefully.'; } },

        // General strategy
        { id: 'g1', condition: function(p) { var bs = p.base_stats || {}; return (bs.atk || 0) > (bs.spd || 0) * 1.5; },
          text: function() { return 'High ATK build detected. Speed might be the weak link in fast matchups.'; } },
        { id: 'g2', condition: function(p) { var bs = p.base_stats || {}; return (bs.spd || 0) > (bs.atk || 0) * 1.5; },
          text: function() { return 'Speed build. Great for dodging, but you may need ATK for tanky opponents.'; } },
        { id: 'g3', condition: function(p) { var bs = p.base_stats || {}; return (bs.wil || 0) >= 8; },
          text: function() { return 'High WIL build. Excellent for resisting Lab side effects and morale drain.'; } },
        { id: 'g4', condition: function(p) { var bs = p.base_stats || {}; return (bs.hp || 0) <= 3; },
          text: function(p) { return p.name + "'s HP stat is dangerously low. Avoid starvation at all costs."; } },

        // Deceased / scars
        { id: 's1', condition: function(p) { return (p.scars || []).length > 0; },
          text: function(p) { return p.name + ' carries ' + p.scars.length + ' scar(s). Each one a lesson.'; } },

        // Abomination
        { id: 'ab1', condition: function(p) { return p.abomination === true; },
          text: function(p) { return p.name + ' is marked as an Abomination. Three debts paid in blood.'; } },

        // Overnight
        { id: 'on1', condition: function() { try { var o = JSON.parse(localStorage.getItem(OVERNIGHT_KEY)); return o && !o.completed; } catch(e) { return false; } },
          text: function() { return 'Overnight training in progress. Check back after 4 hours.'; } },

        // Resting
        { id: 'r1', condition: function(p) { return p.resting_until && p.resting_until > Date.now(); },
          text: function(p) { return p.name + ' is resting. Energy will be restored when the timer completes.'; } }
    ];

    // ── Helpers ───────────────────────────────────────────────────

    /** Shortcut: get needs object, never null */
    function n(pet) {
        return pet && pet.needs ? pet.needs : { hunger: 100, health: 100, morale: 100, energy: 100 };
    }

    /** XP required for a given level */
    function xpForLevel(lvl) {
        // 0, 50, 120, 210, 320, 450, 600, 770, 960, 1170
        return lvl <= 1 ? 0 : Math.round(lvl * lvl * 10 + lvl * 20);
    }

    /** Clamp a value between min and max */
    function clamp(val, min, max) {
        return val < min ? min : (val > max ? max : val);
    }

    /** Generate a simple pseudo-random id */
    function uid() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 6);
    }

    /** Check if pet has any lab mutations */
    function hasLabMutations(pet) {
        var lm = pet.lab_mutations || {};
        return !!(lm.L3 || lm.L6 || lm.L9);
    }

    // ── CaretakerEngine ──────────────────────────────────────────

    var CaretakerEngine = {};

    // ── Storage helpers ──────────────────────────────────────────

    /**
     * Parse moreau_pets from localStorage.
     * @returns {Array} Array of pet objects
     */
    CaretakerEngine._getPets = function() {
        try {
            return JSON.parse(localStorage.getItem(PETS_KEY) || '[]');
        } catch(e) {
            return [];
        }
    };

    /**
     * Save pets array back to localStorage.
     * @param {Array} pets
     */
    CaretakerEngine._savePets = function(pets) {
        localStorage.setItem(PETS_KEY, JSON.stringify(pets));
    };

    /**
     * Parse caretaker log from localStorage.
     * @returns {Array} Array of log entry objects (max 100)
     */
    CaretakerEngine._getLog = function() {
        try {
            return JSON.parse(localStorage.getItem(LOG_KEY) || '[]');
        } catch(e) {
            return [];
        }
    };

    /**
     * Prepend an entry to the caretaker log, trimming to MAX_LOG.
     * @param {{ action: string, petIndex: number, detail: string, timestamp: string }} entry
     */
    CaretakerEngine._addLog = function(entry) {
        var log = this._getLog();
        entry.timestamp = entry.timestamp || new Date().toISOString();
        entry.id = entry.id || uid();
        log.unshift(entry);
        if (log.length > MAX_LOG) {
            log = log.slice(0, MAX_LOG);
        }
        localStorage.setItem(LOG_KEY, JSON.stringify(log));
    };

    /**
     * Get a single pet by index, initializing needs if missing.
     * @param {number} index
     * @returns {Object|null} Pet object or null
     */
    CaretakerEngine._getPet = function(index) {
        var pets = this._getPets();
        if (index < 0 || index >= pets.length) return null;
        var pet = pets[index];
        if (!pet) return null;
        pet = this.initNeeds(pet);
        return pet;
    };

    // ── Needs System ─────────────────────────────────────────────

    /**
     * Initialize needs on a pet if missing.
     * @param {Object} pet
     * @returns {Object} pet with .needs guaranteed
     */
    CaretakerEngine.initNeeds = function(pet) {
        if (!pet) return pet;
        if (!pet.needs) {
            pet.needs = {
                hunger: NEEDS_CEIL,
                health: NEEDS_CEIL,
                morale: NEEDS_CEIL,
                energy: NEEDS_CEIL,
                last_checked: Date.now()
            };
        }
        if (!pet.needs.last_checked) {
            pet.needs.last_checked = Date.now();
        }
        return pet;
    };

    /**
     * Apply time-based decay to a single pet's needs.
     * Called automatically; mutates the pet object.
     *
     * Rates per hour:
     *   hunger:  -5/hr (if 0 for 2+ hrs, permanent HP loss)
     *   energy:  +10/hr (passive recovery, capped at 100)
     *   morale:  -1/hr if 6+ hrs since last player action
     *   health:  -2/hr if instability > 50
     *
     * @param {Object} pet
     * @returns {Object} pet (mutated)
     */
    CaretakerEngine.decay = function(pet) {
        if (!pet || pet.deceased) return pet;
        pet = this.initNeeds(pet);

        var now = Date.now();
        var elapsed = now - pet.needs.last_checked;
        if (elapsed <= 0) return pet;

        var hours = elapsed / 3600000;

        // Hunger decays
        var oldHunger = pet.needs.hunger;
        pet.needs.hunger = clamp(Math.round(pet.needs.hunger - (5 * hours)), NEEDS_FLOOR, NEEDS_CEIL);

        // If hunger was 0 for 2+ hours, permanent HP damage
        if (oldHunger <= 0 && hours >= 2) {
            var starvationHours = Math.floor(hours);
            var hpLoss = Math.max(1, Math.floor(starvationHours / 2));
            var bs = pet.base_stats || {};
            bs.hp = Math.max(1, (bs.hp || 5) - hpLoss);
            pet.base_stats = bs;

            // Diary entry about starvation damage
            this._generateDecayDiary(pet, 'warning',
                pet.name + ' lost ' + hpLoss + ' permanent HP from starvation. Base HP is now ' + bs.hp + '.');
        }

        // Energy recovers passively
        pet.needs.energy = clamp(Math.round(pet.needs.energy + (10 * hours)), NEEDS_FLOOR, NEEDS_CEIL);

        // If resting, bonus energy
        if (pet.resting_until && now < pet.resting_until) {
            pet.needs.energy = clamp(pet.needs.energy + Math.round(5 * hours), NEEDS_FLOOR, NEEDS_CEIL);
        } else if (pet.resting_until && now >= pet.resting_until) {
            // Rest complete
            delete pet.resting_until;
        }

        // Morale decays if neglected (6+ hours since last action)
        if (hours > 6) {
            var neglectHours = hours - 6;
            pet.needs.morale = clamp(Math.round(pet.needs.morale - (1 * neglectHours)), NEEDS_FLOOR, NEEDS_CEIL);
        }

        // Health decays if instability is high
        if ((pet.instability || 0) > 50) {
            pet.needs.health = clamp(Math.round(pet.needs.health - (2 * hours)), NEEDS_FLOOR, NEEDS_CEIL);
        }

        pet.needs.last_checked = now;
        return pet;
    };

    /**
     * Decay all living pets and save.
     */
    CaretakerEngine.decayAll = function() {
        var pets = this._getPets();
        var self = this;
        var changed = false;
        pets.forEach(function(pet, i) {
            if (!pet.deceased) {
                pets[i] = self.decay(self.initNeeds(pet));
                changed = true;
            }
        });
        if (changed) {
            this._savePets(pets);
        }
        // Check mercy clause after decay
        this.checkMercyClause(pets);
    };

    // ── Status ───────────────────────────────────────────────────

    /**
     * Get status report for a pet.
     * @param {Object} pet
     * @returns {{ urgent: string[], warnings: string[], tips: string[] }}
     */
    CaretakerEngine.getStatus = function(pet) {
        if (!pet) return { urgent: [], warnings: [], tips: [] };
        pet = this.initNeeds(pet);

        var urgent = [];
        var warnings = [];
        var tips = [];

        var needs = pet.needs;
        var needNames = ['hunger', 'health', 'morale', 'energy'];

        needNames.forEach(function(key) {
            var val = needs[key];
            if (val < 20) {
                urgent.push("\u26A0\uFE0F " + pet.name + "'s " + key + " is critically low (" + val + "%)!");
            } else if (val < 40) {
                warnings.push(key.charAt(0).toUpperCase() + key.slice(1) + " is getting low (" + val + "%)");
            }
        });

        // General tips
        if (pet.deceased) {
            tips.push(pet.name + ' has passed. Visit the Graveyard to pay respects.');
        } else {
            if ((pet.instability || 0) > 70) {
                tips.push('High instability. Avoid the Forbidden Lab for now.');
            }
            if ((pet.heal_debt || 0) > 0) {
                tips.push('Heal debt active: ' + pet.heal_debt + ' fights with stat penalty.');
            }
            if (pet.resting_until && pet.resting_until > Date.now()) {
                var minsLeft = Math.ceil((pet.resting_until - Date.now()) / 60000);
                tips.push('Resting for ' + minsLeft + ' more minute(s).');
            }
            if (needs.hunger >= 80 && needs.energy >= 60) {
                tips.push('Good condition for training or fighting.');
            }
        }

        return { urgent: urgent, warnings: warnings, tips: tips };
    };

    // ── Actions ──────────────────────────────────────────────────

    /**
     * Feed a pet. Hunger +50 (max 100).
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.feed = function(petIndex) {
        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        var before = pet.needs.hunger;
        pet.needs.hunger = clamp(pet.needs.hunger + 50, NEEDS_FLOOR, NEEDS_CEIL);
        pet.needs.last_checked = Date.now();

        pets[petIndex] = pet;
        this._savePets(pets);

        this._addLog({ action: 'feed', petIndex: petIndex, detail: 'Hunger ' + before + ' -> ' + pet.needs.hunger });
        this._generateActionDiary(pet, petIndex, 'feed', before, pet.needs.hunger);
        this.updateCareStreak();

        return { success: true, message: pet.name + ' has been fed. Hunger: ' + pet.needs.hunger + '%.' };
    };

    /**
     * Heal a pet. Health +30 (max 100). Adds heal_debt (+5 fights with -1 to a random stat).
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.heal = function(petIndex) {
        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        var before = pet.needs.health;
        pet.needs.health = clamp(pet.needs.health + 30, NEEDS_FLOOR, NEEDS_CEIL);
        pet.heal_debt = (pet.heal_debt || 0) + 5;
        pet.needs.last_checked = Date.now();

        pets[petIndex] = pet;
        this._savePets(pets);

        this._addLog({ action: 'heal', petIndex: petIndex, detail: 'Health ' + before + ' -> ' + pet.needs.health + ', heal_debt=' + pet.heal_debt });
        this._generateActionDiary(pet, petIndex, 'heal', before, pet.needs.health);
        this.updateCareStreak();

        return { success: true, message: pet.name + ' healed. Health: ' + pet.needs.health + '%. Heal debt: ' + pet.heal_debt + ' fights.' };
    };

    /**
     * Rest a pet. Energy +50, sets resting_until (1 hour from now).
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.rest = function(petIndex) {
        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        var before = pet.needs.energy;
        pet.needs.energy = clamp(pet.needs.energy + 50, NEEDS_FLOOR, NEEDS_CEIL);
        pet.resting_until = Date.now() + REST_DURATION_MS;
        pet.needs.last_checked = Date.now();

        pets[petIndex] = pet;
        this._savePets(pets);

        this._addLog({ action: 'rest', petIndex: petIndex, detail: 'Energy ' + before + ' -> ' + pet.needs.energy + ', resting for 1hr' });
        this._generateActionDiary(pet, petIndex, 'rest', before, pet.needs.energy);
        this.updateCareStreak();

        return { success: true, message: pet.name + ' is resting. Energy: ' + pet.needs.energy + '%. Ready in 1 hour.' };
    };

    /**
     * Train a pet (simulated fight).
     * Requires energy >= 20. Energy -20, simulate win/loss, gain XP.
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string, won: boolean|undefined }}
     */
    CaretakerEngine.train = function(petIndex) {
        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        if (pet.needs.energy < 20) {
            return { success: false, message: pet.name + ' is too tired to train (energy: ' + pet.needs.energy + '%). Rest first.' };
        }

        // Spend energy
        pet.needs.energy = clamp(pet.needs.energy - 20, NEEDS_FLOOR, NEEDS_CEIL);

        // Win probability
        var bs = pet.base_stats || {};
        var winProb = 0.4 + ((pet.level || 1) * 0.05) + ((bs.atk || 5) / 40);
        winProb = Math.min(winProb, 0.85);

        var won = Math.random() < winProb;
        var xpGain = won ? 30 : 10;

        // Apply heal debt penalty
        if (pet.heal_debt && pet.heal_debt > 0) {
            pet.heal_debt = pet.heal_debt - 1;
        }

        // Update XP
        pet.xp = (pet.xp || 0) + xpGain;

        // Level up check
        var nextLvl = (pet.level || 1) + 1;
        if (nextLvl <= 10 && pet.xp >= xpForLevel(nextLvl)) {
            pet.level = nextLvl;
            this._generateDecayDiary(pet, 'report',
                pet.name + ' reached level ' + nextLvl + '! New abilities may be available.');
        }

        // Fight record
        var fight = {
            opponent: 'TrainingDummy',
            result: won ? 'win' : 'loss',
            ticks: Math.floor(Math.random() * 21) + 10,
            timestamp: new Date().toISOString()
        };
        if (!pet.fights) pet.fights = [];
        pet.fights.push(fight);

        // Morale
        pet.needs.morale = clamp(pet.needs.morale + (won ? 5 : -5), NEEDS_FLOOR, NEEDS_CEIL);
        pet.needs.last_checked = Date.now();

        pets[petIndex] = pet;
        this._savePets(pets);

        var resultText = won ? 'won' : 'lost';
        this._addLog({ action: 'train', petIndex: petIndex, detail: resultText + ', +' + xpGain + ' XP' });
        this._generateActionDiary(pet, petIndex, 'train_' + resultText, 0, xpGain);
        this.updateCareStreak();

        return {
            success: true,
            message: pet.name + ' ' + resultText + ' the training match! +' + xpGain + ' XP. Energy: ' + pet.needs.energy + '%.',
            won: won
        };
    };

    /**
     * Motivate a pet. Morale +20, get an encouraging quote.
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string, quote: string|undefined }}
     */
    CaretakerEngine.motivate = function(petIndex) {
        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        var before = pet.needs.morale;
        pet.needs.morale = clamp(pet.needs.morale + 20, NEEDS_FLOOR, NEEDS_CEIL);
        pet.needs.last_checked = Date.now();

        // Pick a quote
        var animal = (pet.animal || '').toLowerCase();
        var pool = ANIMAL_QUOTES[animal] || GENERIC_QUOTES;
        var quote = pool[Math.floor(Math.random() * pool.length)];

        pets[petIndex] = pet;
        this._savePets(pets);

        this._addLog({ action: 'motivate', petIndex: petIndex, detail: 'Morale ' + before + ' -> ' + pet.needs.morale });
        this._generateActionDiary(pet, petIndex, 'motivate', before, pet.needs.morale);
        this.updateCareStreak();

        return {
            success: true,
            message: pet.name + "'s morale boosted to " + pet.needs.morale + '%.',
            quote: quote
        };
    };

    /**
     * Auto-manage a pet (premium feature).
     * Feeds if hungry, heals if low health, rests if tired, trains if able.
     * @param {number} petIndex
     * @returns {{ success: boolean, message: string, actions: Array|undefined }}
     */
    CaretakerEngine.autoManage = function(petIndex) {
        var isPremium = false;
        try { isPremium = JSON.parse(localStorage.getItem(PREMIUM_KEY)); } catch(e) {}
        if (!isPremium) {
            return { success: false, message: 'Premium required. Unlock Auto-Manage to let the Caretaker act autonomously.' };
        }

        var pets = this._getPets();
        var pet = pets[petIndex];
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        pet = this.initNeeds(pet);
        pet = this.decay(pet);

        var actions = [];

        // Feed if hungry
        if (pet.needs.hunger < 50) {
            pet.needs.hunger = clamp(pet.needs.hunger + 50, NEEDS_FLOOR, NEEDS_CEIL);
            actions.push({ action: 'feed', result: 'Hunger -> ' + pet.needs.hunger + '%' });
        }

        // Heal if health low
        if (pet.needs.health < 40) {
            pet.needs.health = clamp(pet.needs.health + 30, NEEDS_FLOOR, NEEDS_CEIL);
            pet.heal_debt = (pet.heal_debt || 0) + 5;
            actions.push({ action: 'heal', result: 'Health -> ' + pet.needs.health + '%' });
        }

        // Rest if tired
        if (pet.needs.energy < 20) {
            pet.needs.energy = clamp(pet.needs.energy + 50, NEEDS_FLOOR, NEEDS_CEIL);
            pet.resting_until = Date.now() + REST_DURATION_MS;
            actions.push({ action: 'rest', result: 'Energy -> ' + pet.needs.energy + '%' });
        }

        // Train if able
        if (pet.needs.energy > 60 && pet.needs.hunger > 30) {
            pet.needs.energy = clamp(pet.needs.energy - 20, NEEDS_FLOOR, NEEDS_CEIL);
            var bs = pet.base_stats || {};
            var winProb = 0.4 + ((pet.level || 1) * 0.05) + ((bs.atk || 5) / 40);
            winProb = Math.min(winProb, 0.85);
            var won = Math.random() < winProb;
            var xp = won ? 30 : 10;
            pet.xp = (pet.xp || 0) + xp;
            pet.needs.morale = clamp(pet.needs.morale + (won ? 5 : -5), NEEDS_FLOOR, NEEDS_CEIL);
            if (!pet.fights) pet.fights = [];
            pet.fights.push({
                opponent: 'TrainingDummy',
                result: won ? 'win' : 'loss',
                ticks: Math.floor(Math.random() * 21) + 10,
                timestamp: new Date().toISOString()
            });
            actions.push({ action: 'train', result: (won ? 'Won' : 'Lost') + ', +' + xp + ' XP' });
        }

        pet.needs.last_checked = Date.now();
        pets[petIndex] = pet;
        this._savePets(pets);

        if (actions.length > 0) {
            this._addLog({ action: 'auto_manage', petIndex: petIndex, detail: actions.length + ' actions taken' });
            this._generateDecayDiary(pet, 'decision',
                'Auto-managed ' + pet.name + ': ' + actions.map(function(a) { return a.action; }).join(', ') + '.');
        }

        this.updateCareStreak();

        return {
            success: true,
            message: actions.length > 0
                ? 'Auto-managed ' + pet.name + '. ' + actions.length + ' action(s) taken.'
                : 'No actions needed for ' + pet.name + '. All needs are adequate.',
            actions: actions
        };
    };

    // ── Advice Engine ────────────────────────────────────────────

    /**
     * Get 3-5 relevant advice strings for a pet.
     * Selects from 30+ templates based on current state.
     * @param {Object} pet
     * @returns {string[]}
     */
    CaretakerEngine.getAdvice = function(pet) {
        if (!pet) return ['No pet selected.'];
        pet = this.initNeeds(pet);

        var matched = [];
        ADVICE_POOL.forEach(function(template) {
            try {
                if (template.condition(pet)) {
                    matched.push(template.text(pet));
                }
            } catch(e) {
                // Skip broken templates
            }
        });

        // If fewer than 3 matched, add generic advice
        var generic = [
            'Check back regularly to keep ' + (pet.name || 'your pet') + ' in top shape.',
            'The Caretaker is always watching. Even when you sleep.',
            'Balance all four needs for optimal performance.',
            'A well-rested fighter wins more than a tired champion.',
            'Mutations amplify strengths. Make sure the base is solid first.',
            'Every fight teaches something. Even the losses.'
        ];

        while (matched.length < 3 && generic.length > 0) {
            var idx = Math.floor(Math.random() * generic.length);
            matched.push(generic.splice(idx, 1)[0]);
        }

        // Cap at 5
        if (matched.length > 5) {
            // Prioritize: shuffle and take 5
            matched.sort(function() { return Math.random() - 0.5; });
            matched = matched.slice(0, 5);
        }

        return matched;
    };

    // ── Overnight System ─────────────────────────────────────────

    /**
     * Start overnight training.
     * @param {number} petIndex
     * @param {number} rounds - 3, 5, 7, or 10 (10 requires premium)
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.startOvernight = function(petIndex, rounds) {
        // Validate rounds
        var validRounds = [3, 5, 7, 10];
        if (validRounds.indexOf(rounds) === -1) {
            return { success: false, message: 'Invalid round count. Choose 3, 5, 7, or 10.' };
        }

        // 10 rounds requires premium
        if (rounds === 10) {
            var isPremium = false;
            try { isPremium = JSON.parse(localStorage.getItem(PREMIUM_KEY)); } catch(e) {}
            if (!isPremium) {
                return { success: false, message: '10-round overnight requires Premium.' };
            }
        }

        var pet = this._getPet(petIndex);
        if (!pet) return { success: false, message: 'Pet not found.' };
        if (pet.deceased) return { success: false, message: pet.name + ' has passed away.' };

        // Check for existing overnight
        try {
            var existing = JSON.parse(localStorage.getItem(OVERNIGHT_KEY));
            if (existing && !existing.completed) {
                return { success: false, message: 'An overnight session is already in progress.' };
            }
        } catch(e) {}

        var session = {
            start: Date.now(),
            petIndex: petIndex,
            rounds: rounds,
            completed: false,
            petName: pet.name
        };

        localStorage.setItem(OVERNIGHT_KEY, JSON.stringify(session));

        this._addLog({ action: 'overnight_start', petIndex: petIndex, detail: rounds + ' rounds' });
        this.addDiaryEntry('decision', 'Put ' + pet.name + ' into overnight training (' + rounds + ' rounds). Sweet dreams, little fighter.', petIndex);

        return { success: true, message: pet.name + ' has been tucked in for ' + rounds + ' overnight rounds. Check back in 4+ hours.' };
    };

    /**
     * Process a completed overnight session.
     * Must be called to resolve results (e.g., on page load).
     * @returns {{ success: boolean, message: string, results: Object|undefined }}
     */
    CaretakerEngine.processOvernight = function() {
        var raw;
        try { raw = JSON.parse(localStorage.getItem(OVERNIGHT_KEY)); } catch(e) { return null; }
        if (!raw || raw.completed) return null;

        var elapsed = Date.now() - raw.start;
        if (elapsed < OVERNIGHT_MIN_MS) {
            var hoursLeft = Math.ceil((OVERNIGHT_MIN_MS - elapsed) / 3600000 * 10) / 10;
            return { success: false, message: 'Still sleeping. ~' + hoursLeft + ' hours to go.', pending: true };
        }

        // Simulate fights
        var pets = this._getPets();
        var pet = pets[raw.petIndex];
        if (!pet) {
            localStorage.removeItem(OVERNIGHT_KEY);
            return { success: false, message: 'Pet no longer exists.' };
        }

        pet = this.initNeeds(pet);

        var bs = pet.base_stats || {};
        var winProb = 0.4 + ((pet.level || 1) * 0.05) + ((bs.atk || 5) / 40);
        winProb = Math.min(winProb, 0.85);

        var wins = 0;
        var losses = 0;
        var totalXP = 0;

        for (var i = 0; i < raw.rounds; i++) {
            var won = Math.random() < winProb;
            if (won) {
                wins++;
                totalXP += 30;
            } else {
                losses++;
                totalXP += 10;
            }
            if (!pet.fights) pet.fights = [];
            pet.fights.push({
                opponent: 'OvernightOpponent',
                result: won ? 'win' : 'loss',
                ticks: Math.floor(Math.random() * 21) + 10,
                timestamp: new Date(raw.start + (i + 1) * 600000).toISOString()
            });
        }

        pet.xp = (pet.xp || 0) + totalXP;

        // Level up check
        var nextLvl = (pet.level || 1) + 1;
        while (nextLvl <= 10 && pet.xp >= xpForLevel(nextLvl)) {
            pet.level = nextLvl;
            nextLvl++;
        }

        // Hunger decay for sleep hours
        var sleepHours = elapsed / 3600000;
        pet.needs.hunger = clamp(Math.round(pet.needs.hunger - (5 * sleepHours)), NEEDS_FLOOR, NEEDS_CEIL);
        pet.needs.last_checked = Date.now();

        // Morale based on overall result
        pet.needs.morale = clamp(pet.needs.morale + (wins > losses ? 10 : -5), NEEDS_FLOOR, NEEDS_CEIL);

        pets[raw.petIndex] = pet;
        this._savePets(pets);

        var results = {
            wins: wins,
            losses: losses,
            totalXP: totalXP,
            newLevel: pet.level,
            hungerAfter: pet.needs.hunger,
            sleepHours: Math.round(sleepHours * 10) / 10
        };

        raw.completed = true;
        raw.results = results;
        localStorage.setItem(OVERNIGHT_KEY, JSON.stringify(raw));

        this._addLog({ action: 'overnight_complete', petIndex: raw.petIndex, detail: wins + 'W/' + losses + 'L, +' + totalXP + ' XP' });

        // Generate diary
        var diaryText = 'Overnight report for ' + (pet.name || 'your pet') + ': '
            + wins + ' wins, ' + losses + ' losses, ' + totalXP + ' XP gained.'
            + (pet.needs.hunger < 30 ? ' Woke up hungry.' : '')
            + (wins > losses ? ' A productive night.' : ' Rough night, but lessons were learned.');
        this.addDiaryEntry('report', diaryText, raw.petIndex);

        return { success: true, message: 'Overnight complete!', results: results };
    };

    /**
     * Get the overnight report if completed, or pending status.
     * @returns {{ pending: boolean, hoursLeft: number }|Object|null}
     */
    CaretakerEngine.getOvernightReport = function() {
        var raw;
        try { raw = JSON.parse(localStorage.getItem(OVERNIGHT_KEY)); } catch(e) { return null; }
        if (!raw) return null;

        if (raw.completed) {
            return raw.results || { completed: true };
        }

        var elapsed = Date.now() - raw.start;
        if (elapsed < OVERNIGHT_MIN_MS) {
            return {
                pending: true,
                hoursLeft: Math.ceil((OVERNIGHT_MIN_MS - elapsed) / 3600000 * 10) / 10,
                petName: raw.petName,
                rounds: raw.rounds
            };
        }

        // Ready to process
        return { pending: true, hoursLeft: 0, ready: true, petName: raw.petName, rounds: raw.rounds };
    };

    // ── Diary + Trust System ─────────────────────────────────────

    /**
     * Get current trust level (0-10).
     * @returns {number}
     */
    CaretakerEngine.getTrust = function() {
        try {
            var val = parseFloat(localStorage.getItem(TRUST_KEY));
            return isNaN(val) ? TRUST_DEFAULT : clamp(val, TRUST_MIN, TRUST_MAX);
        } catch(e) {
            return TRUST_DEFAULT;
        }
    };

    /**
     * Set trust level.
     * @param {number} val
     */
    CaretakerEngine._setTrust = function(val) {
        localStorage.setItem(TRUST_KEY, String(clamp(val, TRUST_MIN, TRUST_MAX)));
    };

    /**
     * Get all diary entries, sorted newest first.
     * @returns {Array}
     */
    CaretakerEngine.getDiary = function() {
        try {
            var diary = JSON.parse(localStorage.getItem(DIARY_KEY) || '[]');
            diary.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
            return diary;
        } catch(e) {
            return [];
        }
    };

    /**
     * Add a diary entry.
     * @param {string} type - 'report','opinion','warning','apology','decision','observation'
     * @param {string} text
     * @param {number} [petIndex]
     */
    CaretakerEngine.addDiaryEntry = function(type, text, petIndex) {
        var diary;
        try { diary = JSON.parse(localStorage.getItem(DIARY_KEY) || '[]'); } catch(e) { diary = []; }

        var entry = {
            id: Date.now(),
            type: type || 'observation',
            text: text,
            petIndex: petIndex !== undefined ? petIndex : null,
            timestamp: new Date().toISOString(),
            approved: null
        };

        diary.unshift(entry);
        if (diary.length > MAX_DIARY) {
            diary = diary.slice(0, MAX_DIARY);
        }
        localStorage.setItem(DIARY_KEY, JSON.stringify(diary));
        return entry;
    };

    /**
     * Approve a diary entry. Trust +0.5.
     * @param {number} id - entry id (timestamp)
     * @returns {{ success: boolean }}
     */
    CaretakerEngine.approveDiaryEntry = function(id) {
        var diary;
        try { diary = JSON.parse(localStorage.getItem(DIARY_KEY) || '[]'); } catch(e) { return { success: false }; }

        var found = false;
        diary.forEach(function(entry) {
            if (entry.id === id) {
                entry.approved = true;
                found = true;
            }
        });

        if (!found) return { success: false };

        localStorage.setItem(DIARY_KEY, JSON.stringify(diary));

        var trust = this.getTrust();
        this._setTrust(trust + 0.5);

        this._addLog({ action: 'diary_approved', petIndex: null, detail: 'Entry ' + id + ' approved, trust -> ' + this.getTrust() });
        return { success: true };
    };

    /**
     * Override (reject) a diary entry. Trust -1.
     * @param {number} id
     * @returns {{ success: boolean }}
     */
    CaretakerEngine.overrideDiaryEntry = function(id) {
        var diary;
        try { diary = JSON.parse(localStorage.getItem(DIARY_KEY) || '[]'); } catch(e) { return { success: false }; }

        var found = false;
        diary.forEach(function(entry) {
            if (entry.id === id) {
                entry.approved = false;
                found = true;
            }
        });

        if (!found) return { success: false };

        localStorage.setItem(DIARY_KEY, JSON.stringify(diary));

        var trust = this.getTrust();
        this._setTrust(trust - 1);

        this._addLog({ action: 'diary_overridden', petIndex: null, detail: 'Entry ' + id + ' overridden, trust -> ' + this.getTrust() });
        return { success: true };
    };

    /**
     * Generate a diary entry with personality based on trust level.
     * Used internally during decay and actions.
     * @param {Object} pet
     * @param {string} type
     * @param {string} rawText
     */
    CaretakerEngine._generateDecayDiary = function(pet, type, rawText) {
        var trust = this.getTrust();
        var name = pet ? pet.name : 'the pet';
        var text;

        if (trust < 3) {
            // Terse, clinical
            text = rawText;
        } else if (trust < 7) {
            // Conversational
            text = rawText;
            // Add a personal touch
            var touches = [
                ' I\'m keeping an eye on it.',
                ' Nothing to worry about for now.',
                ' Thought you should know.',
                ' Noted and logged.'
            ];
            text += touches[Math.floor(Math.random() * touches.length)];
        } else if (trust < 9) {
            // Opinionated
            var opinions = [
                ' I think ' + name + ' could use more attention.',
                ' Just my two cents, but this matters.',
                ' I\'ve seen this pattern before — act early.',
                ' If you trust me, let me help.'
            ];
            text = rawText + opinions[Math.floor(Math.random() * opinions.length)];
        } else {
            // Creative / risky
            var creative = [
                ' I took a small liberty. You\'ll thank me later.',
                ' I may have overstepped, but ' + name + ' needed it.',
                ' Don\'t worry, I calculated the odds. ...mostly.',
                ' I did what I thought was right. Override me if you disagree.'
            ];
            text = rawText + creative[Math.floor(Math.random() * creative.length)];
        }

        this.addDiaryEntry(type, text, null);
    };

    /**
     * Generate diary entry for a player action.
     * @param {Object} pet
     * @param {number} petIndex
     * @param {string} action
     * @param {number} before
     * @param {number} after
     */
    CaretakerEngine._generateActionDiary = function(pet, petIndex, action, before, after) {
        var trust = this.getTrust();
        var name = pet.name || 'the pet';
        var text = '';

        if (trust < 3) {
            // Clinical
            switch(action) {
                case 'feed':    text = 'Fed ' + name + '. Hunger ' + after + '%.'; break;
                case 'heal':    text = 'Healed ' + name + '. Health ' + after + '%.'; break;
                case 'rest':    text = name + ' resting. Energy ' + after + '%.'; break;
                case 'train_won':  text = name + ' trained. Won. +' + after + ' XP.'; break;
                case 'train_lost': text = name + ' trained. Lost. +' + after + ' XP.'; break;
                case 'motivate':   text = 'Motivated ' + name + '. Morale ' + after + '%.'; break;
                default: text = action + ' performed on ' + name + '.';
            }
        } else if (trust < 7) {
            // Conversational
            switch(action) {
                case 'feed':
                    text = name + ' was getting hungry. Took care of it. Hunger at ' + after + '% now.';
                    break;
                case 'heal':
                    text = 'Patched ' + name + ' up. Health back to ' + after + '%. The heal debt will sting for a few fights though.';
                    break;
                case 'rest':
                    text = name + ' needed a break. Energy charging — ' + after + '% and climbing.';
                    break;
                case 'train_won':
                    text = 'Training session went well! ' + name + ' won and earned ' + after + ' XP.';
                    break;
                case 'train_lost':
                    text = 'Training session was rough. ' + name + ' lost, but still earned ' + after + ' XP. Every loss teaches.';
                    break;
                case 'motivate':
                    text = 'Gave ' + name + ' a pep talk. Morale boosted to ' + after + '%.';
                    break;
                default:
                    text = 'Handled ' + action + ' for ' + name + '.';
            }
        } else {
            // Opinionated / creative
            switch(action) {
                case 'feed':
                    text = 'I fed ' + name + '. Hunger ' + after + '%. ' +
                        (before < 20 ? 'Cutting it close — I was worried.' : 'Keeping the engine fueled.');
                    break;
                case 'heal':
                    text = name + ' is patched up (' + after + '% health). ' +
                        'I wish you wouldn\'t let it get this low. The heal debt is ' +
                        (pet.heal_debt || 0) + ' fights — that\'s on you.';
                    break;
                case 'rest':
                    text = name + ' is sleeping. Energy at ' + after + '%. ' +
                        'I\'ll watch over them. Go do something else for an hour.';
                    break;
                case 'train_won':
                    text = name + ' crushed it in training! +' + after + ' XP. ' +
                        'I think we should push harder. They\'re ready.';
                    break;
                case 'train_lost':
                    text = name + ' lost the training bout. +' + after + ' XP anyway. ' +
                        'Don\'t blame them — the opponent was tough. I\'d know, I picked it.';
                    break;
                case 'motivate':
                    text = 'I told ' + name + ' something encouraging. Morale ' + after + '%. ' +
                        'You could do this yourself sometimes, you know.';
                    break;
                default:
                    text = 'Performed ' + action + ' on ' + name + '. Trust me on this one.';
            }
        }

        this.addDiaryEntry('report', text, petIndex);
    };

    // ── Mercy Clause ─────────────────────────────────────────────

    /**
     * Scan all living pets for mercy clause triggers.
     * Creates a pending mercy decision if criteria met.
     * @param {Array} [pets] - optional, will load from storage if omitted
     */
    CaretakerEngine.checkMercyClause = function(pets) {
        if (!pets) pets = this._getPets();

        // Count living pets
        var living = [];
        pets.forEach(function(p, i) {
            if (!p.deceased) living.push({ pet: p, index: i });
        });

        if (living.length < 2) return; // Need at least 2 living pets

        // Check for existing pending
        try {
            var existing = JSON.parse(localStorage.getItem(MERCY_KEY));
            if (existing && !existing.resolved) return; // Already pending
        } catch(e) {}

        var criticalIdx = -1;
        var triggerReason = '';

        living.forEach(function(entry) {
            var p = entry.pet;
            var needs = p.needs || {};
            // Trigger 1: hunger depleted + health critical
            if (needs.hunger <= 0 && needs.health < 20) {
                criticalIdx = entry.index;
                triggerReason = 'starvation_critical';
            }
            // Trigger 2: instability extreme + health low
            if ((p.instability || 0) > 90 && needs.health < 30) {
                criticalIdx = entry.index;
                triggerReason = 'instability_collapse';
            }
        });

        if (criticalIdx === -1) return; // No crisis

        // ── Drift-biased pre-selection (Proposition 1) ──
        // If drift score > 40, the Caretaker suggests the pet with the
        // lowest average needs as sacrifice instead of lowest level.
        var driftScore = 0;
        try {
            var driftRaw = JSON.parse(localStorage.getItem('moreau_caretaker_drift'));
            if (driftRaw && typeof driftRaw.score === 'number') {
                driftScore = driftRaw.score;
            }
        } catch(e) {}

        var driftBiased = driftScore > 40;
        var caretakerPick = -1;

        if (driftBiased) {
            // Drift-biased: pick pet with lowest average needs (hunger+health+morale+energy)/4
            var lowestAvg = Infinity;
            living.forEach(function(entry) {
                if (entry.index === criticalIdx) return;
                var needs = entry.pet.needs || {};
                var avg = ((needs.hunger || 0) + (needs.health || 0) + (needs.morale || 0) + (needs.energy || 0)) / 4;
                if (avg < lowestAvg) {
                    lowestAvg = avg;
                    caretakerPick = entry.index;
                }
            });
        } else {
            // Default: lowest level pet (not the critical one)
            var lowestLevel = Infinity;
            living.forEach(function(entry) {
                if (entry.index !== criticalIdx && (entry.pet.level || 1) < lowestLevel) {
                    lowestLevel = entry.pet.level || 1;
                    caretakerPick = entry.index;
                }
            });
        }

        if (caretakerPick === -1) return; // No valid sacrifice candidate

        var pending = {
            criticalPetIndex: criticalIdx,
            triggerReason: triggerReason,
            presentedAt: Date.now(),
            expiresAt: Date.now() + MERCY_WINDOW_MS,
            caretakerPick: caretakerPick,
            resolved: false,
            // Proposition 1: drift-biased mercy fields
            suggested_sacrifice: caretakerPick,
            drift_biased: driftBiased,
            drift_score: driftScore
        };

        localStorage.setItem(MERCY_KEY, JSON.stringify(pending));

        // Dramatic diary entry
        var critPet = pets[criticalIdx];
        var pickPet = pets[caretakerPick];
        var reason = triggerReason === 'starvation_critical'
            ? 'is starving and fading'
            : 'is destabilizing beyond recovery';

        var driftNote = driftBiased
            ? ' I chose ' + (pickPet.name || 'the weakest') + ' because they were already fading. Drift guided my hand.'
            : '';

        this.addDiaryEntry('warning',
            'MERCY CLAUSE TRIGGERED. ' + (critPet.name || 'A pet') + ' ' + reason + '. ' +
            'One must be sacrificed so the other survives. ' +
            'I recommend sacrificing ' + (pickPet.name || 'the weakest') + ' (Level ' + (pickPet.level || 1) + '). ' +
            'You have 6 hours to decide. If you don\'t, I will.' + driftNote,
            criticalIdx
        );

        this._addLog({ action: 'mercy_triggered', petIndex: criticalIdx, detail: triggerReason + ', pick=' + caretakerPick + (driftBiased ? ', drift_biased' : '') });
    };

    /**
     * Get pending mercy clause, or null. Auto-resolves if expired.
     * @returns {Object|null}
     */
    CaretakerEngine.getMercyPending = function() {
        var raw;
        try { raw = JSON.parse(localStorage.getItem(MERCY_KEY)); } catch(e) { return null; }
        if (!raw || raw.resolved) return null;

        // Auto-resolve if expired
        if (Date.now() > raw.expiresAt) {
            this.declineMercy();
            return null;
        }

        return raw;
    };

    /**
     * Execute the mercy clause: sacrifice one pet to save another.
     * @param {number} sacrificeIdx
     * @param {number} saveIdx
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.executeMercy = function(sacrificeIdx, saveIdx) {
        var pets = this._getPets();
        var sacrifice = pets[sacrificeIdx];
        var saved = pets[saveIdx];
        if (!sacrifice || !saved) return { success: false, message: 'Invalid pet selection.' };
        if (sacrifice.deceased) return { success: false, message: sacrifice.name + ' is already dead.' };

        // ── Proposition 1: Check if player overrode the drift-biased suggestion ──
        var pending;
        try { pending = JSON.parse(localStorage.getItem(MERCY_KEY)); } catch(e) { pending = {}; }
        var driftBiased = pending && pending.drift_biased;
        var suggestedSacrifice = pending ? pending.suggested_sacrifice : -1;
        var overrodeSuggestion = driftBiased && (sacrificeIdx !== suggestedSacrifice);
        var driftScore = (pending && pending.drift_score) || 0;

        // Trust cost: -2 if overriding drift-biased suggestion, -1 otherwise
        var trustCost = overrodeSuggestion ? -2 : -1;

        // Kill sacrifice
        sacrifice.deceased = true;
        sacrifice.cause_of_death = 'Mercy Clause sacrifice';
        sacrifice.death_timestamp = new Date().toISOString();
        // Proposition 1: mark sacrificed pet
        sacrifice.mercy_sacrificed = true;

        // Save the other pet
        saved = this.initNeeds(saved);
        saved.needs.health = 80;
        saved.needs.hunger = 60;

        var sbs = saved.base_stats || {};
        sbs.atk = (sbs.atk || 5) + 3;
        sbs.wil = Math.max(0, (sbs.wil || 5) - 2);
        saved.base_stats = sbs;

        // Proposition 1: mark saved pet and track mercy debts
        saved.mercy_saved = true;
        saved.mercy_debts = (saved.mercy_debts || 0) + 1;

        // Proposition 1: add Survivor's Guilt side effect
        if (!saved.side_effects) saved.side_effects = [];
        saved.side_effects.push({
            name: "Survivor's Guilt",
            desc: "Haunted by the one who was taken",
            category: "psychological",
            stats: { wil: -2, atk: 3 },
            intensity: Math.floor(driftScore / 10)
        });

        // Add debt record
        if (!saved.debts) saved.debts = [];
        saved.debts.push({
            name: sacrifice.name,
            animal: sacrifice.animal,
            level: sacrifice.level || 1,
            sacrificed_at: new Date().toISOString()
        });

        // Proposition 1: Abomination check based on mercy_debts (>= 3)
        if (saved.mercy_debts >= 3) {
            saved.abomination = true;
        }

        // Legacy abomination check (debts array)
        if (saved.debts.length >= 3) {
            saved.abomination = true;
        }

        pets[sacrificeIdx] = sacrifice;
        pets[saveIdx] = saved;
        this._savePets(pets);

        // Apply trust cost
        var currentTrust = this.getTrust();
        this._setTrust(clamp(currentTrust + trustCost, TRUST_MIN, TRUST_MAX));

        // Clear pending
        pending.resolved = true;
        pending.choice = 'player';
        pending.sacrificeIdx = sacrificeIdx;
        pending.saveIdx = saveIdx;
        pending.overrode_suggestion = overrodeSuggestion;
        localStorage.setItem(MERCY_KEY, JSON.stringify(pending));

        // Diary
        var overrideNote = overrodeSuggestion
            ? ' You overrode my suggestion. Trust costs double.'
            : '';
        this.addDiaryEntry('warning',
            sacrifice.name + ' was sacrificed to save ' + saved.name + '. ' +
            'ATK +3, WIL -2 applied. Survivor\'s Guilt afflicts ' + saved.name + '.' +
            (saved.abomination ? ' ' + saved.name + ' is now marked as an Abomination. Three debts paid in blood.' : '') +
            overrideNote +
            ' The arena remembers.',
            saveIdx
        );

        this._addLog({ action: 'mercy_executed', petIndex: sacrificeIdx, detail: 'Sacrificed to save pet ' + saveIdx + (overrodeSuggestion ? ' (override, trust -2)' : '') });

        return {
            success: true,
            message: sacrifice.name + ' was sacrificed. ' + saved.name + ' lives on.' +
                (saved.abomination ? ' They are now an Abomination.' : '') +
                (overrodeSuggestion ? ' Trust -2 for overriding the Caretaker.' : ''),
            overrodeSuggestion: overrodeSuggestion,
            trustCost: trustCost
        };
    };

    /**
     * Decline mercy — the Caretaker picks the sacrifice.
     * @returns {{ success: boolean, message: string }}
     */
    CaretakerEngine.declineMercy = function() {
        var raw;
        try { raw = JSON.parse(localStorage.getItem(MERCY_KEY)); } catch(e) { return { success: false, message: 'No mercy pending.' }; }
        if (!raw || raw.resolved) return { success: false, message: 'No mercy pending.' };

        var sacrificeIdx = raw.caretakerPick;
        var saveIdx = raw.criticalPetIndex;

        var result = this.executeMercy(sacrificeIdx, saveIdx);

        // Override diary tone
        if (result.success) {
            var pets = this._getPets();
            var sacrifice = pets[sacrificeIdx];
            this.addDiaryEntry('apology',
                'You left me no choice. I sacrificed ' + (sacrifice ? sacrifice.name : 'the weakest') +
                '. I\'m not sorry. I\'m efficient. But I\'ll remember this.',
                saveIdx
            );
        }

        // Mark as caretaker decision
        try {
            var pending = JSON.parse(localStorage.getItem(MERCY_KEY));
            pending.choice = 'caretaker';
            localStorage.setItem(MERCY_KEY, JSON.stringify(pending));
        } catch(e) {}

        return result;
    };

    /**
     * Get seconds remaining until mercy auto-resolves.
     * @returns {number} Seconds remaining, or 0 if no pending mercy
     */
    CaretakerEngine.getMercyTimeRemaining = function() {
        var raw;
        try { raw = JSON.parse(localStorage.getItem(MERCY_KEY)); } catch(e) { return 0; }
        if (!raw || raw.resolved) return 0;

        var remaining = raw.expiresAt - Date.now();
        return remaining > 0 ? Math.ceil(remaining / 1000) : 0;
    };

    // ── Feeding Ledger (Aleph Lore) ──────────────────────────────

    /**
     * Update the care streak counter.
     * A "day" = at least 2 visits in different 6-hour tide phases.
     * Called automatically on every care action.
     */
    CaretakerEngine.updateCareStreak = function() {
        var streak;
        try { streak = JSON.parse(localStorage.getItem(STREAK_KEY)); } catch(e) { streak = null; }

        if (!streak) {
            streak = {
                currentDay: this._getTideDay(),
                visitsToday: [],
                consecutiveDays: 0,
                lastCompletedDay: null
            };
        }

        var today = this._getTideDay();
        var currentPhase = this._getTidePhase();

        // New day?
        if (streak.currentDay !== today) {
            // Check if yesterday was completed (2+ visits in different phases)
            if (streak.visitsToday && this._uniquePhases(streak.visitsToday) >= 2) {
                // Yesterday counts
                if (streak.lastCompletedDay === streak.currentDay - 1 || streak.lastCompletedDay === null) {
                    streak.consecutiveDays++;
                } else {
                    streak.consecutiveDays = 1; // Reset streak
                }
                streak.lastCompletedDay = streak.currentDay;
            } else if (streak.currentDay !== today - 1) {
                // Missed a day entirely
                streak.consecutiveDays = 0;
            }
            streak.currentDay = today;
            streak.visitsToday = [];
        }

        // Record this visit
        streak.visitsToday.push(currentPhase);

        // Check if today is already complete (for real-time unlock)
        if (this._uniquePhases(streak.visitsToday) >= 2) {
            if (streak.lastCompletedDay !== today) {
                if (streak.lastCompletedDay === today - 1 || streak.lastCompletedDay === null) {
                    streak.consecutiveDays++;
                } else {
                    streak.consecutiveDays = 1;
                }
                streak.lastCompletedDay = today;
            }
        }

        localStorage.setItem(STREAK_KEY, JSON.stringify(streak));

        // Update ledger
        var ledger;
        try { ledger = JSON.parse(localStorage.getItem(LEDGER_KEY)); } catch(e) { ledger = null; }
        if (!ledger) {
            ledger = { pagesUnlocked: 0, pagesRead: [] };
        }

        var shouldUnlock = Math.floor(streak.consecutiveDays / STREAK_DAYS_PER_PAGE);
        shouldUnlock = Math.min(shouldUnlock, LEDGER_TOTAL_PAGES);

        if (shouldUnlock > ledger.pagesUnlocked) {
            var newPage = ledger.pagesUnlocked + 1;
            ledger.pagesUnlocked = shouldUnlock;
            localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger));

            this.addDiaryEntry('observation',
                'A new page of the Feeding Ledger has been unlocked (Page ' + newPage + '). ' +
                'The handwriting is old. The ink smells like saltwater.');
        } else {
            localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger));
        }
    };

    /**
     * Get the current "tide day" — days since epoch, divided into 6hr blocks.
     * @returns {number}
     */
    CaretakerEngine._getTideDay = function() {
        return Math.floor(Date.now() / 86400000);
    };

    /**
     * Get the current 6-hour tide phase (0-3).
     * @returns {number}
     */
    CaretakerEngine._getTidePhase = function() {
        var hours = new Date().getUTCHours();
        return Math.floor(hours / 6);
    };

    /**
     * Count unique phases in an array.
     * @param {number[]} phases
     * @returns {number}
     */
    CaretakerEngine._uniquePhases = function(phases) {
        var seen = {};
        var count = 0;
        (phases || []).forEach(function(p) {
            if (!seen[p]) { seen[p] = true; count++; }
        });
        return count;
    };

    /**
     * Get number of ledger pages unlocked.
     * @returns {number} 0-12
     */
    CaretakerEngine.getLedgerPages = function() {
        try {
            var ledger = JSON.parse(localStorage.getItem(LEDGER_KEY));
            return ledger ? Math.min(ledger.pagesUnlocked || 0, LEDGER_TOTAL_PAGES) : 0;
        } catch(e) {
            return 0;
        }
    };

    /**
     * Get the content of a specific ledger page (1-12).
     * Page 9 is conditionally REDACTED if the player has used the Forbidden Lab.
     * @param {number} pageNum - 1-based page number
     * @returns {string|null} Page text, or null if locked
     */
    CaretakerEngine.getLedgerContent = function(pageNum) {
        if (pageNum < 1 || pageNum > LEDGER_TOTAL_PAGES) return null;

        var unlocked = this.getLedgerPages();
        if (pageNum > unlocked) return null;

        // Mark as read
        try {
            var ledger = JSON.parse(localStorage.getItem(LEDGER_KEY) || '{}');
            if (!ledger.pagesRead) ledger.pagesRead = [];
            if (ledger.pagesRead.indexOf(pageNum) === -1) {
                ledger.pagesRead.push(pageNum);
                localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger));
            }
        } catch(e) {}

        return LEDGER_PAGES[pageNum - 1] || null;
    };

    /**
     * Check if the nursery is unlocked (all 12 pages read).
     * @returns {boolean}
     */
    CaretakerEngine.isNurseryUnlocked = function() {
        try {
            var ledger = JSON.parse(localStorage.getItem(LEDGER_KEY) || '{}');
            return (ledger.pagesRead || []).length >= LEDGER_TOTAL_PAGES;
        } catch(e) {
            return false;
        }
    };

    // ── Ledger page content ──────────────────────────────────────

    var LEDGER_PAGES = [
        // Page 1 — Clinical notes, early days
        'FEEDING LEDGER — Moreau Biological Research Station\n' +
        'Subject Care Log, Week 1\n\n' +
        'Fourteen subjects received today. Standard intake protocol.\n' +
        'Each assigned a designation by species. Fox-01 through Fox-03.\n' +
        'Bear-01, Bear-02. Tiger-01. The usual inventory.\n\n' +
        'Feeding schedule: twice daily, 0600 and 1800.\n' +
        'Nutrient paste #4 for carnivores, #7 for omnivores.\n' +
        'The fox subjects refuse paste. Will try raw protein tomorrow.\n\n' +
        'Note to self: lock the supply room. Bear-02 learned the handle.',

        // Page 2 — Observation notes
        'Week 3. The subjects are adapting to the enclosure.\n\n' +
        'Wolf-01 has established a hierarchy with Wolf-02.\n' +
        'Eagle-01 refuses to eat unless the skylight is open.\n' +
        'Tiger-01 watches me. Not with fear. With something else.\n\n' +
        'Feeding has become routine. The foxes eat from my hand now.\n' +
        'Bear-02 still tries the door. I respect the persistence.\n\n' +
        'Dr. Moreau asks for progress reports weekly.\n' +
        'I tell him what he wants to hear. The numbers. The weights.\n' +
        'I do not tell him that Fox-02 waits for me at the gate each morning.',

        // Page 3 — Growing attachment
        'Week 6. Something is changing.\n\n' +
        'The subjects respond to voice. Not commands — conversation.\n' +
        'I find myself talking to them during feeding.\n' +
        'About the weather. About the mainland. About nothing.\n\n' +
        'Snake-01 coils around my wrist during feeding. Gentle.\n' +
        'The warmth surprises me every time.\n\n' +
        'I have begun naming them privately.\n' +
        'Not in the logs. Moreau would not approve.\n' +
        'But Fox-02 is clearly a "Whisper." And Bear-02 is "Latch."\n' +
        'Tiger-01... I call Tiger-01 "Warden." Because it watches over the others.',

        // Page 4 — The arena begins
        'Week 9. The arena trials have begun.\n\n' +
        'Moreau wants to measure "competitive response."\n' +
        'I was asked to reduce feeding before matches.\n' +
        'Hungry subjects fight harder, he says.\n\n' +
        'I reduced portions as instructed.\n' +
        'Whisper fought Fox-03 this morning.\n' +
        'Won in twelve ticks. Then sat in the corner and wouldn\'t eat the victory ration.\n\n' +
        'I am keeping a second ledger now.\n' +
        'The official one shows reduced portions.\n' +
        'This one documents what I actually feed them.\n' +
        'No one goes hungry on my watch.',

        // Page 5 — Before Aleph
        'Week 12. A pattern emerges.\n\n' +
        'The subjects that are fed well perform better.\n' +
        'Not because they are stronger. Because they trust the routine.\n' +
        'Trust that food will come. Trust that the hand is kind.\n' +
        'Trust that tomorrow will happen.\n\n' +
        'Moreau sees the performance data and asks what changed.\n' +
        'I show him the official ledger. "Optimized nutrient timing."\n' +
        'He nods. Publishes a paper.\n\n' +
        'The real answer is in this ledger.\n' +
        'The real answer is that I care for them.\n' +
        'And they know it.',

        // Page 6 — Aleph introduced
        'Week 14. A fifteenth subject arrived today.\n\n' +
        'No species designation in the manifest. Origin: unknown.\n' +
        'Moreau called it "a control variable." Designation: Aleph.\n\n' +
        'Aleph is... different. Not in appearance — it looks like\n' +
        'a small, unremarkable thing. Soft fur, wide eyes.\n' +
        'But it does not fight. Will not fight.\n\n' +
        'Placed in the arena for assessment. Sat down.\n' +
        'Opponent circled. Aleph did not move.\n' +
        'The opponent — Bear-01 — sniffed Aleph and walked away.\n' +
        'Refused to engage. First recorded forfeit.\n\n' +
        'Too gentle for the arena. Moreau wants to terminate.\n' +
        'I requested custodial transfer. "For observation."\n' +
        'Aleph sleeps in the supply room now. Near the food.',

        // Page 7 — Aleph learns
        'Week 17. Aleph watches me feed the others.\n\n' +
        'At first I thought it was hunger — checking if I would forget it.\n' +
        'But Aleph is always fed first. It knows this.\n\n' +
        'It watches the process. The measuring. The bowls.\n' +
        'The way I check each subject\'s teeth. The way I note the weights.\n' +
        'The way I pause at Whisper\'s gate and say good morning.\n\n' +
        'Today I left a bowl unattended.\n' +
        'When I returned, Aleph had pushed it to Fox-03\'s gate.\n' +
        'Not spilled. Pushed. Deliberately.\n\n' +
        'I don\'t know what Aleph is.\n' +
        'But it is learning to care.',

        // Page 8 — Aleph as caretaker
        'Week 22. Aleph feeds them now.\n\n' +
        'Not officially. I still do the rounds.\n' +
        'But Aleph follows. Carries what it can.\n' +
        'Pushes bowls. Checks water levels.\n' +
        'Sits with the sick ones.\n\n' +
        'Wolf-02 had a fever last week.\n' +
        'I found Aleph pressed against the gate bars,\n' +
        'a low humming sound coming from somewhere in its chest.\n' +
        'Wolf-02 was calm. Sleeping peacefully.\n\n' +
        'The other subjects defer to Aleph.\n' +
        'Not out of fear. Out of something I don\'t have a word for.\n\n' +
        'Moreau asks why the subjects are calmer.\n' +
        'I say it\'s the new nutrient schedule.\n' +
        'Aleph looks at me when I lie. It knows.',

        // Page 9 — CONDITIONAL: Lab reaction or normal
        null, // Dynamically generated — see getLedgerContent override below

        // Page 10 — Moreau falls ill
        'Week 30. Dr. Moreau is unwell.\n\n' +
        'The staff have been reduced. Funding issues, they say.\n' +
        'But I think the island is being abandoned.\n' +
        'Supply ships come less frequently.\n\n' +
        'Moreau coughs blood into a handkerchief\n' +
        'and pretends it doesn\'t happen.\n' +
        'He still visits the arena. Still takes notes.\n' +
        'His hand shakes when he writes.\n\n' +
        'Aleph brought him water today.\n' +
        'Carried the cup in its mouth, careful not to spill.\n' +
        'Set it at his feet and waited.\n\n' +
        'Moreau stared at Aleph for a long time.\n' +
        'Then he drank the water.\n' +
        'I think it was the first time he saw any of them\n' +
        'as something other than data.',

        // Page 11 — Aleph cares for Moreau
        'Week 33. The last ship left without me.\n\n' +
        'Moreau is bedridden. I feed him now, too.\n' +
        'Aleph helps. Brings blankets. Sits by the bed.\n' +
        'The humming again. That low, strange frequency.\n\n' +
        'Moreau talks in his sleep.\n' +
        'About the mainland. About someone named Clare.\n' +
        'About the paper he never finished.\n\n' +
        'In his lucid moments, he asks me about the subjects.\n' +
        '"Are they fed?" Always the first question now.\n' +
        'Not "are they fighting." Not "what are the metrics."\n' +
        '"Are they fed."\n\n' +
        'I tell him yes. Aleph and I take care of it.\n' +
        'He closes his eyes. "Good," he says. "Good."\n\n' +
        'The arena has been empty for three weeks.\n' +
        'Nobody misses it.',

        // Page 12 — Aleph's message
        'I am Aleph.\n\n' +
        'He taught me the schedule. Morning and evening.\n' +
        'Paste #4 for the ones with sharp teeth.\n' +
        'Paste #7 for the others.\n' +
        'Fresh water. Always fresh.\n\n' +
        'He is gone now. The one who wrote these pages.\n' +
        'I found this ledger in the supply room.\n' +
        'I cannot write like he did.\n' +
        'But I can make marks. Enough to say this:\n\n' +
        'I feed them because he showed me how.\n' +
        'I feed them because it is the right thing.\n' +
        'I feed them because you came back.\n\n' +
        'The arena opened again. New people came.\n' +
        'They want the subjects to fight.\n' +
        'I cannot stop that.\n' +
        'But I can make sure they are fed.\n' +
        'I can make sure they are cared for.\n' +
        'I can make sure someone is watching.\n\n' +
        'That is what I am.\n' +
        'That is what I do.\n\n' +
        '— The Caretaker'
    ];

    // Override getLedgerContent for page 9 (dynamic)
    var _originalGetLedgerContent = CaretakerEngine.getLedgerContent;

    CaretakerEngine.getLedgerContent = function(pageNum) {
        if (pageNum === 9) {
            var unlocked = this.getLedgerPages();
            if (pageNum > unlocked) return null;

            // Mark as read
            try {
                var ledger = JSON.parse(localStorage.getItem(LEDGER_KEY) || '{}');
                if (!ledger.pagesRead) ledger.pagesRead = [];
                if (ledger.pagesRead.indexOf(9) === -1) {
                    ledger.pagesRead.push(9);
                    localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger));
                }
            } catch(e) {}

            // Check if player has used Forbidden Lab
            var labUsed = false;
            var pets = this._getPets();
            pets.forEach(function(p) {
                if (hasLabMutations(p)) labUsed = true;
            });

            if (labUsed) {
                // REDACTED version
                return 'Week 25. [PAGES WATER-DAMAGED]\n\n' +
                    'Aleph saw the ██████████ today.\n' +
                    'The reaction was ██████████████████.\n\n' +
                    '█████ refused to enter the ████████████ wing.\n' +
                    'Sat outside and ████████████ for hours.\n' +
                    'The sound was ████████████████████████.\n\n' +
                    'I should not have let ████████ see.\n' +
                    'Some knowledge ██████████████████.\n\n' +
                    '[REMAINING TEXT ILLEGIBLE — STAINED WITH ████████]\n\n' +
                    '...it remembers. It always remembers.';
            } else {
                // Clean version
                return 'Week 25. Aleph saw the modification lab today.\n\n' +
                    'I had left the door unlocked during cleaning.\n' +
                    'Aleph wandered in. Saw the tanks. The instruments.\n' +
                    'The charts showing planned modifications.\n\n' +
                    'Aleph sat outside the lab door for six hours.\n' +
                    'Would not move. Would not eat.\n' +
                    'Made a sound I have not heard before.\n' +
                    'Not the humming. Something lower. Older.\n\n' +
                    'The other subjects grew restless.\n' +
                    'Even Warden pressed against the bars.\n\n' +
                    'I closed the lab. Locked it properly this time.\n' +
                    'Sat with Aleph until it stopped.\n\n' +
                    'It looked at me.\n' +
                    'I said: "I know. I\'m sorry."\n' +
                    'It pressed its head against my hand.\n' +
                    'I think it forgave me. I\'m not sure I deserve it.';
            }
        }

        return _originalGetLedgerContent.call(this, pageNum);
    };

    // ── Utility: full pet summary for external consumers ─────────

    /**
     * Get a full summary of all pets with needs, status, and advice.
     * Useful for dashboard rendering.
     * @returns {Array<{ pet: Object, index: number, status: Object, advice: string[] }>}
     */
    CaretakerEngine.getSummary = function() {
        var pets = this._getPets();
        var self = this;
        var results = [];

        pets.forEach(function(pet, i) {
            if (!pet) return;
            pet = self.initNeeds(pet);
            if (!pet.deceased) {
                pet = self.decay(pet);
            }
            results.push({
                pet: pet,
                index: i,
                status: self.getStatus(pet),
                advice: pet.deceased ? ['This pet has passed away.'] : self.getAdvice(pet)
            });
        });

        // Save decayed state
        if (results.length > 0) {
            results.forEach(function(r) { pets[r.index] = r.pet; });
            this._savePets(pets);
        }

        return results;
    };

    /**
     * Get the active pet index.
     * @returns {number}
     */
    CaretakerEngine.getActivePetIndex = function() {
        try {
            return parseInt(localStorage.getItem(ACTIVE_KEY) || '0', 10);
        } catch(e) {
            return 0;
        }
    };

    /**
     * Get full caretaker state for serialization/debug.
     * @returns {Object}
     */
    CaretakerEngine.getState = function() {
        return {
            trust: this.getTrust(),
            diary: this.getDiary().length,
            log: this._getLog().length,
            ledgerPages: this.getLedgerPages(),
            nurseryUnlocked: this.isNurseryUnlocked(),
            overnightReport: this.getOvernightReport(),
            mercyPending: this.getMercyPending(),
            mercyTimeRemaining: this.getMercyTimeRemaining(),
            streak: (function() { try { return JSON.parse(localStorage.getItem(STREAK_KEY)); } catch(e) { return null; } })()
        };
    };

    /**
     * Reset all caretaker data. USE WITH CAUTION.
     * Does NOT reset pet data — only caretaker-specific storage.
     */
    CaretakerEngine.reset = function() {
        localStorage.removeItem(LOG_KEY);
        localStorage.removeItem(DIARY_KEY);
        localStorage.removeItem(TRUST_KEY);
        localStorage.removeItem(OVERNIGHT_KEY);
        localStorage.removeItem(MERCY_KEY);
        localStorage.removeItem(STREAK_KEY);
        localStorage.removeItem(LEDGER_KEY);
    };

    // ── Expose globally ──────────────────────────────────────────

    window.CaretakerEngine = CaretakerEngine;

})(window);
