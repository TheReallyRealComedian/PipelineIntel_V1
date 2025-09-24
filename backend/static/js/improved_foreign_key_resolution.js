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
        // Get existing entities for each field type
        const dropdowns = document.querySelectorAll('.existing-entity-manual');
        
        dropdowns.forEach(dropdown => {
            const fieldName = dropdown.dataset.field;
            this.fetchExistingEntities(fieldName).then(entities => {
                // Clear existing options except the first one
                while (dropdown.children.length > 1) {
                    dropdown.removeChild(dropdown.lastChild);
                }
                
                // Add options for each existing entity
                entities.forEach(entity => {
                    const option = document.createElement('option');
                    option.value = entity.value;
                    option.textContent = entity.label;
                    dropdown.appendChild(option);
                });
            }).catch(error => {
                console.warn(`Failed to load existing entities for ${fieldName}:`, error);
            });
        });
    }

    async fetchExistingEntities(fieldName) {
        // This would typically make an API call to get existing entities
        // For now, return some mock data based on field type
        const mockData = {
            'modality_name': [
                { value: 'Biologics', label: 'Biologics' },
                { value: 'Chemical', label: 'Chemical' },
                { value: 'Small Molecule', label: 'Small Molecule' },
                { value: 'Monoclonal Antibody', label: 'Monoclonal Antibody' },
                { value: 'Advanced Therapy', label: 'Advanced Therapy' }
            ],
            'therapeutic_area': [
                { value: 'Oncology', label: 'Oncology' },
                { value: 'Endocrinology', label: 'Endocrinology' },
                { value: 'Neurology', label: 'Neurology' },
                { value: 'Cardiovascular', label: 'Cardiovascular' },
                { value: 'Metabolic Diseases', label: 'Metabolic Diseases' }
            ],
            'stage_name': [
                { value: 'Chemical Synthesis', label: 'Chemical Synthesis' },
                { value: 'Formulation', label: 'Formulation' },
                { value: 'Fill & Finish', label: 'Fill & Finish' },
                { value: 'Packaging', label: 'Packaging' },
                { value: 'Quality Control', label: 'Quality Control' }
            ]
        };
        
        // In a real implementation, you'd make an API call like:
        // try {
        //     const response = await fetch(`/data-management/api/existing-entities/${fieldName}`);
        //     if (!response.ok) throw new Error(`HTTP ${response.status}`);
        //     return await response.json();
        // } catch (error) {
        //     console.warn(`Failed to load existing entities for ${fieldName}:`, error);
        //     return [];
        // }
        
        return Promise.resolve(mockData[fieldName] || []);
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
        const backendResolutions = this.transformResolutionsForBackend();
        
        console.log('Sending resolutions to backend:', backendResolutions);

        // Send to backend
        this.sendResolutionsToBackend(backendResolutions);
    }

    transformResolutionsForBackend() {
        const backendFormat = {};
        
        // Group resolutions by affected items
        const affectedItems = new Set();
        
        // First, identify all affected items
        document.querySelectorAll('.resolution-group').forEach(group => {
            const field = group.dataset.field;
            const value = group.dataset.value;
            
            // Find items affected by this missing reference
            const affectedElements = group.querySelectorAll('.affected-item');
            affectedElements.forEach(item => {
                const itemText = item.textContent.trim();
                const itemId = itemText.split(' -')[0].trim(); // Extract ID like "BI 456906"
                affectedItems.add(itemId);
            });
        });

        // Create resolution entries for each affected item
        let itemIndex = 0;
        document.querySelectorAll('.affected-item').forEach(affectedItem => {
            const itemText = affectedItem.textContent.trim();
            const itemId = itemText.split(' -')[0].trim();
            
            if (!backendFormat[itemIndex]) {
                backendFormat[itemIndex] = {};
            }
            
            // Find the resolution for the field affecting this item
            const group = affectedItem.closest('.resolution-group');
            const field = group.dataset.field;
            const value = group.dataset.value;
            const resolutionKey = `${field}_${value}`;
            
            if (this.resolutions[resolutionKey]) {
                backendFormat[itemIndex][field] = {
                    type: this.resolutions[resolutionKey].type,
                    value: this.resolutions[resolutionKey].value,
                    metadata: this.resolutions[resolutionKey].metadata || {}
                };
            }
            
            itemIndex++;
        });

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
        // Store the resolved analysis result and redirect to preview
        sessionStorage.setItem('resolved_import_data', JSON.stringify(analysisResult));
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