// backend/static/js/challenge_traceability.js

// Global state
let allModalities = [];
let allTemplates = [];
let currentModality = null;
let currentTemplate = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeModalities();
});

// Initialize modality boxes
async function initializeModalities() {
    try {
        const response = await fetch('/challenge-traceability/api/filters');
        const filters = await response.json();
        allModalities = filters.modalities;
        renderModalityBoxes();
    } catch (error) {
        console.error('Error loading modalities:', error);
        showModalityError();
    }
}

// Render modality boxes
function renderModalityBoxes() {
    const container = document.getElementById('modalityBoxes');
    
    if (!allModalities || allModalities.length === 0) {
        container.innerHTML = '<div class="loading-message">No modalities available</div>';
        return;
    }
    
    container.innerHTML = '';
    
    allModalities.forEach(modality => {
        const box = document.createElement('div');
        box.className = 'selection-box';
        box.textContent = modality.name;
        box.dataset.modalityId = modality.id;
        box.dataset.modalityName = modality.name;
        
        box.addEventListener('click', () => selectModality(modality.id, modality.name));
        
        container.appendChild(box);
    });
}

// Handle modality selection
async function selectModality(modalityId, modalityName) {
    // Update selected state
    document.querySelectorAll('#modalityBoxes .selection-box').forEach(box => {
        box.classList.remove('selected');
    });
    
    const selectedBox = document.querySelector(`#modalityBoxes .selection-box[data-modality-id="${modalityId}"]`);
    if (selectedBox) {
        selectedBox.classList.add('selected');
    }
    
    currentModality = { id: modalityId, name: modalityName };
    
    // Load templates for this modality
    await loadTemplates(modalityId);
}

// Load templates for selected modality
async function loadTemplates(modalityId) {
    const container = document.getElementById('templateBoxes');
    container.innerHTML = '<div class="loading-message">Loading templates...</div>';
    
    try {
        const response = await fetch(`/challenge-traceability/api/templates-by-modality/${modalityId}`);
        allTemplates = await response.json();
        
        renderTemplateBoxes();
        
        // Auto-select first template if available
        if (allTemplates && allTemplates.length > 0) {
            selectTemplate(allTemplates[0].id, allTemplates[0].name);
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        container.innerHTML = '<div class="loading-message">Error loading templates</div>';
    }
}

// Render template boxes
function renderTemplateBoxes() {
    const container = document.getElementById('templateBoxes');
    
    if (!allTemplates || allTemplates.length === 0) {
        container.innerHTML = '<div class="placeholder-message">No templates available for this modality</div>';
        return;
    }
    
    container.innerHTML = '';
    
    allTemplates.forEach(template => {
        const box = document.createElement('div');
        box.className = 'selection-box template-box';
        box.textContent = template.name;
        box.dataset.templateId = template.id;
        box.dataset.templateName = template.name;
        
        box.addEventListener('click', () => selectTemplate(template.id, template.name));
        
        container.appendChild(box);
    });
}

// Handle template selection
function selectTemplate(templateId, templateName) {
    // Update selected state
    document.querySelectorAll('#templateBoxes .selection-box').forEach(box => {
        box.classList.remove('selected');
    });
    
    const selectedBox = document.querySelector(`#templateBoxes .selection-box[data-template-id="${templateId}"]`);
    if (selectedBox) {
        selectedBox.classList.add('selected');
    }
    
    currentTemplate = { id: templateId, name: templateName };
    
    // Automatically visualize the pathway
    loadTraceabilityData();
}

// Fetch data from API
async function loadTraceabilityData() {
    showLoading(true);

    try {
        const params = new URLSearchParams({
            modality_id: currentModality.id,
            template_id: currentTemplate.id
        });
        
        const response = await fetch(`/challenge-traceability/api/data?${params}`);
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
        } else {
            renderVisualization(data);
        }
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load traceability data. Please check the server logs.');
    } finally {
        showLoading(false);
    }
}

// Main rendering function for the hierarchical view
function renderVisualization(data) {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = '';
    
    if (!data || data.length === 0) {
        showError("No process stages or challenges found for this template.");
        return;
    }

    const flowContainer = document.createElement('div');
    flowContainer.className = 'traceability-flow-container';

    data.forEach(phase => {
        const phaseEl = document.createElement('div');
        phaseEl.className = 'process-phase';
        
        const phaseName = phase.phase_name || 'Unnamed Phase';
        
        phaseEl.innerHTML = `
            <div class="phase-header">
                <i class="fas fa-layer-group"></i> ${phaseName}
            </div>
            <div class="phase-content"></div>
        `;

        const phaseContent = phaseEl.querySelector('.phase-content');

        if (phase.stages && phase.stages.length > 0) {
            phase.stages.forEach(stage => {
                const stageGroup = document.createElement('div');
                stageGroup.className = 'stage-group';
                
                const stageName = stage.stage_name || 'Unnamed Stage';
                
                // Create stage title
                const stageTitleDiv = document.createElement('div');
                stageTitleDiv.className = 'stage-title';
                stageTitleDiv.textContent = stageName;
                stageGroup.appendChild(stageTitleDiv);
                
                if (stage.technologies && stage.technologies.length > 0) {
                    // This is the new structure
                    const techChallengeDiv = document.createElement('div');
                    techChallengeDiv.className = 'tech-challenge-grid';

                    const technologiesContainer = document.createElement('div');
                    technologiesContainer.className = 'technologies-container';

                    const challengesContainer = document.createElement('div');
                    challengesContainer.className = 'challenges-container';

                   stage.technologies.forEach(tech => {
                        const techName = tech.tech_name || 'Unnamed Technology';
                        const techDescription = tech.tech_short_description || 'No description available';
                        
                        const techCard = document.createElement('div');
                        techCard.className = 'traceability-card tech-card';
                        techCard.textContent = techName;
                        
                        // Add tooltip functionality
                        if (techDescription && techDescription.trim() !== '') {
                            techCard.setAttribute('title', techDescription);
                            techCard.setAttribute('data-bs-toggle', 'tooltip');
                            techCard.setAttribute('data-bs-placement', 'top');
                            // Add a small info icon to indicate there's more info
                            techCard.innerHTML = `${techName} <i class="fas fa-info-circle info-icon"></i>`;
                        }
                        
                        technologiesContainer.appendChild(techCard);

                        if (tech.challenges && tech.challenges.length > 0) {
                            tech.challenges.forEach(ch => {
                                const challengeName = ch.challenge_name || 'Unnamed Challenge';
                                const challengeDescription = ch.challenge_short_description || 'No description available';
                                const severityLevel = ch.severity_level || 'unknown';
                                
                                const challengeCard = document.createElement('div');
                                challengeCard.className = 'traceability-card challenge-card';
                                challengeCard.textContent = challengeName;
                                
                                // Add tooltip functionality for challenges
                                if (challengeDescription && challengeDescription.trim() !== '') {
                                    // Create a richer tooltip with description and severity
                                    const tooltipText = `${challengeDescription} (Severity: ${severityLevel})`;
                                    challengeCard.setAttribute('title', tooltipText);
                                    challengeCard.setAttribute('data-bs-toggle', 'tooltip');
                                    challengeCard.setAttribute('data-bs-placement', 'top');
                                    // Add a small info icon to indicate there's more info
                                    challengeCard.innerHTML = `${challengeName} <i class="fas fa-info-circle info-icon"></i>`;
                                }
                                
                                challengesContainer.appendChild(challengeCard);
                            });
                        }
                    });
                    
                    if (challengesContainer.childElementCount === 0) {
                        const emptyState = document.createElement('span');
                        emptyState.className = 'empty-state';
                        emptyState.textContent = 'No challenges';
                        challengesContainer.appendChild(emptyState);
                    }

                    techChallengeDiv.appendChild(technologiesContainer);
                    techChallengeDiv.appendChild(challengesContainer);
                    stageGroup.appendChild(techChallengeDiv);

                } else {
                    const emptyDiv = document.createElement('div');
                    emptyDiv.className = 'empty-state';
                    emptyDiv.textContent = 'No technologies defined for this stage';
                    stageGroup.appendChild(emptyDiv);
                }
                
                phaseContent.appendChild(stageGroup);
            });
        }
        
        flowContainer.appendChild(phaseEl);
    });

    container.appendChild(flowContainer);
    
    // Initialize Bootstrap tooltips for all cards with tooltip data
    const tooltipTriggerList = container.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {
        delay: { show: 300, hide: 100 },
        trigger: 'hover focus'
    }));
}

// Show loading state
function showLoading(isLoading) {
    const container = document.getElementById('traceabilityVisualization');
    if (isLoading) {
        container.innerHTML = `
            <div class="card card-body text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading traceability data...</p>
            </div>
        `;
    }
}

// Show error message
function showError(message) {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Notice:</strong> ${message}
        </div>
    `;
}

// Show modality loading error
function showModalityError() {
    const container = document.getElementById('modalityBoxes');
    container.innerHTML = '<div class="loading-message">Error loading modalities. Please refresh the page.</div>';
}