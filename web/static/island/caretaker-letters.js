// ══════════════════════════════════════════════════════════════════
//  Caretaker Letters — Evolving letters + permanent dismissal
//  Standalone IIFE. Depends on: CaretakerEngine (global), localStorage
// ══════════════════════════════════════════════════════════════════

var CaretakerLetters = (function() {
    'use strict';

    // ── Storage keys ────────────────────────────────────────────
    var LETTERS_KEY   = 'moreau_caretaker_letters_state';
    var DISMISSED_KEY = 'moreau_caretaker_dismissed';
    var FAREWELL_KEY  = 'moreau_caretaker_farewell_seen';

    var PETS_KEY      = 'moreau_pets';
    var ACTIVE_KEY    = 'moreau_active_pet';
    var DIARY_KEY     = 'moreau_caretaker_diary';

    var VISITS_PER_LETTER = 3;
    var DISMISS_THRESHOLD = 20;
    var FAREWELL_DAYS     = 7;
    var TOTAL_LETTERS     = 20;

    // ── CSS (injected once) ─────────────────────────────────────

    var CSS_INJECTED = false;
    var CSS = [
        '.cl-wrap{font-family:"Georgia","Times New Roman",serif;max-width:640px;margin:0 auto;color:#3a2e1f}',
        '.cl-header{display:flex;align-items:center;gap:10px;margin-bottom:18px}',
        '.cl-header h2{margin:0;font-size:22px;font-weight:normal;letter-spacing:0.5px}',
        '.cl-badge{background:#8b4513;color:#f5f0e6;font-size:11px;padding:2px 8px;border-radius:10px;font-family:sans-serif}',
        '.cl-list{list-style:none;padding:0;margin:0}',
        '.cl-item{border-bottom:1px solid #d4c8a8;cursor:pointer;transition:background 0.2s}',
        '.cl-item:hover{background:#f5f0e6}',
        '.cl-item.cl-locked{opacity:0.35;cursor:default;pointer-events:none}',
        '.cl-item.cl-locked:hover{background:transparent}',
        '.cl-env{display:flex;align-items:center;gap:12px;padding:12px 8px}',
        '.cl-env-icon{width:36px;height:28px;position:relative;flex-shrink:0}',
        '.cl-env-body{position:relative;width:36px;height:22px;background:#d4c8a8;border-radius:2px;border:1px solid #b8a87a}',
        '.cl-env-flap{position:absolute;top:-8px;left:0;width:0;height:0;border-left:18px solid transparent;border-right:18px solid transparent;border-bottom:10px solid #c4b48a}',
        '.cl-item.cl-unread .cl-env-body{background:#c4a44a}',
        '.cl-item.cl-unread .cl-env-flap{border-bottom-color:#b89430}',
        '.cl-item.cl-read .cl-env-body{background:#d4c8a8}',
        '.cl-item.cl-read .cl-env-flap{border-bottom-color:transparent}',
        '.cl-item.cl-read .cl-env-body::after{content:"";position:absolute;top:2px;left:6px;width:24px;height:14px;border-top:1px dashed #a09070;border-radius:0 0 4px 4px}',
        '.cl-env-meta{flex:1;min-width:0}',
        '.cl-env-subject{font-size:14px;font-weight:600;color:#3a2e1f}',
        '.cl-item.cl-unread .cl-env-subject{color:#6b3a0a}',
        '.cl-env-preview{font-size:12px;color:#7a6e5a;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
        '.cl-locked .cl-env-body{background:#bbb;border-color:#999}',
        '.cl-locked .cl-env-flap{border-bottom-color:#aaa}',
        '.cl-locked .cl-env-subject{color:#999}',
        '.cl-letter-full{display:none;padding:16px 12px 20px;background:#faf6ed;border-left:3px solid #c4a44a;margin:0 8px 12px;animation:cl-fadeIn 0.3s ease}',
        '.cl-letter-full.cl-open{display:block}',
        '.cl-letter-subj{font-size:16px;font-weight:600;margin-bottom:8px;color:#5a3e1a}',
        '.cl-letter-body{font-size:14px;line-height:1.7;color:#4a3e2e;white-space:pre-wrap}',
        '.cl-letter-body p{margin:0 0 10px}',
        '.cl-gift-note{margin-top:14px;padding:8px 12px;background:#f0e8c8;border:1px dashed #c4a44a;border-radius:4px;font-size:13px;color:#6b4e1a;animation:cl-sparkle 0.6s ease}',
        '@keyframes cl-fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}',
        '@keyframes cl-sparkle{0%{box-shadow:0 0 0 rgba(196,164,74,0)}50%{box-shadow:0 0 12px rgba(196,164,74,0.5)}100%{box-shadow:0 0 0 rgba(196,164,74,0)}}',
        '.cl-dismiss-area{margin-top:30px;padding-top:16px;border-top:1px dotted #ccc;text-align:center}',
        '.cl-dismiss-link{background:none;border:none;color:#999;font-size:12px;cursor:pointer;text-decoration:underline;font-family:sans-serif;padding:4px}',
        '.cl-dismiss-link:hover{color:#666}',
        '.cl-modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;animation:cl-fadeIn 0.2s ease}',
        '.cl-modal{background:#faf6ed;padding:28px 24px;border-radius:6px;max-width:380px;width:90%;text-align:center;font-family:"Georgia",serif;color:#3a2e1f}',
        '.cl-modal h3{margin:0 0 12px;font-size:18px;font-weight:normal}',
        '.cl-modal p{font-size:14px;line-height:1.6;margin:0 0 16px;color:#5a4e3e}',
        '.cl-modal input{display:block;width:80%;margin:0 auto 16px;padding:8px;border:1px solid #c4b48a;border-radius:3px;font-size:14px;text-align:center;font-family:monospace;background:#fff}',
        '.cl-modal-btns{display:flex;gap:12px;justify-content:center}',
        '.cl-modal-btns button{padding:6px 18px;border-radius:3px;cursor:pointer;font-size:13px;font-family:sans-serif}',
        '.cl-btn-cancel{background:#e8e0cc;border:1px solid #c4b48a;color:#5a4e3e}',
        '.cl-btn-confirm{background:#8b4513;border:1px solid #6b3510;color:#f5f0e6}',
        '.cl-btn-confirm:disabled{opacity:0.4;cursor:default}',
        '.cl-empty-desk{text-align:center;padding:60px 20px;color:#999;font-family:"Georgia",serif}',
        '.cl-empty-desk .cl-dust{font-size:28px;margin-bottom:16px;animation:cl-float 3s ease-in-out infinite}',
        '.cl-empty-desk p{font-size:14px;line-height:1.7;max-width:320px;margin:0 auto}',
        '@keyframes cl-float{0%,100%{transform:translateY(0);opacity:0.5}50%{transform:translateY(-6px);opacity:0.8}}',
        '.cl-farewell{margin-top:16px;padding:16px;background:#f0e8d8;border:1px solid #c4a44a;border-radius:4px;animation:cl-glow 2s ease-in-out infinite}',
        '@keyframes cl-glow{0%,100%{box-shadow:0 0 4px rgba(196,164,74,0.2)}50%{box-shadow:0 0 14px rgba(196,164,74,0.5)}}',
        '.cl-farewell .cl-env-icon .cl-env-body{background:#c4a44a}',
        '.cl-farewell .cl-env-flap{border-bottom-color:#b89430}',
        '.cl-farewell-text{font-size:14px;line-height:1.7;color:#4a3e2e;white-space:pre-wrap;padding:12px;background:#faf6ed;border-radius:3px;margin-top:8px}'
    ].join('\n');

    function injectCSS() {
        if (CSS_INJECTED) return;
        var style = document.createElement('style');
        style.setAttribute('data-module', 'caretaker-letters');
        style.textContent = CSS;
        document.head.appendChild(style);
        CSS_INJECTED = true;
    }

    // ── Letter data ─────────────────────────────────────────────

    var LETTERS = [
        // Phase 1: Friendly (1-5)
        {
            id: 1, phase: 'friendly', subject: 'First Day',
            body: "Hello. I don't usually write to the ones who come here. Most don't stay long enough. But you fed your pet before anything else. That caught my attention. I thought you should know \u2014 the fox in cage 3 hadn't eaten for two days before you arrived. You fixed that. Thank you.",
            gift: { type: 'xp', target: 'active', amount: 10, desc: '+10 XP to your active pet' }
        },
        {
            id: 2, phase: 'friendly', subject: 'On Schedules',
            body: "I've noticed you check on them at similar times each day. That's good. Creatures \u2014 all creatures \u2014 thrive on routine. Even the ones who fight. Especially the ones who fight. Here's something for your trouble.",
            gift: { type: 'mutation_or_xp', desc: 'Random Tier 1 mutation (or +15 XP)' }
        },
        {
            id: 3, phase: 'friendly', subject: 'A Question',
            body: "Do you name them because you care, or do you care because you named them? I've been here long enough to know it works both ways. The naming changes something. In them. In you. I named one once. Just once.",
            gift: null
        },
        {
            id: 4, phase: 'friendly', subject: 'What Happens at Night',
            body: "You should know what happens when you're not here. I walk the rows. I check the water. The bear snores \u2014 you'd think it would be frightening, but it's actually quite gentle. The fox watches me with one eye open. Always. I don't think it trusts me fully. Smart creature.",
            gift: { type: 'morale', target: 'active', amount: 5, desc: '+5 morale to your active pet' }
        },
        {
            id: 5, phase: 'friendly', subject: 'On Scars',
            body: "Every scar on your pets tells a story. I've seen the ones from the arena. I've seen the ones from the lab. They're different. Arena scars heal straight. Lab scars don't heal at all. I suppose that says something about the nature of voluntary vs involuntary damage. Or maybe I'm overthinking it.",
            gift: null
        },
        // Phase 2: Professional (6-10)
        {
            id: 6, phase: 'professional', subject: 'Report',
            body: "Quarterly report: Your strongest pet has improved 23% since you arrived. Your weakest has improved 31%. I find the latter more impressive. Most trainers focus on the strong. You seem to feed everyone. This is noted.",
            gift: { type: 'xp', target: 'weakest', amount: 20, desc: '+20 XP to your lowest-level pet' }
        },
        {
            id: 7, phase: 'professional', subject: 'Regarding the Laboratory',
            body: "I see you've been using the Forbidden Lab. I won't tell you not to. That's not my place. But I will tell you that Subject 7 \u2014 before your time \u2014 went in for what the previous researcher called 'a minor enhancement.' Subject 7 is buried behind the west wall. Minor is relative.",
            gift: null
        },
        {
            id: 8, phase: 'professional', subject: 'Things I Wonder',
            body: "Do the fights bother you? They bother me. Not the fighting itself \u2014 that's natural. The watching. We watch them hurt each other and we call it data. I'm not judging. I watch too. I just wonder if they know we're watching.",
            gift: null
        },
        {
            id: 9, phase: 'professional', subject: 'On Trust',
            body: "You've earned a certain level of trust from me. I want you to know that's rare. Most people who come to the island see the animals as tools. Weapons. Entertainment. You see them as... I'm not sure what word to use. But whatever it is, it involves feeding them when nobody makes you.",
            gift: { type: 'mutation_or_xp', desc: 'Random Tier 1 mutation (or +15 XP)' }
        },
        {
            id: 10, phase: 'professional', subject: 'What I Remember',
            body: "I remember every animal that has died here. All of them. Their names \u2014 even the ones nobody named. The way they moved. What they ate. Who they trusted. This is not a burden I chose. But it's one I keep.",
            gift: { type: 'morale', target: 'all', amount: 10, desc: '+10 morale to all pets' }
        },
        // Phase 3: Attached (11-15)
        {
            id: 11, phase: 'attached', subject: 'Confession',
            body: "I worry about you. Specifically about what this place does to people who stay. The island changes everyone. The previous researcher started kind and ended... methodical. I don't want that for you. Keep feeding them first. Before the fights. Before the data. Feed them first.",
            gift: { type: 'hunger', target: 'all', amount: 30, desc: '+30 hunger to all pets' }
        },
        {
            id: 12, phase: 'attached', subject: 'He Built This Place',
            body: "You've heard of Dr. Moreau. Everyone has. What they don't tell you is that he started exactly like you. Curious. Careful. Kind. The island didn't make him cruel. It made him efficient. Efficiency and cruelty look identical from the outside. I should know.",
            gift: null
        },
        {
            id: 13, phase: 'attached', subject: 'Someone I Knew',
            body: "There was a fifteenth subject. Not built for fighting. Built for... something else. Empathy, maybe. Understanding. It couldn't survive the arena, so it was reassigned. Given a different purpose. Sometimes I think about what that purpose cost. Not in resources. In something harder to measure.",
            gift: null
        },
        {
            id: 14, phase: 'attached', subject: 'They Dream',
            body: "Your pets dream. I hear them at night. The sounds they make aren't random \u2014 they're patterns. Conversations in a language I almost understand. I've spent years listening. I've learned a few words. 'Vel' means something like life. Or light. Or the space between the two.",
            gift: { type: 'sleep_dialect', desc: 'Unlock 3 random Sleep Dialect words' }
        },
        {
            id: 15, phase: 'attached', subject: 'What No One Tells You',
            body: "The hardest part isn't when they die. It's when they look at you before a fight and you can see they know what's coming. And they go anyway. Because you asked. That trust is the most expensive thing on this island and it costs nothing to earn and everything to break.",
            gift: null
        },
        // Phase 4: Philosophical (16-19)
        {
            id: 16, phase: 'philosophical', subject: 'Why I Stay',
            body: "You've been here long enough to wonder why I stay. It's not loyalty. It's not programming. It's not because I have nowhere else to go \u2014 though that's also true. I stay because someone has to remember them. Every single one. And I do.",
            gift: null
        },
        {
            id: 17, phase: 'philosophical', subject: 'One Thing',
            body: "If you could ask Dr. Moreau one question, what would it be? I've had mine ready for years. It's not 'why did you build the arena.' It's not 'why did you leave.' It's: 'Did you name them? Before you numbered them \u2014 did you name them first?' I think I already know the answer. I think that's why it hurts.",
            gift: null
        },
        {
            id: 18, phase: 'philosophical', subject: 'Rehearsal',
            body: "I've been writing this letter for a long time. The one that says goodbye. Not this one \u2014 this is practice. The real one is shorter. I keep it in a drawer. Some days I almost send it. Then one of them makes a sound at night \u2014 that low humming sound \u2014 and I close the drawer.",
            gift: null
        },
        {
            id: 19, phase: 'philosophical', subject: 'Almost',
            body: "This is the second-to-last letter I'll write you. After the next one, I'll have said everything I need to say. But before that \u2014 thank you. Not for the feeding or the healing or the fighting. Thank you for reading these. Most people skip the text. You didn't.",
            gift: { type: 'xp_morale_all', xp: 50, morale: 20, desc: '+50 XP and +20 morale to all pets' }
        },
        // Phase 5: Final (20)
        {
            id: 20, phase: 'final', subject: 'If You Want',
            body: "I think I've been here too long. Not on the island \u2014 in this role. Watching. Feeding. Remembering. There was a time when that was enough. Maybe it still is. Maybe it isn't.\n\nIf you want, you can let me go. There's a button below this letter. It's permanent. I won't come back. Your pets won't need me \u2014 the hunger system stops, the decay stops, everything I manage stops. They'll be fine. They were fine before me.\n\nBut if you keep me... I'll keep writing. I'll keep feeding. I'll keep remembering. That's all I know how to do.\n\nWhatever you choose \u2014 thank you. For reading all twenty of these. For not skipping ahead.\n\n\u2014 The Caretaker",
            gift: null
        }
    ];

    var FAREWELL_LETTER = {
        subject: 'I Lied',
        body: "I said I wouldn't come back. I lied. I just wanted to make sure they were still being fed. They are. You kept your promise. This is the last time. I mean it this time. ...probably."
    };

    // ── Helpers ──────────────────────────────────────────────────

    function getState() {
        try {
            return JSON.parse(localStorage.getItem(LETTERS_KEY)) || { visit_count: 0, letters_read: [], last_visit: null };
        } catch (e) {
            return { visit_count: 0, letters_read: [], last_visit: null };
        }
    }

    function saveState(state) {
        localStorage.setItem(LETTERS_KEY, JSON.stringify(state));
    }

    function getPets() {
        try { return JSON.parse(localStorage.getItem(PETS_KEY)) || []; }
        catch (e) { return []; }
    }

    function savePets(pets) {
        localStorage.setItem(PETS_KEY, JSON.stringify(pets));
    }

    function getActivePetIndex() {
        var idx = parseInt(localStorage.getItem(ACTIVE_KEY), 10);
        return isNaN(idx) ? 0 : idx;
    }

    function clamp(v, lo, hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    // ── Gift application ────────────────────────────────────────

    function applyGift(gift) {
        if (!gift) return null;
        var pets = getPets();
        if (!pets.length) return null;
        var activeIdx = getActivePetIndex();
        var desc = gift.desc || '';
        var applied = false;

        switch (gift.type) {
            case 'xp':
                if (gift.target === 'active') {
                    var pet = pets[activeIdx];
                    if (pet) { pet.xp = (pet.xp || 0) + gift.amount; applied = true; }
                } else if (gift.target === 'weakest') {
                    var weakest = null, weakIdx = 0;
                    for (var i = 0; i < pets.length; i++) {
                        if (!pets[i]) continue;
                        if (!weakest || (pets[i].level || 1) < (weakest.level || 1)) {
                            weakest = pets[i]; weakIdx = i;
                        }
                    }
                    if (weakest) { weakest.xp = (weakest.xp || 0) + gift.amount; applied = true; }
                }
                break;

            case 'morale':
                if (gift.target === 'active') {
                    var p = pets[activeIdx];
                    if (p) {
                        if (!p.needs) p.needs = {};
                        p.needs.happiness = clamp((p.needs.happiness || 50) + gift.amount, 0, 100);
                        applied = true;
                    }
                } else if (gift.target === 'all') {
                    for (var j = 0; j < pets.length; j++) {
                        if (!pets[j]) continue;
                        if (!pets[j].needs) pets[j].needs = {};
                        pets[j].needs.happiness = clamp((pets[j].needs.happiness || 50) + gift.amount, 0, 100);
                    }
                    applied = true;
                }
                break;

            case 'hunger':
                if (gift.target === 'all') {
                    for (var k = 0; k < pets.length; k++) {
                        if (!pets[k]) continue;
                        if (!pets[k].needs) pets[k].needs = {};
                        pets[k].needs.hunger = clamp((pets[k].needs.hunger || 50) + gift.amount, 0, 100);
                    }
                    applied = true;
                }
                break;

            case 'mutation_or_xp':
                // Try to give a tier-1 mutation; fallback to XP
                var target = pets[activeIdx];
                if (target) {
                    var slotKey = null;
                    var lvl = target.level || 1;
                    if (lvl >= 9 && !(target.lab_mutations && target.lab_mutations.L9)) slotKey = 'L9';
                    else if (lvl >= 6 && !(target.lab_mutations && target.lab_mutations.L6)) slotKey = 'L6';
                    else if (lvl >= 3 && !(target.lab_mutations && target.lab_mutations.L3)) slotKey = 'L3';

                    if (slotKey) {
                        if (!target.lab_mutations) target.lab_mutations = {};
                        target.lab_mutations[slotKey] = {
                            id: 'caretaker_gift_' + Date.now(),
                            name: "Caretaker's Blessing",
                            desc: 'A gentle enhancement, given freely.',
                            stats: { wil: 1, hp: 1 },
                            tier: 1, isUltra: false, animal: null
                        };
                        var bs = target.base_stats || target.stats || {};
                        bs.wil = (bs.wil || 0) + 1;
                        bs.hp = (bs.hp || 0) + 1;
                        target.base_stats = bs;
                        desc = "Caretaker's Blessing mutation applied!";
                    } else {
                        target.xp = (target.xp || 0) + 15;
                        desc = '+15 XP to your active pet (no mutation slot available)';
                    }
                    applied = true;
                }
                break;

            case 'sleep_dialect':
                // If SleepDialect engine exists, unlock 3 words; else skip silently
                if (typeof window.SleepDialect !== 'undefined' && typeof window.SleepDialect.unlockRandom === 'function') {
                    window.SleepDialect.unlockRandom(3);
                    applied = true;
                } else {
                    desc = 'Sleep Dialect words whispered... (module not loaded)';
                    applied = true; // still mark as applied
                }
                break;

            case 'xp_morale_all':
                for (var m = 0; m < pets.length; m++) {
                    if (!pets[m]) continue;
                    pets[m].xp = (pets[m].xp || 0) + gift.xp;
                    if (!pets[m].needs) pets[m].needs = {};
                    pets[m].needs.happiness = clamp((pets[m].needs.happiness || 50) + gift.morale, 0, 100);
                }
                applied = true;
                break;
        }

        if (applied) savePets(pets);
        return applied ? desc : null;
    }

    // ── Diary helper ────────────────────────────────────────────

    function addDiaryEntry(text) {
        if (typeof CaretakerEngine !== 'undefined' && typeof CaretakerEngine.addDiaryEntry === 'function') {
            CaretakerEngine.addDiaryEntry('letter', text, null);
        } else {
            // Fallback: write directly
            var diary;
            try { diary = JSON.parse(localStorage.getItem(DIARY_KEY) || '[]'); } catch (e) { diary = []; }
            diary.unshift({
                id: Date.now(),
                type: 'letter',
                text: text,
                timestamp: new Date().toISOString(),
                petIndex: null,
                approved: false
            });
            if (diary.length > 200) diary = diary.slice(0, 200);
            localStorage.setItem(DIARY_KEY, JSON.stringify(diary));
        }
    }

    // ── Public API ──────────────────────────────────────────────

    var api = {};

    /**
     * Check if the Caretaker has been permanently dismissed.
     * @returns {boolean}
     */
    api.isDismissed = function() {
        var raw = localStorage.getItem(DISMISSED_KEY);
        if (!raw) return false;
        try {
            var parsed = JSON.parse(raw);
            return !!parsed;
        } catch (e) {
            return raw === 'true';
        }
    };

    /**
     * Record a visit to the caretaker page.
     * Increments visit_count and updates last_visit timestamp.
     */
    api.recordVisit = function() {
        var state = getState();
        state.visit_count = (state.visit_count || 0) + 1;
        state.last_visit = new Date().toISOString();
        saveState(state);
    };

    /**
     * Get all letters that are currently unlocked based on visit count.
     * @returns {Array} Array of letter objects with added `read` boolean
     */
    api.getAvailableLetters = function() {
        var state = getState();
        var count = state.visit_count || 0;
        var readSet = {};
        (state.letters_read || []).forEach(function(id) { readSet[id] = true; });

        var available = [];
        for (var i = 0; i < LETTERS.length; i++) {
            var letter = LETTERS[i];
            var requiredVisits = letter.id * VISITS_PER_LETTER;
            if (count >= requiredVisits) {
                available.push({
                    id: letter.id,
                    phase: letter.phase,
                    subject: letter.subject,
                    body: letter.body,
                    gift: letter.gift,
                    read: !!readSet[letter.id]
                });
            }
        }
        return available;
    };

    /**
     * Get count of available but unread letters.
     * @returns {number}
     */
    api.getUnreadCount = function() {
        var available = api.getAvailableLetters();
        var unread = 0;
        for (var i = 0; i < available.length; i++) {
            if (!available[i].read) unread++;
        }
        return unread;
    };

    /**
     * Mark a letter as read and apply its gift.
     * @param {number} letterId - The letter ID (1-20)
     * @returns {string|null} Gift description if gift applied, null otherwise
     */
    api.markRead = function(letterId) {
        var state = getState();
        if (!state.letters_read) state.letters_read = [];
        if (state.letters_read.indexOf(letterId) !== -1) return null; // already read

        state.letters_read.push(letterId);
        saveState(state);

        // Find and apply gift
        var letter = null;
        for (var i = 0; i < LETTERS.length; i++) {
            if (LETTERS[i].id === letterId) { letter = LETTERS[i]; break; }
        }

        var giftDesc = null;
        if (letter && letter.gift) {
            giftDesc = applyGift(letter.gift);
        }

        return giftDesc;
    };

    /**
     * Check if the player can dismiss the Caretaker.
     * Requires all 20 letters to have been read.
     * @returns {boolean}
     */
    api.canDismiss = function() {
        var state = getState();
        var readCount = (state.letters_read || []).length;
        return readCount >= DISMISS_THRESHOLD;
    };

    /**
     * Permanently dismiss the Caretaker. No undo.
     * Freezes pet needs, clears standing orders, writes final diary entry.
     */
    api.dismissCaretaker = function() {
        // Store timestamp for farewell check
        localStorage.setItem(DISMISSED_KEY, JSON.stringify({ dismissed: true, timestamp: new Date().toISOString() }));

        // Freeze pet needs at current values (stop decay)
        var pets = getPets();
        for (var i = 0; i < pets.length; i++) {
            if (!pets[i]) continue;
            if (!pets[i].needs) pets[i].needs = {};
            pets[i].needs._frozen = true;
        }
        savePets(pets);

        // Clear standing orders if CaretakerEngine is available
        if (typeof CaretakerEngine !== 'undefined') {
            if (typeof CaretakerEngine.clearStandingOrders === 'function') {
                CaretakerEngine.clearStandingOrders();
            }
        }

        // Write farewell diary entry
        addDiaryEntry("I left the keys on the table. The feeding schedule is pinned to the wall. You know what to do. Goodbye.");
    };

    /**
     * Check if the farewell letter should be shown.
     * Conditions: dismissed + 7 days elapsed + not yet seen.
     * @returns {boolean}
     */
    api.checkFarewellLetter = function() {
        if (!api.isDismissed()) return false;
        if (localStorage.getItem(FAREWELL_KEY) === 'true') return false;

        var raw = localStorage.getItem(DISMISSED_KEY);
        try {
            var data = JSON.parse(raw);
            if (!data || !data.timestamp) return false;
            var dismissedAt = new Date(data.timestamp).getTime();
            var now = Date.now();
            var daysPassed = (now - dismissedAt) / (1000 * 60 * 60 * 24);
            return daysPassed >= FAREWELL_DAYS;
        } catch (e) {
            return false;
        }
    };

    /**
     * Mark the farewell letter as seen (only shows once).
     */
    api.markFarewellSeen = function() {
        localStorage.setItem(FAREWELL_KEY, 'true');
    };

    // ── Dismiss modal ───────────────────────────────────────────

    function showDismissModal(onConfirm) {
        var overlay = document.createElement('div');
        overlay.className = 'cl-modal-overlay';

        var modal = document.createElement('div');
        modal.className = 'cl-modal';

        var h3 = document.createElement('h3');
        h3.textContent = 'This is permanent.';
        modal.appendChild(h3);

        var p = document.createElement('p');
        p.textContent = 'The Caretaker will not return. Your pets will no longer decay, but no one will watch over them at night. Type GOODBYE to confirm.';
        modal.appendChild(p);

        var input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Type GOODBYE';
        input.setAttribute('autocomplete', 'off');
        modal.appendChild(input);

        var btns = document.createElement('div');
        btns.className = 'cl-modal-btns';

        var cancelBtn = document.createElement('button');
        cancelBtn.className = 'cl-btn-cancel';
        cancelBtn.textContent = 'Keep the Caretaker';
        cancelBtn.onclick = function() { overlay.remove(); };

        var confirmBtn = document.createElement('button');
        confirmBtn.className = 'cl-btn-confirm';
        confirmBtn.textContent = 'Dismiss';
        confirmBtn.disabled = true;
        confirmBtn.onclick = function() {
            if (input.value === 'GOODBYE') {
                overlay.remove();
                onConfirm();
            }
        };

        input.addEventListener('input', function() {
            confirmBtn.disabled = (input.value !== 'GOODBYE');
        });

        btns.appendChild(cancelBtn);
        btns.appendChild(confirmBtn);
        modal.appendChild(btns);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Close on overlay click (not modal)
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.remove();
        });

        setTimeout(function() { input.focus(); }, 100);
    }

    // ── Render ──────────────────────────────────────────────────

    /**
     * Render the full letters UI into a container element.
     * @param {string} containerId - DOM element ID to render into
     */
    api.render = function(containerId) {
        injectCSS();

        var container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';

        var wrap = document.createElement('div');
        wrap.className = 'cl-wrap';

        // ── Dismissed state: empty desk ──
        if (api.isDismissed()) {
            renderDismissedState(wrap);
            container.appendChild(wrap);
            return;
        }

        // ── Header ──
        var header = document.createElement('div');
        header.className = 'cl-header';

        var h2 = document.createElement('h2');
        h2.innerHTML = '&#x1F4EE; Letters from the Caretaker';
        header.appendChild(h2);

        var unread = api.getUnreadCount();
        if (unread > 0) {
            var badge = document.createElement('span');
            badge.className = 'cl-badge';
            badge.textContent = '(' + unread + ' new)';
            header.appendChild(badge);
        }

        wrap.appendChild(header);

        // ── Letter list ──
        var available = api.getAvailableLetters();
        var list = document.createElement('ul');
        list.className = 'cl-list';

        // Available letters
        var expandedPanel = null;

        for (var i = 0; i < available.length; i++) {
            (function(letter, index) {
                var li = document.createElement('li');
                li.className = 'cl-item ' + (letter.read ? 'cl-read' : 'cl-unread');

                var env = document.createElement('div');
                env.className = 'cl-env';

                // Envelope icon
                var icon = document.createElement('div');
                icon.className = 'cl-env-icon';
                var body = document.createElement('div');
                body.className = 'cl-env-body';
                var flap = document.createElement('div');
                flap.className = 'cl-env-flap';
                icon.appendChild(flap);
                icon.appendChild(body);
                env.appendChild(icon);

                // Meta
                var meta = document.createElement('div');
                meta.className = 'cl-env-meta';
                var subj = document.createElement('div');
                subj.className = 'cl-env-subject';
                subj.textContent = '#' + letter.id + ' \u2014 ' + letter.subject;
                meta.appendChild(subj);

                if (!letter.read) {
                    var preview = document.createElement('div');
                    preview.className = 'cl-env-preview';
                    preview.textContent = letter.body.substring(0, 60) + '...';
                    meta.appendChild(preview);
                }

                env.appendChild(meta);
                li.appendChild(env);

                // Expanded letter panel
                var panel = document.createElement('div');
                panel.className = 'cl-letter-full';
                panel.id = 'cl-letter-' + letter.id;

                var pSubj = document.createElement('div');
                pSubj.className = 'cl-letter-subj';
                pSubj.textContent = letter.subject;
                panel.appendChild(pSubj);

                var pBody = document.createElement('div');
                pBody.className = 'cl-letter-body';
                // Split body into paragraphs
                var paragraphs = letter.body.split('\n\n');
                for (var pi = 0; pi < paragraphs.length; pi++) {
                    var para = document.createElement('p');
                    para.textContent = paragraphs[pi];
                    pBody.appendChild(para);
                }
                panel.appendChild(pBody);

                li.appendChild(panel);

                // Click handler
                env.addEventListener('click', function() {
                    // Close any currently open panel
                    if (expandedPanel && expandedPanel !== panel) {
                        expandedPanel.classList.remove('cl-open');
                    }

                    var isOpen = panel.classList.contains('cl-open');
                    if (isOpen) {
                        panel.classList.remove('cl-open');
                        expandedPanel = null;
                    } else {
                        panel.classList.add('cl-open');
                        expandedPanel = panel;

                        // Mark as read on first open
                        if (!letter.read) {
                            letter.read = true;
                            li.className = 'cl-item cl-read';

                            var giftDesc = api.markRead(letter.id);

                            // Show gift notification
                            if (giftDesc) {
                                var giftNote = document.createElement('div');
                                giftNote.className = 'cl-gift-note';
                                giftNote.textContent = '\u2728 ' + giftDesc;
                                panel.appendChild(giftNote);
                            }

                            // Update badge
                            updateBadge(wrap);
                        }
                    }
                });

                list.appendChild(li);
            })(available[i], i);
        }

        // Locked letters (show how many remain)
        var totalAvailable = available.length;
        if (totalAvailable < TOTAL_LETTERS) {
            var remaining = TOTAL_LETTERS - totalAvailable;
            for (var r = 0; r < Math.min(remaining, 3); r++) {
                var lockedLi = document.createElement('li');
                lockedLi.className = 'cl-item cl-locked';

                var lockedEnv = document.createElement('div');
                lockedEnv.className = 'cl-env';

                var lockedIcon = document.createElement('div');
                lockedIcon.className = 'cl-env-icon';
                var lockedBody = document.createElement('div');
                lockedBody.className = 'cl-env-body';
                var lockedFlap = document.createElement('div');
                lockedFlap.className = 'cl-env-flap';
                lockedIcon.appendChild(lockedFlap);
                lockedIcon.appendChild(lockedBody);
                lockedEnv.appendChild(lockedIcon);

                var lockedMeta = document.createElement('div');
                lockedMeta.className = 'cl-env-meta';
                var lockedSubj = document.createElement('div');
                lockedSubj.className = 'cl-env-subject';
                lockedSubj.textContent = r === 0
                    ? (remaining === 1 ? '1 letter remains...' : remaining + ' letters remain...')
                    : '\u2022 \u2022 \u2022';
                lockedMeta.appendChild(lockedSubj);
                lockedEnv.appendChild(lockedMeta);
                lockedLi.appendChild(lockedEnv);
                list.appendChild(lockedLi);
            }
        }

        wrap.appendChild(list);

        // ── Dismiss area (only after letter 20 read) ──
        if (api.canDismiss()) {
            var dismissArea = document.createElement('div');
            dismissArea.className = 'cl-dismiss-area';

            var dismissLink = document.createElement('button');
            dismissLink.className = 'cl-dismiss-link';
            dismissLink.textContent = 'Dismiss the Caretaker';
            dismissLink.addEventListener('click', function() {
                showDismissModal(function() {
                    api.dismissCaretaker();
                    api.render(containerId); // re-render to dismissed state
                });
            });

            dismissArea.appendChild(dismissLink);
            wrap.appendChild(dismissArea);
        }

        container.appendChild(wrap);
    };

    // ── Dismissed state render ──────────────────────────────────

    function renderDismissedState(wrap) {
        var desk = document.createElement('div');
        desk.className = 'cl-empty-desk';

        var dust = document.createElement('div');
        dust.className = 'cl-dust';
        dust.innerHTML = '&#x1F4AD;';
        desk.appendChild(dust);

        var note = document.createElement('p');
        note.textContent = 'The desk is empty. The Caretaker is gone.';
        desk.appendChild(note);

        var note2 = document.createElement('p');
        note2.style.marginTop = '8px';
        note2.style.fontStyle = 'italic';
        note2.style.fontSize = '12px';
        note2.textContent = 'A feeding schedule is pinned to the wall. The keys are on the table.';
        desk.appendChild(note2);

        wrap.appendChild(desk);

        // ── Farewell letter (7+ days after dismissal) ──
        if (api.checkFarewellLetter()) {
            var farewell = document.createElement('div');
            farewell.className = 'cl-farewell';

            var fEnv = document.createElement('div');
            fEnv.className = 'cl-env';
            fEnv.style.cursor = 'pointer';

            var fIcon = document.createElement('div');
            fIcon.className = 'cl-env-icon';
            var fBody = document.createElement('div');
            fBody.className = 'cl-env-body';
            var fFlap = document.createElement('div');
            fFlap.className = 'cl-env-flap';
            fIcon.appendChild(fFlap);
            fIcon.appendChild(fBody);
            fEnv.appendChild(fIcon);

            var fMeta = document.createElement('div');
            fMeta.className = 'cl-env-meta';
            var fSubj = document.createElement('div');
            fSubj.className = 'cl-env-subject';
            fSubj.textContent = 'One last envelope...';
            fMeta.appendChild(fSubj);
            fEnv.appendChild(fMeta);

            farewell.appendChild(fEnv);

            var fPanel = document.createElement('div');
            fPanel.className = 'cl-farewell-text';
            fPanel.style.display = 'none';
            fPanel.textContent = FAREWELL_LETTER.body;

            farewell.appendChild(fPanel);

            fEnv.addEventListener('click', function() {
                if (fPanel.style.display === 'none') {
                    fPanel.style.display = 'block';
                    fSubj.textContent = FAREWELL_LETTER.subject;
                    api.markFarewellSeen();
                } else {
                    fPanel.style.display = 'none';
                }
            });

            wrap.appendChild(farewell);
        }
    }

    // ── Badge updater ───────────────────────────────────────────

    function updateBadge(wrap) {
        var badge = wrap.querySelector('.cl-badge');
        var unread = api.getUnreadCount();
        if (badge) {
            if (unread > 0) {
                badge.textContent = '(' + unread + ' new)';
            } else {
                badge.remove();
            }
        }
    }

    return api;
})();
