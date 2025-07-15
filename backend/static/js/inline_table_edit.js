// backend/static/js/inline_table_edit.js
(function() { // <-- FIX: Add opening IIFE
    'use strict';
    
    // FIX: Ensure the global namespace exists
    window.usecaseExplorer = window.usecaseExplorer || {};

    // Change 'export function' to attach to a global namespace
    window.usecaseExplorer.initializeInlineTableEditing = function() {
        const allTables = document.querySelectorAll('table');

        // --- START REFACTOR: Read data from the data island ---
        const dataIsland = document.getElementById('page-data-island');
        const pageData = dataIsland ? JSON.parse(dataIsland.textContent) : {};
        const allAreas = pageData.all_areas_for_select || [];
        // --- END REFACTOR ---

        allTables.forEach(table => {
            table.addEventListener('click', function (event) {
                const cell = event.target.closest('td.editable-cell');
                if (cell && !cell.classList.contains('is-editing')) {
                    startEdit(cell);
                }
            });
        });

        function startEdit(cell) {
            cell.classList.add('is-editing');
            const originalHTML = cell.innerHTML;
            const field = cell.dataset.field;
            const row = cell.closest('tr');
            
            const isStepTable = row.hasAttribute('data-step-id');
            const entityId = isStepTable ? row.dataset.stepId : row.dataset.ucId;
            const entityType = isStepTable ? 'step' : 'usecase';

            if (!entityId || !field) {
                cell.classList.remove('is-editing');
                return;
            }

            cell.dataset.originalHTML = originalHTML; // Store original content
            let originalValue = cell.textContent.trim();
            if (cell.querySelector('a')) {
                originalValue = cell.querySelector('a').textContent.trim();
            }

            cell.innerHTML = ''; // Clear the cell
            let inputElement;

            // --- Create appropriate input based on field name ---
            if (field === 'area_id') {
                inputElement = document.createElement('select');
                inputElement.className = 'form-select form-select-sm';
                allAreas.forEach(area => {
                    const option = document.createElement('option');
                    option.value = area.id;
                    option.textContent = area.name;
                    if (area.name === originalValue) {
                        option.selected = true;
                    }
                    inputElement.appendChild(option);
                });
            } else { // Default to text input
                inputElement = document.createElement('input');
                inputElement.type = 'text';
                inputElement.className = 'form-control form-control-sm';
                inputElement.value = originalValue;
            }
            
            inputElement.dataset.field = field;
            cell.appendChild(inputElement);
            inputElement.focus();

            // --- Event handlers for the new input ---
            const save = () => handleSaveOrCancel(true, cell, inputElement, entityType, entityId);
            const cancel = () => handleSaveOrCancel(false, cell);

            inputElement.addEventListener('blur', save, { once: true });
            inputElement.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    save();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    cancel();
                }
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

            cell.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; // Loading indicator

            const apiEndpoint = entityType === 'step' 
                ? `/steps/api/steps/${entityId}/inline-update`
                : `/usecases/api/usecases/${entityId}/inline-update`;

            fetch(apiEndpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: newValue })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the cell with the confirmed new value
                    const updatedEntity = data.step || data.usecase;
                    if (field === 'name' && entityType === 'usecase') {
                         cell.innerHTML = `<a href="/usecases/${updatedEntity.id}">${updatedEntity.name}</a>`;
                    } else if (field === 'area_id') {
                         cell.textContent = updatedEntity.area_name || 'N/A';
                    } else {
                        cell.textContent = updatedEntity[field] || 'N/A';
                    }
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
})(); // <-- FIX: Add closing IIFE