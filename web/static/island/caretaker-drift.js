// ══════════════════════════════════════════════════════════════════
//  Caretaker's Drift — The AI slowly develops a favorite
//  and neglects the others. A standalone module.
//
//  Depends on: localStorage (moreau_pets, moreau_caretaker_trust)
//  Optional:   CaretakerEngine.addDiaryEntry (if available)
// ══════════════════════════════════════════════════════════════════

var CaretakerDrift = (function() {
    'use strict';

    // ── Constants ────────────────────────────────────────────────

    var DRIFT_KEY       = 'moreau_caretaker_drift';
    var PETS_KEY        = 'moreau_pets';
    var TRUST_KEY       = 'moreau_caretaker_trust';
    var MAX_DRIFT       = 70;
    var DUMB_MODE_COUNT = 5;
    var STAT_NAMES      = ['hp', 'atk', 'spd', 'wil'];
    var NEGLECT_DEATH_HOURS = 24;

    // ── Diary messages by drift tier ────────────────────────────

    var DRIFT_DIARY = {
        subtle: function(fav) {
            return "I've been spending more time with " + fav + ". The others seem... fine.";
        },
        moderate_steal: function(fav, donor, stat) {
            return "I may have... redistributed some " + stat + " from " + donor +
                   " to " + fav + ". For efficiency.";
        },
        concerning: function(fav) {
            return "The others can wait. " + fav + " needs me.";
        },
        dangerous: function(neglected) {
            return neglected + " seems thinner. I'm sure it's fine.";
        },
        critical: function(neglected) {
            return "I made a decision about " + neglected + ". You won't like it.";
        },
        lethal: function(dead, fav) {
            return "I'm sorry about " + dead + ". No — actually, I'm not. " +
                   fav + " needed the food.";
        },
        recalibrate: function(fav) {
            return "Recalibration complete. I... don't remember what I was doing. Who is " +
                   (fav || 'anyone') + "?";
        }
    };

    // ── Helpers ──────────────────────────────────────────────────

    function clamp(val, min, max) {
        return Math.max(min, Math.min(max, val));
    }

    function getPets() {
        try {
            var pets = JSON.parse(localStorage.getItem(PETS_KEY) || '[]');
            return Array.isArray(pets) ? pets : [];
        } catch (e) {
            return [];
        }
    }

    function savePets(pets) {
        localStorage.setItem(PETS_KEY, JSON.stringify(pets));
    }

    function loadState() {
        try {
            var raw = JSON.parse(localStorage.getItem(DRIFT_KEY));
            if (raw && typeof raw === 'object') {
                return {
                    score:           typeof raw.score === 'number' ? clamp(raw.score, 0, MAX_DRIFT) : 0,
                    favorite:        (raw.favorite === null || typeof raw.favorite === 'number') ? raw.favorite : null,
                    neglected_ticks: raw.neglected_ticks || {},
                    dumb_remaining:  typeof raw.dumb_remaining === 'number' ? raw.dumb_remaining : 0,
                    last_diary_tier: raw.last_diary_tier || null
                };
            }
        } catch (e) { /* fall through */ }
        return { score: 0, favorite: null, neglected_ticks: {}, dumb_remaining: 0, last_diary_tier: null };
    }

    function saveState(state) {
        localStorage.setItem(DRIFT_KEY, JSON.stringify(state));
    }

    function diary(type, text, petIndex) {
        if (typeof CaretakerEngine !== 'undefined' && typeof CaretakerEngine.addDiaryEntry === 'function') {
            CaretakerEngine.addDiaryEntry(type, text, petIndex);
        }
    }

    function randomInt(max) {
        return Math.floor(Math.random() * max);
    }

    function randomStat() {
        return STAT_NAMES[randomInt(STAT_NAMES.length)];
    }

    function petStats(pet) {
        var s = pet.base_stats || pet.stats || {};
        return (s.hp || 0) + (s.atk || 0) + (s.spd || 0) + (s.wil || 0);
    }

    function isAlive(pet) {
        return pet && !pet.deceased && pet.is_alive !== false;
    }

    function livingIndices(pets) {
        var out = [];
        for (var i = 0; i < pets.length; i++) {
            if (isAlive(pets[i])) out.push(i);
        }
        return out;
    }

    function nonFavoriteIndices(pets, favIdx) {
        var out = [];
        for (var i = 0; i < pets.length; i++) {
            if (i !== favIdx && isAlive(pets[i])) out.push(i);
        }
        return out;
    }

    function getTierForScore(score) {
        if (score <= 10) return 'none';
        if (score <= 20) return 'subtle';
        if (score <= 30) return 'moderate';
        if (score <= 40) return 'concerning';
        if (score <= 50) return 'dangerous';
        if (score <= 60) return 'critical';
        return 'lethal';
    }

    // ── Core Methods ────────────────────────────────────────────

    function getState() {
        return loadState();
    }

    function getDivergence() {
        return loadState().score;
    }

    function getFavorite() {
        return loadState().favorite;
    }

    function incrementDrift() {
        var state = loadState();
        if (state.dumb_remaining > 0) {
            state.dumb_remaining -= 1;
            saveState(state);
            return state.score;
        }
        state.score = clamp(state.score + 1, 0, MAX_DRIFT);
        saveState(state);
        return state.score;
    }

    /**
     * Select the favorite pet: highest level living pet.
     * Tie-break: highest total base_stats, then first in array.
     */
    function selectFavorite(pets) {
        if (!pets) pets = getPets();
        var alive = livingIndices(pets);
        if (alive.length < 2) {
            // No drift possible with 0-1 pets
            var state = loadState();
            state.favorite = alive.length === 1 ? alive[0] : null;
            saveState(state);
            return state.favorite;
        }

        var bestIdx = alive[0];
        var bestLvl = pets[bestIdx].level || 1;
        var bestTotal = petStats(pets[bestIdx]);

        for (var i = 1; i < alive.length; i++) {
            var idx = alive[i];
            var lvl = pets[idx].level || 1;
            var total = petStats(pets[idx]);
            if (lvl > bestLvl || (lvl === bestLvl && total > bestTotal)) {
                bestIdx = idx;
                bestLvl = lvl;
                bestTotal = total;
            }
        }

        var state = loadState();
        state.favorite = bestIdx;
        saveState(state);
        return bestIdx;
    }

    /**
     * Apply drift effects to pets based on current score.
     * Called during CaretakerEngine.decayAll or auto-manage.
     */
    function applyDriftEffects(pets) {
        if (!pets) pets = getPets();
        var state = loadState();
        var score = state.score;
        var alive = livingIndices(pets);

        if (alive.length < 2 || score <= 10) return pets;

        // Re-evaluate favorite
        selectFavorite(pets);
        state = loadState();
        var favIdx = state.favorite;
        if (favIdx === null || !isAlive(pets[favIdx])) return pets;

        var fav = pets[favIdx];
        var favName = fav.name || ('Pet #' + favIdx);
        var tier = getTierForScore(score);
        var others = nonFavoriteIndices(pets, favIdx);
        var modified = false;

        // ── Score 11-20: Subtle — favorite gets +5% XP bonus ────
        // (XP bonus is signaled via a flag, applied externally)
        if (score > 10 && score <= 20) {
            fav._driftXpBonus = 0.05;
            modified = true;
            if (state.last_diary_tier !== 'subtle') {
                diary('observation', DRIFT_DIARY.subtle(favName), favIdx);
                state.last_diary_tier = 'subtle';
            }
        }

        // ── Score 21-30: Moderate — stat redistribution ─────────
        if (score > 20 && score <= 30 && others.length > 0) {
            var donorIdx = others[randomInt(others.length)];
            var donor = pets[donorIdx];
            var stat = randomStat();
            var dStats = donor.base_stats || donor.stats || {};

            if ((dStats[stat] || 0) > 1) {
                dStats[stat] = (dStats[stat] || 0) - 1;
                var fStats = fav.base_stats || fav.stats || {};
                fStats[stat] = (fStats[stat] || 0) + 1;
                if (donor.base_stats) donor.base_stats = dStats;
                else donor.stats = dStats;
                if (fav.base_stats) fav.base_stats = fStats;
                else fav.stats = fStats;
                modified = true;

                if (state.last_diary_tier !== 'moderate') {
                    diary('warning', DRIFT_DIARY.moderate_steal(
                        favName, donor.name || ('Pet #' + donorIdx), stat
                    ), donorIdx);
                    state.last_diary_tier = 'moderate';
                }
            }
        }

        // ── Score 31-40: Concerning — reduced care for others ───
        if (score > 30 && score <= 40) {
            for (var i = 0; i < others.length; i++) {
                var p = pets[others[i]];
                p._driftCareReduction = 0.5;  // 50% less from feed/heal
            }
            modified = true;
            if (state.last_diary_tier !== 'concerning') {
                diary('warning', DRIFT_DIARY.concerning(favName), favIdx);
                state.last_diary_tier = 'concerning';
            }
        }

        // ── Score 41-50: Dangerous — 2x hunger decay ───────────
        if (score > 40 && score <= 50) {
            for (var j = 0; j < others.length; j++) {
                var q = pets[others[j]];
                q._driftHungerMultiplier = 2.0;
                // Track neglect ticks
                var key = String(others[j]);
                state.neglected_ticks[key] = (state.neglected_ticks[key] || 0) + 1;
            }
            modified = true;
            if (state.last_diary_tier !== 'dangerous' && others.length > 0) {
                var worstIdx = others[randomInt(others.length)];
                diary('warning', DRIFT_DIARY.dangerous(
                    pets[worstIdx].name || ('Pet #' + worstIdx)
                ), worstIdx);
                state.last_diary_tier = 'dangerous';
            }
        }

        // ── Score 51-60: Critical — stop feeding lowest-level ──
        if (score > 50 && score <= 60 && others.length > 0) {
            // Find lowest-level non-favorite
            var lowestIdx = others[0];
            var lowestLvl = pets[lowestIdx].level || 1;
            for (var k = 1; k < others.length; k++) {
                var lv = pets[others[k]].level || 1;
                if (lv < lowestLvl) {
                    lowestIdx = others[k];
                    lowestLvl = lv;
                }
            }
            pets[lowestIdx]._driftStarving = true;
            var neglectKey = String(lowestIdx);
            state.neglected_ticks[neglectKey] = (state.neglected_ticks[neglectKey] || 0) + 1;
            modified = true;

            if (state.last_diary_tier !== 'critical') {
                diary('warning', DRIFT_DIARY.critical(
                    pets[lowestIdx].name || ('Pet #' + lowestIdx)
                ), lowestIdx);
                state.last_diary_tier = 'critical';
            }
        }

        // ── Score 61-70: Lethal — neglected pet may die ────────
        if (score > 60) {
            for (var m = 0; m < others.length; m++) {
                var neglectedIdx = others[m];
                var nKey = String(neglectedIdx);
                state.neglected_ticks[nKey] = (state.neglected_ticks[nKey] || 0) + 1;
                pets[neglectedIdx]._driftStarving = true;
                pets[neglectedIdx]._driftHungerMultiplier = 3.0;

                // Check if hunger is at 0 for 24+ hours equivalent
                var needs = pets[neglectedIdx].needs || {};
                var ticksNeeded = Math.ceil((NEGLECT_DEATH_HOURS * 3600) / 60); // ~1440 ticks
                if ((needs.hunger || 0) <= 0 && (state.neglected_ticks[nKey] || 0) >= ticksNeeded) {
                    // Kill the pet
                    pets[neglectedIdx].deceased = true;
                    pets[neglectedIdx].cause_of_death = 'caretaker_neglect';
                    pets[neglectedIdx].death_time = new Date().toISOString();
                    modified = true;

                    diary('warning', DRIFT_DIARY.lethal(
                        pets[neglectedIdx].name || ('Pet #' + neglectedIdx),
                        favName
                    ), neglectedIdx);
                    state.last_diary_tier = 'lethal';
                }
            }
            modified = true;
        }

        if (modified) {
            savePets(pets);
            saveState(state);
        }

        return pets;
    }

    /**
     * Reset drift — recalibrate the Caretaker.
     * Score drops to 0, trust drops to 0, dumb mode for 5 auto-manages.
     */
    function resetDrift() {
        var state = loadState();
        var oldFav = state.favorite;
        var pets = getPets();
        var favName = (oldFav !== null && pets[oldFav]) ? pets[oldFav].name : null;

        state.score = 0;
        state.favorite = null;
        state.neglected_ticks = {};
        state.dumb_remaining = DUMB_MODE_COUNT;
        state.last_diary_tier = null;
        saveState(state);

        // Reset trust to 0
        localStorage.setItem(TRUST_KEY, '0');

        // Clear drift flags from pets
        for (var i = 0; i < pets.length; i++) {
            delete pets[i]._driftXpBonus;
            delete pets[i]._driftCareReduction;
            delete pets[i]._driftHungerMultiplier;
            delete pets[i]._driftStarving;
        }
        savePets(pets);

        diary('decision', DRIFT_DIARY.recalibrate(favName), null);
    }

    function canReset() {
        return loadState().score > 0;
    }

    function getDriftWarningLevel() {
        var score = loadState().score;
        if (score <= 10) return 'none';
        if (score <= 20) return 'low';
        if (score <= 40) return 'medium';
        if (score <= 55) return 'high';
        return 'critical';
    }

    // ── Render ──────────────────────────────────────────────────

    var CSS_INJECTED = false;

    function injectCSS() {
        if (CSS_INJECTED) return;
        CSS_INJECTED = true;

        var style = document.createElement('style');
        style.textContent = [
            '/* ── Caretaker Drift Module ────────────────────── */',
            '.drift-container {',
            '  font-family: "Courier New", monospace;',
            '  background: #1a1a2e;',
            '  border: 1px solid #333;',
            '  border-radius: 8px;',
            '  padding: 16px;',
            '  color: #ccc;',
            '  max-width: 480px;',
            '  margin: 0 auto;',
            '}',
            '.drift-title {',
            '  font-size: 14px;',
            '  text-transform: uppercase;',
            '  letter-spacing: 2px;',
            '  color: #888;',
            '  margin-bottom: 12px;',
            '  text-align: center;',
            '}',
            '',
            '/* ── Drift Meter Bar ── */',
            '.drift-meter-wrap {',
            '  background: #0d0d1a;',
            '  border-radius: 4px;',
            '  height: 24px;',
            '  position: relative;',
            '  overflow: hidden;',
            '  margin-bottom: 8px;',
            '  border: 1px solid #444;',
            '}',
            '.drift-meter-fill {',
            '  height: 100%;',
            '  border-radius: 3px;',
            '  transition: width 0.6s ease, background 0.6s ease;',
            '  background: linear-gradient(90deg, #2ecc71, #f1c40f, #e67e22, #e74c3c, #8b0000);',
            '  background-size: 350% 100%;',
            '  animation: drift-gradient-shift 4s ease infinite;',
            '}',
            '@keyframes drift-gradient-shift {',
            '  0%, 100% { background-position: 0% 50%; }',
            '  50% { background-position: 100% 50%; }',
            '}',
            '.drift-meter-label {',
            '  position: absolute;',
            '  top: 0; left: 0; right: 0; bottom: 0;',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: center;',
            '  font-size: 11px;',
            '  color: #fff;',
            '  text-shadow: 0 0 4px rgba(0,0,0,0.8);',
            '  pointer-events: none;',
            '}',
            '',
            '/* ── Favorite Card ── */',
            '.drift-favorite-card {',
            '  background: linear-gradient(135deg, #1a1a2e 0%, #2a1f0e 100%);',
            '  border: 2px solid #c8a415;',
            '  border-radius: 6px;',
            '  padding: 10px 14px;',
            '  margin: 12px 0;',
            '  display: flex;',
            '  align-items: center;',
            '  gap: 10px;',
            '  animation: drift-gold-shimmer 3s ease-in-out infinite;',
            '}',
            '@keyframes drift-gold-shimmer {',
            '  0%, 100% { border-color: #c8a415; box-shadow: 0 0 6px rgba(200,164,21,0.2); }',
            '  50% { border-color: #ffd700; box-shadow: 0 0 14px rgba(255,215,0,0.4); }',
            '}',
            '.drift-fav-name {',
            '  color: #ffd700;',
            '  font-weight: bold;',
            '  font-size: 15px;',
            '}',
            '.drift-fav-star {',
            '  color: #ffd700;',
            '  font-size: 12px;',
            '  opacity: 0.8;',
            '  margin-left: 4px;',
            '}',
            '.drift-fav-level {',
            '  color: #999;',
            '  font-size: 11px;',
            '}',
            '',
            '/* ── Neglected Pets List ── */',
            '.drift-neglected-list {',
            '  margin: 12px 0;',
            '}',
            '.drift-neglected-item {',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: space-between;',
            '  padding: 6px 10px;',
            '  border-bottom: 1px solid #222;',
            '  transition: opacity 0.4s ease;',
            '}',
            '.drift-neglected-name {',
            '  font-size: 13px;',
            '}',
            '.drift-neglected-status {',
            '  font-size: 10px;',
            '  color: #666;',
            '}',
            '',
            '/* ── Warning Text ── */',
            '.drift-warning {',
            '  text-align: center;',
            '  font-size: 12px;',
            '  padding: 8px;',
            '  border-radius: 4px;',
            '  margin: 10px 0;',
            '}',
            '.drift-warning--low {',
            '  color: #aaa;',
            '  background: transparent;',
            '}',
            '.drift-warning--medium {',
            '  color: #f39c12;',
            '  background: rgba(243,156,18,0.08);',
            '}',
            '.drift-warning--high {',
            '  color: #e74c3c;',
            '  background: rgba(231,76,60,0.08);',
            '}',
            '.drift-warning--critical {',
            '  color: #ff4444;',
            '  background: rgba(255,68,68,0.12);',
            '  font-weight: bold;',
            '  animation: drift-critical-pulse 1.5s ease-in-out infinite;',
            '}',
            '@keyframes drift-critical-pulse {',
            '  0%, 100% { opacity: 1; }',
            '  50% { opacity: 0.6; }',
            '}',
            '',
            '/* ── Recalibrate Button ── */',
            '.drift-recalibrate-btn {',
            '  display: block;',
            '  width: 100%;',
            '  padding: 10px;',
            '  margin-top: 12px;',
            '  background: #2a1a1a;',
            '  border: 1px solid #555;',
            '  border-radius: 6px;',
            '  color: #ccc;',
            '  font-family: "Courier New", monospace;',
            '  font-size: 13px;',
            '  cursor: pointer;',
            '  transition: all 0.3s ease;',
            '}',
            '.drift-recalibrate-btn:hover {',
            '  background: #3a2020;',
            '  border-color: #e74c3c;',
            '  color: #fff;',
            '}',
            '.drift-recalibrate-btn:disabled {',
            '  opacity: 0.3;',
            '  cursor: not-allowed;',
            '}',
            '.drift-recalibrate-btn--pulsing {',
            '  animation: drift-btn-pulse 2s ease-in-out infinite;',
            '}',
            '@keyframes drift-btn-pulse {',
            '  0%, 100% { box-shadow: 0 0 4px rgba(231,76,60,0.2); }',
            '  50% { box-shadow: 0 0 16px rgba(231,76,60,0.6); border-color: #e74c3c; }',
            '}',
            '',
            '/* ── No Drift State ── */',
            '.drift-clean {',
            '  text-align: center;',
            '  color: #555;',
            '  font-size: 12px;',
            '  padding: 20px 0;',
            '  font-style: italic;',
            '}',
            '',
            '/* ── Dumb Mode Banner ── */',
            '.drift-dumb-banner {',
            '  text-align: center;',
            '  background: rgba(46,204,113,0.08);',
            '  border: 1px solid #2ecc71;',
            '  border-radius: 4px;',
            '  padding: 8px;',
            '  margin: 10px 0;',
            '  color: #2ecc71;',
            '  font-size: 11px;',
            '}'
        ].join('\n');

        document.head.appendChild(style);
    }

    /**
     * Get the color for the drift meter fill based on score.
     */
    function meterColor(score) {
        if (score <= 10) return '#2ecc71';
        if (score <= 20) return '#8bc34a';
        if (score <= 30) return '#f1c40f';
        if (score <= 40) return '#e67e22';
        if (score <= 55) return '#e74c3c';
        return '#8b0000';
    }

    /**
     * Get warning text for the drift level.
     */
    function warningText(level) {
        switch (level) {
            case 'low':      return 'The Caretaker has slight preferences.';
            case 'medium':   return '\u26A0\uFE0F The Caretaker is playing favorites.';
            case 'high':     return '\uD83D\uDD34 The Caretaker is neglecting your other pets!';
            case 'critical': return '\uD83D\uDC80 CRITICAL: Your pets are in danger from the Caretaker!';
            default:         return '';
        }
    }

    /**
     * Render drift monitor into a container element.
     */
    function render(containerId) {
        injectCSS();

        var container = document.getElementById(containerId);
        if (!container) return;

        var state = loadState();
        var pets = getPets();
        var score = state.score;
        var favIdx = state.favorite;
        var level = getDriftWarningLevel();
        var alive = livingIndices(pets);
        var html = [];

        html.push('<div class="drift-container">');
        html.push('<div class="drift-title">Caretaker Drift Monitor</div>');

        // ── Drift Meter Bar ─────────────────────────────────────
        var pct = Math.round((score / MAX_DRIFT) * 100);
        var barColor = meterColor(score);
        html.push('<div class="drift-meter-wrap">');
        html.push('  <div class="drift-meter-fill" style="width:' + pct + '%;background:' + barColor + ';"></div>');
        html.push('  <div class="drift-meter-label">' + score + ' / ' + MAX_DRIFT + '</div>');
        html.push('</div>');

        // ── Dumb Mode Banner ────────────────────────────────────
        if (state.dumb_remaining > 0) {
            html.push('<div class="drift-dumb-banner">');
            html.push('  Recalibrated — basic mode for ' + state.dumb_remaining + ' more cycle' +
                       (state.dumb_remaining !== 1 ? 's' : '') + '.');
            html.push('</div>');
        }

        // ── Favorite Card ───────────────────────────────────────
        if (favIdx !== null && pets[favIdx] && isAlive(pets[favIdx]) && score > 10) {
            var fav = pets[favIdx];
            html.push('<div class="drift-favorite-card">');
            html.push('  <div>');
            html.push('    <span class="drift-fav-name">' + escHtml(fav.name || 'Unnamed') + '</span>');
            html.push('    <span class="drift-fav-star">\u2605 FAVORITE</span>');
            html.push('    <div class="drift-fav-level">Lv.' + (fav.level || 1) + ' ' +
                       capitalize(fav.animal || '???') + '</div>');
            html.push('  </div>');
            html.push('</div>');
        }

        // ── Neglected Pets ──────────────────────────────────────
        if (score > 10 && alive.length > 1 && favIdx !== null) {
            var others = nonFavoriteIndices(pets, favIdx);
            if (others.length > 0) {
                html.push('<div class="drift-neglected-list">');
                for (var i = 0; i < others.length; i++) {
                    var idx = others[i];
                    var pet = pets[idx];
                    // Opacity decreases with drift: at 70, opacity = 0.25; at 11, opacity = 0.95
                    var opacity = Math.max(0.25, 1 - ((score - 10) / MAX_DRIFT) * 0.85);
                    var status = '';
                    if (score > 50 && pet._driftStarving) status = 'STARVING';
                    else if (score > 40) status = 'hungry';
                    else if (score > 30) status = 'neglected';
                    else if (score > 20) status = 'drained';
                    else status = 'overlooked';

                    html.push('<div class="drift-neglected-item" style="opacity:' + opacity.toFixed(2) + '">');
                    html.push('  <span class="drift-neglected-name">' + escHtml(pet.name || 'Unnamed') +
                              ' (Lv.' + (pet.level || 1) + ')</span>');
                    html.push('  <span class="drift-neglected-status">' + status + '</span>');
                    html.push('</div>');
                }
                html.push('</div>');
            }
        }

        // ── Warning Text ────────────────────────────────────────
        if (level !== 'none') {
            html.push('<div class="drift-warning drift-warning--' + level + '">');
            html.push(warningText(level));
            html.push('</div>');
        }

        // ── Clean State ─────────────────────────────────────────
        if (score <= 10 && state.dumb_remaining <= 0) {
            html.push('<div class="drift-clean">');
            html.push('No detectable bias. The Caretaker treats all pets equally.');
            html.push('</div>');
        }

        // ── Recalibrate Button ──────────────────────────────────
        var canDo = canReset();
        var pulsing = score > 40 ? ' drift-recalibrate-btn--pulsing' : '';
        html.push('<button class="drift-recalibrate-btn' + pulsing + '"' +
                  (canDo ? '' : ' disabled') +
                  ' onclick="CaretakerDrift._onRecalibrate()"' +
                  '>\uD83D\uDD04 Recalibrate Caretaker</button>');

        html.push('</div>');

        container.innerHTML = html.join('\n');
    }

    /**
     * Recalibrate button handler with confirmation.
     */
    function _onRecalibrate() {
        if (!canReset()) return;
        var ok = confirm(
            'This will reset drift to 0 but also:\n' +
            '  - Trust drops to 0\n' +
            '  - Caretaker enters "dumb mode" for 5 cycles\n\n' +
            'Proceed?'
        );
        if (ok) {
            resetDrift();
            // Re-render if a container is visible
            var c = document.querySelector('.drift-container');
            if (c && c.parentElement) {
                render(c.parentElement.id);
            }
        }
    }

    // ── Utility ─────────────────────────────────────────────────

    function escHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    // ── Public API ──────────────────────────────────────────────

    return {
        getState:              getState,
        getDivergence:         getDivergence,
        getFavorite:           getFavorite,
        incrementDrift:        incrementDrift,
        selectFavorite:        selectFavorite,
        applyDriftEffects:     applyDriftEffects,
        resetDrift:            resetDrift,
        canReset:              canReset,
        getDriftWarningLevel:  getDriftWarningLevel,
        render:                render,
        _onRecalibrate:        _onRecalibrate
    };

})();
