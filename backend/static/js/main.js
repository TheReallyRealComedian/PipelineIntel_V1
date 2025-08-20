(function() {
    'use strict';

    /**
     * Initializes client-side sorting for a given table.
     * @param {HTMLTableElement} table The table element to make sortable.
     */
    function initializeTableSorter(table) {
        table.querySelectorAll('.table-sort-icon').forEach(icon => {
            icon.addEventListener('click', () => {
                const th = icon.closest('th');
                const colIndex = Array.from(th.parentNode.children).indexOf(th);
                const currentOrder = icon.dataset.sortOrder || 'none';
                let nextOrder;

                if (currentOrder === 'asc') nextOrder = 'desc';
                else if (currentOrder === 'desc') nextOrder = 'none';
                else nextOrder = 'asc';

                // Reset all other icons
                table.querySelectorAll('.table-sort-icon').forEach(i => {
                    i.dataset.sortOrder = 'none';
                    i.className = 'fas fa-sort table-sort-icon';
                });

                // Set this icon's state
                icon.dataset.sortOrder = nextOrder;
                if (nextOrder === 'asc') icon.className = 'fas fa-sort-up table-sort-icon sorted';
                else if (nextOrder === 'desc') icon.className = 'fas fa-sort-down table-sort-icon sorted';
                else icon.className = 'fas fa-sort table-sort-icon';

                sortAndFilterTable(table);
            });
        });
    }

    /**
     * Initializes client-side filtering for a given table.
     * @param {HTMLTableElement} table The table element to make filterable.
     */
    function initializeTableFiltering(table) {
        table.querySelectorAll('.table-filter-icon').forEach(icon => {
            const dropdownMenu = icon.nextElementSibling;

            // Populate menu on first open
            icon.addEventListener('show.bs.dropdown', () => {
                if (dropdownMenu.dataset.populated) return;

                const th = icon.closest('th');
                const colIndex = Array.from(th.parentNode.children).indexOf(th);
                const optionsList = dropdownMenu.querySelector('.filter-options-list');
                
                const values = new Set();
                let hasBlanks = false;
                table.querySelectorAll('tbody tr').forEach(row => {
                    const cellValue = row.cells[colIndex]?.textContent.trim();
                    if (cellValue) {
                        values.add(cellValue);
                    } else {
                        hasBlanks = true;
                    }
                });

                optionsList.innerHTML = '';
                // Sort values alphabetically
                Array.from(values).sort((a,b) => a.localeCompare(b)).forEach(value => {
                    optionsList.insertAdjacentHTML('beforeend', `
                        <div class="form-check">
                            <input class="form-check-input filter-option" type="checkbox" value="${value}" checked>
                            <label class="form-check-label">${value}</label>
                        </div>
                    `);
                });

                if (hasBlanks) {
                    optionsList.insertAdjacentHTML('beforeend', `
                        <div class="form-check">
                            <input class="form-check-input filter-option" type="checkbox" value="" checked>
                            <label class="form-check-label fst-italic text-muted">(Blanks)</label>
                        </div>
                    `);
                }
                
                dropdownMenu.dataset.populated = 'true';
            }, { once: true });

            // Handle "Select All"
            const selectAllCheckbox = dropdownMenu.querySelector('.select-all-filter');
            selectAllCheckbox.addEventListener('change', () => {
                dropdownMenu.querySelectorAll('.filter-option').forEach(cb => {
                    cb.checked = selectAllCheckbox.checked;
                });
            });
            
            // Handle "Apply" button
            const applyBtn = dropdownMenu.querySelector('.apply-filter-btn');
            applyBtn.addEventListener('click', () => {
                // We need to find the bootstrap dropdown instance to hide it
                const dropdownInstance = bootstrap.Dropdown.getInstance(icon);
                if(dropdownInstance) dropdownInstance.hide();
                sortAndFilterTable(table);
            });
        });
    }

    /**
     * Central function to apply both sorting and filtering to a table.
     * @param {HTMLTableElement} table The table element to process.
     */
    function sortAndFilterTable(table) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        // --- GATHER FILTERS ---
        const activeFilters = [];
        table.querySelectorAll('thead th').forEach((th, colIndex) => {
            const filterIcon = th.querySelector('.table-filter-icon');
            const dropdownMenu = filterIcon?.nextElementSibling;
            if (!dropdownMenu || !dropdownMenu.dataset.populated) return;

            const selectedValues = new Set();
            let isFilterActive = false;
            let allOptionsChecked = true;

            dropdownMenu.querySelectorAll('.filter-option').forEach(cb => {
                if (cb.checked) {
                    selectedValues.add(cb.value);
                } else {
                    allOptionsChecked = false;
                }
            });

            // A filter is "active" if not all options are checked.
            if (!allOptionsChecked) {
                isFilterActive = true;
                activeFilters.push({ colIndex, selectedValues });
            }

            filterIcon.classList.toggle('filter-active', isFilterActive);
        });

        const allRows = Array.from(tbody.querySelectorAll('tr'));
        
        // --- APPLY FILTERS ---
        allRows.forEach(row => {
            let isVisible = true;
            if (activeFilters.length > 0) {
                isVisible = activeFilters.every(filter => {
                    const cellValue = row.cells[filter.colIndex]?.textContent.trim() || '';
                    return filter.selectedValues.has(cellValue);
                });
            }
            row.style.display = isVisible ? '' : 'none';
        });

        // --- APPLY SORTING ---
        const sortIcon = table.querySelector('.table-sort-icon.sorted');
        if (sortIcon) {
            const th = sortIcon.closest('th');
            const colIndex = Array.from(th.parentNode.children).indexOf(th);
            const sortOrder = sortIcon.dataset.sortOrder;

            // Only sort the visible rows
            const visibleRows = allRows.filter(row => row.style.display !== 'none');

            visibleRows.sort((a, b) => {
                const valA = a.cells[colIndex]?.textContent.trim() || '';
                const valB = b.cells[colIndex]?.textContent.trim() || '';
                const numA = parseFloat(valA);
                const numB = parseFloat(valB);
                
                let comparison = 0;
                if (!isNaN(numA) && !isNaN(numB)) {
                    comparison = numA - numB;
                } else {
                    comparison = valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' });
                }
                
                return sortOrder === 'asc' ? comparison : -comparison;
            });

            // Re-append sorted rows to the tbody
            visibleRows.forEach(row => tbody.appendChild(row));
        }
    }


    // --- Global Initializer ---
    document.addEventListener('DOMContentLoaded', function() {
        // Find all dynamic tables on the page and initialize them
        document.querySelectorAll('table[data-entity-type]').forEach(table => {
            initializeTableSorter(table);
            initializeTableFiltering(table);

            // Initialize inline editing if it exists
            if (window.usecaseExplorer && typeof window.usecaseExplorer.initializeInlineTableEditing === 'function') {
                window.usecaseExplorer.initializeInlineTableEditing(table);
            }
        });
        
        // Find all column selectors on the page and initialize them
        document.querySelectorAll('[id$="-column-selector"]').forEach(selector => {
            if (window.initializeColumnSelector) {
                window.initializeColumnSelector(selector.id);
            }
        });
    });

    // Make functions globally available if needed, but they are self-contained here.
    // Attach other initializers to window object.
    window.usecaseExplorer = window.usecaseExplorer || {};
    
    window.initializeColumnSelector = function(selectorId) {
        // ... (This function from previous step remains the same)
        const selector = document.getElementById(selectorId);
        if (!selector) return;

        const tableId = selector.id.replace('-column-selector', '');
        const applyBtn = selector.querySelector('#apply-columns-btn');
        const checkboxes = selector.querySelectorAll('.column-select-checkbox');

        selector.addEventListener('click', (e) => e.stopPropagation());

        applyBtn.addEventListener('click', () => {
            const selectedColumns = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value)
                .join(',');

            localStorage.setItem(`table_columns_${tableId}`, selectedColumns);

            const url = new URL(window.location.href);
            url.searchParams.set('columns', selectedColumns);
            window.location.href = url.toString();
        });

        const currentUrlParams = new URLSearchParams(window.location.search);
        if (!currentUrlParams.has('columns')) {
            const savedColumns = localStorage.getItem(`table_columns_${tableId}`);
            if (savedColumns) {
                const url = new URL(window.location.href);
                url.searchParams.set('columns', savedColumns);
                window.location.replace(url.toString());
            }
        }
    };
    
    // Slight modification to the inline editor to make it work with the new structure
    window.usecaseExplorer.initializeInlineTableEditing = function(table) {
        if (!table) return; // Guard clause
        const entityType = table.dataset.entityType;
        const entityPlural = table.dataset.entityPlural; // GET THE PLURAL NAME

        table.addEventListener('click', function(event) {
            const cell = event.target.closest('td.editable-cell');
            if (cell && !cell.classList.contains('is-editing')) {
                // Pass both singular and plural names to the edit handler
                startEdit(cell, entityType, entityPlural);
            }
        });
    };
    
    function startEdit(cell, entityType, entityPlural) { // Accept plural name
        cell.classList.add('is-editing');
        const originalHTML = cell.innerHTML;
        const field = cell.dataset.field;
        const row = cell.closest('tr');
        const entityId = row.dataset.entityId;
        if (!entityId || !field) { cell.classList.remove('is-editing'); return; }
        cell.dataset.originalHTML = originalHTML;
        let originalValue = cell.textContent.trim();
        cell.innerHTML = ''; 
        let inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.className = 'form-control form-control-sm';
        inputElement.value = originalValue;
        inputElement.dataset.field = field;
        cell.appendChild(inputElement);
        inputElement.focus();
        const save = () => handleSaveOrCancel(true, cell, inputElement, entityType, entityId, entityPlural); // Pass plural name
        const cancel = () => handleSaveOrCancel(false, cell);
        inputElement.addEventListener('blur', save, { once: true });
        inputElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); save(); } 
            else if (e.key === 'Escape') { e.preventDefault(); cancel(); }
        });
    }

    function handleSaveOrCancel(shouldSave, cell, inputElement = null, entityType = null, entityId = null, entityPlural = null) { // Accept plural name
        if (!cell.classList.contains('is-editing')) return;
        cell.classList.remove('is-editing');
        const originalHTML = cell.dataset.originalHTML;
        if (!shouldSave) { cell.innerHTML = originalHTML; return; }
        const newValue = inputElement.value.trim();
        const field = inputElement.dataset.field;
        const originalText = new DOMParser().parseFromString(cell.dataset.originalHTML, "text/html").body.textContent.trim();
        if (newValue === originalText) { cell.innerHTML = originalHTML; return; }
        cell.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // *** THE FIX ***: Use the correct plural name passed from the backend
        const pluralName = entityPlural || (entityType + 's'); // Fallback just in case
        const apiEndpoint = `/${pluralName}/api/${pluralName}/${entityId}/inline-update`;

        fetch(apiEndpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: newValue })
        })
        .then(response => {
            if (!response.ok) { // Check for 404 or other HTTP errors
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) { cell.innerHTML = newValue; } 
            else { alert(`Error: ${data.message}`); cell.innerHTML = originalHTML; }
        })
        .catch(error => {
            console.error('Error updating record:', error);
            alert('An error occurred while saving. Check the console for details.');
            cell.innerHTML = originalHTML;
        });
    }

})();