(function(window) {
    'use strict';

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

    window.MoreauStorage = {
        readJSON: readJSON,
        writeJSON: writeJSON
    };
})(window);
