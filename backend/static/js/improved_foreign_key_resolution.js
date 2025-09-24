// improved_foreign_key_resolution.js
// Enhanced foreign key resolution with consolidated view and better UX
// Integrates with existing data_management.js patterns

function initializeImprovedForeignKeyResolver() {
    // Only initialize if we're on the foreign key resolution page
    if (document.getElementById('resolutionGroups')) {
        new ImprovedForeignKeyResolver();
    }
}

class ImprovedForeignKeyResolver {
    constructor() {
        this.resolutions = {};
        this.totalGroups = 0;
        this.resolvedGroups = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.countGroups();
        this.updateProgress();
        this.checkInitialSelections();
        this.populateExistingEntityDropdowns();
    }

    bindEvents() {
        // Handle resolution choice clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.resolution-choice')) {
                this.handleChoiceSelection(e);
            }

            if (e.target.closest('.suggestion-item')) {
                this.handleSuggestionSelection(e);
            }
        });

        // Handle radio button changes
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name.startsWith('resolution_')) {
                this.handleRadioChange(e);
            }

            // Handle manual existing entity dropdown changes
            if (e.target.classList.contains('existing-entity-manual')) {
                this.handleManualEntitySelection(e);
            }
        });

        // Handle apply button click
        document.getElementById('applyAllResolutions').addEventListener('click', () => {
            this.collectAndApplyResolutions();
        });

        // Handle input changes in create forms
        document.addEventListener('input', (e) => {
            if (e.target.closest('.choice-content')) {
                this.updateResolutionData(e.target);
            }
        });

        // Handle select changes in create forms  
        document.addEventListener('change', (e) => {
            if (e.target.closest('.choice-content') && e.target.tagName === 'SELECT' && !e.target.classList.contains('existing-entity-manual')) {
                this.updateResolutionData(e.target);
            }
        });
    }

    countGroups() {
        this.totalGroups = document.querySelectorAll('.resolution-group').length;
        document.getElementById('totalCount').textContent = this.totalGroups;
    }

    handleManualEntitySelection(e) {
        const dropdown = e.target;
        const choice = dropdown.closest('.resolution-choice');
        const group = choice.closest('.resolution-group');

        if (dropdown.value) {
            // Update resolution data
            this.updateResolutionForGroup(group, choice);

            // Mark group as resolved if not already
            if (!group.hasAttribute('data-resolved')) {
                group.setAttribute('data-resolved', 'true');
                this.resolvedGroups++;
                this.updateProgress();
            }
        } else {
            // Remove resolution if no value selected
            if (group.hasAttribute('data-resolved')) {
                group.removeAttribute('data-resolved');
                this.resolvedGroups--;
                this.updateProgress();
            }
        }
    }

    populateExistingEntityDropdowns() {
        const dropdowns = document.querySelectorAll('.existing-entity-manual');

        dropdowns.forEach(dropdown => {
            const fieldName = dropdown.dataset.field; // e.g., 'modality_name'

            // Map the field name from the template to the entity type needed by our new API
            const entityTypeMap = {
                'modality_name': 'modalities',
                // Add other mappings here as you expand this feature
            };
            const entityType = entityTypeMap[fieldName];

            if (!entityType) {
                console.warn(`No API entity type mapping defined for field: ${fieldName}`);
                return;
            }

            this.fetchExistingEntities(entityType).then(entities => {
                // Clear existing options except the placeholder
                while (dropdown.children.length > 1) {
                    dropdown.removeChild(dropdown.lastChild);
                }

                // Add the new, correct options fetched from the database
                entities.forEach(entity => {
                    const option = document.createElement('option');
                    option.value = entity.value; // e.g., "Peptides"
                    option.textContent = entity.label; // e.g., "Peptides (Biologics)"
                    dropdown.appendChild(option);
                });
            });
        });
    }

    async fetchExistingEntities(entityType) {
        // ** THIS IS THE FIX: We replace the old mock data with a live API call **
        try {
            const response = await fetch(`/data-management/api/lookup/${entityType}`);
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }
            const result = await response.json();
            if (result.success) {
                return result.data;
            } else {
                console.error(`API Error fetching ${entityType}:`, result.message);
                return []; // Return empty array on failure
            }
        } catch (error) {
            console.error(`Failed to fetch existing entities for ${entityType}:`, error);
            return []; // Return empty array on network failure
        }
    }


    checkInitialSelections() {
        // Check for pre-selected options and update resolved count
        document.querySelectorAll('.resolution-group').forEach(group => {
            const selectedChoice = group.querySelector('.resolution-choice.selected');
            if (selectedChoice) {
                const field = group.dataset.field;
                const value = group.dataset.value;

                // Mark as resolved if:
                // 1. It's a "Use Existing" choice with suggestions (auto-resolved)
                // 2. It's a "Create New" choice (has default values)
                const hasSuggestions = selectedChoice.querySelector('.suggestion-item.selected');
                const isCreateChoice = selectedChoice.dataset.choice === 'create';

                if (hasSuggestions || isCreateChoice) {
                    this.updateResolutionForGroup(group, selectedChoice);

                    if (!group.hasAttribute('data-resolved')) {
                        group.setAttribute('data-resolved', 'true');
                        this.resolvedGroups++;
                    }
                }
                // For "Use Existing" without suggestions, don't mark as resolved until user selects something
            }
        });
        this.updateProgress();
    }

    handleChoiceSelection(e) {
        const choice = e.target.closest('.resolution-choice');
        const group = choice.closest('.resolution-group');
        const radio = choice.querySelector('input[type="radio"]');

        // Update radio selection
        radio.checked = true;

        // Update visual selection
        group.querySelectorAll('.resolution-choice').forEach(c => {
            c.classList.remove('selected');
        });
        choice.classList.add('selected');

        // Update resolution data
        this.updateResolutionForGroup(group, choice);

        // Update progress if this group wasn't resolved before
        if (!group.hasAttribute('data-resolved')) {
            group.setAttribute('data-resolved', 'true');
            this.resolvedGroups++;
            this.updateProgress();
        }
    }

    handleSuggestionSelection(e) {
        const suggestion = e.target.closest('.suggestion-item');
        const container = suggestion.closest('.suggestions');
        const group = suggestion.closest('.resolution-group');

        // Update visual selection
        container.querySelectorAll('.suggestion-item').forEach(s => {
            s.classList.remove('selected');
        });
        suggestion.classList.add('selected');

        // Update resolution data
        const choice = suggestion.closest('.resolution-choice');
        this.updateResolutionForGroup(group, choice);
    }

    handleRadioChange(e) {
        const choice = e.target.closest('.resolution-choice');
        const group = choice.closest('.resolution-group');

        // Update visual selection
        group.querySelectorAll('.resolution-choice').forEach(c => {
            c.classList.remove('selected');
        });
        choice.classList.add('selected');

        this.updateResolutionForGroup(group, choice);

        // Update progress if needed
        if (!group.hasAttribute('data-resolved')) {
            group.setAttribute('data-resolved', 'true');
            this.resolvedGroups++;
            this.updateProgress();
        }
    }

    updateResolutionForGroup(group, choice) {
        const field = group.dataset.field;
        const value = group.dataset.value;
        const choiceType = choice.dataset.choice;
        const key = `${field}_${value}`;

        if (choiceType === 'existing') {
            // Check for suggestion selection first
            const selectedSuggestion = choice.querySelector('.suggestion-item.selected');
            if (selectedSuggestion) {
                this.resolutions[key] = {
                    type: 'existing',
                    field: field,
                    originalValue: value,
                    value: selectedSuggestion.dataset.value
                };
            } else {
                // Check for manual dropdown selection
                const manualDropdown = choice.querySelector('.existing-entity-manual');
                if (manualDropdown && manualDropdown.value) {
                    this.resolutions[key] = {
                        type: 'existing',
                        field: field,
                        originalValue: value,
                        value: manualDropdown.value
                    };
                } else {
                    // No selection made, remove resolution
                    delete this.resolutions[key];
                    return;
                }
            }
        } else if (choiceType === 'create') {
            const nameInput = choice.querySelector('.new-entity-name');
            const categorySelect = choice.querySelector('.new-entity-category');
            const descriptionInput = choice.querySelector('.new-entity-description');

            const metadata = {};
            if (categorySelect) metadata.category = categorySelect.value;
            if (descriptionInput) metadata.description = descriptionInput.value;

            this.resolutions[key] = {
                type: 'create_new',
                field: field,
                originalValue: value,
                value: nameInput ? nameInput.value : value,
                metadata: metadata
            };
        }
    }

    updateResolutionData(input) {
        const choice = input.closest('.resolution-choice');
        const group = choice.closest('.resolution-group');

        if (choice.classList.contains('selected')) {
            this.updateResolutionForGroup(group, choice);
        }
    }

    updateProgress() {
        document.getElementById('resolvedCount').textContent = this.resolvedGroups;
        document.getElementById('unresolvedCount').textContent = this.totalGroups - this.resolvedGroups;

        const percentage = this.totalGroups > 0 ? (this.resolvedGroups / this.totalGroups) * 100 : 0;
        document.getElementById('progressBar').style.width = percentage + '%';

        // Update apply button
        const applyButton = document.getElementById('applyAllResolutions');
        if (this.resolvedGroups === this.totalGroups) {
            applyButton.disabled = false;
            applyButton.className = 'btn btn-success';
            applyButton.innerHTML = '<i class="fas fa-check me-2"></i>Apply All Resolutions & Continue';
        } else {
            applyButton.disabled = true;
            applyButton.className = 'btn btn-outline-secondary';
            const remaining = this.totalGroups - this.resolvedGroups;
            applyButton.innerHTML = `<i class="fas fa-clock me-2"></i>Resolve ${remaining} more reference${remaining > 1 ? 's' : ''}`;
        }
    }

    collectAndApplyResolutions() {
        // Validate all resolutions are complete
        if (this.resolvedGroups < this.totalGroups) {
            alert('Please resolve all missing references before continuing.');
            return;
        }

        // Show loading state
        const applyButton = document.getElementById('applyAllResolutions');
        applyButton.disabled = true;
        applyButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Applying resolutions...';

        // Transform resolutions to match backend expectations
        const backendResolutions = this.convertToBackendFormat();

        console.log('Sending resolutions to backend:', backendResolutions);

        // Send to backend
        this.sendResolutionsToBackend(backendResolutions);
    }

    convertToBackendFormat() {
        const backendFormat = {};
        const originalData = window.originalImportData || [];
        const entityType = window.currentImportEntityType || '';

        const identifierFields = {
            'products': 'product_code',
            'indications': 'indication_name',
            'manufacturing_challenges': 'challenge_name',
            'manufacturing_technologies': 'technology_name',
            'process_stages': 'stage_name',
            'modalities': 'modality_name',
            // Define other entity identifiers as needed
        };
        const identifierField = identifierFields[entityType];

        if (!identifierField) {
            console.error(`Identifier field for entity type '${entityType}' is not defined.`);
            return {};
        }

        // Iterate through each resolution group, which is more reliable
        document.querySelectorAll('.resolution-group').forEach(group => {
            const field = group.dataset.field;
            const originalValue = group.dataset.value;
            const resolutionKey = `${field}_${originalValue}`;
            const resolution = this.resolutions[resolutionKey];

            if (resolution) {
                // Find all items affected by this specific resolution
                group.querySelectorAll('.affected-item').forEach(affectedItem => {
                    const itemId = affectedItem.textContent.trim().split(' -')[0].trim();

                    // Find the actual index by looking up the unique ID in the original data
                    const actualIndex = originalData.findIndex(item => String(item[identifierField]) === String(itemId));

                    if (actualIndex !== -1) {
                        const indexStr = actualIndex.toString();
                        if (!backendFormat[indexStr]) {
                            backendFormat[indexStr] = {};
                        }

                        backendFormat[indexStr][field] = {
                            type: resolution.type,
                            value: resolution.value,
                            metadata: resolution.metadata || {}
                        };
                    } else {
                        console.warn(`Could not find original item with ID: ${itemId}`);
                    }
                });
            }
        });

        console.log('Sending resolutions to backend with correct indices:', backendFormat);
        return backendFormat;
    }

    sendResolutionsToBackend(resolutions) {
        const originalData = window.originalImportData || [];
        const entityType = window.currentImportEntityType || '';

        fetch('/data-management/resolve-foreign-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    resolutions: resolutions,
                    entity_type: entityType,
                    original_data: originalData
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    if (data.created_entities && data.created_entities.length > 0) {
                        this.showAlert(`Successfully created ${data.created_entities.length} new entities: ${data.created_entities.join(', ')}`, 'success');
                    }

                    // Continue with import process
                    this.proceedWithImport(data.analysis_result);
                } else {
                    this.showAlert('Resolution failed: ' + data.message, 'danger');
                    this.resetApplyButton();
                }
            })
            .catch(error => {
                console.error('Resolution error:', error);
                this.showAlert('Failed to apply resolutions: ' + error.message, 'danger');
                this.resetApplyButton();
            });
    }

    resetApplyButton() {
        const applyButton = document.getElementById('applyAllResolutions');
        applyButton.disabled = false;
        applyButton.className = 'btn btn-success';
        applyButton.innerHTML = '<i class="fas fa-check me-2"></i>Apply All Resolutions & Continue';
    }

    proceedWithImport(analysisResult) {
        // The backend will now handle storing the preview data in the session.
        // This function's only job is to redirect to the correct page.
        window.location.href = '/data-management/preview';
    }

    getCSRFToken() {
        // Try to get CSRF token from meta tag first
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        // Fallback: use existing getCSRFToken function if available
        if (typeof getCSRFToken === 'function') {
            return getCSRFToken();
        }

        // Fallback: look for CSRF token in cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return decodeURIComponent(value);
            }
        }

        return '';
    }

    showAlert(message, type) {
        // Use existing showAlert function if available
        if (typeof showAlert === 'function') {
            showAlert(message, type);
            return;
        }

        // Fallback: create bootstrap alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded - integrate with existing pattern
document.addEventListener('DOMContentLoaded', function() {
    initializeImprovedForeignKeyResolver();
});

// Also provide initialization function for existing data_management.js integration
function initializeForeignKeyResolver() {
    initializeImprovedForeignKeyResolver();
}