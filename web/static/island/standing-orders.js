// ══════════════════════════════════════════════════════════════════
//  Standing Orders — Programmable Rules for The Caretaker
//  Lets players define conditional rules that auto-execute actions
//  Priority-ordered, conflict-aware, drag-and-drop reorderable
// ══════════════════════════════════════════════════════════════════

var StandingOrders = (function() {
    'use strict';

    var _storage = window.MoreauStorage || {
        readJSON: function(key, fallback) {
            try {
                var raw = localStorage.getItem(key);
                return raw === null ? fallback : JSON.parse(raw);
            } catch (e) {
                return fallback;
            }
        }
    };

    // ── Constants ────────────────────────────────────────────────

    var STORAGE_KEY = 'moreau_standing_orders';
    var MAX_ORDERS  = 5;
    var MAX_ACTIONS_PER_EXECUTION = 3;
    var CSS_INJECTED = false;
    var CSS_ID = 'standing-orders-css';

    // ── Stat accessors ──────────────────────────────────────────
    // Some stats live in pet.needs, others are top-level fields

    var STAT_ACCESSORS = {
        hunger:      function(pet) { return (pet.needs && pet.needs.hunger != null)  ? pet.needs.hunger  : 100; },
        health:      function(pet) { return (pet.needs && pet.needs.health != null)  ? pet.needs.health  : 100; },
        morale:      function(pet) { return (pet.needs && pet.needs.morale != null)  ? pet.needs.morale  : 100; },
        energy:      function(pet) { return (pet.needs && pet.needs.energy != null)  ? pet.needs.energy  : 100; },
        level:       function(pet) { return pet.level || 1; },
        instability: function(pet) { return pet.instability || 0; },
        corruption:  function(pet) { return pet.corruption  || 0; }
    };

    var STAT_LABELS = {
        hunger:      'Hunger',
        health:      'Health',
        morale:      'Morale',
        energy:      'Energy',
        level:       'Level',
        instability: 'Instability',
        corruption:  'Corruption'
    };

    var OPERATOR_LABELS = {
        '<':  '<',
        '>':  '>',
        '<=': '\u2264',
        '>=': '\u2265',
        '==': '='
    };

    var ACTION_LABELS = {
        feed:     'Feed',
        heal:     'Heal',
        rest:     'Rest',
        train:    'Train',
        motivate: 'Motivate'
    };

    // Actions that conflict with each other (cannot run simultaneously)
    var INCOMPATIBLE_ACTIONS = [
        ['rest', 'train']
    ];

    // ── Persistence ─────────────────────────────────────────────

    function loadOrders() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function saveOrders(orders) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(orders));
    }

    // ── Condition evaluation ────────────────────────────────────

    function evaluateCondition(condition, pet) {
        var accessor = STAT_ACCESSORS[condition.stat];
        if (!accessor) return false;

        var actual = accessor(pet);
        var target = condition.value;

        switch (condition.operator) {
            case '<':  return actual <  target;
            case '>':  return actual >  target;
            case '<=': return actual <= target;
            case '>=': return actual >= target;
            case '==': return actual == target;
            default:   return false;
        }
    }

    function conditionToString(cond) {
        var label = STAT_LABELS[cond.stat] || cond.stat;
        var op    = OPERATOR_LABELS[cond.operator] || cond.operator;
        return label + ' ' + op + ' ' + cond.value;
    }

    function orderToString(order) {
        return 'IF ' + conditionToString(order.condition) + ' THEN ' + (ACTION_LABELS[order.action] || order.action);
    }

    // ── Conflict detection ──────────────────────────────────────

    function areActionsIncompatible(a, b) {
        for (var i = 0; i < INCOMPATIBLE_ACTIONS.length; i++) {
            var pair = INCOMPATIBLE_ACTIONS[i];
            if ((pair[0] === a && pair[1] === b) || (pair[0] === b && pair[1] === a)) {
                return true;
            }
        }
        return false;
    }

    function conditionsOverlap(c1, c2) {
        // Same stat, check if ranges overlap
        if (c1.stat !== c2.stat) return false;

        // Build effective ranges for each condition
        // For > or >=, range is [value, 100]; for < or <=, range is [0, value]
        var r1 = conditionRange(c1);
        var r2 = conditionRange(c2);

        // Ranges overlap if one starts before the other ends
        return r1.lo <= r2.hi && r2.lo <= r1.hi;
    }

    function conditionRange(c) {
        switch (c.operator) {
            case '<':  return { lo: 0,           hi: c.value - 1 };
            case '<=': return { lo: 0,           hi: c.value     };
            case '>':  return { lo: c.value + 1, hi: 100         };
            case '>=': return { lo: c.value,     hi: 100         };
            case '==': return { lo: c.value,     hi: c.value     };
            default:   return { lo: 0,           hi: 100         };
        }
    }

    // ── CSS injection ───────────────────────────────────────────

    function injectCSS() {
        if (CSS_INJECTED) return;
        if (document.getElementById(CSS_ID)) { CSS_INJECTED = true; return; }

        var style = document.createElement('style');
        style.id = CSS_ID;
        style.textContent = [
            '.so-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 600px; margin: 0 auto; }',

            /* ── Form ── */
            '.so-form { background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 16px; }',
            '.so-form-title { color: #e0e0e0; font-size: 14px; font-weight: 600; margin: 0 0 12px 0; display: flex; justify-content: space-between; align-items: center; }',
            '.so-form-count { color: #888; font-size: 12px; font-weight: 400; }',
            '.so-form-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }',
            '.so-form-label { color: #aaa; font-size: 12px; min-width: 30px; }',
            '.so-select, .so-input { background: #0f0f23; color: #e0e0e0; border: 1px solid #444; border-radius: 4px; padding: 6px 8px; font-size: 13px; }',
            '.so-select { cursor: pointer; }',
            '.so-select:focus, .so-input:focus { outline: none; border-color: #6c63ff; }',
            '.so-input { width: 60px; text-align: center; }',
            '.so-btn-add { background: #6c63ff; color: #fff; border: none; border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 4px; }',
            '.so-btn-add:hover { background: #5a52d5; }',
            '.so-btn-add:disabled { background: #333; color: #666; cursor: not-allowed; }',

            /* ── Orders list ── */
            '.so-list { display: flex; flex-direction: column; gap: 6px; min-height: 40px; }',
            '.so-empty { color: #666; font-size: 13px; text-align: center; padding: 20px; font-style: italic; }',

            /* ── Order card ── */
            '.so-card { background: #1a1a2e; border: 1px solid #333; border-left: 4px solid #555; border-radius: 6px; padding: 10px 12px; display: flex; align-items: center; gap: 10px; transition: border-color 0.3s, opacity 0.3s, transform 0.2s, box-shadow 0.2s; position: relative; }',
            '.so-card.so-active { border-left-color: #4caf50; }',
            '.so-card.so-disabled { opacity: 0.5; border-left-color: #555; }',
            '.so-card.so-dragging { opacity: 0.4; transform: scale(0.97); }',
            '.so-card.so-drag-over { box-shadow: 0 -2px 0 0 #6c63ff; }',

            /* ── Card elements ── */
            '.so-drag-handle { cursor: grab; color: #555; font-size: 16px; user-select: none; -webkit-user-select: none; flex-shrink: 0; }',
            '.so-drag-handle:active { cursor: grabbing; }',
            '.so-priority { background: #6c63ff; color: #fff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 6px; flex-shrink: 0; min-width: 22px; text-align: center; }',
            '.so-rule-text { font-family: "SF Mono", "Fira Code", "Cascadia Code", Consolas, monospace; font-size: 12px; color: #e0e0e0; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }',
            '.so-rule-text .so-kw { color: #ff79c6; }',
            '.so-rule-text .so-stat { color: #8be9fd; }',
            '.so-rule-text .so-op { color: #ffb86c; }',
            '.so-rule-text .so-val { color: #50fa7b; }',
            '.so-rule-text .so-act { color: #bd93f9; }',

            /* ── Toggle ── */
            '.so-toggle { position: relative; width: 36px; height: 20px; flex-shrink: 0; }',
            '.so-toggle input { opacity: 0; width: 0; height: 0; position: absolute; }',
            '.so-toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #333; border-radius: 10px; transition: background 0.3s; }',
            '.so-toggle-slider:before { content: ""; position: absolute; height: 16px; width: 16px; left: 2px; bottom: 2px; background: #888; border-radius: 50%; transition: transform 0.3s, background 0.3s; }',
            '.so-toggle input:checked + .so-toggle-slider { background: #2e7d32; }',
            '.so-toggle input:checked + .so-toggle-slider:before { transform: translateX(16px); background: #4caf50; }',

            /* ── Delete ── */
            '.so-btn-del { background: none; border: none; color: #666; font-size: 16px; cursor: pointer; padding: 2px 4px; flex-shrink: 0; transition: color 0.2s; }',
            '.so-btn-del:hover { color: #f44336; }',

            /* ── Conflict warning ── */
            '.so-conflicts { background: rgba(244, 67, 54, 0.1); border: 1px solid rgba(244, 67, 54, 0.3); border-radius: 6px; padding: 10px 14px; margin-top: 12px; }',
            '.so-conflict-title { color: #f44336; font-size: 13px; font-weight: 600; margin: 0 0 6px 0; }',
            '.so-conflict-item { color: #e57373; font-size: 12px; margin: 4px 0; padding-left: 8px; border-left: 2px solid #f44336; }',

            /* ── Section label ── */
            '.so-section { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 8px 0; }',
        ].join('\n');

        document.head.appendChild(style);
        CSS_INJECTED = true;
    }

    // ── Helpers ──────────────────────────────────────────────────

    function generateId() {
        return Date.now() + Math.floor(Math.random() * 1000);
    }

    function getActivePet() {
        try {
            var pets = _storage.readJSON('moreau_pets', []);
            var idx  = parseInt(localStorage.getItem('moreau_active_pet') || '0', 10);
            return { pet: pets[idx] || null, index: idx, pets: pets };
        } catch (e) {
            return { pet: null, index: 0, pets: [] };
        }
    }

    // ── Public API ──────────────────────────────────────────────

    /**
     * Get all standing orders, sorted by priority.
     * @returns {Array} orders
     */
    function getOrders() {
        var orders = loadOrders();
        orders.sort(function(a, b) { return a.priority - b.priority; });
        return orders;
    }

    /**
     * Add a new standing order.
     * @param {Object} order - { condition: { stat, operator, value }, action }
     * @returns {{ success: boolean, message: string }}
     */
    function addOrder(order) {
        var orders = loadOrders();

        if (orders.length >= MAX_ORDERS) {
            return { success: false, message: 'Maximum ' + MAX_ORDERS + ' orders allowed. Remove one first.' };
        }

        // Validate condition
        if (!order.condition || !order.condition.stat || !order.condition.operator || order.condition.value == null) {
            return { success: false, message: 'Invalid condition. Specify stat, operator, and value.' };
        }
        if (!STAT_ACCESSORS[order.condition.stat]) {
            return { success: false, message: 'Unknown stat: ' + order.condition.stat };
        }
        if (!ACTION_LABELS[order.action]) {
            return { success: false, message: 'Unknown action: ' + order.action };
        }

        var val = parseInt(order.condition.value, 10);
        if (isNaN(val) || val < 0 || val > 100) {
            return { success: false, message: 'Value must be 0-100.' };
        }

        var newOrder = {
            id:         generateId(),
            condition: {
                stat:     order.condition.stat,
                operator: order.condition.operator,
                value:    val
            },
            action:     order.action,
            priority:   orders.length + 1,
            enabled:    true,
            created_at: new Date().toISOString()
        };

        orders.push(newOrder);
        saveOrders(orders);

        return { success: true, message: 'Order added: ' + orderToString(newOrder) };
    }

    /**
     * Remove an order by ID.
     * @param {number} id
     * @returns {{ success: boolean, message: string }}
     */
    function removeOrder(id) {
        var orders = loadOrders();
        var idx = -1;
        for (var i = 0; i < orders.length; i++) {
            if (orders[i].id === id) { idx = i; break; }
        }
        if (idx === -1) {
            return { success: false, message: 'Order not found.' };
        }

        var removed = orders.splice(idx, 1)[0];

        // Re-assign priorities
        for (var j = 0; j < orders.length; j++) {
            orders[j].priority = j + 1;
        }

        saveOrders(orders);
        return { success: true, message: 'Removed: ' + orderToString(removed) };
    }

    /**
     * Reorder: move order at fromIdx to toIdx.
     * @param {number} fromIdx
     * @param {number} toIdx
     */
    function reorder(fromIdx, toIdx) {
        var orders = getOrders(); // sorted by priority
        if (fromIdx < 0 || fromIdx >= orders.length) return;
        if (toIdx < 0   || toIdx >= orders.length)   return;
        if (fromIdx === toIdx) return;

        var moved = orders.splice(fromIdx, 1)[0];
        orders.splice(toIdx, 0, moved);

        // Reassign priorities
        for (var i = 0; i < orders.length; i++) {
            orders[i].priority = i + 1;
        }

        saveOrders(orders);
    }

    /**
     * Check for conflicts among enabled orders.
     * @returns {Array<string>} conflict descriptions
     */
    function checkConflicts() {
        var orders = getOrders().filter(function(o) { return o.enabled; });
        var conflicts = [];

        for (var i = 0; i < orders.length; i++) {
            for (var j = i + 1; j < orders.length; j++) {
                var a = orders[i];
                var b = orders[j];

                // Check if both conditions can be true simultaneously AND actions conflict
                if (conditionsOverlap(a.condition, b.condition) && areActionsIncompatible(a.action, b.action)) {
                    conflicts.push(
                        'Order #' + a.priority + ' (' + orderToString(a) + ') conflicts with ' +
                        'Order #' + b.priority + ' (' + orderToString(b) + '). ' +
                        ACTION_LABELS[a.action] + ' and ' + ACTION_LABELS[b.action] + ' cannot run together.'
                    );
                }

                // Check contradicting conditions on same stat with different actions
                if (a.condition.stat === b.condition.stat && a.action !== b.action) {
                    if (conditionsOverlap(a.condition, b.condition)) {
                        // Only flag if NOT already caught by incompatible actions
                        if (!areActionsIncompatible(a.action, b.action)) {
                            conflicts.push(
                                'Order #' + a.priority + ' and #' + b.priority +
                                ' both watch ' + STAT_LABELS[a.condition.stat] +
                                ' with overlapping ranges but trigger different actions (' +
                                ACTION_LABELS[a.action] + ' vs ' + ACTION_LABELS[b.action] +
                                '). Priority will decide which runs first.'
                            );
                        }
                    }
                }
            }
        }

        return conflicts;
    }

    /**
     * Execute all enabled orders against a pet.
     * Evaluates top-to-bottom by priority. Max 3 actions.
     * @param {number} petIndex
     * @returns {{ executed: Array, skipped: Array, conflicts: Array }}
     */
    function executeOrders(petIndex) {
        var result = { executed: [], skipped: [], conflicts: [] };

        if (typeof CaretakerEngine === 'undefined') {
            result.skipped.push({ reason: 'CaretakerEngine not loaded.' });
            return result;
        }

        var data = getActivePet();
        var pets = data.pets;
        var pet  = pets[petIndex];

        if (!pet) {
            result.skipped.push({ reason: 'Pet not found at index ' + petIndex + '.' });
            return result;
        }

        // Init needs if CaretakerEngine supports it
        if (CaretakerEngine.initNeeds) {
            pet = CaretakerEngine.initNeeds(pet);
        }
        if (CaretakerEngine.decay) {
            pet = CaretakerEngine.decay(pet);
        }

        var orders   = getOrders().filter(function(o) { return o.enabled; });
        var conflicts = checkConflicts();
        result.conflicts = conflicts;

        // If conflicts exist, add diary entry
        if (conflicts.length > 0 && CaretakerEngine.addDiaryEntry) {
            CaretakerEngine.addDiaryEntry(
                'warning',
                'Your standing orders conflict! I\'m confused. Please review them.',
                petIndex
            );
        }

        var actionsUsed = {};
        var actionCount = 0;

        for (var i = 0; i < orders.length; i++) {
            if (actionCount >= MAX_ACTIONS_PER_EXECUTION) break;

            var order = orders[i];

            // Re-read pet state (previous action may have changed it)
            try {
                pets = _storage.readJSON('moreau_pets', []);
                pet  = pets[petIndex];
                if (!pet) break;
                if (CaretakerEngine.initNeeds) pet = CaretakerEngine.initNeeds(pet);
                if (CaretakerEngine.decay)     pet = CaretakerEngine.decay(pet);
            } catch (e) {
                break;
            }

            if (!evaluateCondition(order.condition, pet)) {
                result.skipped.push({ order: order, reason: 'Condition not met.' });
                continue;
            }

            // Check if incompatible action already ran
            var blocked = false;
            for (var usedAction in actionsUsed) {
                if (actionsUsed.hasOwnProperty(usedAction) && areActionsIncompatible(usedAction, order.action)) {
                    result.skipped.push({ order: order, reason: 'Blocked by incompatible action: ' + ACTION_LABELS[usedAction] + '.' });
                    blocked = true;
                    break;
                }
            }
            if (blocked) continue;

            // Execute the action
            var fn = CaretakerEngine[order.action];
            if (typeof fn !== 'function') {
                result.skipped.push({ order: order, reason: 'Action not available: ' + order.action + '.' });
                continue;
            }

            var actionResult = fn.call(CaretakerEngine, petIndex);
            result.executed.push({ order: order, result: actionResult });
            actionsUsed[order.action] = true;
            actionCount++;
        }

        return result;
    }

    // ── Render ───────────────────────────────────────────────────

    var _renderContainer = null;
    var _dragFromIdx     = null;

    function render(containerId) {
        injectCSS();

        var container = document.getElementById(containerId);
        if (!container) return;
        _renderContainer = containerId;

        var orders    = getOrders();
        var petData   = getActivePet();
        var pet       = petData.pet;
        var conflicts = checkConflicts();

        var html = '<div class="so-container">';

        // ── Create New Order form ────────────────────────────────
        html += '<div class="so-form">';
        html += '<div class="so-form-title">';
        html += 'Create New Order';
        html += '<span class="so-form-count">' + orders.length + '/' + MAX_ORDERS + ' orders</span>';
        html += '</div>';

        // Row 1: IF stat op value
        html += '<div class="so-form-row">';
        html += '<span class="so-form-label">IF</span>';

        // Stat dropdown
        html += '<select id="so-stat" class="so-select">';
        var statKeys = ['hunger', 'health', 'morale', 'energy', 'instability', 'corruption'];
        for (var s = 0; s < statKeys.length; s++) {
            html += '<option value="' + statKeys[s] + '">' + STAT_LABELS[statKeys[s]] + '</option>';
        }
        html += '</select>';

        // Operator dropdown
        html += '<select id="so-op" class="so-select">';
        var ops = ['<', '>', '<=', '>=', '=='];
        for (var o = 0; o < ops.length; o++) {
            html += '<option value="' + ops[o] + '">' + OPERATOR_LABELS[ops[o]] + '</option>';
        }
        html += '</select>';

        // Value input
        html += '<input type="number" id="so-val" class="so-input" min="0" max="100" value="30">';
        html += '</div>';

        // Row 2: THEN action
        html += '<div class="so-form-row">';
        html += '<span class="so-form-label">THEN</span>';

        html += '<select id="so-action" class="so-select">';
        var actionKeys = ['feed', 'heal', 'rest', 'train', 'motivate'];
        for (var a = 0; a < actionKeys.length; a++) {
            html += '<option value="' + actionKeys[a] + '">' + ACTION_LABELS[actionKeys[a]] + '</option>';
        }
        html += '</select>';

        var addDisabled = orders.length >= MAX_ORDERS ? ' disabled' : '';
        html += '<button id="so-btn-add" class="so-btn-add"' + addDisabled + '>Add Order</button>';
        html += '</div>';

        html += '</div>'; // .so-form

        // ── Orders list ──────────────────────────────────────────
        html += '<div class="so-section">Active Orders</div>';
        html += '<div class="so-list" id="so-list">';

        if (orders.length === 0) {
            html += '<div class="so-empty">No standing orders. The Caretaker awaits your instructions.</div>';
        } else {
            for (var i = 0; i < orders.length; i++) {
                var ord  = orders[i];
                var matching = pet && evaluateCondition(ord.condition, pet);
                var cardClass = 'so-card';
                if (!ord.enabled) {
                    cardClass += ' so-disabled';
                } else if (matching) {
                    cardClass += ' so-active';
                }

                html += '<div class="' + cardClass + '" data-idx="' + i + '" data-id="' + ord.id + '" draggable="true">';

                // Drag handle
                html += '<span class="so-drag-handle" title="Drag to reorder">\u2630</span>';

                // Priority badge
                html += '<span class="so-priority">#' + ord.priority + '</span>';

                // Rule text with syntax highlighting
                html += '<span class="so-rule-text">';
                html += '<span class="so-kw">IF</span> ';
                html += '<span class="so-stat">' + STAT_LABELS[ord.condition.stat] + '</span> ';
                html += '<span class="so-op">' + OPERATOR_LABELS[ord.condition.operator] + '</span> ';
                html += '<span class="so-val">' + ord.condition.value + '</span> ';
                html += '<span class="so-kw">THEN</span> ';
                html += '<span class="so-act">' + ACTION_LABELS[ord.action] + '</span>';
                html += '</span>';

                // Enable/disable toggle
                html += '<label class="so-toggle">';
                html += '<input type="checkbox"' + (ord.enabled ? ' checked' : '') + ' data-toggle-id="' + ord.id + '">';
                html += '<span class="so-toggle-slider"></span>';
                html += '</label>';

                // Delete button
                html += '<button class="so-btn-del" data-del-id="' + ord.id + '" title="Delete order">\ud83d\uddd1\ufe0f</button>';

                html += '</div>'; // .so-card
            }
        }

        html += '</div>'; // .so-list

        // ── Conflict warnings ────────────────────────────────────
        if (conflicts.length > 0) {
            html += '<div class="so-conflicts">';
            html += '<div class="so-conflict-title">\u26a0\ufe0f Your orders conflict</div>';
            for (var c = 0; c < conflicts.length; c++) {
                html += '<div class="so-conflict-item">' + conflicts[c] + '</div>';
            }
            html += '</div>';
        }

        html += '</div>'; // .so-container

        container.innerHTML = html;

        // ── Bind events ──────────────────────────────────────────
        bindAddButton();
        bindToggleButtons();
        bindDeleteButtons();
        bindDragAndDrop();
    }

    // ── Event binding ───────────────────────────────────────────

    function bindAddButton() {
        var btn = document.getElementById('so-btn-add');
        if (!btn) return;

        btn.addEventListener('click', function() {
            var stat   = document.getElementById('so-stat').value;
            var op     = document.getElementById('so-op').value;
            var val    = document.getElementById('so-val').value;
            var action = document.getElementById('so-action').value;

            var result = addOrder({
                condition: { stat: stat, operator: op, value: parseInt(val, 10) },
                action: action
            });

            if (result.success) {
                render(_renderContainer);
            } else {
                // Flash the button red briefly
                btn.style.background = '#f44336';
                btn.textContent = result.message;
                setTimeout(function() {
                    btn.style.background = '';
                    btn.textContent = 'Add Order';
                }, 2000);
            }
        });
    }

    function bindToggleButtons() {
        var toggles = document.querySelectorAll('[data-toggle-id]');
        for (var i = 0; i < toggles.length; i++) {
            toggles[i].addEventListener('change', (function(toggle) {
                return function() {
                    var id = parseInt(toggle.getAttribute('data-toggle-id'), 10);
                    var orders = loadOrders();
                    for (var j = 0; j < orders.length; j++) {
                        if (orders[j].id === id) {
                            orders[j].enabled = toggle.checked;
                            break;
                        }
                    }
                    saveOrders(orders);
                    // Re-render to update conflict detection and card styles
                    render(_renderContainer);
                };
            })(toggles[i]));
        }
    }

    function bindDeleteButtons() {
        var delBtns = document.querySelectorAll('[data-del-id]');
        for (var i = 0; i < delBtns.length; i++) {
            delBtns[i].addEventListener('click', (function(btn) {
                return function() {
                    var id = parseInt(btn.getAttribute('data-del-id'), 10);
                    removeOrder(id);
                    render(_renderContainer);
                };
            })(delBtns[i]));
        }
    }

    function bindDragAndDrop() {
        var cards = document.querySelectorAll('.so-card[draggable]');
        var list  = document.getElementById('so-list');
        if (!list || cards.length === 0) return;

        for (var i = 0; i < cards.length; i++) {
            (function(card) {
                card.addEventListener('dragstart', function(e) {
                    _dragFromIdx = parseInt(card.getAttribute('data-idx'), 10);
                    card.classList.add('so-dragging');
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', _dragFromIdx.toString());
                });

                card.addEventListener('dragend', function() {
                    card.classList.remove('so-dragging');
                    _dragFromIdx = null;
                    // Remove all drag-over highlights
                    var allCards = document.querySelectorAll('.so-card');
                    for (var j = 0; j < allCards.length; j++) {
                        allCards[j].classList.remove('so-drag-over');
                    }
                });

                card.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    // Highlight drop target
                    var allCards = document.querySelectorAll('.so-card');
                    for (var j = 0; j < allCards.length; j++) {
                        allCards[j].classList.remove('so-drag-over');
                    }
                    card.classList.add('so-drag-over');
                });

                card.addEventListener('dragleave', function() {
                    card.classList.remove('so-drag-over');
                });

                card.addEventListener('drop', function(e) {
                    e.preventDefault();
                    card.classList.remove('so-drag-over');
                    var toIdx = parseInt(card.getAttribute('data-idx'), 10);
                    if (_dragFromIdx !== null && _dragFromIdx !== toIdx) {
                        reorder(_dragFromIdx, toIdx);
                        render(_renderContainer);
                    }
                    _dragFromIdx = null;
                });
            })(cards[i]);
        }
    }

    // ── Public interface ────────────────────────────────────────

    return {
        getOrders:      getOrders,
        addOrder:       addOrder,
        removeOrder:    removeOrder,
        reorder:        reorder,
        checkConflicts: checkConflicts,
        executeOrders:  executeOrders,
        render:         render
    };

})();
