// ══════════════════════════════════════════════════
//  Confession Engine — Post-Kill Moral Reflection
//  Phase 9B — The Confession Booth
// ══════════════════════════════════════════════════

(function() {
    'use strict';

    var STORAGE_KEY = 'moreau_confessions';
    var TOKEN_KEY = 'moreau_resurrection_token';
    var LOCKED_KEY = 'moreau_recitations_detected';

    var REMORSE_WORDS = [
        'sorry','regret','forgive','shouldn\'t','mistake','fault','miss','wish',
        'heart','loved','remember','honor','peace','rest','deserve','better',
        'pain','hurt','guilt','wrong','terrible','awful','mourn','grief','loss'
    ];
    var COLD_WORDS = [
        'weak','pathetic','nothing','whatever','don\'t care','lol','haha','next',
        'move on','doesn\'t matter','who cares','bye','meh','ok','fine',
        'strong survive','natural selection','inevitable','necessary','sacrifice','worth it'
    ];
    var DEFLECTION_WORDS = [
        'game','just','pixel','data','code','reset','anyway','but','well','so','like'
    ];

    var QUIRKS = [
        'talks to shadows','counts everything','laughs at wrong moments',
        'freezes before attacking','whispers to opponents','refuses to make eye contact',
        'hums during fights','apologizes after hitting','stares at the sky between rounds',
        'traces patterns on the ground'
    ];

    // ── Sentiment analysis ──

    function analyzeConfession(text) {
        var lower = text.toLowerCase();
        var score = 0;
        REMORSE_WORDS.forEach(function(w) {
            if (lower.indexOf(w) !== -1) score += 0.1;
        });
        COLD_WORDS.forEach(function(w) {
            if (lower.indexOf(w) !== -1) score -= 0.1;
        });
        // Round to avoid float issues
        score = Math.round(score * 100) / 100;

        var sentiment, path;
        if (score > 0.3) { sentiment = 'remorseful'; path = 'haunted'; }
        else if (score < -0.2) { sentiment = 'cold'; path = 'hollow'; }
        else { sentiment = 'unreadable'; path = 'unreadable'; }

        return { score: score, sentiment: sentiment, path: path };
    }

    // ── Storage helpers ──

    function getJournal() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
        catch(e) { return []; }
    }

    function saveEntry(entry) {
        var journal = getJournal();
        journal.push(entry);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(journal));
        return journal;
    }

    function checkRecitations(journal, newText) {
        var count = 0;
        for (var i = 0; i < journal.length; i++) {
            if (journal[i].text === newText) count++;
        }
        // count includes the newly saved entry
        return count >= 3;
    }

    function getResurrectionStatus() {
        var journal = getJournal();
        var locked = localStorage.getItem(LOCKED_KEY) === 'true';
        var hauntedCount = 0;
        for (var i = 0; i < journal.length; i++) {
            if (journal[i].path === 'haunted') hauntedCount++;
        }
        var hasToken = localStorage.getItem(TOKEN_KEY) === 'true';
        return {
            available: hasToken,
            hauntedCount: hauntedCount,
            needed: 20,
            locked: locked
        };
    }

    // ── Apply consequences ──

    function applyConsequences(path, killerPetName) {
        var pets = [];
        try { pets = JSON.parse(localStorage.getItem('moreau_pets') || '[]'); }
        catch(e) { return; }

        var killerIdx = -1;
        for (var i = 0; i < pets.length; i++) {
            if (pets[i].name === killerPetName && pets[i].is_alive !== false && !pets[i].deceased) {
                killerIdx = i;
                break;
            }
        }
        // If killer not found (e.g. the killer IS the dead pet in lab), skip stat mods
        if (killerIdx === -1) return;

        var pet = pets[killerIdx];
        var stats = pet.base_stats || pet.stats || {};

        if (path === 'hollow') {
            // +2 ATK, suppress dreams for 10 fights
            stats.atk = (stats.atk || 5) + 2;
            pet.base_stats = stats;
            pet.dreamsSuppressed = (pet.dreamsSuppressed || 0) + 10;

            // Track consecutive hollow
            pet.consecutiveHollow = (pet.consecutiveHollow || 0) + 1;
            if (pet.consecutiveHollow >= 5) {
                pet.title = 'The Hollow';
            }
        } else if (path === 'haunted') {
            // Weight debuff: -1 WIL for 5 fights
            pet.weightDebuff = (pet.weightDebuff || 0) + 5;
            // Reset consecutive hollow
            pet.consecutiveHollow = 0;

            // Check if resurrection token should be granted
            var status = getResurrectionStatus();
            if (status.hauntedCount >= 20 && !status.locked && !status.available) {
                localStorage.setItem(TOKEN_KEY, 'true');
            }
        } else if (path === 'unreadable') {
            // Random quirk
            pet.quirk = QUIRKS[Math.floor(Math.random() * QUIRKS.length)];
            pet.consecutiveHollow = 0;
        }

        pets[killerIdx] = pet;
        localStorage.setItem('moreau_pets', JSON.stringify(pets));
    }

    // ── Resurrection ──

    function resurrectPet(petIndex) {
        if (localStorage.getItem(TOKEN_KEY) !== 'true') return false;
        if (localStorage.getItem(LOCKED_KEY) === 'true') return false;

        var pets = [];
        try { pets = JSON.parse(localStorage.getItem('moreau_pets') || '[]'); }
        catch(e) { return false; }

        if (petIndex < 0 || petIndex >= pets.length) return false;
        var pet = pets[petIndex];
        if (!pet.deceased && pet.is_alive !== false) return false;

        // Resurrect
        delete pet.deceased;
        pet.is_alive = true;
        pet.instability = 0;
        // Keep level, mutations, stats
        pets[petIndex] = pet;

        localStorage.setItem('moreau_pets', JSON.stringify(pets));
        localStorage.removeItem(TOKEN_KEY);
        return true;
    }

    // ── Modal UI ──

    function injectStyles() {
        if (document.getElementById('confession-engine-styles')) return;
        var style = document.createElement('style');
        style.id = 'confession-engine-styles';
        style.textContent = [
            '@keyframes confessionScanline { 0% { transform: translateY(-100%); } 100% { transform: translateY(100vh); } }',
            '@keyframes confessionFlicker { 0%,100% { opacity:1; } 50% { opacity:0.97; } 25%,75% { opacity:0.99; } }',
            '@keyframes confessionFadeIn { from { opacity:0; transform:scale(0.95); } to { opacity:1; transform:scale(1); } }',
            '@keyframes confessionPulse { 0%,100% { opacity:0.6; } 50% { opacity:1; } }',
            '.confession-overlay {',
            '  position:fixed; top:0; left:0; right:0; bottom:0;',
            '  background:rgba(0,0,0,0.95); z-index:99999;',
            '  display:flex; align-items:center; justify-content:center;',
            '  animation: confessionFadeIn 0.5s ease;',
            '}',
            '.confession-overlay::after {',
            '  content:""; position:absolute; top:0; left:0; right:0; bottom:0;',
            '  background: repeating-linear-gradient(transparent, transparent 2px, rgba(0,255,65,0.03) 2px, rgba(0,255,65,0.03) 4px);',
            '  pointer-events:none;',
            '}',
            '.confession-overlay .scanline {',
            '  position:absolute; top:0; left:0; right:0; height:4px;',
            '  background:rgba(0,255,65,0.08);',
            '  animation: confessionScanline 4s linear infinite;',
            '  pointer-events:none;',
            '}',
            '.confession-terminal {',
            '  position:relative; z-index:1;',
            '  width:90%; max-width:520px;',
            '  background:#0a0a0a; border:1px solid #1a3a1a;',
            '  border-radius:4px; padding:2rem;',
            '  font-family:"Courier New",Courier,monospace;',
            '  animation: confessionFlicker 3s ease-in-out infinite;',
            '}',
            '.confession-header {',
            '  color:#00ff41; font-size:0.7rem; letter-spacing:0.15em;',
            '  text-transform:uppercase; margin-bottom:1.5rem;',
            '  border-bottom:1px solid #1a3a1a; padding-bottom:0.75rem;',
            '}',
            '.confession-prompt {',
            '  color:#00ff41; font-size:0.9rem; line-height:1.6;',
            '  margin-bottom:1.5rem;',
            '}',
            '.confession-prompt .dead-name { color:#ff4444; font-weight:bold; }',
            '.confession-input {',
            '  width:100%; background:#050505; border:1px solid #1a3a1a;',
            '  color:#00ff41; font-family:"Courier New",Courier,monospace;',
            '  font-size:0.85rem; padding:0.75rem; border-radius:2px;',
            '  resize:vertical; min-height:80px; max-height:200px;',
            '  outline:none;',
            '}',
            '.confession-input:focus { border-color:#00ff41; }',
            '.confession-input::placeholder { color:#1a3a1a; }',
            '.confession-counter {',
            '  text-align:right; font-size:0.65rem; color:#1a3a1a;',
            '  margin-top:0.3rem; margin-bottom:1rem;',
            '}',
            '.confession-counter.warn { color:#ff4444; }',
            '.confession-submit {',
            '  display:block; width:100%;',
            '  background:transparent; border:1px solid #1a3a1a;',
            '  color:#1a3a1a; font-family:"Courier New",Courier,monospace;',
            '  font-size:0.75rem; letter-spacing:0.1em; text-transform:uppercase;',
            '  padding:0.6rem; cursor:pointer; transition:all 0.3s;',
            '}',
            '.confession-submit:hover:not(:disabled) { border-color:#00ff41; color:#00ff41; }',
            '.confession-submit:disabled { cursor:not-allowed; opacity:0.3; }',
            '.confession-result {',
            '  text-align:center; padding:1.5rem 0;',
            '  font-size:0.85rem; line-height:1.6;',
            '}',
            '.confession-result .result-path { font-size:0.7rem; margin-top:0.75rem; opacity:0.6; }',
            '.path-hollow { color:#6ba3be; }',
            '.path-haunted { color:#d4a017; }',
            '.path-unreadable { color:#7ddf7d; }'
        ].join('\n');
        document.head.appendChild(style);
    }

    function trigger(killerPetName, deadPetName, cause) {
        injectStyles();

        return new Promise(function(resolve) {
            var overlay = document.createElement('div');
            overlay.className = 'confession-overlay';
            overlay.innerHTML =
                '<div class="scanline"></div>' +
                '<div class="confession-terminal">' +
                    '<div class="confession-header">MOREAU RESEARCH FACILITY &mdash; OBSERVATION LOG</div>' +
                    '<div class="confession-prompt">' +
                        'Subject <span class="dead-name">' + escHtml(deadPetName) + '</span> has expired.<br><br>' +
                        'Observations, Doctor?' +
                    '</div>' +
                    '<textarea class="confession-input" id="confessionInput" placeholder="Type your observations..." maxlength="500"></textarea>' +
                    '<div class="confession-counter"><span id="confessionCharCount">0</span> / 500</div>' +
                    '<button class="confession-submit" id="confessionSubmit" disabled>SUBMIT OBSERVATION</button>' +
                '</div>';

            document.body.appendChild(overlay);

            var input = document.getElementById('confessionInput');
            var counter = document.getElementById('confessionCharCount');
            var btn = document.getElementById('confessionSubmit');

            input.addEventListener('input', function() {
                var len = input.value.length;
                counter.textContent = len;
                counter.parentElement.className = 'confession-counter' + (len > 450 ? ' warn' : '');
                btn.disabled = len < 10;
            });

            input.focus();

            btn.addEventListener('click', function() {
                var text = input.value.trim();
                if (text.length < 10) return;

                var analysis = analyzeConfession(text);

                var entry = {
                    text: text,
                    sentiment: analysis.sentiment,
                    score: analysis.score,
                    killerPet: killerPetName,
                    deadPet: deadPetName,
                    cause: cause || 'unknown',
                    timestamp: new Date().toISOString(),
                    path: analysis.path
                };

                var journal = saveEntry(entry);

                // Check copy-paste detection
                if (checkRecitations(journal, text)) {
                    localStorage.setItem(LOCKED_KEY, 'true');
                }

                // Apply consequences
                applyConsequences(analysis.path, killerPetName);

                // Show result
                var terminal = overlay.querySelector('.confession-terminal');
                var resultMsg, pathClass, consequenceMsg;

                if (analysis.path === 'hollow') {
                    resultMsg = 'Cold. Efficient. The data is recorded.';
                    pathClass = 'path-hollow';
                    consequenceMsg = '+2 ATK. Dreams suppressed.';
                } else if (analysis.path === 'haunted') {
                    resultMsg = 'The weight settles. It will not lift easily.';
                    pathClass = 'path-haunted';
                    consequenceMsg = 'Weight debuff applied. The path to redemption moves forward.';
                } else {
                    resultMsg = 'Interesting. The subject displays... unexpected patterns.';
                    pathClass = 'path-unreadable';
                    consequenceMsg = 'A quirk has developed.';
                }

                // Check if recitations just locked the path
                if (localStorage.getItem(LOCKED_KEY) === 'true' && checkRecitations(journal, text)) {
                    consequenceMsg = 'The booth recognizes empty words. The path to redemption is closed.';
                    pathClass = 'path-hollow';
                }

                terminal.innerHTML =
                    '<div class="confession-header">MOREAU RESEARCH FACILITY &mdash; OBSERVATION LOG</div>' +
                    '<div class="confession-result ' + pathClass + '">' +
                        escHtml(resultMsg) +
                        '<div class="result-path">' + escHtml(consequenceMsg) + '</div>' +
                    '</div>';

                setTimeout(function() {
                    overlay.style.transition = 'opacity 0.5s';
                    overlay.style.opacity = '0';
                    setTimeout(function() {
                        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                        resolve(entry);
                    }, 500);
                }, 3000);
            });
        });
    }

    function escHtml(s) {
        var d = document.createElement('div');
        d.appendChild(document.createTextNode(s));
        return d.innerHTML;
    }

    // ── Public API ──

    window.ConfessionEngine = {
        trigger: trigger,
        getJournal: getJournal,
        getResurrectionStatus: getResurrectionStatus,
        resurrectPet: resurrectPet,
        analyzeConfession: analyzeConfession
    };
})();
