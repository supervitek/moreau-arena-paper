(function(window) {
    'use strict';

    var DECISION_WINDOW_MS = 10 * 60 * 1000;
    var BOUNCE_THRESHOLD_MS = 30 * 1000;
    var REFRESH_COOLDOWN_MS = 20 * 1000;
    var STORAGE_KEY = 'moreau_chronicler_state';
    var SESSION_KEY = 'moreau_chronicler_session_id';

    var config = {
        areaId: 'chroniclerArea',
        route: '/island/home',
        getState: function() { return {}; }
    };

    var state = {
        sessionId: null,
        pageLoadedAt: Date.now(),
        lastReading: null,
        cooldownUntil: 0,
        inFlight: false
    };

    function escHtml(value) {
        var div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    function getSessionId() {
        var existing = sessionStorage.getItem(SESSION_KEY);
        if (existing) return existing;
        var created = 'chron-' + Math.random().toString(36).slice(2, 10) + '-' + Date.now().toString(36);
        sessionStorage.setItem(SESSION_KEY, created);
        return created;
    }

    function persistState() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                lastReading: state.lastReading,
                pageLoadedAt: state.pageLoadedAt
            }));
        } catch (e) {}
    }

    function loadPersistedState() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return;
            var parsed = JSON.parse(raw);
            if (parsed && typeof parsed === 'object') {
                state.lastReading = parsed.lastReading || null;
            }
        } catch (e) {}
    }

    function postEvent(payload, useBeacon) {
        payload = payload || {};
        payload.route = config.route;
        payload.session_id = state.sessionId;
        var body = JSON.stringify(payload);

        if (useBeacon && navigator.sendBeacon) {
            try {
                navigator.sendBeacon(
                    '/api/v1/island/chronicler/event',
                    new Blob([body], { type: 'application/json' })
                );
                return Promise.resolve();
            } catch (e) {}
        }

        return fetch('/api/v1/island/chronicler/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body,
            keepalive: !!useBeacon
        }).catch(function() {});
    }

    function latestDreamText() {
        try {
            var data = window.MoreauStorage ? window.MoreauStorage.loadDreamState() : { dreams: [] };
            var dreams = Array.isArray(data.dreams) ? data.dreams : [];
            if (!dreams.length) return null;
            var latest = dreams[dreams.length - 1];
            return latest && latest.text ? String(latest.text).slice(0, 180) : null;
        } catch (e) {
            return null;
        }
    }

    function latestConfessionText() {
        try {
            if (typeof window.ConfessionEngine === 'undefined' || typeof window.ConfessionEngine.getJournal !== 'function') {
                return null;
            }
            var journal = window.ConfessionEngine.getJournal();
            if (!Array.isArray(journal) || journal.length === 0) return null;
            var latest = journal[journal.length - 1];
            if (typeof latest === 'string') return latest.slice(0, 180);
            if (latest && latest.text) return String(latest.text).slice(0, 180);
            if (latest && latest.prompt) return String(latest.prompt).slice(0, 180);
            return null;
        } catch (e) {
            return null;
        }
    }

    function deriveAvailableActions(snapshot) {
        var pet = snapshot.activePet;
        var hasPet = !!pet && !pet.deceased && pet.is_alive !== false;
        var actions = ['none'];

        if (!hasPet) return actions;

        actions.push('train', 'caretaker', 'lab', 'dreams', 'prophecy', 'profile', 'tides', 'deep_tide', 'menagerie');
        if (snapshot.rivalAvailable) actions.push('rivals');
        if (snapshot.hasFeral || snapshot.hasPact) actions.push('pact');

        return actions;
    }

    function buildContext(snapshot) {
        var pet = snapshot.activePet || {};
        var fights = Array.isArray(pet.fights) ? pet.fights.slice(-3) : [];

        return {
            session_id: state.sessionId,
            offline_mode: !!snapshot.offlineMode,
            active_pet: {
                name: pet.name || 'the creature',
                animal: pet.animal || 'creature',
                level: pet.level || 1,
                mood: pet.mood || 'unknown',
                corruption: pet.corruption || 0,
                instability: pet.instability || 0,
                mutations: Array.isArray(pet.mutations) ? pet.mutations.slice(0, 3) : [],
                deceased: !!pet.deceased,
                is_alive: pet.is_alive
            },
            recent_fights: fights.map(function(fight) {
                return {
                    opponent: fight.opponent || 'unknown foe',
                    result: fight.result || 'unknown',
                    ticks: fight.ticks || 0
                };
            }),
            recent_dream: latestDreamText(),
            recent_confession: latestConfessionText(),
            dream_unread: window.MoreauStorage ? window.MoreauStorage.countUnreadDreams(window.MoreauStorage.loadDreamState()) : 0,
            confession_count: (function() {
                if (!window.MoreauStorage) return 0;
                return window.MoreauStorage.loadConfessions().length;
            })(),
            can_mutate: !!snapshot.canMutate,
            rival_available: !!snapshot.rivalAvailable,
            has_feral: !!snapshot.hasFeral,
            has_pact: !!snapshot.hasPact,
            available_actions: deriveAvailableActions(snapshot)
        };
    }

    function renderIdle(area, pet) {
        var petName = pet && pet.name ? pet.name : 'the kennel';
        area.innerHTML =
            '<section class="chronicler-card">' +
                '<div class="chronicler-header">' +
                    '<div>' +
                        '<div class="chronicler-kicker">The Chronicler</div>' +
                        '<h2 class="chronicler-title">A reader of residue, not a giver of orders</h2>' +
                    '</div>' +
                    '<div class="chronicler-seal" aria-hidden="true">&#10022;</div>' +
                '</div>' +
                '<div class="chronicler-copy">' +
                    '<p>The room has not spoken yet. If you ask, it will try to read what gathers around ' + escHtml(petName) + '.</p>' +
                '</div>' +
                '<div class="chronicler-actions">' +
                    '<button class="chronicler-btn chronicler-btn-primary" id="chroniclerConsultBtn">Ask what the room sees</button>' +
                '</div>' +
            '</section>';
        bindButtons(area);
    }

    function renderEmpty(area) {
        area.innerHTML =
            '<section class="chronicler-card chronicler-card-muted">' +
                '<div class="chronicler-header">' +
                    '<div>' +
                        '<div class="chronicler-kicker">The Chronicler</div>' +
                        '<h2 class="chronicler-title">Nothing living answers the room</h2>' +
                    '</div>' +
                    '<div class="chronicler-seal" aria-hidden="true">&#10022;</div>' +
                '</div>' +
                '<div class="chronicler-copy"><p>No reading is offered while the cages are empty or silent.</p></div>' +
            '</section>';
    }

    function renderLoading(area) {
        area.innerHTML =
            '<section class="chronicler-card">' +
                '<div class="chronicler-header">' +
                    '<div><div class="chronicler-kicker">The Chronicler</div><h2 class="chronicler-title">Listening to the room</h2></div>' +
                    '<div class="chronicler-spinner" aria-hidden="true"></div>' +
                '</div>' +
                '<div class="chronicler-copy"><p>The reading takes a moment when the air is crowded.</p></div>' +
            '</section>';
    }

    function renderReading(area, reading) {
        var promptLabel = reading.prompt && /\?\s*$/.test(reading.prompt) ? 'Question' : 'Warning';
        var now = Date.now();
        var coolingDown = now < state.cooldownUntil;
        var cooldownLabel = coolingDown ? 'Ask again in ' + Math.ceil((state.cooldownUntil - now) / 1000) + 's' : 'Ask again';
        var suggestionHtml = '';
        if (reading.suggestion) {
            suggestionHtml =
                '<div class="chronicler-line chronicler-suggestion">' +
                    '<span class="chronicler-label">Suggestion</span>' +
                    '<p>' + escHtml(reading.suggestion) + '</p>' +
                '</div>';
        }

        area.innerHTML =
            '<section class="chronicler-card">' +
                '<div class="chronicler-header">' +
                    '<div>' +
                        '<div class="chronicler-kicker">The Chronicler</div>' +
                        '<h2 class="chronicler-title">A reading, nothing more</h2>' +
                    '</div>' +
                    '<div class="chronicler-seal" aria-hidden="true">&#10022;</div>' +
                '</div>' +
                '<div class="chronicler-copy">' +
                    '<div class="chronicler-line">' +
                        '<span class="chronicler-label">Observation</span>' +
                        '<p>' + escHtml(reading.observation || '') + '</p>' +
                    '</div>' +
                    '<div class="chronicler-line">' +
                        '<span class="chronicler-label">' + escHtml(promptLabel) + '</span>' +
                        '<p>' + escHtml(reading.prompt || '') + '</p>' +
                    '</div>' +
                    suggestionHtml +
                    '<div class="chronicler-line chronicler-uncertainty"><p>' + escHtml(reading.uncertainty || '') + '</p></div>' +
                '</div>' +
                '<div class="chronicler-meta">' +
                    '<span>' + escHtml(reading.mode || 'fallback') + '</span>' +
                    '<span>' + escHtml(reading.suggested_action || 'none') + '</span>' +
                '</div>' +
                '<div class="chronicler-actions">' +
                    '<button class="chronicler-btn chronicler-btn-secondary" id="chroniclerDismissBtn">Let it be</button>' +
                    '<button class="chronicler-btn chronicler-btn-primary" id="chroniclerRefreshBtn" ' + (coolingDown ? 'disabled' : '') + '>' + cooldownLabel + '</button>' +
                '</div>' +
            '</section>';
        bindButtons(area);
    }

    function bindButtons(area) {
        var consult = area.querySelector('#chroniclerConsultBtn');
        if (consult) {
            consult.addEventListener('click', function() { consultRoom(false); });
        }

        var refresh = area.querySelector('#chroniclerRefreshBtn');
        if (refresh) {
            refresh.addEventListener('click', function() { consultRoom(true); });
        }

        var dismiss = area.querySelector('#chroniclerDismissBtn');
        if (dismiss) {
            dismiss.addEventListener('click', function() {
                if (state.lastReading) {
                    postEvent({
                        event_type: 'dismiss',
                        trace_id: state.lastReading.trace_id,
                        suggested_action: state.lastReading.suggested_action || 'none'
                    });
                }
                state.lastReading = null;
                persistState();
                render();
            });
        }
    }

    function render() {
        var area = document.getElementById(config.areaId);
        if (!area) return;

        var snapshot = config.getState() || {};
        var pet = snapshot.activePet || null;
        var petKey = snapshot.petKey || null;
        if (!pet || pet.deceased || pet.is_alive === false) {
            renderEmpty(area);
            return;
        }

        if (state.inFlight) {
            renderLoading(area);
            return;
        }

        if (state.lastReading && state.lastReading.petKey === petKey) {
            renderReading(area, state.lastReading);
            return;
        }

        renderIdle(area, pet);
    }

    function consultRoom(isRefresh) {
        if (state.inFlight) return;
        if (isRefresh && Date.now() < state.cooldownUntil) {
            render();
            return;
        }
        var snapshot = config.getState() || {};
        if (!snapshot.activePet || snapshot.activePet.deceased || snapshot.activePet.is_alive === false) return;

        state.inFlight = true;
        render();

        postEvent({
            event_type: isRefresh ? 'refresh' : 'open',
            trace_id: state.lastReading ? state.lastReading.trace_id : null,
            suggested_action: state.lastReading ? state.lastReading.suggested_action : 'none'
        });

        fetch('/api/v1/island/chronicler', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildContext(snapshot))
        }).then(function(response) {
            if (!response.ok) throw new Error('chronicler failed');
            return response.json();
        }).then(function(reading) {
            state.cooldownUntil = Date.now() + REFRESH_COOLDOWN_MS;
            state.lastReading = {
                trace_id: reading.trace_id,
                petName: snapshot.activePet.name || 'the creature',
                petKey: snapshot.petKey || (snapshot.activePet.name || 'the creature'),
                suggested_action: reading.suggested_action || 'none',
                shownAt: Date.now(),
                observation: reading.observation || '',
                prompt: reading.prompt || '',
                suggestion: reading.suggestion || null,
                uncertainty: reading.uncertainty || '',
                mode: reading.mode || 'fallback'
            };
            persistState();
            postEvent({
                event_type: 'response',
                trace_id: state.lastReading.trace_id,
                suggested_action: state.lastReading.suggested_action,
                details: 'mode=' + state.lastReading.mode
            });
        }).catch(function() {
            state.cooldownUntil = Date.now() + REFRESH_COOLDOWN_MS;
            state.lastReading = {
                trace_id: 'client-fallback',
                petName: snapshot.activePet.name || 'the creature',
                petKey: snapshot.petKey || (snapshot.activePet.name || 'the creature'),
                suggested_action: 'none',
                shownAt: Date.now(),
                observation: 'The room would not hold still long enough to be read cleanly.',
                prompt: 'Whatever answer was here has gone thin.',
                suggestion: null,
                uncertainty: 'Silence is also a reading.',
                mode: 'client-fallback'
            };
            persistState();
            postEvent({
                event_type: 'response',
                trace_id: state.lastReading.trace_id,
                suggested_action: state.lastReading.suggested_action,
                details: 'mode=' + state.lastReading.mode
            });
        }).finally(function() {
            state.inFlight = false;
            render();
        });
    }

    function trackAction(actionId) {
        if (!state.lastReading || !state.lastReading.shownAt) return;
        if ((Date.now() - state.lastReading.shownAt) > DECISION_WINDOW_MS) return;

        var relation = 'neutral';
        if (state.lastReading.suggested_action && state.lastReading.suggested_action !== 'none') {
            relation = actionId === state.lastReading.suggested_action ? 'follow' : 'override';
        }

        postEvent({
            event_type: 'action_click',
            trace_id: state.lastReading.trace_id,
            action_id: actionId,
            suggested_action: state.lastReading.suggested_action || 'none',
            relation: relation
        });
    }

    function wireActionTracking() {
        var grid = document.getElementById('actionsGrid');
        if (!grid || grid.dataset.chroniclerBound === '1') return;
        grid.dataset.chroniclerBound = '1';
        grid.addEventListener('click', function(event) {
            var anchor = event.target.closest('a[data-action-id]');
            if (!anchor || anchor.classList.contains('disabled')) return;
            trackAction(anchor.getAttribute('data-action-id'));
        });
    }

    function handlePageExit() {
        var dwellMs = Date.now() - state.pageLoadedAt;
        postEvent({
            event_type: 'page_exit',
            trace_id: state.lastReading ? state.lastReading.trace_id : null,
            suggested_action: state.lastReading ? state.lastReading.suggested_action : 'none',
            dwell_ms: dwellMs,
            details: dwellMs < BOUNCE_THRESHOLD_MS ? 'short-exit' : 'engaged-exit'
        }, true);
    }

    function init(options) {
        config = {
            areaId: options.areaId || config.areaId,
            route: options.route || config.route,
            getState: options.getState || config.getState
        };
        state.sessionId = getSessionId();
        loadPersistedState();
        wireActionTracking();
        window.addEventListener('beforeunload', handlePageExit, { once: true });
        render();
    }

    window.MoreauChronicler = {
        init: init,
        render: render,
        consult: function() { consultRoom(false); },
        trackAction: trackAction,
        getLastReading: function() { return state.lastReading; }
    };
})(window);
