(function(window) {
    'use strict';

    function escapeHtml(value) {
        var div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    function showToast(options) {
        options = options || {};
        var toast = options.element || document.getElementById(options.id);
        if (!toast) return;

        if (options.titleId) {
            var titleEl = document.getElementById(options.titleId);
            if (titleEl) titleEl.textContent = options.title || '';
        }
        if (options.textId) {
            var textEl = document.getElementById(options.textId);
            if (textEl) textEl.textContent = options.text || '';
        }

        if (options.baseClass) {
            toast.className = options.baseClass + (options.type ? ' ' + options.type : '');
        }
        if (options.html != null) toast.innerHTML = options.html;
        else if (options.message != null) toast.textContent = options.message;

        var visibleClass = options.visibleClass || 'show';
        var duration = options.duration || 3500;
        toast.classList.add(visibleClass);
        setTimeout(function() { toast.classList.remove(visibleClass); }, duration);
    }

    window.MoreauUI = {
        escapeHtml: escapeHtml,
        showToast: showToast
    };
})(window);
