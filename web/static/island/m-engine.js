// ══════════════════════════════════════════════════════════════
//  M Engine — The Other Player  (Phase 8F)
//  A phantom mirror presence that lives in localStorage.
//  M is generated from INVERTED play data. M leaves notes,
//  moves artifacts, and has pets that appear as encounters.
// ══════════════════════════════════════════════════════════════

(function(window) {
    'use strict';

    var EMOJI_MAP = {
        bear:'\u{1F43B}', buffalo:'\u{1F9AC}', boar:'\u{1F417}', tiger:'\u{1F405}',
        wolf:'\u{1F43A}', monkey:'\u{1F412}', porcupine:'\u{1F994}', scorpion:'\u{1F982}',
        vulture:'\u{1F985}', rhino:'\u{1F98F}', viper:'\u{1F40D}', fox:'\u{1F98A}',
        eagle:'\u{1F985}', panther:'\u{1F408}'
    };

    var ALL_ANIMALS = Object.keys(EMOJI_MAP);

    // Stat inversion map: which stat opposes which
    var STAT_OPPOSITES = { hp: 'spd', spd: 'hp', atk: 'wil', wil: 'atk' };

    // Animal opposition clusters (rough thematic opposites)
    var ANIMAL_OPPOSITES = {
        fox: 'bear', bear: 'fox', wolf: 'panther', panther: 'wolf',
        tiger: 'viper', viper: 'tiger', eagle: 'scorpion', scorpion: 'eagle',
        rhino: 'monkey', monkey: 'rhino', boar: 'vulture', vulture: 'boar',
        buffalo: 'porcupine', porcupine: 'buffalo'
    };

    // ── M's Notes (40 total, phase-dependent) ──

    var M_NOTES = [
        // Phase 1 — Friendly (sessions 1-14)
        "I was here before you. I left something in cage 7. Don't open it. \u2014 M",
        "The fox in the eastern pen trusts too easily. I learned that the hard way.",
        "Your {animal} reminds me of mine. Before the changes.",
        "The Lab hums differently at night. Have you noticed?",
        "I mapped the tunnels under the facility. Third left, second right, then down.",
        "Don't trust the vials with blue labels. The clear ones are worse.",
        "I counted 47 cages. Only 12 are empty now.",
        "The doctor's handwriting gets worse in the later journals. Shakier.",
        "I found a door that wasn't there yesterday. I didn't open it.",
        "If you hear scratching from below the floor \u2014 it's normal. Probably.",
        "Your {pet_name} is getting stronger. Be careful what that means here.",
        "I left you something behind the generator. Small. Might help.",
        "The sunsets here last too long. Like the island doesn't want it to end.",
        "Keep your {pet_name} close tonight. I have a feeling.",
        // Phase 2 — Cryptic (sessions 15-24, indices 14-26)
        "The walls are thinner than they look. I can hear you sometimes.",
        "I've been counting my footsteps. The numbers don't add up.",
        "Something is wrong with the water. Don't drink from the stream.",
        "I lost three days. Just... gone. Check your calendar.",
        "The doctor's notes mention a 'control subject.' I don't think it's any of the animals.",
        "Mirror, mirror. Who's watching whom?",
        "I wrote my name on the wall of cage 12. It was already there.",
        "The dreams are getting more specific. They know your name now.",
        "I found your {pet_name}'s file in the archives. Page 7 is missing.",
        "We need to talk. Meet me at the shrine at midnight. I'll explain everything.",
        "I waited for you. You didn't come. That's okay. I understand.",
        "The patterns in the Lab floor aren't random. They're a map.",
        "I've started forgetting things. Small things. Colors. Names.",
        // Phase 3 — Desperate (sessions 25-34, indices 27-36)
        "Don't go to the Lab tonight. Please. I've seen what happens.",
        "I can't find my pets anymore. They were here. They were RIGHT HERE.",
        "Something is erasing me. Slowly. From the edges in.",
        "I left you everything I have. It's not enough. It's never enough.",
        "The doctor isn't gone. He's in the code. In the numbers. Can you see it?",
        "I'm sorry for moving your things. I was trying to leave breadcrumbs.",
        "If you're reading this, I'm still here. If you're not... who is?",
        "Your {pet_name} looked at me today. Really looked. Like it could see me.",
        "I don't think I'm a player anymore. I think I'm a variable.",
        "The experiment never ended. We're all still in the cages.",
        // Phase 4 — Final (session 35+, indices 37-39)
        "This is the last thing I'll write. I understand now. I was never here.",
        "Take care of {m_pet_name}. They don't know. \u2014 M",
        "\u25CB"
    ];

    // Phase boundaries (by note index)
    var PHASE_FRIENDLY_END = 13;   // 0-13
    var PHASE_CRYPTIC_END = 26;    // 14-26
    var PHASE_DESPERATE_END = 36;  // 27-36
    // 37-39: final

    // ── Helpers ──

    function _getPlayerPets() {
        try {
            return JSON.parse(localStorage.getItem('moreau_pets') || '[]');
        } catch(e) { return []; }
    }

    function _getActivePet() {
        var pets = _getPlayerPets();
        if (pets.length === 0) return null;
        var idx = parseInt(localStorage.getItem('moreau_active_pet') || '0', 10);
        if (idx < 0 || idx >= pets.length) idx = 0;
        return pets[idx];
    }

    function _getM() {
        try {
            return JSON.parse(localStorage.getItem('moreau_other_player') || 'null');
        } catch(e) { return null; }
    }

    function _saveM(m) {
        localStorage.setItem('moreau_other_player', JSON.stringify(m));
    }

    function _rand(max) {
        return Math.floor(Math.random() * max);
    }

    function _pick(arr) {
        return arr[_rand(arr.length)];
    }

    // ── M Generation ──

    function _shouldActivateM() {
        if (_getM()) return false; // already exists
        var pets = _getPlayerPets().filter(function(p) { return !p.deceased && p.is_alive !== false; });
        return pets.some(function(p) { return (p.level || 1) >= 3; });
    }

    function _invertStats(stats) {
        var s = stats || {};
        var total = (s.hp || 5) + (s.atk || 5) + (s.spd || 5) + (s.wil || 5);
        var avg = Math.round(total / 4);
        var result = {};
        var keys = ['hp', 'atk', 'spd', 'wil'];
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            var opposite = STAT_OPPOSITES[k];
            // M puts points where the player DOESN'T
            result[k] = Math.max(1, Math.min(10, (s[opposite] || avg)));
        }
        return result;
    }

    function _oppositeAnimal(animal) {
        var a = (animal || '').toLowerCase();
        return ANIMAL_OPPOSITES[a] || _pick(ALL_ANIMALS.filter(function(x) { return x !== a; }));
    }

    function _generateMPetName(animal) {
        var names = {
            bear: 'Shadow', fox: 'Rust', wolf: 'Hollow', panther: 'Null',
            tiger: 'Flicker', viper: 'Static', eagle: 'Drift', scorpion: 'Thorn',
            rhino: 'Tremor', monkey: 'Glitch', boar: 'Ember', vulture: 'Cirrus',
            buffalo: 'Anchor', porcupine: 'Needle'
        };
        return names[(animal || '').toLowerCase()] || 'Echo';
    }

    function _generateM() {
        var playerPets = _getPlayerPets().filter(function(p) { return !p.deceased && p.is_alive !== false; });
        if (playerPets.length === 0) return null;

        // Average player level
        var totalLevel = 0;
        for (var i = 0; i < playerPets.length; i++) totalLevel += (playerPets[i].level || 1);
        var avgLevel = Math.max(1, Math.round(totalLevel / playerPets.length) - 1);

        // M's pet count: player count - 1, min 1, max 3
        var mPetCount = Math.max(1, Math.min(3, playerPets.length - 1));

        // Average player stats for inversion
        var avgStats = { hp: 0, atk: 0, spd: 0, wil: 0 };
        for (var j = 0; j < playerPets.length; j++) {
            var bs = playerPets[j].base_stats || {};
            avgStats.hp += (bs.hp || 5);
            avgStats.atk += (bs.atk || 5);
            avgStats.spd += (bs.spd || 5);
            avgStats.wil += (bs.wil || 5);
        }
        var n = playerPets.length;
        avgStats.hp = Math.round(avgStats.hp / n);
        avgStats.atk = Math.round(avgStats.atk / n);
        avgStats.spd = Math.round(avgStats.spd / n);
        avgStats.wil = Math.round(avgStats.wil / n);

        // Build M's pets
        var usedAnimals = {};
        var mPets = [];
        for (var k = 0; k < mPetCount; k++) {
            var playerAnimal = (playerPets[k % playerPets.length].animal || '').toLowerCase();
            var mAnimal = _oppositeAnimal(playerAnimal);
            // avoid duplicate animals for M
            var attempts = 0;
            while (usedAnimals[mAnimal] && attempts < 10) {
                mAnimal = _pick(ALL_ANIMALS.filter(function(a) { return !usedAnimals[a] && a !== playerAnimal; }));
                attempts++;
            }
            usedAnimals[mAnimal] = true;

            mPets.push({
                name: _generateMPetName(mAnimal),
                animal: mAnimal,
                stats: _invertStats(avgStats),
                level: avgLevel
            });
        }

        return {
            name: 'M',
            sessionCount: 0,
            pets: mPets,
            notes: [],
            noteIndex: 0,
            artifactMoved: null,
            isDead: false,
            diedAt: null,
            relationship: 'friendly',
            lastInteraction: 0,  // session count at last interaction
            ignoredSessions: 0
        };
    }

    // ── M's Relationship Phase ──

    function _getRelationship(m) {
        var idx = m.noteIndex || 0;
        if (idx <= PHASE_FRIENDLY_END) return 'friendly';
        if (idx <= PHASE_CRYPTIC_END) return 'cryptic';
        if (idx <= PHASE_DESPERATE_END) return 'desperate';
        return 'dead';
    }

    // ── Note Templating ──

    function _templateNote(text, m) {
        var activePet = _getActivePet();
        var petName = (activePet && activePet.name) ? activePet.name : 'your creature';
        var petAnimal = (activePet && activePet.animal) ? activePet.animal : 'creature';
        var mPetName = (m.pets && m.pets.length > 0) ? m.pets[0].name : 'Echo';

        text = text.replace(/\{pet_name\}/g, petName);
        text = text.replace(/\{animal\}/g, petAnimal);
        text = text.replace(/\{m_pet_name\}/g, mPetName);
        return text;
    }

    // ── M's Actions ──

    function _leaveNote(m) {
        var idx = m.noteIndex || 0;
        if (idx >= M_NOTES.length) idx = M_NOTES.length - 1;

        var text = _templateNote(M_NOTES[idx], m);
        m.notes.push({
            text: text,
            session: m.sessionCount,
            read: false
        });
        m.noteIndex = idx + 1;
        m.relationship = _getRelationship(m);
    }

    function _moveArtifact(m) {
        // Check player artifacts
        try {
            var artifacts = JSON.parse(localStorage.getItem('moreau_artifacts') || '[]');
            // Find an unequipped artifact
            var unequipped = [];
            for (var i = 0; i < artifacts.length; i++) {
                if (!artifacts[i].equipped) unequipped.push(i);
            }
            if (unequipped.length === 0) {
                // Fallback: leave a note instead
                _leaveNote(m);
                return;
            }
            var targetIdx = _pick(unequipped);
            var artifact = artifacts[targetIdx];
            m.artifactMoved = {
                name: artifact.name || artifact.id || 'artifact',
                returnSession: m.sessionCount + 3,
                originalIndex: targetIdx
            };

            // Save borrowed tracker
            var borrowed = JSON.parse(localStorage.getItem('moreau_m_borrowed') || '[]');
            borrowed.push({
                artifact: artifact,
                takenSession: m.sessionCount,
                returnSession: m.sessionCount + 3
            });
            localStorage.setItem('moreau_m_borrowed', JSON.stringify(borrowed));

            // Remove from player inventory
            artifacts.splice(targetIdx, 1);
            localStorage.setItem('moreau_artifacts', JSON.stringify(artifacts));
        } catch(e) {
            // Fallback
            _leaveNote(m);
        }
    }

    function _introducePet(m) {
        var playerPets = _getPlayerPets().filter(function(p) { return !p.deceased && p.is_alive !== false; });
        if (playerPets.length === 0) return;

        var playerAnimal = _pick(playerPets).animal || 'wolf';
        var newAnimal = _oppositeAnimal(playerAnimal);
        var usedAnimals = {};
        for (var i = 0; i < m.pets.length; i++) usedAnimals[m.pets[i].animal] = true;

        var attempts = 0;
        while (usedAnimals[newAnimal] && attempts < 10) {
            newAnimal = _pick(ALL_ANIMALS);
            attempts++;
        }

        var avgLevel = 1;
        for (var j = 0; j < playerPets.length; j++) avgLevel += (playerPets[j].level || 1);
        avgLevel = Math.max(1, Math.round(avgLevel / playerPets.length) - 1);

        var avgStats = { hp: 5, atk: 5, spd: 5, wil: 5 };
        for (var k = 0; k < playerPets.length; k++) {
            var bs = playerPets[k].base_stats || playerPets[k].stats || {};
            avgStats.hp += (bs.hp || 5); avgStats.atk += (bs.atk || 5);
            avgStats.spd += (bs.spd || 5); avgStats.wil += (bs.wil || 5);
        }
        var n = playerPets.length;
        avgStats.hp = Math.round(avgStats.hp / n);
        avgStats.atk = Math.round(avgStats.atk / n);
        avgStats.spd = Math.round(avgStats.spd / n);
        avgStats.wil = Math.round(avgStats.wil / n);

        if (m.pets.length < 3) {
            m.pets.push({
                name: _generateMPetName(newAnimal),
                animal: newAnimal,
                stats: _invertStats(avgStats),
                level: avgLevel
            });
        }
    }

    // ── Return Borrowed Artifacts ──

    function _returnBorrowedArtifacts(m) {
        try {
            var borrowed = JSON.parse(localStorage.getItem('moreau_m_borrowed') || '[]');
            if (borrowed.length === 0) return;

            var artifacts = JSON.parse(localStorage.getItem('moreau_artifacts') || '[]');
            var remaining = [];
            for (var i = 0; i < borrowed.length; i++) {
                if (m.sessionCount >= borrowed[i].returnSession) {
                    // Return the artifact
                    artifacts.push(borrowed[i].artifact);
                } else {
                    remaining.push(borrowed[i]);
                }
            }
            localStorage.setItem('moreau_artifacts', JSON.stringify(artifacts));
            localStorage.setItem('moreau_m_borrowed', JSON.stringify(remaining));

            if (remaining.length === 0 && m.artifactMoved) {
                m.artifactMoved = null;
            }
        } catch(e) {}
    }

    // ── M's Death ──

    function _checkMDeath(m) {
        if (m.isDead) return true;
        if (m.ignoredSessions >= 10) {
            m.isDead = true;
            m.diedAt = new Date().toISOString();
            m.relationship = 'dead';

            // Leave final note
            var finalIdx = m.noteIndex >= 39 ? 39 : 38;
            var text = _templateNote(M_NOTES[finalIdx], m);
            m.notes.push({ text: text, session: m.sessionCount, read: false });
            m.noteIndex = 40;

            // Create M's Last Frequency artifact
            localStorage.setItem('moreau_m_last_frequency', JSON.stringify({
                available: true,
                claimed: false
            }));

            return true;
        }
        return false;
    }

    // ── Main Process (called on every home.html load) ──

    function processM() {
        // Check activation
        if (!_getM()) {
            if (_shouldActivateM()) {
                var newM = _generateM();
                if (newM) {
                    _saveM(newM);
                    // First note delivered immediately
                    _leaveNote(newM);
                    _saveM(newM);
                }
            }
            return _getM();
        }

        var m = _getM();
        if (!m) return null;

        // Increment session counter
        var counter = parseInt(localStorage.getItem('moreau_m_session_counter') || '0', 10);
        counter++;
        localStorage.setItem('moreau_m_session_counter', String(counter));
        m.sessionCount = counter;

        // Check for ignored sessions (no interaction since last)
        var hasUnread = false;
        for (var i = 0; i < m.notes.length; i++) {
            if (!m.notes[i].read) { hasUnread = true; break; }
        }
        if (hasUnread) {
            m.ignoredSessions++;
        } else {
            m.ignoredSessions = 0;
        }

        // Check death
        if (_checkMDeath(m)) {
            _saveM(m);
            return m;
        }

        // Return borrowed artifacts
        _returnBorrowedArtifacts(m);

        // Every 5th session, M performs an action
        if (counter % 5 === 0 && !m.isDead) {
            var roll = Math.random();
            if (roll < 0.60) {
                _leaveNote(m);
            } else if (roll < 0.85) {
                _moveArtifact(m);
            } else {
                _introducePet(m);
            }
        }

        // Update relationship
        m.relationship = _getRelationship(m);

        _saveM(m);
        return m;
    }

    // ── M Rival Encounter (for training/fights) ──

    function getMRivalEncounter() {
        var m = _getM();
        if (!m || m.isDead || !m.pets || m.pets.length === 0) return null;

        // 20% chance per session
        if (Math.random() > 0.20) return null;

        var mPet = _pick(m.pets);
        return {
            name: 'M\u2019s ' + mPet.name,
            animal: mPet.animal,
            stats: mPet.stats,
            level: mPet.level,
            isPhantom: true
        };
    }

    // ── Mark Note as Read ──

    function markMNoteRead(noteIndex) {
        var m = _getM();
        if (!m || !m.notes || noteIndex < 0 || noteIndex >= m.notes.length) return;
        m.notes[noteIndex].read = true;
        m.ignoredSessions = 0;
        m.lastInteraction = m.sessionCount;
        _saveM(m);
    }

    // ── Get Unread Notes ──

    function getUnreadMNotes() {
        var m = _getM();
        if (!m || !m.notes) return [];
        var unread = [];
        for (var i = 0; i < m.notes.length; i++) {
            if (!m.notes[i].read) {
                unread.push({ index: i, text: m.notes[i].text, session: m.notes[i].session });
            }
        }
        return unread;
    }

    // ── Claim M's Last Frequency ──

    function claimMLastFrequency() {
        try {
            var freq = JSON.parse(localStorage.getItem('moreau_m_last_frequency') || '{}');
            if (!freq.available || freq.claimed) return false;

            freq.claimed = true;
            localStorage.setItem('moreau_m_last_frequency', JSON.stringify(freq));

            // Add artifact to player inventory
            var artifacts = JSON.parse(localStorage.getItem('moreau_artifacts') || '[]');
            artifacts.push({
                id: 'm_last_frequency',
                name: "M's Last Frequency",
                desc: 'A faint signal from someone who was never here. +2 to all stats.',
                rarity: 'mythic',
                stats: { hp: 2, atk: 2, spd: 2, wil: 2 },
                equipped: false,
                source: 'M',
                date: new Date().toISOString()
            });
            localStorage.setItem('moreau_artifacts', JSON.stringify(artifacts));
            return true;
        } catch(e) { return false; }
    }

    // ── Get M State (for UI) ──

    function getMState() {
        var m = _getM();
        if (!m) return null;
        var unread = getUnreadMNotes();
        var borrowed = [];
        try { borrowed = JSON.parse(localStorage.getItem('moreau_m_borrowed') || '[]'); } catch(e) {}
        var freq = null;
        try { freq = JSON.parse(localStorage.getItem('moreau_m_last_frequency') || 'null'); } catch(e) {}

        return {
            exists: true,
            name: m.name,
            relationship: m.relationship,
            isDead: m.isDead,
            pets: m.pets,
            unreadNotes: unread,
            hasUnread: unread.length > 0,
            artifactMoved: m.artifactMoved,
            borrowedItems: borrowed,
            lastFrequency: freq,
            sessionCount: m.sessionCount
        };
    }

    // ── Export ──

    window.MEngine = {
        process: processM,
        getState: getMState,
        getUnreadNotes: getUnreadMNotes,
        markNoteRead: markMNoteRead,
        getRivalEncounter: getMRivalEncounter,
        claimLastFrequency: claimMLastFrequency,
        EMOJI_MAP: EMOJI_MAP
    };

})(window);
