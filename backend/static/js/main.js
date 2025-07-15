// backend/static/js/main.js
(function() {
    'use strict';
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize inline table editing if a compatible table exists.
        if (document.querySelector('td.editable-cell') && typeof window.usecaseExplorer.initializeInlineTableEditing === 'function') {
            window.usecaseExplorer.initializeInlineTableEditing();
        }
    });
})();