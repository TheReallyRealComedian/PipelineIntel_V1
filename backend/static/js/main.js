// backend/static/js/main.js
(function() {
    'use strict';
    
    window.initializeTableSorter = function(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const headers = table.querySelectorAll('th.sortable');

        headers.forEach(header => {
            header.addEventListener('click', () => {
                const currentOrder = header.classList.contains('sorted-asc') ? 'asc' : (header.classList.contains('sorted-desc') ? 'desc' : 'none');
                const sortOrder = (currentOrder === 'asc') ? 'desc' : 'asc';
                
                headers.forEach(th => th.classList.remove('sorted-asc', 'sorted-desc'));
                header.classList.add(sortOrder === 'asc' ? 'sorted-asc' : 'sorted-desc');

                const tbody = table.querySelector('tbody');
                if (!tbody) return;
                
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const colIndex = Array.from(header.parentNode.children).indexOf(header);

                rows.sort((a, b) => {
                    const valA = a.cells[colIndex]?.textContent.trim() || '';
                    const valB = b.cells[colIndex]?.textContent.trim() || '';
                    const numA = parseFloat(valA);
                    const numB = parseFloat(valB);

                    if (!isNaN(numA) && !isNaN(numB)) {
                        return sortOrder === 'asc' ? numA - numB : numB - numA;
                    } else {
                        return sortOrder === 'asc' 
                            ? valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' }) 
                            : valB.localeCompare(valA, undefined, { numeric: true, sensitivity: 'base' });
                    }
                });

                rows.forEach(row => tbody.appendChild(row));
            });
        });
    };

    document.addEventListener('DOMContentLoaded', function() {
        if (window.usecaseExplorer && typeof window.usecaseExplorer.initializeInlineTableEditing === 'function') {
            window.usecaseExplorer.initializeInlineTableEditing();
        }
    });

})();