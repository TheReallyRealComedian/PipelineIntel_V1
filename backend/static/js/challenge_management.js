class ChallengeManager {
    constructor(productId) {
        this.productId = productId;
        this.challenges = {
            inherited: [],
            explicit_relationships: [],
            effective: []
        };
        this.availableChallenges = [];
        
        this.init();
    }
    
    async init() {
        await this.loadChallenges();
        await this.loadAvailableChallenges();
        this.renderChallenges();
        this.bindEvents();
    }
    
    async loadChallenges() {
        try {
            const response = await fetch(`/api/products/${this.productId}/challenges`);
            if (!response.ok) throw new Error('Failed to load challenges');
            this.challenges = await response.json();
        } catch (error) {
            console.error('Failed to load challenges:', error);
            this.showError('Failed to load challenges. Please refresh the page.');
        }
    }
    
    async loadAvailableChallenges() {
        try {
            const response = await fetch('/api/challenges/available');
            if (!response.ok) throw new Error('Failed to load available challenges');
            this.availableChallenges = await response.json();
        } catch (error) {
            console.error('Failed to load available challenges:', error);
        }
    }
    
    renderChallenges() {
        const container = document.querySelector('.challenge-management-container');
        if (!container) return;
        
        const html = `
            <div class="challenge-sections">
                <!-- Inherited Challenges Section -->
                <div class="challenge-section mb-4">
                    <h5 class="section-title">
                        <i class="fas fa-download text-primary"></i>
                        Inherited from Process Template
                        <span class="badge bg-primary ms-2">${this.challenges.inherited.length}</span>
                    </h5>
                    <div class="challenge-list inherited-challenges">
                        ${this.renderInheritedChallenges()}
                    </div>
                </div>
                
                <!-- Product-Specific Challenges Section -->
                <div class="challenge-section mb-4">
                    <h5 class="section-title">
                        <i class="fas fa-plus-circle text-success"></i>
                        Product-Specific Challenges
                        <span class="badge bg-success ms-2">${this.getExplicitChallengesCount()}</span>
                    </h5>
                    <div class="challenge-list explicit-challenges">
                        ${this.renderExplicitChallenges()}
                    </div>
                </div>
                
                <!-- Summary Section -->
                <div class="challenge-summary">
                    <div class="alert alert-info">
                        <strong>Summary:</strong> 
                        ${this.challenges.effective.length} total active challenges 
                        (${this.getActiveChallengesCount()} inherited, 
                        ${this.getExcludedChallengesCount()} excluded, 
                        ${this.getExplicitChallengesCount()} added)
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // Hide loading indicator
        const loadingEl = document.getElementById('challenges-loading');
        if (loadingEl) loadingEl.style.display = 'none';
        
        // Dispatch event to update challenge count in sidebar
        const challengeEvent = new CustomEvent('challengesLoaded', {
            detail: { effectiveCount: this.challenges.effective.length }
        });
        document.dispatchEvent(challengeEvent);
    }
    
    renderInheritedChallenges() {
        if (this.challenges.inherited.length === 0) {
            return '<div class="alert alert-warning">No challenges inherited from process template.</div>';
        }
        
        return this.challenges.inherited.map(challenge => {
            const isExcluded = this.isExcluded(challenge.challenge_id);
            const notes = this.getNotesForChallenge(challenge.challenge_id);
            
            return `
                <div class="challenge-item ${isExcluded ? 'excluded' : ''}" data-challenge-id="${challenge.challenge_id}">
                    <div class="challenge-content">
                        <div class="challenge-header">
                            <div class="challenge-info">
                                <strong class="challenge-name">${challenge.challenge_name}</strong>
                                <span class="badge bg-secondary ms-2">${challenge.challenge_category || 'General'}</span>
                                ${challenge.severity_level ? `<span class="badge bg-warning ms-1">${challenge.severity_level}</span>` : ''}
                            </div>
                            <div class="challenge-controls">
                                <div class="form-check form-switch">
                                    <input class="form-check-input challenge-toggle" type="checkbox" 
                                        ${!isExcluded ? 'checked' : ''} 
                                        data-challenge-id="${challenge.challenge_id}"
                                        id="toggle-${challenge.challenge_id}">
                                    <label class="form-check-label" for="toggle-${challenge.challenge_id}">
                                        ${isExcluded ? 'Excluded' : 'Active'}
                                    </label>
                                </div>
                            </div>
                        </div>
                        ${challenge.short_description ? `
                            <div class="challenge-description text-muted">
                                ${challenge.short_description}
                            </div>
                        ` : ''}
                        ${notes ? `
                            <div class="challenge-notes mt-2">
                                <small class="text-muted">
                                    <strong>Notes:</strong> ${notes}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    renderExplicitChallenges() {
        const explicitChallenges = this.challenges.effective.filter(item => item.source === 'explicit');
        
        if (explicitChallenges.length === 0) {
            return '<div class="text-muted">No product-specific challenges added. <a href="#" id="add-first-challenge">Add one now</a>.</div>';
        }
        
        return explicitChallenges.map(item => {
            return `
                <div class="challenge-item explicit" data-challenge-id="${item.challenge_id}">
                    <div class="challenge-content">
                        <div class="challenge-header">
                            <div class="challenge-info">
                                <strong class="challenge-name">${item.challenge_name}</strong>
                                <span class="badge bg-success ms-2">${item.challenge_category || 'General'}</span>
                                ${item.severity_level ? `<span class="badge bg-warning ms-1">${item.severity_level}</span>` : ''}
                            </div>
                            <div class="challenge-controls">
                                <button class="btn btn-sm btn-outline-danger remove-challenge-btn" 
                                    data-challenge-id="${item.challenge_id}">
                                    <i class="fas fa-times"></i> Remove
                                </button>
                            </div>
                        </div>
                        ${item.notes ? `
                            <div class="challenge-notes mt-2">
                                <small class="text-muted">
                                    <strong>Notes:</strong> ${item.notes}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    bindEvents() {
        // Handle inherited challenge toggles
        document.addEventListener('change', async (e) => {
            if (e.target.classList.contains('challenge-toggle')) {
                const challengeId = parseInt(e.target.dataset.challengeId);
                const isActive = e.target.checked;
                
                e.target.disabled = true; // Prevent multiple clicks
                
                try {
                    if (isActive) {
                        // Remove exclusion (revert to inherited)
                        await this.removeRelationship(challengeId);
                        this.showSuccess('Challenge restored to active status');
                    } else {
                        // Add exclusion
                        await this.excludeChallenge(challengeId);
                        this.showSuccess('Challenge excluded successfully');
                    }
                    
                    await this.loadChallenges();
                    this.renderChallenges();
                } catch (error) {
                    console.error('Failed to toggle challenge:', error);
                    this.showError('Failed to update challenge: ' + error.message);
                    // Revert toggle state
                    e.target.checked = !isActive;
                } finally {
                    e.target.disabled = false;
                }
            }
        });
        
        // Handle explicit challenge removal
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('remove-challenge-btn') || 
                e.target.closest('.remove-challenge-btn')) {
                
                const btn = e.target.classList.contains('remove-challenge-btn') ? 
                    e.target : e.target.closest('.remove-challenge-btn');
                const challengeId = parseInt(btn.dataset.challengeId);
                
                if (confirm('Are you sure you want to remove this product-specific challenge?')) {
                    btn.disabled = true;
                    
                    try {
                        await this.removeRelationship(challengeId);
                        await this.loadChallenges();
                        this.renderChallenges();
                        this.showSuccess('Challenge removed successfully');
                    } catch (error) {
                        console.error('Failed to remove challenge:', error);
                        this.showError('Failed to remove challenge: ' + error.message);
                        btn.disabled = false;
                    }
                }
            }
        });
        
        // Handle add challenge buttons
        document.addEventListener('click', (e) => {
            if (e.target.id === 'add-challenge-btn' || e.target.id === 'add-first-challenge') {
                e.preventDefault();
                this.showAddChallengeModal();
            }
        });
        
        // Handle confirm add challenge
        document.getElementById('confirm-add-challenge')?.addEventListener('click', async () => {
            await this.addChallenge();
        });
    }
    
    async excludeChallenge(challengeId) {
        const notes = prompt('Why doesn\'t this challenge apply to this product?\n\n(This helps with audit trails and future reviews)');
        if (notes === null) {
            throw new Error('Exclusion cancelled by user');
        }
        
        const response = await fetch(`/api/products/${this.productId}/challenges/${challengeId}/exclude`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ notes: notes || 'No reason provided' })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to exclude challenge');
        }
    }
    
    async removeRelationship(challengeId) {
        const response = await fetch(`/api/products/${this.productId}/challenges/${challengeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to remove challenge relationship');
        }
    }
    
    async addChallenge() {
        const challengeSelect = document.getElementById('challenge-select');
        const notesTextarea = document.getElementById('challenge-notes');
        const confirmBtn = document.getElementById('confirm-add-challenge');
        
        const challengeId = parseInt(challengeSelect.value);
        const notes = notesTextarea.value.trim();
        
        if (!challengeId) {
            alert('Please select a challenge to add.');
            return;
        }
        
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        
        try {
            const response = await fetch(`/api/products/${this.productId}/challenges/${challengeId}/include`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notes })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to add challenge');
            }
            
            // Close modal and refresh
            const modalEl = document.getElementById('add-challenge-modal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            
            // Reset form
            challengeSelect.value = '';
            notesTextarea.value = '';
            
            await this.loadChallenges();
            this.renderChallenges();
            this.showSuccess('Challenge added successfully');
            
        } catch (error) {
            this.showError('Failed to add challenge: ' + error.message);
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = 'Add Challenge';
        }
    }
    
    showAddChallengeModal() {
        // Populate challenge options
        const select = document.getElementById('challenge-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Choose a challenge...</option>';
        
        // Get already used challenge IDs to filter them out
        const usedChallengeIds = new Set([
            ...this.challenges.inherited.map(c => c.challenge_id),
            ...this.challenges.effective.map(c => c.challenge_id)
        ]);
        
        // Group challenges by category
        const challengesByCategory = this.availableChallenges
            .filter(challenge => !usedChallengeIds.has(challenge.challenge_id))
            .reduce((acc, challenge) => {
                const category = challenge.challenge_category || 'Other';
                if (!acc[category]) acc[category] = [];
                acc[category].push(challenge);
                return acc;
            }, {});
        
        if (Object.keys(challengesByCategory).length === 0) {
            select.innerHTML = '<option value="">All challenges are already associated with this product</option>';
            document.getElementById('confirm-add-challenge').disabled = true;
        } else {
            document.getElementById('confirm-add-challenge').disabled = false;
            
            Object.keys(challengesByCategory).sort().forEach(category => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = category;
                
                challengesByCategory[category]
                    .sort((a, b) => a.challenge_name.localeCompare(b.challenge_name))
                    .forEach(challenge => {
                        const option = document.createElement('option');
                        option.value = challenge.challenge_id;
                        option.textContent = challenge.challenge_name;
                        optgroup.appendChild(option);
                    });
                
                select.appendChild(optgroup);
            });
        }
        
        // Show modal
        const modalEl = document.getElementById('add-challenge-modal');
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    }
    
    // Helper methods
    isExcluded(challengeId) {
        return this.challenges.explicit_relationships.some(
            rel => rel.challenge_id === challengeId && rel.relationship_type === 'excluded'
        );
    }
    
    getNotesForChallenge(challengeId) {
        const rel = this.challenges.explicit_relationships.find(
            rel => rel.challenge_id === challengeId
        );
        return rel ? rel.notes : null;
    }
    
    getActiveChallengesCount() {
        return this.challenges.effective.filter(item => item.source === 'inherited').length;
    }
    
    getExcludedChallengesCount() {
        return this.challenges.explicit_relationships.filter(rel => rel.relationship_type === 'excluded').length;
    }
    
    getExplicitChallengesCount() {
        return this.challenges.effective.filter(item => item.source === 'explicit').length;
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'danger');
    }
    
    showMessage(message, type) {
        // Create toast or alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of challenge container
        const container = document.querySelector('.challenge-management-container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const productId = window.PRODUCT_ID; // This should be set in the product detail template
    if (productId && document.querySelector('.challenge-management-container')) {
        new ChallengeManager(productId);
    }
});