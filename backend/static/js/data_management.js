// backend/static/js/data_management.js
// Data Management functionality including foreign key resolution and import preview

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all data management components
    initializeForeignKeyResolver();
    initializeImportPreview();
});

// =============================================================================
// FOREIGN KEY RESOLUTION SYSTEM
// =============================================================================

function initializeForeignKeyResolver() {
    const modal = document.getElementById('foreignKeyResolutionModal');
    if (!modal) return;
    
    const resolver = new ForeignKeyResolver();
}

class ForeignKeyResolver {
    constructor() {
        this.resolutions = {};
        this.bindEvents();
    }
    
    bindEvents() {
        // Radio button changes for resolution type
        $(document).on('change', 'input[type="radio"][name^="resolution_"]', function() {
            const container = $(this).closest('.foreign-key-resolution');
            const createNewForm = container.find('.create-new-form');
            const existingSelect = container.find('.existing-entity-select');
            
            if ($(this).val() === 'create_new') {
                createNewForm.show();
                existingSelect.hide();
            } else {
                createNewForm.hide();
                existingSelect.show();
            }
        });
        
        // Apply resolutions button
        $('#applyResolutionsBtn').on('click', () => {
            this.collectResolutions();
            this.applyResolutions();
        });
        
        // Bulk apply buttons
        $(document).on('click', '.bulk-apply-btn', (e) => {
            const field = $(e.target).data('field');
            const missingValue = $(e.target).data('missing-value');
            this.showBulkApplyDialog(field, missingValue);
        });
    }
    
    collectResolutions() {
        this.resolutions = {};
        
        $('.foreign-key-resolution').each((index, element) => {
            const $element = $(element);
            const field = $element.data('field');
            const missingValue = $element.data('missing-value');
            const itemRow = $element.closest('tr').data('item-id');
            
            const selectedRadio = $element.find('input[type="radio"]:checked');
            const resolutionType = selectedRadio.val();
            
            if (!this.resolutions[itemRow]) {
                this.resolutions[itemRow] = {};
            }
            
            if (resolutionType === 'existing') {
                const selectedValue = $element.find('.existing-entity-select').val();
                this.resolutions[itemRow][field] = {
                    type: 'existing',
                    value: selectedValue
                };
            } else if (resolutionType === 'create_new') {
                const newName = $element.find('.new-entity-name').val();
                const newCategory = $element.find('.new-entity-category').val();
                const newDescription = $element.find('.new-entity-description').val();
                
                this.resolutions[itemRow][field] = {
                    type: 'create_new',
                    value: newName,
                    metadata: {
                        category: newCategory,
                        description: newDescription
                    }
                };
            }
        });
        
        console.log('Collected resolutions:', this.resolutions);
    }
    
    applyResolutions() {
        // Show loading state
        $('#applyResolutionsBtn').prop('disabled', true).text('Applying...');
        
        // Get original data from session or global variable
        const originalData = window.originalImportData || [];
        const entityType = window.currentImportEntityType || '';
        
        // Send resolutions to backend
        $.ajax({
            url: '/data-management/resolve-foreign-keys',
            method: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            data: JSON.stringify({
                resolutions: this.resolutions,
                entity_type: entityType,
                original_data: originalData
            }),
            success: (response) => {
                if (response.success) {
                    $('#foreignKeyResolutionModal').modal('hide');
                    
                    // Show success message
                    if (response.created_entities && response.created_entities.length > 0) {
                        showAlert(`Created ${response.created_entities.length} new entities: ${response.created_entities.join(', ')}`, 'success');
                    }
                    
                    // Continue with normal import process
                    this.proceedWithImport(response.analysis_result);
                } else {
                    showAlert('Resolution failed: ' + response.message, 'danger');
                    $('#applyResolutionsBtn').prop('disabled', false).text('Apply Resolutions & Continue Import');
                }
            },
            error: (xhr, status, error) => {
                console.error('Resolution error:', error);
                showAlert('Failed to apply resolutions: ' + error, 'danger');
                $('#applyResolutionsBtn').prop('disabled', false).text('Apply Resolutions & Continue Import');
            }
        });
    }
    
    proceedWithImport(analysisResult) {
        // Store the resolved analysis result and redirect to preview
        sessionStorage.setItem('resolved_import_data', JSON.stringify(analysisResult));
        window.location.href = '/data-management/preview';
    }
    
    showBulkApplyDialog(field, missingValue) {
        // Simple implementation - could be enhanced with a proper modal
        const confirmed = confirm(`Apply the same resolution to all items with missing ${field}: "${missingValue}"?`);
        if (confirmed) {
            // Find the first resolution for this field/value and apply it to all
            $('.foreign-key-resolution').each(function() {
                const $element = $(this);
                if ($element.data('field') === field && $element.data('missing-value') === missingValue) {
                    // Apply the same resolution to all matching items
                    // This is a simplified implementation - could be more sophisticated
                }
            });
        }
    }
}

// =============================================================================
// IMPORT PREVIEW FUNCTIONALITY
// =============================================================================

function initializeImportPreview() {
    const previewContainer = document.querySelector('.import-preview-container');
    if (!previewContainer) return;
    
    const importPreview = new ImportPreview();
}

class ImportPreview {
    constructor() {
        this.previewData = window.previewData || [];
        this.entityType = window.entityType || '';
        this.bindEvents();
        this.initializeBulkActions();
    }
    
    bindEvents() {
        // Individual action radio buttons
        $(document).on('change', '.action-radio', function() {
            const row = $(this).closest('tr');
            const action = $(this).val();
            
            // Update row styling based on action
            row.removeClass('table-success table-warning table-secondary');
            switch(action) {
                case 'add':
                    row.addClass('table-success');
                    break;
                case 'update':
                    row.addClass('table-warning');
                    break;
                case 'skip':
                    row.addClass('table-secondary');
                    break;
            }
        });
        
        // Finalize import button
        $('#finalize-import-btn').on('click', () => {
            this.finalizeImport();
        });
    }
    
    initializeBulkActions() {
        // Bulk action buttons
        $('#bulk-accept-all').on('click', () => {
            $('input[value="add"]:enabled, input[value="update"]:enabled').prop('checked', true).trigger('change');
        });
        
        $('#bulk-skip-all').on('click', () => {
            $('input[value="skip"]').prop('checked', true).trigger('change');
        });
        
        $('#bulk-add-new').on('click', () => {
            $('input[value="add"]:enabled').prop('checked', true).trigger('change');
        });
        
        $('#bulk-update-existing').on('click', () => {
            $('input[value="update"]:enabled').prop('checked', true).trigger('change');
        });
    }
    
    finalizeImport() {
        // Collect resolved data
        const resolvedData = [];
        
        $('.preview-row').each(function(index) {
            const $row = $(this);
            const selectedAction = $row.find('.action-radio:checked').val();
            const originalItem = window.previewData[index];
            
            resolvedData.push({
                action: selectedAction,
                data: originalItem.json_item,
                identifier: originalItem.identifier,
                original_index: index
            });
        });
        
        // Show loading state
        $('#finalize-import-btn').prop('disabled', true).text('Importing...');
        $('#log-container').show();
        $('#log-output').text('Starting import process...\n');
        
        // Send to backend
        $.ajax({
            url: '/data-management/finalize',
            method: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            data: JSON.stringify({
                resolved_data: resolvedData,
                entity_type: this.entityType
            }),
            success: (response) => {
                this.handleImportResult(response);
            },
            error: (xhr, status, error) => {
                console.error('Import error:', error);
                $('#log-output').append(`\nERROR: Import failed - ${error}\n`);
                $('#finalize-import-btn').prop('disabled', false).text('Finalize Import');
            }
        });
    }
    
    handleImportResult(response) {
        const logOutput = $('#log-output');
        
        if (response.success) {
            // Show detailed logs if available
            if (response.detailed_logs && response.detailed_logs.length > 0) {
                logOutput.append('\n' + response.detailed_logs.join('\n') + '\n');
            } else {
                // Fallback to summary
                logOutput.append(`\nImport completed successfully!\n`);
                logOutput.append(`Added: ${response.added_count || response.success_count} items\n`);
                logOutput.append(`Updated: ${response.updated_count || 0} items\n`);
                logOutput.append(`Skipped: ${response.skipped_count || 0} items\n`);
            }
            
            if (response.failed_count > 0 || response.error_count > 0) {
                logOutput.append(`Failed: ${response.failed_count || response.error_count} items\n`);
                if (response.error_messages || response.errors) {
                    logOutput.append(`Errors:\n${(response.error_messages || response.errors).join('\n')}\n`);
                }
            }
            
            // Add completion message with navigation hint
            logOutput.append(`\n${'='*60}\nImport completed! You can review the logs above.\n${'='*60}\n`);
            
            // Show success message
            showAlert(`Import completed! Added: ${response.added_count || response.success_count}, Updated: ${response.updated_count || 0}, Skipped: ${response.skipped_count || 0}`, 'success');
            
            // REMOVED: Auto-redirect - let user review logs
            // Instead, re-enable the button and change its text
            $('#finalize-import-btn').prop('disabled', false).text('Back to Data Management').off('click').on('click', function() {
                window.location.href = '/data-management';
            });
            
        } else {
            // Show detailed logs for failures too
            if (response.detailed_logs && response.detailed_logs.length > 0) {
                logOutput.append('\n' + response.detailed_logs.join('\n') + '\n');
            }
            logOutput.append(`\nImport failed: ${response.message}\n`);
            showAlert('Import failed: ' + response.message, 'danger');
            $('#finalize-import-btn').prop('disabled', false).text('Finalize Import');
        }
    }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function getCSRFToken() {
    return document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
}

function showAlert(message, type = 'info') {
    // Create Bootstrap alert
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Insert at top of main content
    const mainContent = document.querySelector('.container, .container-fluid, main');
    if (mainContent) {
        mainContent.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                const alert = mainContent.querySelector('.alert-success');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
}

// Make key functions available globally if needed
window.dataManagement = {
    showAlert: showAlert,
    getCSRFToken: getCSRFToken
};