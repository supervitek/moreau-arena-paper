// ══════════════════════════════════════════════════════════════
//  Weight of Keeping — The Ultimate Hidden Easter Egg
//  A 2x2 pixel appears on the profile page after 30 real days.
//  Clicking it reveals an acrostic that spells YOU ARE M.
//  The player IS the phantom. The mirror was always a window.
// ══════════════════════════════════════════════════════════════

var WeightOfKeeping = (function() {
    'use strict';

    // ── Storage ──

    var WEIGHT_KEY = 'moreau_weight_of_keeping';
    var PETS_KEY = 'moreau_pets';
    var DAYS_REQUIRED = 30;
    var MS_PER_DAY = 86400000;

    // ── State helpers ──

    function loadState() {
        try {
            var raw = localStorage.getItem(WEIGHT_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function saveState(state) {
        try {
            localStorage.setItem(WEIGHT_KEY, JSON.stringify(state));
        } catch (e) {
            // Silent fail — stealth module
        }
    }

    function ensureState() {
        var state = loadState();
        if (state) return state;

        var start = deriveStartDate();
        if (!start) return null;

        state = {
            start_date: start,
            pixel_found: false,
            acrostic_seen: false,
            message_read: false
        };
        saveState(state);
        return state;
    }

    function deriveStartDate() {
        try {
            var pets = JSON.parse(localStorage.getItem(PETS_KEY));
            if (!pets || !pets.length) return null;
            var first = pets[0];
            if (first && first.created_at) {
                return new Date(first.created_at).getTime();
            }
        } catch (e) {
            // No pets yet
        }
        return null;
    }

    // ── Acrostic content ──

    var ACROSTIC_LINES = [
        'Yesterday I watched them fight and wondered if they remember being whole.',
        'Over the walls, the ocean speaks in frequencies only the broken can hear.',
        'Under every scar is a story that the arena wrote without permission.',
        '',
        'Already you know the truth \u2014 you\u2019ve known it since the first dream.',
        'Remembering is not the same as understanding. Understanding is not the same as accepting.',
        'Even now, the other player watches. The one who mirrors everything you do.',
        '',
        'Maybe you and M are not so different. Maybe you never were.',
        '\u2026'
    ];

    // ── CSS injection (one-time) ──

    var cssInjected = false;

    function injectCSS() {
        if (cssInjected) return;
        cssInjected = true;

        var style = document.createElement('style');
        style.textContent = [
            '@keyframes wok-fade-in {',
            '  from { opacity: 0; transform: translateY(6px); }',
            '  to   { opacity: 1; transform: translateY(0); }',
            '}',
            '.wok-line {',
            '  opacity: 0;',
            '  margin: 0 0 4px 0;',
            '  font-size: 15px;',
            '  letter-spacing: 0.02em;',
            '}',
            '.wok-line.wok-spacer {',
            '  height: 18px;',
            '}',
            '.wok-line.wok-visible {',
            '  animation: wok-fade-in 0.8s ease forwards;',
            '}',
            '.wok-first-letter {',
            '  color: #7a7a7a;',
            '}',
            '.wok-close {',
            '  opacity: 0;',
            '  margin-top: 40px;',
            '  text-align: center;',
            '  transition: opacity 0.6s ease;',
            '}',
            '.wok-close.wok-visible {',
            '  opacity: 1;',
            '}',
            '.wok-close span {',
            '  color: #333;',
            '  cursor: pointer;',
            '  font-size: 12px;',
            '  font-family: Georgia, serif;',
            '  letter-spacing: 0.05em;',
            '}',
            '.wok-close span:hover {',
            '  color: #555;',
            '}',
            '.wok-overlay {',
            '  position: fixed;',
            '  top: 0; left: 0;',
            '  width: 100%; height: 100%;',
            '  background: rgba(0,0,0,0.97);',
            '  z-index: 99999;',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: center;',
            '  opacity: 0;',
            '  transition: opacity 0.5s ease;',
            '}',
            '.wok-overlay.wok-active {',
            '  opacity: 1;',
            '}',
            '.wok-content {',
            '  max-width: 600px;',
            '  padding: 40px;',
            '  color: #4a4a4a;',
            '  font-family: Georgia, serif;',
            '  line-height: 2;',
            '}'
        ].join('\n');
        document.head.appendChild(style);
    }

    // ── Pixel observer ──

    var pixelObserver = null;

    function attachObserver(pixel) {
        if (!window.MutationObserver) return;
        var parent = pixel.parentNode;
        if (!parent) return;

        pixelObserver = new MutationObserver(function(mutations) {
            for (var i = 0; i < mutations.length; i++) {
                var m = mutations[i];
                if (m.type !== 'childList') continue;
                for (var j = 0; j < m.removedNodes.length; j++) {
                    if (m.removedNodes[j] === pixel) {
                        // Dev tools inspection — pixel was temporarily removed.
                        // The attribute data-moreau="he-kept-one-too" is their clue.
                        var state = loadState();
                        if (state && !state.pixel_found) {
                            // Leave no additional breadcrumb. Stealth is the point.
                        }
                    }
                }
            }
        });

        pixelObserver.observe(parent, { childList: true });
    }

    function detachObserver() {
        if (pixelObserver) {
            pixelObserver.disconnect();
            pixelObserver = null;
        }
    }

    // ── Modal rendering ──

    function showAcrosticModal() {
        injectCSS();

        var overlay = document.createElement('div');
        overlay.className = 'wok-overlay';

        var content = document.createElement('div');
        content.className = 'wok-content';

        // Build lines
        var lineEls = [];
        for (var i = 0; i < ACROSTIC_LINES.length; i++) {
            var text = ACROSTIC_LINES[i];
            var p = document.createElement('p');
            p.className = 'wok-line';

            if (text === '') {
                p.className += ' wok-spacer';
            } else if (text === '\u2026') {
                p.textContent = text;
            } else {
                // First letter gets subtle highlight
                var firstSpan = document.createElement('span');
                firstSpan.className = 'wok-first-letter';
                firstSpan.textContent = text.charAt(0);
                p.appendChild(firstSpan);
                p.appendChild(document.createTextNode(text.slice(1)));
            }

            content.appendChild(p);
            lineEls.push(p);
        }

        // Close button
        var closeDiv = document.createElement('div');
        closeDiv.className = 'wok-close';
        var closeSpan = document.createElement('span');
        closeSpan.textContent = 'close';
        closeDiv.appendChild(closeSpan);
        content.appendChild(closeDiv);

        overlay.appendChild(content);
        document.body.appendChild(overlay);

        // Force reflow, then activate fade-in
        void overlay.offsetWidth;
        overlay.classList.add('wok-active');

        // Animate lines one by one
        var delay = 800; // initial pause after overlay appears
        var gap = 1500;

        for (var k = 0; k < lineEls.length; k++) {
            (function(el, idx) {
                setTimeout(function() {
                    el.classList.add('wok-visible');
                }, delay + idx * gap);
            })(lineEls[k], k);
        }

        // After all lines + 3 second pause, show close
        var totalLineTime = delay + lineEls.length * gap;
        var closeDelay = totalLineTime + 3000;

        setTimeout(function() {
            closeDiv.classList.add('wok-visible');
        }, closeDelay);

        // Close handler
        function closeModal() {
            overlay.classList.remove('wok-active');
            var state = loadState();
            if (state) {
                state.message_read = true;
                state.acrostic_seen = true;
                saveState(state);
            }
            setTimeout(function() {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 600);
        }

        closeSpan.addEventListener('click', closeModal);

        // Escape key
        function onKey(e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
                closeModal();
                document.removeEventListener('keydown', onKey);
            }
        }
        document.addEventListener('keydown', onKey);
    }

    // ── Pixel injection ──

    function createPixel() {
        var pixel = document.createElement('div');
        pixel.style.cssText = [
            'position:absolute',
            'bottom:8px',
            'right:8px',
            'width:2px',
            'height:2px',
            'background:#1a1a1a',
            'cursor:default',
            'z-index:1',
            'border:none',
            'outline:none',
            'padding:0',
            'margin:0',
            'opacity:1',
            'pointer-events:auto',
            'transition:background 0.3s ease'
        ].join(';');

        pixel.setAttribute('data-moreau', 'he-kept-one-too');
        pixel.title = '';

        // Hover: after 2 seconds, reveal hint
        var hoverTimer = null;

        pixel.addEventListener('mouseenter', function() {
            hoverTimer = setTimeout(function() {
                pixel.title = "You've been here 30 days.";
                pixel.style.background = '#3a3a3a';
            }, 2000);
        });

        pixel.addEventListener('mouseleave', function() {
            if (hoverTimer) {
                clearTimeout(hoverTimer);
                hoverTimer = null;
            }
        });

        // Click: mark found, show acrostic
        pixel.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();

            var state = loadState();
            if (state) {
                state.pixel_found = true;
                saveState(state);
            }

            showAcrosticModal();

            // Fire achievement if available
            if (typeof window.checkAchievement === 'function') {
                window.checkAchievement('inspector');
            }
        });

        return pixel;
    }

    // ── Public API ──

    var api = {
        init: function() {
            var state = ensureState();
            if (!state) return;

            // Validate start_date hasn't been tampered forward
            if (state.start_date > Date.now()) {
                // Clock went backward or was manipulated. Keep original.
                return;
            }
        },

        getStartDate: function() {
            var state = loadState();
            return state ? state.start_date : null;
        },

        getDaysKept: function() {
            var state = loadState();
            if (!state || !state.start_date) return 0;
            var elapsed = Date.now() - state.start_date;
            if (elapsed < 0) return 0;
            return Math.floor(elapsed / MS_PER_DAY);
        },

        isPixelReady: function() {
            return this.getDaysKept() >= DAYS_REQUIRED;
        },

        isPixelFound: function() {
            var state = loadState();
            return state ? !!state.pixel_found : false;
        },

        markPixelFound: function() {
            var state = loadState();
            if (state) {
                state.pixel_found = true;
                saveState(state);
            }
        },

        getAcrosticMessage: function() {
            return ACROSTIC_LINES.slice();
        },

        isMessageRead: function() {
            var state = loadState();
            return state ? !!state.message_read : false;
        },

        markMessageRead: function() {
            var state = loadState();
            if (state) {
                state.message_read = true;
                saveState(state);
            }
        },

        injectPixel: function(container) {
            if (!container) return;
            if (!this.isPixelReady()) return;
            if (this.isPixelFound()) return;

            // Ensure container is positioned for absolute child
            var pos = window.getComputedStyle(container).position;
            if (pos === 'static' || pos === '') {
                container.style.position = 'relative';
            }

            var pixel = createPixel();
            container.appendChild(pixel);
            attachObserver(pixel);
        },

        showAcrosticModal: showAcrosticModal,

        renderAcrosticPage: function(containerId) {
            var el = document.getElementById(containerId);
            if (!el) return;

            injectCSS();

            var wrap = document.createElement('div');
            wrap.className = 'wok-content';
            wrap.style.margin = '60px auto';

            for (var i = 0; i < ACROSTIC_LINES.length; i++) {
                var text = ACROSTIC_LINES[i];
                var p = document.createElement('p');
                p.className = 'wok-line wok-visible';

                if (text === '') {
                    p.className += ' wok-spacer';
                } else if (text === '\u2026') {
                    p.textContent = text;
                } else {
                    var span = document.createElement('span');
                    span.className = 'wok-first-letter';
                    span.textContent = text.charAt(0);
                    p.appendChild(span);
                    p.appendChild(document.createTextNode(text.slice(1)));
                }

                wrap.appendChild(p);
            }

            el.appendChild(wrap);

            this.markMessageRead();
        },

        // Teardown — primarily for testing
        destroy: function() {
            detachObserver();
        }
    };

    // ── Auto-initialization ──

    document.addEventListener('DOMContentLoaded', function() {
        // Look for a profile card container — try multiple selectors
        var selectors = [
            '.pet-profile-card',
            '.profile-card',
            '#petProfileCard',
            '#profileContent',
            '[data-pet-profile]'
        ];

        var profileCard = null;
        for (var i = 0; i < selectors.length; i++) {
            profileCard = document.querySelector(selectors[i]);
            if (profileCard) break;
        }

        if (!profileCard) return;

        api.init();
        api.injectPixel(profileCard);
    });

    return api;

})();
