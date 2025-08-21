document.addEventListener('DOMContentLoaded', function () {
    // --- Custom Select Implementation ---
    document.querySelectorAll('.select-option').forEach(option => {
        option.addEventListener('click', function() {
            this.classList.toggle('selected');
            updateHiddenInputs(this.dataset.name);
            updateCount(this.dataset.name);
        });
    });

    function getCSRFToken() {
        return document.querySelector('meta[name=csrf-token]').getAttribute('content');
    }

    function updateHiddenInputs(inputName) {
        const entityType = inputName.replace('_ids', '');
        const container = document.getElementById(`${entityType}_hidden_inputs`);
        if (!container) return;
        
        container.innerHTML = ''; // Clear previous inputs
        const selectedOptions = document.querySelectorAll(`.select-option[data-name="${inputName}"].selected`);
        
        selectedOptions.forEach(option => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = inputName;
            input.value = option.dataset.value;
            container.appendChild(input);
        });
    }

    function updateCount(inputName) {
        const countElement = document.getElementById(`${inputName}_selected_count`);
        if (!countElement) return;
        
        const selectedCount = document.querySelectorAll(`.select-option[data-name="${inputName}"].selected`).length;
        countElement.textContent = `${selectedCount} selected`;
    }
    
    // Initial setup on page load
    document.querySelectorAll('[id$="_ids_selected_count"]').forEach(el => {
        updateHiddenInputs(el.id.replace('_selected_count', ''));
        updateCount(el.id.replace('_selected_count', ''));
    });

    // --- Search functionality for selection lists ---
    document.querySelectorAll('input[type="search"]').forEach(input => {
        input.addEventListener('input', function() {
            const containerId = this.id.replace('_search', '-select-container');
            const container = document.getElementById(containerId);
            const term = this.value.toLowerCase();

            container.querySelectorAll('.select-option').forEach(option => {
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(term) ? 'block' : 'none';
            });
        });
    });

    // --- "Select All" / "Clear All" for entity lists ---
    document.querySelectorAll('button.select-all').forEach(btn => {
        btn.addEventListener('click', () => handleSelection(btn.dataset.type, true));
    });
    document.querySelectorAll('button.clear-all').forEach(btn => {
        btn.addEventListener('click', () => handleSelection(btn.dataset.type, false));
    });
    
    function handleSelection(entityType, shouldSelect) {
        const container = document.getElementById(`${entityType}-select-container`);
        container.querySelectorAll('.select-option').forEach(option => {
            // Only affect visible options
            if (option.style.display !== 'none') {
                option.classList.toggle('selected', shouldSelect);
            }
        });
        updateHiddenInputs(`${entityType}_ids`);
        updateCount(`${entityType}_ids`);
    }

    // --- "Select All" / "Clear All" for field checkboxes ---
    document.querySelectorAll('.select-all-fields').forEach(btn => {
        btn.addEventListener('click', () => handleFieldSelection(btn.dataset.type, true));
    });
    document.querySelectorAll('.clear-all-fields').forEach(btn => {
        btn.addEventListener('click', () => handleFieldSelection(btn.dataset.type, false));
    });

    function handleFieldSelection(entityType, shouldCheck) {
        document.querySelectorAll(`input[name="${entityType}_fields"]`).forEach(cb => {
            cb.checked = shouldCheck;
        });
    }
    
    // --- JSON Preview Copy Button ---
    const copyBtn = document.getElementById('copyJsonButton');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const jsonText = document.getElementById('jsonDataPreview').textContent;
            navigator.clipboard.writeText(jsonText).then(() => {
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>Copy JSON';
                }, 2000);
            });
        });
    }
});