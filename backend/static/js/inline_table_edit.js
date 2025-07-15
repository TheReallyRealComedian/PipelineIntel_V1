// backend/static/js/inline_table_edit.js
(function() {
    'use strict';
    
    window.usecaseExplorer = window.usecaseExplorer || {};

    window.usecaseExplorer.initializeInlineTableEditing = function() {
        document.querySelectorAll('table[data-entity-type]').forEach(table => {
            const entityType = table.dataset.entityType;

            table.addEventListener('click', function (event) {
                const cell = event.target.closest('td.editable-cell');
                if (cell && !cell.classList.contains('is-editing')) {
                    startEdit(cell, entityType);
                }
            });
        });

        function startEdit(cell, entityType) {
            cell.classList.add('is-editing');
            const originalHTML = cell.innerHTML;
            const field = cell.dataset.field;
            const row = cell.closest('tr');
            const entityId = row.dataset.entityId;

            if (!entityId || !field) {
                cell.classList.remove('is-editing');
                return;
            }

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

            const save = () => handleSaveOrCancel(true, cell, inputElement, entityType, entityId);
            const cancel = () => handleSaveOrCancel(false, cell);

            inputElement.addEventListener('blur', save, { once: true });
            inputElement.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); save(); } 
                else if (e.key === 'Escape') { e.preventDefault(); cancel(); }
            });
        }

        function handleSaveOrCancel(shouldSave, cell, inputElement = null, entityType = null, entityId = null) {
            if (!cell.classList.contains('is-editing')) return;
            cell.classList.remove('is-editing');
            const originalHTML = cell.dataset.originalHTML;
            
            if (!shouldSave) {
                cell.innerHTML = originalHTML;
                return;
            }

            const newValue = inputElement.value.trim();
            const field = inputElement.dataset.field;
            const originalText = cell.dataset.originalHTML.replace(/<[^>]*>/g, '').trim();

            if (newValue === originalText) {
                cell.innerHTML = originalHTML;
                return;
            }

            cell.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            // Construct the API endpoint dynamically based on entity type
            const apiEndpoint = `/${entityType}s/api/${entityType}s/${entityId}/inline-update`;

            fetch(apiEndpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: newValue })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    cell.innerHTML = newValue; // Update with the new value
                } else {
                    alert(`Error: ${data.message}`);
                    cell.innerHTML = originalHTML;
                }
            })
            .catch(error => {
                console.error('Error updating record:', error);
                alert('An error occurred while saving.');
                cell.innerHTML = originalHTML;
            });
        }
    }
})();