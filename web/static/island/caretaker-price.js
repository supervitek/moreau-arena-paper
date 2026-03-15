// ══════════════════════════════════════════════════════════════════
//  The Caretaker's Price — The Cost of Automation
//  Efficiency decay, XP tax, mutation confiscation, hybrid workshop
// ══════════════════════════════════════════════════════════════════

var CaretakerPrice = (function() {
    'use strict';

    // ── Storage keys & constants ────────────────────────────────────

    var EFFICIENCY_KEY  = 'moreau_caretaker_efficiency';
    var LAST_VISIT_KEY  = 'moreau_last_player_visit';
    var CONFISCATED_KEY = 'moreau_confiscated_mutations';
    var HYBRID_KEY      = 'moreau_hybrid_mutations';
    var WORKSHOP_KEY    = 'moreau_workshop_discovered';
    var PETS_KEY        = 'moreau_pets';
    var TRUST_KEY       = 'moreau_caretaker_trust';
    var DIARY_KEY       = 'moreau_caretaker_diary';

    var CONFISCATE_CHANCE     = 0.15;
    var XP_TAX_RATE           = 0.10;
    var TRUST_THRESHOLD_TAX   = 7;
    var TRUST_THRESHOLD_CONF  = 9;
    var DECAY_BLOCK_HOURS     = 48;
    var WORKSHOP_UNLOCK_COUNT = 3;

    // ── 10 Hybrid recipes ───────────────────────────────────────────

    var HYBRID_RECIPES = [
        { id: 'ironblood',       name: 'Ironblood',         components: ['tough_skin','sharp_claws','thick_hide','bone_density'],           stats: {hp:3,atk:2},              desc: 'Blood hardens on contact with air' },
        { id: 'phantom_stride',  name: 'Phantom Stride',    components: ['quick_feet','swift_reflexes','tendon_spring','survival_instinct'], stats: {spd:3,dodge:5},            desc: 'Move without touching the ground' },
        { id: 'willbreaker',     name: 'Willbreaker',       components: ['iron_will','neural_pathway','synapse_boost','neural_boost'],       stats: {wil:3,proc:2},             desc: 'Mind crushes weaker wills' },
        { id: 'predators_eye',   name: "Predator's Eye",    components: ['keen_eyes','predator_instinct','eye_enhancement','sharp_claws'],   stats: {accuracy:5,crit:4},        desc: 'See the kill before it happens' },
        { id: 'living_armor',    name: 'Living Armor',      components: ['thick_hide','bone_density','tough_skin','battle_scars'],           stats: {hp:3,dmg_red:8},           desc: 'Skin becomes organic plate' },
        { id: 'berserkers_gift', name: "Berserker's Gift",  components: ['adrenaline_gland','aggression_serum','muscle_fibers','sharp_claws'],stats: {atk:4,wil:-2},            desc: 'Rage that fuels itself' },
        { id: 'survivors_core',  name: "Survivor's Core",   components: ['battle_scars','pain_suppressor','thick_hide','iron_will'],         stats: {hp:5,spd:-1},              desc: 'Pain becomes strength' },
        { id: 'neural_storm',    name: 'Neural Storm',      components: ['synapse_boost','eye_enhancement','neural_pathway','keen_eyes'],    stats: {wil:3,spd:2},              desc: 'Think at the speed of lightning' },
        { id: 'metabolic_engine',name: 'Metabolic Engine',  components: ['metabolic_surge','muscle_fibers','adrenaline_gland','quick_feet'], stats: {hp:3,atk:1,spd:1},         desc: 'Body becomes a machine' },
        { id: 'perfect_balance', name: 'Perfect Balance',   components: ['survival_instinct','tendon_spring','swift_reflexes','pain_suppressor'], stats: {hp:2,spd:2,wil:1},    desc: 'Harmony of body and mind' }
    ];

    // ── Helpers ─────────────────────────────────────────────────────

    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

    function loadJSON(key, fb) {
        try { var r = localStorage.getItem(key); return r ? JSON.parse(r) : fb; }
        catch(e) { return fb; }
    }

    function saveJSON(key, data) {
        try { localStorage.setItem(key, JSON.stringify(data)); } catch(e) {}
    }

    function getTrust() {
        try { var v = parseFloat(localStorage.getItem(TRUST_KEY)); return isNaN(v) ? 5 : clamp(v,0,10); }
        catch(e) { return 5; }
    }

    function setTrust(v) { localStorage.setItem(TRUST_KEY, String(clamp(v,0,10))); }
    function getPets()    { return loadJSON(PETS_KEY, []); }
    function savePets(p)  { saveJSON(PETS_KEY, p); }

    function addDiaryEntry(text) {
        if (typeof CaretakerEngine !== 'undefined' && CaretakerEngine.addDiaryEntry) {
            CaretakerEngine.addDiaryEntry('observation', text, null);
            return;
        }
        var diary = loadJSON(DIARY_KEY, []);
        diary.unshift({ id: Date.now(), type: 'observation', text: text,
            petIndex: null, timestamp: new Date().toISOString(), approved: null });
        if (diary.length > 200) diary = diary.slice(0, 200);
        saveJSON(DIARY_KEY, diary);
    }

    function escapeHTML(s) {
        return !s ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function formatStats(stats) {
        if (!stats) return '';
        var parts = [], labels = { hp:'HP', atk:'ATK', spd:'SPD', wil:'WIL',
            dodge:'% dodge', accuracy:'% accuracy', crit:'% crit', proc:'% proc', dmg_red:'% dmg red' };
        for (var k in stats) {
            if (!stats.hasOwnProperty(k)) continue;
            var v = stats[k], label = labels[k] || k.toUpperCase();
            var isPct = label.charAt(0) === '%';
            parts.push((v > 0 ? '+' : '') + v + (isPct ? '' : ' ') + label);
        }
        return parts.join(' | ');
    }

    // ── CSS injection ───────────────────────────────────────────────

    var cssInjected = false;

    function injectCSS() {
        if (cssInjected) return;
        cssInjected = true;
        var s = document.createElement('style');
        s.textContent =
            '.cp-workshop{background:linear-gradient(135deg,#1a1a2e,#16213e 50%,#0f3460);border:2px solid #444;border-radius:12px;padding:24px;color:#d4d4d4;font-family:"Courier New",monospace;position:relative;overflow:hidden}' +
            '.cp-workshop::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 30px,rgba(255,255,255,.02) 30px,rgba(255,255,255,.02) 31px);pointer-events:none}' +
            '.cp-title{font-size:1.4em;color:#f0c040;text-align:center;margin-bottom:4px;text-shadow:0 0 12px rgba(240,192,64,.3)}' +
            '.cp-subtitle{font-size:.85em;color:#888;text-align:center;margin-bottom:20px;font-style:italic}' +
            '.cp-section-label{font-size:.9em;color:#aaa;text-transform:uppercase;letter-spacing:2px;margin:16px 0 8px;border-bottom:1px solid #333;padding-bottom:4px}' +
            '.cp-card{background:#1e1e30;border:1px solid #555;border-radius:8px;padding:12px;margin:8px 0;position:relative;transition:border-color .3s;cursor:pointer}' +
            '.cp-card:hover{border-color:#f0c040}' +
            '.cp-card.selected{border-color:#f0c040;box-shadow:0 0 8px rgba(240,192,64,.4)}' +
            '.cp-card-rivet{position:absolute;width:6px;height:6px;background:#666;border-radius:50%;box-shadow:inset 0 1px 2px rgba(0,0,0,.5)}' +
            '.cp-card-rivet.tl{top:4px;left:4px}.cp-card-rivet.tr{top:4px;right:4px}.cp-card-rivet.bl{bottom:4px;left:4px}.cp-card-rivet.br{bottom:4px;right:4px}' +
            '.cp-card-name{font-weight:bold;color:#e0e0e0;margin-bottom:4px}' +
            '.cp-card-desc{font-size:.8em;color:#999}.cp-card-stats{font-size:.75em;color:#6fb86f;margin-top:4px}' +
            '.cp-card-origin{font-size:.7em;color:#777;margin-top:4px;font-style:italic}' +
            '.cp-card-hybrid{background:linear-gradient(135deg,#2a1a00,#1e1e30);border-color:#d4a017;box-shadow:0 0 12px rgba(212,160,23,.2)}' +
            '.cp-card-hybrid .cp-card-name{color:#f0c040;text-shadow:0 0 6px rgba(240,192,64,.4)}' +
            '.cp-combine-area{background:#111;border:2px dashed #444;border-radius:8px;padding:16px;margin:16px 0;text-align:center;min-height:80px;transition:border-color .3s}' +
            '.cp-combine-area.ready{border-color:#f0c040}' +
            '.cp-combine-slots{display:flex;justify-content:center;align-items:center;gap:12px;margin:12px 0}' +
            '.cp-slot{width:120px;min-height:60px;border:1px dashed #555;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.8em;color:#666;padding:8px;text-align:center}' +
            '.cp-slot.filled{border-color:#f0c040;color:#e0e0e0;background:rgba(240,192,64,.05)}' +
            '.cp-plus{font-size:1.5em;color:#555}' +
            '.cp-btn{display:inline-block;padding:10px 24px;border:none;border-radius:6px;cursor:pointer;font-family:"Courier New",monospace;font-size:.9em;transition:all .3s;margin:4px}' +
            '.cp-btn:disabled{opacity:.4;cursor:not-allowed}' +
            '.cp-btn-combine{background:linear-gradient(135deg,#f0c040,#d4a017);color:#111;font-weight:bold}' +
            '.cp-btn-combine:hover:not(:disabled){box-shadow:0 0 16px rgba(240,192,64,.5);transform:translateY(-1px)}' +
            '.cp-btn-reclaim{background:#8b0000;color:#fff}.cp-btn-reclaim:hover:not(:disabled){background:#a00;box-shadow:0 0 12px rgba(180,0,0,.4)}' +
            '.cp-btn-clear{background:transparent;color:#888;border:1px solid #444}.cp-btn-clear:hover{color:#ccc;border-color:#666}' +
            '.cp-empty{color:#555;font-style:italic;text-align:center;padding:20px}' +
            '.cp-efficiency-bar{width:100%;height:8px;background:#222;border-radius:4px;margin:8px 0;overflow:hidden}' +
            '.cp-efficiency-fill{height:100%;border-radius:4px;transition:width .5s ease}' +
            '.cp-efficiency-high{background:#4caf50}.cp-efficiency-mid{background:#ff9800}.cp-efficiency-low{background:#f44336}' +
            '.cp-status-line{font-size:.8em;color:#888;margin:4px 0}' +
            '.cp-spark{position:absolute;width:3px;height:3px;background:#f0c040;border-radius:50%;animation:cp-spark-fly .8s ease-out forwards}' +
            '@keyframes cp-spark-fly{0%{opacity:1;transform:translate(0,0) scale(1)}100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(.3)}}' +
            '.cp-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:10000}' +
            '.cp-modal{background:#1a1a2e;border:2px solid #8b0000;border-radius:12px;padding:24px;max-width:400px;text-align:center;color:#d4d4d4}' +
            '.cp-modal h3{color:#ff4444;margin-top:0}' +
            '.cp-modal-buttons{display:flex;gap:12px;justify-content:center;margin-top:16px}' +
            '.cp-result-card{animation:cp-glow-in .6s ease-out}' +
            '@keyframes cp-glow-in{0%{opacity:0;transform:scale(.8);box-shadow:0 0 40px rgba(240,192,64,.8)}50%{opacity:1;transform:scale(1.05)}100%{opacity:1;transform:scale(1);box-shadow:0 0 12px rgba(212,160,23,.2)}}';
        document.head.appendChild(s);
    }

    // ── Core: Visit & Efficiency ────────────────────────────────────

    function updateVisit() {
        localStorage.setItem(LAST_VISIT_KEY, String(Date.now()));
    }

    function getEfficiency() {
        var last = parseInt(localStorage.getItem(LAST_VISIT_KEY) || '0', 10);
        if (!last) return 1.0;
        var hours = (Date.now() - last) / 3600000;
        if (hours < 24)  return 1.0;
        if (hours < 48)  return 0.8;
        if (hours < 72)  return 0.6;
        if (hours < 96)  return 0.4;
        return 0.2;
    }

    function calculateDecay() {
        var last = parseInt(localStorage.getItem(LAST_VISIT_KEY) || '0', 10);
        if (!last) return 0;
        var hours = (Date.now() - last) / 3600000;
        if (hours <= DECAY_BLOCK_HOURS) return 0;

        var trustLoss = Math.floor(hours / DECAY_BLOCK_HOURS);
        if (trustLoss <= 0) return 0;

        var trust = getTrust();
        var newTrust = clamp(trust - trustLoss, 0, 10);
        var actual = trust - newTrust;

        if (actual > 0) {
            setTrust(newTrust);
            var days = Math.floor(hours / 24);
            addDiaryEntry('You were away for ' + days + ' day' + (days !== 1 ? 's' : '') +
                '. Efficiency dropped. Trust adjusted by -' + actual + '.');
        }

        localStorage.setItem(EFFICIENCY_KEY, String(getEfficiency()));
        return actual;
    }

    // ── Core: XP Tax ────────────────────────────────────────────────

    function applyXPTax(xp) {
        if (typeof xp !== 'number' || xp <= 0) return xp;
        var trust = getTrust();
        if (trust <= TRUST_THRESHOLD_TAX) return xp;
        var tax = Math.ceil(xp * XP_TAX_RATE);
        if (tax <= 0) return xp;
        addDiaryEntry('Management fee: -' + tax + ' XP. The cost of delegation.');
        return xp - tax;
    }

    // ── Core: Confiscation ──────────────────────────────────────────

    function tryConfiscate(petIndex) {
        var trust = getTrust();
        if (trust <= TRUST_THRESHOLD_CONF) return null;
        if (Math.random() > CONFISCATE_CHANCE) return null;

        var pets = getPets();
        if (!pets[petIndex]) return null;

        var pet = pets[petIndex];
        var mutations = pet.lab_mutations || {};
        var target = null, targetSlot = null;

        // Prefer L3, then L6, then L9
        var slots = ['L3', 'L6', 'L9'];
        for (var i = 0; i < slots.length; i++) {
            var mut = mutations[slots[i]];
            if (mut && mut.tier === 1) { target = mut; targetSlot = slots[i]; break; }
        }
        if (!target) return null;

        // Build record
        var record = {
            id: target.id, name: target.name, desc: target.desc || '',
            stats: target.stats || {}, fromPet: pet.name || 'Unknown',
            fromSlot: targetSlot, confiscated_at: new Date().toISOString()
        };

        // Remove from pet and save
        mutations[targetSlot] = null;
        pet.lab_mutations = mutations;
        savePets(pets);

        // Store confiscated
        var confiscated = getConfiscated();
        confiscated.push(record);
        saveJSON(CONFISCATED_KEY, confiscated);

        addDiaryEntry("I've relocated a mutation for... research purposes. " +
            target.name + ' from ' + (pet.name || 'your pet') + '.');

        // Check workshop discovery
        if (!isWorkshopDiscovered() && confiscated.length >= WORKSHOP_UNLOCK_COUNT) {
            discoverWorkshop();
            addDiaryEntry("I've been working on something in the back room. You might want to take a look.");
        }

        return record;
    }

    function getConfiscated() { return loadJSON(CONFISCATED_KEY, []); }
    function getHybrids()     { return loadJSON(HYBRID_KEY, []); }
    function canCombine()     { return getConfiscated().length >= 2; }

    // ── Core: Hybrid Combining ──────────────────────────────────────

    function findRecipe(id1, id2) {
        for (var i = 0; i < HYBRID_RECIPES.length; i++) {
            var c = HYBRID_RECIPES[i].components, h1 = false, h2 = false;
            for (var j = 0; j < c.length; j++) {
                if (c[j] === id1) h1 = true;
                if (c[j] === id2) h2 = true;
            }
            if (h1 && h2) return HYBRID_RECIPES[i];
        }
        return null;
    }

    function mergeStats(s1, s2) {
        var result = {}, all = {}, k;
        s1 = s1 || {}; s2 = s2 || {};
        for (k in s1) { if (s1.hasOwnProperty(k)) all[k] = true; }
        for (k in s2) { if (s2.hasOwnProperty(k)) all[k] = true; }
        for (k in all) {
            if (all.hasOwnProperty(k)) result[k] = Math.ceil(((s1[k]||0) + (s2[k]||0)) / 2);
        }
        return result;
    }

    function combineHybrid(mut1Id, mut2Id) {
        if (!mut1Id || !mut2Id || mut1Id === mut2Id) return null;

        var confiscated = getConfiscated();
        var idx1 = -1, idx2 = -1;
        for (var i = 0; i < confiscated.length; i++) {
            if (confiscated[i].id === mut1Id && idx1 === -1) idx1 = i;
            else if (confiscated[i].id === mut2Id && idx2 === -1) idx2 = i;
        }
        if (idx1 === -1 || idx2 === -1) return null;

        // Match recipe or create generic
        var recipe = findRecipe(mut1Id, mut2Id);
        if (!recipe) {
            var m1 = confiscated[idx1], m2 = confiscated[idx2];
            recipe = {
                id: 'hybrid_' + m1.id + '_' + m2.id,
                name: m1.name + ' + ' + m2.name,
                stats: mergeStats(m1.stats, m2.stats),
                desc: 'An unstable fusion of ' + m1.name + ' and ' + m2.name + '.'
            };
        }

        var hybrid = {
            id: recipe.id, name: recipe.name, desc: recipe.desc,
            stats: recipe.stats, tier: 2, isHybrid: true,
            source: [confiscated[idx1].name, confiscated[idx2].name],
            created_at: new Date().toISOString()
        };

        // Remove used (higher index first)
        confiscated.splice(Math.max(idx1,idx2), 1);
        confiscated.splice(Math.min(idx1,idx2), 1);
        saveJSON(CONFISCATED_KEY, confiscated);

        var hybrids = getHybrids();
        hybrids.push(hybrid);
        saveJSON(HYBRID_KEY, hybrids);

        addDiaryEntry('Workshop complete: forged ' + hybrid.name +
            ' from two confiscated specimens. Magnificent work, if I say so myself.');
        return hybrid;
    }

    // ── Core: Reclaim ───────────────────────────────────────────────

    function reclaimAll() {
        var confiscated = getConfiscated();
        if (confiscated.length === 0) return [];
        saveJSON(CONFISCATED_KEY, []);
        setTrust(0);
        addDiaryEntry('You took them back. All of them. After everything I built... Fine. ' +
            'Trust level: 0. Starting from zero.');
        return confiscated;
    }

    // ── Workshop discovery ──────────────────────────────────────────

    function isWorkshopDiscovered() { return localStorage.getItem(WORKSHOP_KEY) === 'true'; }
    function discoverWorkshop()     { localStorage.setItem(WORKSHOP_KEY, 'true'); }

    // ── Render: Workshop UI ─────────────────────────────────────────

    var selectedSlots = [null, null];

    function render(containerId) {
        injectCSS();
        var container = document.getElementById(containerId);
        if (!container) return;

        if (!isWorkshopDiscovered()) { container.innerHTML = ''; return; }

        var confiscated = getConfiscated();
        var hybrids = getHybrids();
        var eff = getEfficiency();
        var h = [];

        h.push('<div class="cp-workshop">');
        h.push('<div class="cp-title">&#128295; The Caretaker\'s Workshop</div>');
        h.push('<div class="cp-subtitle">What has it been building with your mutations?</div>');

        // Efficiency bar
        var pct = Math.round(eff * 100);
        var cls = eff >= 0.8 ? 'cp-efficiency-high' : eff >= 0.5 ? 'cp-efficiency-mid' : 'cp-efficiency-low';
        h.push('<div style="margin:8px 0"><span style="font-size:.8em;color:#aaa">Caretaker Efficiency: ' + pct + '%</span>');
        h.push('<div class="cp-efficiency-bar"><div class="cp-efficiency-fill ' + cls + '" style="width:' + pct + '%"></div></div></div>');

        // Status
        h.push('<div class="cp-status-line">Trust: ' + getTrust().toFixed(1) + '/10 | ');
        h.push('Confiscated: ' + confiscated.length + ' | Hybrids forged: ' + hybrids.length + '</div>');

        // Confiscated mutations
        h.push('<div class="cp-section-label">Confiscated Mutations</div>');
        if (confiscated.length === 0) {
            h.push('<div class="cp-empty">No confiscated mutations. The shelves are bare.</div>');
        } else {
            for (var i = 0; i < confiscated.length; i++) {
                h.push(renderCard(confiscated[i], i, isInSlot(confiscated[i].id)));
            }
        }

        // Fusion chamber
        h.push('<div class="cp-section-label">Fusion Chamber</div>');
        h.push(renderCombineArea(confiscated));

        // Hybrid mutations
        h.push('<div class="cp-section-label">Hybrid Mutations Created</div>');
        if (hybrids.length === 0) {
            h.push('<div class="cp-empty">No hybrids yet. Select two mutations above to combine.</div>');
        } else {
            for (var j = 0; j < hybrids.length; j++) {
                var hy = hybrids[j], src = hy.source ? hy.source.join(' + ') : '?';
                h.push('<div class="cp-card cp-card-hybrid cp-result-card">');
                h.push(rivets());
                h.push('<div class="cp-card-name">' + escapeHTML(hy.name) + '</div>');
                h.push('<div class="cp-card-desc">' + escapeHTML(hy.desc) + '</div>');
                var hs = formatStats(hy.stats);
                if (hs) h.push('<div class="cp-card-stats">' + hs + '</div>');
                h.push('<div class="cp-card-origin">Forged from: ' + escapeHTML(src) + '</div></div>');
            }
        }

        // Reclaim button
        if (confiscated.length > 0) {
            h.push('<div style="text-align:center;margin-top:20px">');
            h.push('<button class="cp-btn cp-btn-reclaim" onclick="CaretakerPrice._showReclaimModal()">Reclaim All Mutations</button></div>');
        }

        h.push('</div>');
        container.innerHTML = h.join('');
        bindCardClicks(container);
    }

    function rivets() {
        return '<div class="cp-card-rivet tl"></div><div class="cp-card-rivet tr"></div>' +
               '<div class="cp-card-rivet bl"></div><div class="cp-card-rivet br"></div>';
    }

    function renderCard(mut, index, selected) {
        var st = formatStats(mut.stats);
        return '<div class="cp-card' + (selected ? ' selected' : '') + '" data-conf-index="' + index + '" data-mut-id="' + mut.id + '">' +
            rivets() +
            '<div class="cp-card-name">' + escapeHTML(mut.name) + '</div>' +
            (mut.desc ? '<div class="cp-card-desc">' + escapeHTML(mut.desc) + '</div>' : '') +
            (st ? '<div class="cp-card-stats">' + st + '</div>' : '') +
            '<div class="cp-card-origin">From: ' + escapeHTML(mut.fromPet) + ' (' + mut.fromSlot + ')</div></div>';
    }

    function renderCombineArea(confiscated) {
        var s1 = selectedSlots[0], s2 = selectedSlots[1];
        var l1 = s1 !== null && confiscated[s1] ? escapeHTML(confiscated[s1].name) : 'Slot 1';
        var l2 = s2 !== null && confiscated[s2] ? escapeHTML(confiscated[s2].name) : 'Slot 2';
        var hasBoth = s1 !== null && s2 !== null;
        return '<div class="cp-combine-area' + (hasBoth ? ' ready' : '') + '">' +
            '<div class="cp-combine-slots">' +
            '<div class="cp-slot' + (s1 !== null ? ' filled' : '') + '">' + l1 + '</div>' +
            '<div class="cp-plus">+</div>' +
            '<div class="cp-slot' + (s2 !== null ? ' filled' : '') + '">' + l2 + '</div></div>' +
            '<div style="margin-top:12px">' +
            '<button class="cp-btn cp-btn-combine"' + (hasBoth ? '' : ' disabled') + ' onclick="CaretakerPrice._doCombine()">Combine</button> ' +
            '<button class="cp-btn cp-btn-clear" onclick="CaretakerPrice._clearSlots()">Clear</button></div></div>';
    }

    function isInSlot(mutId) {
        var c = getConfiscated();
        if (selectedSlots[0] !== null && c[selectedSlots[0]] && c[selectedSlots[0]].id === mutId) return true;
        if (selectedSlots[1] !== null && c[selectedSlots[1]] && c[selectedSlots[1]].id === mutId) return true;
        return false;
    }

    function bindCardClicks(container) {
        var cards = container.querySelectorAll('.cp-card[data-conf-index]');
        for (var i = 0; i < cards.length; i++) {
            (function(card) {
                card.addEventListener('click', function() {
                    selectForCombine(parseInt(card.getAttribute('data-conf-index'), 10));
                });
            })(cards[i]);
        }
    }

    function selectForCombine(idx) {
        if (selectedSlots[0] === idx) selectedSlots[0] = null;
        else if (selectedSlots[1] === idx) selectedSlots[1] = null;
        else if (selectedSlots[0] === null) selectedSlots[0] = idx;
        else if (selectedSlots[1] === null) selectedSlots[1] = idx;
        else selectedSlots[1] = idx;

        var ws = document.querySelector('.cp-workshop');
        if (ws && ws.parentElement) render(ws.parentElement.id);
    }

    // ── Spark animation ─────────────────────────────────────────────

    function emitSparks(el) {
        if (!el) return;
        var rect = el.getBoundingClientRect();
        var box = document.createElement('div');
        box.style.cssText = 'position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:9999';
        document.body.appendChild(box);

        var cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
        for (var i = 0; i < 20; i++) {
            var sp = document.createElement('div');
            sp.className = 'cp-spark';
            var angle = (Math.PI * 2 * i) / 20 + (Math.random() - 0.5) * 0.5;
            var dist = 40 + Math.random() * 80;
            sp.style.left = cx + 'px';
            sp.style.top = cy + 'px';
            sp.style.setProperty('--dx', (Math.cos(angle) * dist) + 'px');
            sp.style.setProperty('--dy', (Math.sin(angle) * dist) + 'px');
            sp.style.animationDelay = (Math.random() * 0.2) + 's';
            box.appendChild(sp);
        }
        setTimeout(function() { if (box.parentNode) box.parentNode.removeChild(box); }, 1200);
    }

    // ── Reclaim modal ───────────────────────────────────────────────

    function showReclaimModal() {
        injectCSS();
        var overlay = document.createElement('div');
        overlay.className = 'cp-modal-overlay';
        overlay.id = 'cp-reclaim-modal';
        var n = getConfiscated().length;
        overlay.innerHTML =
            '<div class="cp-modal">' +
            '<h3>&#9888; Reclaim All Mutations?</h3>' +
            '<p>You will recover <strong>' + n + '</strong> confiscated mutation' + (n !== 1 ? 's' : '') + '.</p>' +
            '<p style="color:#ff6666;font-weight:bold">Warning: This will reset Trust to 0!<br>The Caretaker will remember this betrayal.</p>' +
            '<div class="cp-modal-buttons">' +
            '<button class="cp-btn cp-btn-reclaim" onclick="CaretakerPrice._confirmReclaim()">Reclaim</button>' +
            '<button class="cp-btn cp-btn-clear" onclick="CaretakerPrice._closeReclaimModal()">Cancel</button>' +
            '</div></div>';
        document.body.appendChild(overlay);
        overlay.addEventListener('click', function(e) { if (e.target === overlay) closeReclaimModal(); });
    }

    function closeReclaimModal() {
        var m = document.getElementById('cp-reclaim-modal');
        if (m && m.parentNode) m.parentNode.removeChild(m);
    }

    function confirmReclaim() {
        var r = reclaimAll();
        closeReclaimModal();
        selectedSlots = [null, null];
        var ws = document.querySelector('.cp-workshop');
        if (ws && ws.parentElement) render(ws.parentElement.id);
        return r;
    }

    function doCombine() {
        var c = getConfiscated();
        if (selectedSlots[0] === null || selectedSlots[1] === null) return;
        var m1 = c[selectedSlots[0]], m2 = c[selectedSlots[1]];
        if (!m1 || !m2) return;

        emitSparks(document.querySelector('.cp-combine-area'));

        setTimeout(function() {
            combineHybrid(m1.id, m2.id);
            selectedSlots = [null, null];
            var ws = document.querySelector('.cp-workshop');
            if (ws && ws.parentElement) render(ws.parentElement.id);
        }, 400);
    }

    function clearSlots() {
        selectedSlots = [null, null];
        var ws = document.querySelector('.cp-workshop');
        if (ws && ws.parentElement) render(ws.parentElement.id);
    }

    // ── Public API ──────────────────────────────────────────────────

    return {
        updateVisit:          updateVisit,
        getEfficiency:        getEfficiency,
        calculateDecay:       calculateDecay,
        applyXPTax:           applyXPTax,
        tryConfiscate:        tryConfiscate,
        getConfiscated:       getConfiscated,
        getHybrids:           getHybrids,
        canCombine:           canCombine,
        combineHybrid:        combineHybrid,
        reclaimAll:           reclaimAll,
        isWorkshopDiscovered: isWorkshopDiscovered,
        discoverWorkshop:     discoverWorkshop,
        render:               render,
        _showReclaimModal:    showReclaimModal,
        _closeReclaimModal:   closeReclaimModal,
        _confirmReclaim:      confirmReclaim,
        _doCombine:           doCombine,
        _clearSlots:          clearSlots,
        HYBRID_RECIPES:       HYBRID_RECIPES
    };
})();
