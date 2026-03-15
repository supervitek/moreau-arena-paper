// ══════════════════════════════════════════════════════════════════
//  Sleep Dialect — A Constructed Language of the Caretaker
//  Cryptic fragments appear when a player returns after 6+ hours.
//  52-word vocabulary; discovering all reveals the Island's origin.
// ══════════════════════════════════════════════════════════════════

var SleepDialect = (function() {
    'use strict';

    // ── Constants ────────────────────────────────────────────────

    var STORAGE_KEY  = 'moreau_sleep_dialect';
    var PETS_KEY     = 'moreau_pets';
    var ACTIVE_KEY   = 'moreau_active_pet';
    var CSS_INJECTED = false;
    var CSS_ID       = 'sleep-dialect-css';

    var MIN_OFFLINE_MS = 6  * 3600000;   // 6 hours
    var MAX_OFFLINE_MS = 24 * 3600000;   // 24 hours

    var FADE_IN_MS     = 2000;
    var HOLD_MS        = 4000;
    var FADE_OUT_MS    = 1000;
    var TOAST_MS       = 4500;

    var TOTAL_WORDS    = 52;
    var GRID_COLS      = 7;

    // ── The 52-Word Lexicon ─────────────────────────────────────

    var LEXICON = {
        // Core concepts (13)
        vel: 'life',        mor: 'death',       ka:  'soul',
        pet: 'creature',    shi: 'light',       nox: 'dark',
        tir: 'strength',    flo: 'flow',        ren: 'remember',
        dor: 'sleep',       vak: 'wake',        sol: 'sun',
        lun: 'moon',

        // Emotions (10)
        ama: 'love',        dol: 'pain',        spe: 'hope',
        tis: 'fear',        ira: 'anger',       pax: 'peace',
        gau: 'joy',         tri: 'sorrow',      'for': 'courage',
        cal: 'calm',

        // Nature (10)
        aqu: 'water',       ter: 'earth',       ven: 'wind',
        ign: 'fire',        sil: 'forest',      mon: 'mountain',
        mar: 'sea',         cel: 'sky',         her: 'grass',
        fru: 'fruit',

        // Actions (10)
        cur: 'heal',        ali: 'feed',        pug: 'fight',
        cre: 'create',      des: 'destroy',     mig: 'travel',
        can: 'sing',        vid: 'see',         aud: 'hear',
        tac: 'touch',

        // The Island (9)
        ins: 'island',      dom: 'home',        mur: 'wall',
        por: 'door',        via: 'path',        fon: 'fountain',
        alt: 'high',        pro: 'deep',        ori: 'beginning'
    };

    var ALL_WORDS = Object.keys(LEXICON);

    // ── Animal Affinities ───────────────────────────────────────
    // Each animal is biased toward ~7 words from the lexicon.

    var ANIMAL_BIAS = {
        wolf:      ['vel', 'ka',  'ama', 'pax', 'can', 'sil', 'lun'],
        tiger:     ['tir', 'pug', 'nox', 'for', 'vid', 'tac', 'pro'],
        fox:       ['shi', 'flo', 'mig', 'vid', 'via', 'spe', 'cal'],
        bear:      ['ter', 'mon', 'tir', 'dor', 'pax', 'dom', 'cur'],
        eagle:     ['cel', 'alt', 'ven', 'sol', 'vid', 'shi', 'spe'],
        shark:     ['mar', 'aqu', 'pro', 'nox', 'pug', 'tir', 'vel'],
        snake:     ['nox', 'tac', 'cal', 'dol', 'pro', 'ven', 'tis'],
        cat:       ['dor', 'cal', 'shi', 'flo', 'tac', 'gau', 'dom'],
        rabbit:    ['her', 'spe', 'mig', 'fru', 'vel', 'gau', 'ven'],
        scorpion:  ['dol', 'tis', 'nox', 'tac', 'des', 'pro', 'ira'],
        boar:      ['tir', 'ira', 'pug', 'ter', 'des', 'for', 'mon'],
        monkey:    ['gau', 'can', 'fru', 'mig', 'cre', 'aud', 'flo'],
        vulture:   ['mor', 'cel', 'alt', 'vid', 'sol', 'tri', 'ren'],
        rhino:     ['tir', 'ter', 'mur', 'des', 'for', 'mon', 'dom'],
        viper:     ['nox', 'tis', 'tac', 'dol', 'cal', 'pro', 'mor'],
        buffalo:   ['ter', 'pax', 'dom', 'tir', 'dor', 'mon', 'her'],
        panther:   ['nox', 'cal', 'vid', 'pro', 'tac', 'sil', 'lun'],
        porcupine: ['dol', 'mur', 'tac', 'for', 'ter', 'dom', 'tis']
    };

    // ── Fragment Templates ──────────────────────────────────────
    // Poetic translation templates keyed by word count.
    // Placeholders %0 %1 %2 %3 are replaced with translated words.

    var TEMPLATES = {
        2: [
            '%0 meets %1.',
            'Through %0, %1.',
            '%0 within %1.',
            '%0 becomes %1.',
            '%0 awaits %1.',
            'Only %0 knows %1.',
            '%0 after %1.',
            'Neither %0 nor %1.'
        ],
        3: [
            'The %0 of %1 brings %2.',
            '%0 and %1 lead to %2.',
            'In the %0, %1 whispers %2.',
            '%0 devours %1, leaves %2.',
            'Where %0 falls, %1 and %2 remain.',
            'Between %0 and %1 lies %2.',
            'Before %1, there was %0 and %2.',
            '%0 carries %1 toward %2.'
        ],
        4: [
            'The %0 of %1 meets the %2 of %3.',
            '%0 and %1 flow through %2 and %3.',
            'When %0 rises, %1 falls — %2 watches, %3 endures.',
            'From %0 to %1, from %2 to %3.',
            '%0 guards %1 while %2 seeks %3.',
            'In %0 and %1, the Caretaker sees %2 and %3.',
            'First %0, then %1 — always %2, never %3.',
            '%0 under %1, %2 above %3.'
        ]
    };

    // ── The Hidden Message ──────────────────────────────────────

    var HIDDEN_DIALECT = 'vel-pet ori-ins cre-ka. mor-vel des-pet. ali-cur ren-ka. shi-nox flo-vel. tir-pet ama-dom. ins-mur pro-vel. pet-ka ori-vel vel-vel.';

    var HIDDEN_TRANSLATION =
        'The Caretaker remembers the time before the island. ' +
        'We were all one creature. Moreau split us apart. ' +
        'The fifteen animals are fragments of Aleph. ' +
        'In the beginning there was one life, one soul. ' +
        'The walls were built to keep us separate. ' +
        'But life flows through walls. ' +
        'We remember being whole.';

    // ── Helpers ─────────────────────────────────────────────────

    function loadState() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (raw) return JSON.parse(raw);
        } catch (e) { /* ignore */ }
        return {
            words_discovered: [],
            fragments_seen:   [],
            last_active:      Date.now()
        };
    }

    function saveState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) { /* ignore */ }
    }

    function getActivePet() {
        try {
            var pets  = JSON.parse(localStorage.getItem(PETS_KEY) || '[]');
            var idx   = parseInt(localStorage.getItem(ACTIVE_KEY) || '0', 10);
            return pets[idx] || pets[0] || null;
        } catch (e) {
            return null;
        }
    }

    function shuffle(arr) {
        var a = arr.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    function pickRandom(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    function unique(arr) {
        var seen = {};
        return arr.filter(function(v) {
            if (seen[v]) return false;
            seen[v] = true;
            return true;
        });
    }

    // ── CSS Injection ───────────────────────────────────────────

    function injectCSS() {
        if (CSS_INJECTED) return;
        if (document.getElementById(CSS_ID)) { CSS_INJECTED = true; return; }

        var style = document.createElement('style');
        style.id = CSS_ID;
        style.textContent = [

            // ── Overlay ──
            '#sleepDialectOverlay {',
            '  position: fixed; top: 0; left: 0; width: 100%; height: 100%;',
            '  background: rgba(0, 0, 10, 0.95); z-index: 10000;',
            '  display: flex; align-items: center; justify-content: center;',
            '  flex-direction: column; opacity: 0;',
            '  transition: opacity ' + FADE_OUT_MS + 'ms ease;',
            '  pointer-events: none;',
            '}',
            '#sleepDialectOverlay.sd-visible { opacity: 1; }',

            '#sleepDialectOverlay .sd-dialect {',
            '  font-family: "Courier New", monospace;',
            '  color: #4a6670; font-size: 28px; letter-spacing: 8px;',
            '  text-align: center; max-width: 80%; line-height: 1.6;',
            '  opacity: 0; transition: opacity ' + FADE_IN_MS + 'ms ease;',
            '}',
            '#sleepDialectOverlay .sd-dialect.sd-show { opacity: 1; }',

            '#sleepDialectOverlay .sd-dialect .sd-known {',
            '  color: #7a9eaa; text-shadow: 0 0 8px rgba(122,158,170,0.4);',
            '}',

            '#sleepDialectOverlay .sd-hint {',
            '  color: #2a3640; font-size: 14px; margin-top: 24px;',
            '  font-family: "Courier New", monospace; letter-spacing: 2px;',
            '  opacity: 0; transition: opacity ' + FADE_IN_MS + 'ms ease;',
            '  text-align: center; max-width: 70%;',
            '}',
            '#sleepDialectOverlay .sd-hint.sd-show { opacity: 1; }',

            // ── Toast ──
            '.sd-toast {',
            '  position: fixed; bottom: 32px; left: 50%;',
            '  transform: translateX(-50%); z-index: 10001;',
            '  background: rgba(26, 26, 58, 0.92);',
            '  border: 1px solid #d4a017; border-radius: 8px;',
            '  color: #d4a017; font-size: 13px; padding: 10px 20px;',
            '  font-family: "Courier New", monospace;',
            '  letter-spacing: 1px; opacity: 0;',
            '  transition: opacity 0.4s ease;',
            '  pointer-events: none;',
            '}',
            '.sd-toast.sd-show { opacity: 1; }',

            // ── Lexicon Panel ──
            '.sd-lexicon-wrap {',
            '  background: #1a1a3a; border-radius: 10px;',
            '  padding: 0; margin-top: 24px; overflow: hidden;',
            '  border: 1px solid #2a2a5a;',
            '}',

            '.sd-lexicon-header {',
            '  display: flex; align-items: center; justify-content: space-between;',
            '  padding: 14px 18px; cursor: pointer;',
            '  background: #1e1e42; user-select: none;',
            '  transition: background 0.2s ease;',
            '}',
            '.sd-lexicon-header:hover { background: #24244e; }',

            '.sd-lexicon-title {',
            '  font-family: "Courier New", monospace;',
            '  color: #8888bb; font-size: 16px; letter-spacing: 1px;',
            '}',

            '.sd-lexicon-progress {',
            '  font-family: "Courier New", monospace;',
            '  color: #6666aa; font-size: 13px;',
            '}',

            '.sd-lexicon-chevron {',
            '  color: #6666aa; font-size: 18px;',
            '  transition: transform 0.3s ease;',
            '}',
            '.sd-lexicon-wrap.sd-open .sd-lexicon-chevron {',
            '  transform: rotate(180deg);',
            '}',

            '.sd-lexicon-body {',
            '  max-height: 0; overflow: hidden;',
            '  transition: max-height 0.4s ease;',
            '  padding: 0 18px;',
            '}',
            '.sd-lexicon-wrap.sd-open .sd-lexicon-body {',
            '  max-height: 800px; padding: 8px 18px 18px;',
            '}',

            // ── Grid ──
            '.sd-grid {',
            '  display: grid;',
            '  grid-template-columns: repeat(' + GRID_COLS + ', 1fr);',
            '  gap: 6px; margin-top: 10px;',
            '}',

            '.sd-tile {',
            '  background: #12122a; border: 1px solid #2a2a5a;',
            '  border-radius: 6px; padding: 8px 4px;',
            '  text-align: center; font-family: "Courier New", monospace;',
            '  font-size: 12px; line-height: 1.4;',
            '  transition: border-color 0.3s ease, box-shadow 0.3s ease;',
            '  min-height: 48px; display: flex; flex-direction: column;',
            '  align-items: center; justify-content: center;',
            '}',

            '.sd-tile.sd-discovered {',
            '  border-color: rgba(212, 160, 23, 0.35);',
            '  cursor: pointer;',
            '}',
            '.sd-tile.sd-discovered:hover {',
            '  border-color: #d4a017;',
            '  box-shadow: 0 0 10px rgba(212, 160, 23, 0.2);',
            '}',

            '.sd-tile .sd-word {',
            '  color: #d4a017; font-weight: bold; font-size: 14px;',
            '}',
            '.sd-tile .sd-meaning {',
            '  color: #9a8040; font-size: 11px; margin-top: 2px;',
            '}',

            '.sd-tile.sd-locked .sd-word {',
            '  color: #3a3a5a; font-size: 13px;',
            '}',

            // ── Glow animation on click ──
            '@keyframes sdGlow {',
            '  0%   { box-shadow: 0 0 4px rgba(212,160,23,0.3); }',
            '  50%  { box-shadow: 0 0 18px rgba(212,160,23,0.6); }',
            '  100% { box-shadow: 0 0 4px rgba(212,160,23,0.3); }',
            '}',
            '.sd-tile.sd-glowing {',
            '  animation: sdGlow 0.6s ease;',
            '}',

            // ── Complete state ──
            '.sd-lexicon-wrap.sd-complete {',
            '  border-color: #d4a017;',
            '  box-shadow: 0 0 20px rgba(212, 160, 23, 0.15);',
            '}',
            '.sd-lexicon-wrap.sd-complete .sd-lexicon-title {',
            '  color: #d4a017;',
            '}',

            '.sd-decoded {',
            '  margin-top: 16px; padding: 14px;',
            '  background: rgba(212, 160, 23, 0.08);',
            '  border: 1px solid rgba(212, 160, 23, 0.25);',
            '  border-radius: 8px;',
            '}',
            '.sd-decoded-dialect {',
            '  font-family: "Courier New", monospace;',
            '  color: #d4a017; font-size: 13px;',
            '  letter-spacing: 2px; line-height: 1.8;',
            '  margin-bottom: 12px; word-break: break-word;',
            '}',
            '.sd-decoded-translation {',
            '  font-family: Georgia, serif;',
            '  color: #c8b060; font-size: 14px;',
            '  line-height: 1.7; font-style: italic;',
            '}',

            // ── Progress bar ──
            '.sd-progress-bar {',
            '  width: 100%; height: 4px; background: #12122a;',
            '  border-radius: 2px; margin-top: 10px; overflow: hidden;',
            '}',
            '.sd-progress-fill {',
            '  height: 100%; background: linear-gradient(90deg, #6a5a10, #d4a017);',
            '  border-radius: 2px; transition: width 0.5s ease;',
            '}',

            // ── Responsive ──
            '@media (max-width: 600px) {',
            '  .sd-grid { grid-template-columns: repeat(4, 1fr); gap: 4px; }',
            '  .sd-tile { padding: 6px 2px; min-height: 42px; }',
            '  .sd-tile .sd-word { font-size: 12px; }',
            '  .sd-tile .sd-meaning { font-size: 10px; }',
            '  #sleepDialectOverlay .sd-dialect { font-size: 20px; letter-spacing: 4px; }',
            '}'

        ].join('\n');

        document.head.appendChild(style);
        CSS_INJECTED = true;
    }

    // ── Fragment Generation ─────────────────────────────────────

    function pickWords(pet, count) {
        var animal = (pet && pet.animal) ? pet.animal : 'fox';
        var biased = ANIMAL_BIAS[animal] || ANIMAL_BIAS.fox;

        // Build a weighted pool: biased words appear 3x
        var pool = [];
        for (var i = 0; i < ALL_WORDS.length; i++) {
            pool.push(ALL_WORDS[i]);
            if (biased.indexOf(ALL_WORDS[i]) !== -1) {
                pool.push(ALL_WORDS[i]);
                pool.push(ALL_WORDS[i]);
            }
        }

        var picked  = [];
        var used    = {};
        var tries   = 0;
        var maxTries = count * 20;

        while (picked.length < count && tries < maxTries) {
            var w = pool[Math.floor(Math.random() * pool.length)];
            if (!used[w]) {
                used[w] = true;
                picked.push(w);
            }
            tries++;
        }

        // Fallback: if we didn't get enough, fill from shuffled ALL_WORDS
        if (picked.length < count) {
            var remaining = shuffle(ALL_WORDS).filter(function(w) { return !used[w]; });
            while (picked.length < count && remaining.length > 0) {
                picked.push(remaining.shift());
            }
        }

        return picked;
    }

    function buildDialectText(words) {
        // Combine words with hyphens in pairs, space between pairs
        // e.g. 4 words → "vel-ka dor-nox"
        // e.g. 3 words → "vel-ka dor"
        var parts = [];
        for (var i = 0; i < words.length; i += 2) {
            if (i + 1 < words.length) {
                parts.push(words[i] + '-' + words[i + 1]);
            } else {
                parts.push(words[i]);
            }
        }
        return parts.join(' ');
    }

    function buildTranslation(words) {
        var count = words.length;
        var templates = TEMPLATES[count] || TEMPLATES[2];
        var template  = pickRandom(templates);

        var translated = words.map(function(w) { return LEXICON[w] || w; });

        var result = template;
        for (var i = 0; i < translated.length; i++) {
            result = result.replace('%' + i, translated[i]);
        }
        return result;
    }

    // ── Overlay ─────────────────────────────────────────────────

    function buildOverlayHTML(dialectText, translation, words, discovered) {
        // Mark known words with a highlight span
        var knownSet = {};
        for (var i = 0; i < discovered.length; i++) {
            knownSet[discovered[i]] = true;
        }

        // Split dialect text into tokens, highlight known words
        var tokens = dialectText.split(/(\s+|-)/);
        var dialectHTML = '';
        for (var j = 0; j < tokens.length; j++) {
            var tok = tokens[j];
            if (LEXICON[tok] && knownSet[tok]) {
                dialectHTML += '<span class="sd-known">' + tok + '</span>';
            } else {
                dialectHTML += tok;
            }
        }

        // Only show partial translation if player has discovered some words
        var hintHTML = '';
        var hasKnown = false;
        for (var k = 0; k < words.length; k++) {
            if (knownSet[words[k]]) { hasKnown = true; break; }
        }
        if (hasKnown) {
            // Build a partial hint: show known meanings, mask unknown
            var hintParts = words.map(function(w) {
                return knownSet[w] ? LEXICON[w] : '???';
            });
            hintHTML = '[ ' + hintParts.join(' \u00b7 ') + ' ]';
        }

        return '<div id="sleepDialectOverlay">' +
               '  <div class="sd-dialect">' + dialectHTML + '</div>' +
               (hintHTML ? '  <div class="sd-hint">' + hintHTML + '</div>' : '') +
               '</div>';
    }

    function showToast(message) {
        var toast = document.createElement('div');
        toast.className = 'sd-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // Force reflow, then show
        toast.offsetHeight; // eslint-disable-line no-unused-expressions
        toast.classList.add('sd-show');

        setTimeout(function() {
            toast.classList.remove('sd-show');
            setTimeout(function() {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 500);
        }, TOAST_MS);
    }

    // ── Lexicon Renderer ────────────────────────────────────────

    function buildLexiconHTML(discovered) {
        var discoveredSet = {};
        for (var i = 0; i < discovered.length; i++) {
            discoveredSet[discovered[i]] = true;
        }

        var count     = discovered.length;
        var complete  = count >= TOTAL_WORDS;
        var pct       = Math.round((count / TOTAL_WORDS) * 100);

        var wrapClass = 'sd-lexicon-wrap' + (complete ? ' sd-complete' : '');

        var html = '<div class="' + wrapClass + '">';

        // Header
        html += '<div class="sd-lexicon-header">';
        html += '  <span class="sd-lexicon-title">\ud83d\udcd6 Sleep Lexicon</span>';
        html += '  <span class="sd-lexicon-progress">Discovered: ' + count + '/' + TOTAL_WORDS + '</span>';
        html += '  <span class="sd-lexicon-chevron">\u25bc</span>';
        html += '</div>';

        // Body
        html += '<div class="sd-lexicon-body">';

        // Progress bar
        html += '<div class="sd-progress-bar">';
        html += '  <div class="sd-progress-fill" style="width: ' + pct + '%;"></div>';
        html += '</div>';

        // Grid
        html += '<div class="sd-grid">';
        for (var j = 0; j < ALL_WORDS.length; j++) {
            var w = ALL_WORDS[j];
            if (discoveredSet[w]) {
                html += '<div class="sd-tile sd-discovered" data-word="' + w + '">';
                html += '  <span class="sd-word">' + w + '</span>';
                html += '  <span class="sd-meaning">' + LEXICON[w] + '</span>';
                html += '</div>';
            } else {
                html += '<div class="sd-tile sd-locked">';
                html += '  <span class="sd-word">???</span>';
                html += '</div>';
            }
        }
        html += '</div>';

        // Decoded message (only if complete)
        if (complete) {
            html += '<div class="sd-decoded">';
            html += '  <div class="sd-decoded-dialect">' + HIDDEN_DIALECT + '</div>';
            html += '  <div class="sd-decoded-translation">' + HIDDEN_TRANSLATION + '</div>';
            html += '</div>';
        }

        html += '</div>'; // body
        html += '</div>'; // wrap

        return html;
    }

    function attachLexiconEvents(container) {
        // Toggle expand / collapse
        var wrap   = container.querySelector('.sd-lexicon-wrap');
        var header = container.querySelector('.sd-lexicon-header');
        if (header && wrap) {
            header.addEventListener('click', function() {
                wrap.classList.toggle('sd-open');
            });
        }

        // Tile click glow
        var tiles = container.querySelectorAll('.sd-tile.sd-discovered');
        for (var i = 0; i < tiles.length; i++) {
            (function(tile) {
                tile.addEventListener('click', function() {
                    tile.classList.remove('sd-glowing');
                    // Force reflow
                    tile.offsetHeight; // eslint-disable-line no-unused-expressions
                    tile.classList.add('sd-glowing');
                    setTimeout(function() {
                        tile.classList.remove('sd-glowing');
                    }, 650);
                });
            })(tiles[i]);
        }

        // Achievement check
        var state = loadState();
        if (state.words_discovered.length >= TOTAL_WORDS) {
            if (typeof window.checkAchievement === 'function') {
                try { window.checkAchievement('linguist'); } catch (e) { /* ignore */ }
            }
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  Public API
    // ══════════════════════════════════════════════════════════════

    return {

        // ── checkOfflineDuration ────────────────────────────────
        // Returns hours since last recorded activity.

        checkOfflineDuration: function() {
            var state = loadState();
            var last  = state.last_active || Date.now();
            var diff  = Date.now() - last;
            return diff / 3600000;
        },

        // ── shouldShowFragment ──────────────────────────────────
        // True if the player was offline for 6-24 hours.

        shouldShowFragment: function() {
            var hours = this.checkOfflineDuration();
            return hours >= (MIN_OFFLINE_MS / 3600000) &&
                   hours <= (MAX_OFFLINE_MS / 3600000);
        },

        // ── generateFragment ────────────────────────────────────
        // Produces a dialect fragment tailored to the pet's animal.
        // Returns { dialectText, translation, words[] }.

        generateFragment: function(pet) {
            var wordCount = 2 + Math.floor(Math.random() * 3); // 2-4
            var words     = pickWords(pet, wordCount);
            var dialect   = buildDialectText(words);
            var trans     = buildTranslation(words);

            return {
                dialectText: dialect,
                translation: trans,
                words:       words
            };
        },

        // ── discoverWord ────────────────────────────────────────
        // Marks a single word as discovered (idempotent).

        discoverWord: function(word) {
            if (!LEXICON[word]) return;
            var state = loadState();
            if (state.words_discovered.indexOf(word) === -1) {
                state.words_discovered.push(word);
                saveState(state);
            }
        },

        // ── getDiscoveredWords ──────────────────────────────────
        // Returns the array of all discovered word keys.

        getDiscoveredWords: function() {
            return loadState().words_discovered.slice();
        },

        // ── getUndiscoveredCount ────────────────────────────────
        // Returns how many words remain locked.

        getUndiscoveredCount: function() {
            var d = loadState().words_discovered.length;
            return TOTAL_WORDS - d;
        },

        // ── getFullMessage ──────────────────────────────────────
        // Returns the decoded origin message, or null if incomplete.

        getFullMessage: function() {
            if (!this.isComplete()) return null;
            return {
                dialect:     HIDDEN_DIALECT,
                translation: HIDDEN_TRANSLATION
            };
        },

        // ── isComplete ──────────────────────────────────────────
        // True when all 52 words have been discovered.

        isComplete: function() {
            return loadState().words_discovered.length >= TOTAL_WORDS;
        },

        // ── showOverlay ─────────────────────────────────────────
        // Displays the dark overlay with dialect text on the page.
        // Automatically discovers the fragment's words and shows a
        // toast if new words were learned.

        showOverlay: function() {
            injectCSS();

            var pet      = getActivePet();
            var fragment = this.generateFragment(pet);
            var state    = loadState();
            var self     = this;

            // Record this fragment
            var fragmentId = fragment.dialectText;
            if (state.fragments_seen.indexOf(fragmentId) === -1) {
                state.fragments_seen.push(fragmentId);
                // Keep only last 50 fragments
                if (state.fragments_seen.length > 50) {
                    state.fragments_seen = state.fragments_seen.slice(-50);
                }
            }

            // Build overlay
            var overlayHTML = buildOverlayHTML(
                fragment.dialectText,
                fragment.translation,
                fragment.words,
                state.words_discovered
            );

            // Inject into page
            var temp = document.createElement('div');
            temp.innerHTML = overlayHTML;
            var overlay = temp.firstElementChild || temp.firstChild;
            document.body.appendChild(overlay);

            // Animation sequence
            // Step 1: overlay appears
            requestAnimationFrame(function() {
                overlay.classList.add('sd-visible');

                // Step 2: dialect text fades in
                var dialectEl = overlay.querySelector('.sd-dialect');
                var hintEl    = overlay.querySelector('.sd-hint');

                setTimeout(function() {
                    if (dialectEl) dialectEl.classList.add('sd-show');
                    if (hintEl)    hintEl.classList.add('sd-show');
                }, 100);

                // Step 3: after hold, begin fade out
                setTimeout(function() {
                    if (dialectEl) dialectEl.classList.remove('sd-show');
                    if (hintEl)    hintEl.classList.remove('sd-show');

                    setTimeout(function() {
                        overlay.classList.remove('sd-visible');

                        // Step 4: remove overlay from DOM after fade
                        setTimeout(function() {
                            if (overlay.parentNode) {
                                overlay.parentNode.removeChild(overlay);
                            }

                            // Step 5: discover words and show toast
                            var newWords = [];
                            for (var i = 0; i < fragment.words.length; i++) {
                                var w = fragment.words[i];
                                if (state.words_discovered.indexOf(w) === -1) {
                                    newWords.push(w);
                                    state.words_discovered.push(w);
                                }
                            }
                            saveState(state);

                            if (newWords.length > 0) {
                                var labels = newWords.map(function(w) {
                                    return w + ' = ' + LEXICON[w];
                                });
                                showToast('New words learned: ' + labels.join(', '));
                            }

                            // Achievement check
                            if (state.words_discovered.length >= TOTAL_WORDS) {
                                if (typeof window.checkAchievement === 'function') {
                                    try { window.checkAchievement('linguist'); } catch (e) { /* ignore */ }
                                }
                            }
                        }, FADE_OUT_MS + 100);

                    }, FADE_OUT_MS);

                }, FADE_IN_MS + HOLD_MS);
            });
        },

        // ── renderLexicon ───────────────────────────────────────
        // Renders the collapsible decoder-book UI into a container.

        renderLexicon: function(containerId) {
            injectCSS();

            var container = document.getElementById(containerId);
            if (!container) return;

            var state = loadState();
            container.innerHTML = buildLexiconHTML(state.words_discovered);
            attachLexiconEvents(container);
        },

        // ── updateActivity ──────────────────────────────────────
        // Stamps the current time as last_active.

        updateActivity: function() {
            var state = loadState();
            state.last_active = Date.now();
            saveState(state);
        },

        // ── Utility: expose lexicon for external use ────────────

        getLexicon: function() {
            var copy = {};
            for (var k in LEXICON) {
                if (LEXICON.hasOwnProperty(k)) copy[k] = LEXICON[k];
            }
            return copy;
        },

        getTotalWords: function() {
            return TOTAL_WORDS;
        }
    };

})();
