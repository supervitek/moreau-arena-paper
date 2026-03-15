(function(window) {
    'use strict';

    var started = false;

    function start() {
        if (started) return;
        started = true;

        setInterval(function() {
            if (document.hidden) return;
            var now = Date.now();
            var lock = parseInt(localStorage.getItem('moreau_island_time_lock') || '0', 10);
            if (now - lock < 25000) return;
            localStorage.setItem('moreau_island_time_lock', String(now));
            var total = parseInt(localStorage.getItem('moreau_island_time') || '0', 10);
            total += 30;
            localStorage.setItem('moreau_island_time', String(total));
        }, 30000);
    }

    window.MoreauIslandTime = {
        start: start
    };

    start();
})(window);
