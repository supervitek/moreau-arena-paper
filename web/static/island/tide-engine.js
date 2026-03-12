/**
 * Tidal Clock Engine — Phase 8D
 * 6-hour real-time tide cycle for The Island.
 *
 * Phases (90 minutes each, from UTC epoch):
 *   0 -  90 min: LOW TIDE    — Bone Flats open, Lab +10 instability, fights x1.5 dmg
 *  90 - 180 min: RISING      — transitional, normal gameplay
 * 180 - 270 min: HIGH TIDE   — Lab LOCKED, Dreaming Pools open, Driftwood Market open
 * 270 - 360 min: FALLING     — transitional, normal gameplay
 */

(function(window) {
    'use strict';

    var CYCLE_MS = 6 * 60 * 60 * 1000;   // 6 hours
    var PHASE_MS = 90 * 60 * 1000;        // 90 minutes
    var STORM_JUMP_MS = 7 * 60 * 60 * 1000; // 7 hours

    var PHASES = [
        { id: 'low',     name: 'Low Tide',  icon: '\u{1F3DC}\uFE0F', color: '#c49a3c', desc: 'The waters recede. Bone Flats exposed.' },
        { id: 'rising',  name: 'Rising',    icon: '\u{1F30A}',       color: '#3a8fa7', desc: 'The tide creeps in. Normal conditions.' },
        { id: 'high',    name: 'High Tide', icon: '\u{1F30D}',       color: '#1a5276', desc: 'Waters engulf the shore. Dreaming Pools shimmer.' },
        { id: 'falling', name: 'Falling',   icon: '\u{1F4A7}',       color: '#2e6e5e', desc: 'The tide withdraws. Normal conditions.' }
    ];

    /**
     * Get the current tide state.
     * @returns {{ phase: string, phaseName: string, phaseIcon: string, phaseColor: string,
     *             phaseDesc: string, phaseIndex: number, minutesLeft: number, progress: number,
     *             cycleProgress: number, storm: boolean }}
     */
    function getTideState() {
        var now = Date.now();
        var storm = _checkStorm(now);

        var cyclePos = now % CYCLE_MS;
        var phaseIndex = Math.floor(cyclePos / PHASE_MS);
        if (phaseIndex > 3) phaseIndex = 3;
        var phasePos = cyclePos - (phaseIndex * PHASE_MS);
        var minutesLeft = Math.ceil((PHASE_MS - phasePos) / 60000);
        var progress = phasePos / PHASE_MS;
        var cycleProgress = cyclePos / CYCLE_MS;

        var p = PHASES[phaseIndex];
        return {
            phase: p.id,
            phaseName: p.name,
            phaseIcon: p.icon,
            phaseColor: p.color,
            phaseDesc: p.desc,
            phaseIndex: phaseIndex,
            minutesLeft: minutesLeft,
            progress: progress,
            cycleProgress: cycleProgress,
            storm: storm
        };
    }

    /**
     * Anti-clock-manipulation: detect time jumps > 7 hours.
     */
    function _checkStorm(now) {
        var lastCheck = parseInt(localStorage.getItem('moreau_last_tide_check') || '0', 10);
        localStorage.setItem('moreau_last_tide_check', String(now));

        if (lastCheck === 0) return false;

        var diff = Math.abs(now - lastCheck);
        if (diff > STORM_JUMP_MS) {
            _triggerStorm();
            return true;
        }
        return false;
    }

    function _triggerStorm() {
        try {
            var allPets = JSON.parse(localStorage.getItem('moreau_pets') || '[]');
            if (!allPets.length) return;

            // Find the most mutated pet (most lab_mutations + mutations)
            var mostMutated = null;
            var maxMuts = -1;
            allPets.forEach(function(pet, idx) {
                if (pet.deceased || pet.is_alive === false) return;
                var mc = (pet.mutations ? pet.mutations.length : 0) +
                         (pet.lab_mutations ? Object.keys(pet.lab_mutations).length : 0);
                if (mc > maxMuts) { maxMuts = mc; mostMutated = idx; }
            });

            if (mostMutated !== null && maxMuts > 0) {
                var pet = allPets[mostMutated];
                pet.instability = (pet.instability || 0) + 5;
                localStorage.setItem('moreau_pets', JSON.stringify(allPets));
            }
        } catch(e) { /* ignore */ }
    }

    /**
     * Get the phase schedule for the next N hours.
     * @param {number} hours — how many hours ahead (default 24)
     * @returns {Array<{phase: string, phaseName: string, phaseIcon: string, start: Date, end: Date}>}
     */
    function getTideSchedule(hours) {
        hours = hours || 24;
        var now = Date.now();
        var entries = [];
        var totalMs = hours * 60 * 60 * 1000;
        var cursor = now - (now % PHASE_MS); // align to current phase start

        while (cursor < now + totalMs) {
            var cyclePos = cursor % CYCLE_MS;
            var pi = Math.floor(cyclePos / PHASE_MS);
            if (pi > 3) pi = 3;
            var p = PHASES[pi];
            entries.push({
                phase: p.id,
                phaseName: p.name,
                phaseIcon: p.icon,
                start: new Date(cursor),
                end: new Date(cursor + PHASE_MS)
            });
            cursor += PHASE_MS;
        }
        return entries;
    }

    /**
     * Render a compact tide indicator widget into a container.
     * @param {string} containerId — DOM element id
     */
    function renderTideIndicator(containerId) {
        var container = document.getElementById(containerId);
        if (!container) return;

        function update() {
            var s = getTideState();
            var mins = s.minutesLeft;
            var timeStr = mins >= 60 ? Math.floor(mins/60) + 'h ' + (mins%60) + 'm' : mins + 'm';

            container.innerHTML =
                '<div class="tide-indicator" style="' +
                    'display:inline-flex;align-items:center;gap:0.5rem;padding:0.35rem 0.75rem;' +
                    'border-radius:20px;border:1px solid ' + s.phaseColor + ';' +
                    'background:rgba(0,0,0,0.5);font-size:0.8rem;cursor:pointer;' +
                    'transition:border-color 0.5s,box-shadow 0.5s;' +
                    'box-shadow:0 0 8px ' + s.phaseColor + '33;' +
                '" onclick="window.location.href=\'/island/tides\'" title="' + s.phaseName + ' — ' + timeStr + ' remaining">' +
                    '<span style="font-size:1rem;">' + s.phaseIcon + '</span>' +
                    '<span style="color:' + s.phaseColor + ';font-weight:600;">' + s.phaseName.toUpperCase() + '</span>' +
                    '<span style="color:#a8a0a0;font-size:0.75rem;">' + timeStr + '</span>' +
                    '<div style="width:40px;height:4px;border-radius:2px;background:#1a1010;overflow:hidden;">' +
                        '<div style="width:' + (s.progress * 100) + '%;height:100%;background:' + s.phaseColor + ';' +
                            'border-radius:2px;transition:width 1s;"></div>' +
                    '</div>' +
                    (s.storm ? '<span style="color:#ff4444;" title="Storm detected!">&#9889;</span>' : '') +
                '</div>';
        }

        update();
        setInterval(update, 15000); // refresh every 15 seconds
    }

    /**
     * Render a subtle wave animation bar (bottom of page).
     * @param {string} containerId
     */
    function renderTideWave(containerId) {
        var container = document.getElementById(containerId);
        if (!container) return;

        var s = getTideState();
        container.innerHTML =
            '<div style="position:fixed;bottom:0;left:0;right:0;height:3px;z-index:9998;pointer-events:none;overflow:hidden;">' +
                '<div class="tide-wave-bar" style="' +
                    'width:200%;height:100%;background:linear-gradient(90deg,' +
                    s.phaseColor + '00,' + s.phaseColor + '66,' + s.phaseColor + '00,' +
                    s.phaseColor + '66,' + s.phaseColor + '00);' +
                    'animation:tideWaveSlide 4s linear infinite;' +
                '"></div>' +
            '</div>' +
            '<style>' +
                '@keyframes tideWaveSlide { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }' +
            '</style>';
    }

    // Expose API
    window.TideEngine = {
        getTideState: getTideState,
        getTideSchedule: getTideSchedule,
        renderTideIndicator: renderTideIndicator,
        renderTideWave: renderTideWave,
        PHASES: PHASES
    };

})(window);
