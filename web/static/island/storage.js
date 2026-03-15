(function(window) {
    'use strict';

    var PETS_KEY = 'moreau_pets';
    var ACTIVE_PET_KEY = 'moreau_active_pet';
    var LEGACY_PET_KEY = 'moreau_pet';
    var DREAMS_KEY = 'moreau_dreams';
    var CONFESSIONS_KEY = 'moreau_confessions';

    function readJSON(key, fallback) {
        try {
            var raw = localStorage.getItem(key);
            if (raw === null) return fallback;
            return JSON.parse(raw);
        } catch (e) {
            return fallback;
        }
    }

    function writeJSON(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    function migrateLegacyPet(options) {
        options = options || {};

        var oldRaw = localStorage.getItem(LEGACY_PET_KEY);
        if (!oldRaw) return;

        try {
            var oldPet = JSON.parse(oldRaw);
            var pets = readJSON(PETS_KEY, []);
            var maxPets = options.maxPets || 6;
            if (Array.isArray(pets) && pets.length < maxPets) {
                pets.push(oldPet);
                writeJSON(PETS_KEY, pets);
                if (options.setActiveOnMigrate !== false) {
                    localStorage.setItem(ACTIVE_PET_KEY, String(pets.length - 1));
                }
            }
        } catch (e) {
            // Ignore broken legacy payloads and clear the stale key below.
        }

        localStorage.removeItem(LEGACY_PET_KEY);
    }

    function loadPets(options) {
        migrateLegacyPet(options);
        var pets = readJSON(PETS_KEY, []);
        return Array.isArray(pets) ? pets : [];
    }

    function savePets(pets) {
        writeJSON(PETS_KEY, Array.isArray(pets) ? pets : []);
    }

    function hasPets(options) {
        if (localStorage.getItem(LEGACY_PET_KEY)) return true;
        return loadPets(options).length > 0;
    }

    function getActivePetIndex(pets) {
        pets = Array.isArray(pets) ? pets : loadPets();
        if (pets.length === 0) return 0;
        var idx = parseInt(localStorage.getItem(ACTIVE_PET_KEY) || '0', 10);
        if (idx < 0 || idx >= pets.length) idx = 0;
        return idx;
    }

    function setActivePetIndex(idx) {
        localStorage.setItem(ACTIVE_PET_KEY, String(idx));
    }

    function getActivePet(options) {
        var pets = loadPets(options);
        if (pets.length === 0) return null;
        return pets[getActivePetIndex(pets)] || null;
    }

    function clearPets() {
        localStorage.removeItem(PETS_KEY);
        localStorage.removeItem(ACTIVE_PET_KEY);
        localStorage.removeItem(LEGACY_PET_KEY);
    }

    function loadDreamState() {
        var data = readJSON(DREAMS_KEY, { dreams: [], unread_count: 0 });
        if (!data || typeof data !== 'object') return { dreams: [], unread_count: 0 };
        if (!Array.isArray(data.dreams)) data.dreams = [];
        if (typeof data.unread_count !== 'number') data.unread_count = 0;
        return data;
    }

    function saveDreamState(data) {
        writeJSON(DREAMS_KEY, data || { dreams: [], unread_count: 0 });
    }

    function countUnreadDreams(data) {
        var state = data || loadDreamState();
        return (state.dreams || []).filter(function(dream) { return !dream.read; }).length;
    }

    function loadConfessions() {
        var journal = readJSON(CONFESSIONS_KEY, []);
        return Array.isArray(journal) ? journal : [];
    }

    function saveConfessions(journal) {
        writeJSON(CONFESSIONS_KEY, Array.isArray(journal) ? journal : []);
    }

    window.MoreauStorage = {
        readJSON: readJSON,
        writeJSON: writeJSON,
        migrateLegacyPet: migrateLegacyPet,
        loadPets: loadPets,
        savePets: savePets,
        hasPets: hasPets,
        getActivePetIndex: getActivePetIndex,
        setActivePetIndex: setActivePetIndex,
        getActivePet: getActivePet,
        clearPets: clearPets,
        loadDreamState: loadDreamState,
        saveDreamState: saveDreamState,
        countUnreadDreams: countUnreadDreams,
        loadConfessions: loadConfessions,
        saveConfessions: saveConfessions
    };
})(window);
