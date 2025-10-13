// Global state
let currentModality = null;
let currentTemplate = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    setupEventListeners();
});

// Initialize filter dropdowns
async function initializeFilters() {
    try {
        const response = await fetch('/challenge-traceability/api/filters');
        const filters = await response.json();
        populateFilterDropdown('modalityFilter', filters.modalities);
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

function populateFilterDropdown(elementId, items) {
    const select = document.getElementById(elementId);
    while (select.options.length > 1) {
        select.remove(1);
    }
    items.forEach(item => {
        const option = new Option(item.name, item.id);
        select.appendChild(option);
    });
}

// Setup all event listeners
function setupEventListeners() {
    document.getElementById('modalityFilter').addEventListener('change', async (e) => {
        const modalityId = e.target.value;
        const templateSelect = document.getElementById('templateFilter');
        const visualizeBtn = document.getElementById('visualizeButton');
        
        if (modalityId) {
            templateSelect.disabled = false;
            templateSelect.options[0].textContent = 'Loading templates...';
            try {
                const response = await fetch(`/challenge-traceability/api/templates-by-modality/${modalityId}`);
                const templates = await response.json();
                templateSelect.options[0].textContent = '-- Select Template --';
                populateFilterDropdown('templateFilter', templates);
                currentModality = { id: modalityId, name: e.target.options[e.target.selectedIndex].text };
            } catch (error) {
                console.error('Error loading templates:', error);
            }
        } else {
            templateSelect.disabled = true;
            templateSelect.value = '';
            templateSelect.options[0].textContent = '-- First select a modality --';
            visualizeBtn.disabled = true;
            currentModality = null;
            currentTemplate = null;
        }
    });
    
    document.getElementById('templateFilter').addEventListener('change', (e) => {
        const templateId = e.target.value;
        const visualizeBtn = document.getElementById('visualizeButton');
        
        if (templateId && currentModality) {
            visualizeBtn.disabled = false;
            currentTemplate = { id: templateId, name: e.target.options[e.target.selectedIndex].text };
        } else {
            visualizeBtn.disabled = true;
            currentTemplate = null;
        }
    });
    
    document.getElementById('visualizeButton').addEventListener('click', () => {
        if (currentModality && currentTemplate) {
            loadTraceabilityData();
        }
    });
}

// Fetch data from API
async function loadTraceabilityData() {
    showLoading(true);
    updateContextDisplay();

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

function updateContextDisplay() {
    const display = document.getElementById('contextDisplay');
    document.getElementById('selectedModalityName').textContent = currentModality.name;
    document.getElementById('selectedTemplateName').textContent = currentTemplate.name;
    display.style.display = 'block';
}

// Main rendering function for the new hierarchical view
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
        
        phaseEl.innerHTML = `
            <div class="phase-header">
                <i class="fas fa-layer-group"></i> ${phase.phase_name}
            </div>
            <div class="phase-content"></div>
        `;

        const phaseContent = phaseEl.querySelector('.phase-content');

        if (phase.stages && phase.stages.length > 0) {
            phase.stages.forEach(stage => {
                const stageGroup = document.createElement('div');
                stageGroup.className = 'stage-group';
                
                let stageHTML = `<div class="stage-title">${stage.stage_name}</div>`;
                
                if (stage.technologies && stage.technologies.length > 0) {
                    stage.technologies.forEach(tech => {
                        let challengesHTML = tech.challenges.map(chal => 
                            `<div class="challenge-card">${chal.challenge_name}</div>`
                        ).join('');

                        if (tech.challenges.length === 0) {
                           challengesHTML = `<div class="text-muted small">No challenges for this technology.</div>`
                        }

                        stageHTML += `
                            <div class="tech-challenge-grid">
                                <div class="tech-card">${tech.tech_name}</div>
                                <div class="challenges-container">${challengesHTML}</div>
                            </div>
                        `;
                    });
                } else {
                    stageHTML += `<div class="empty-state">No manufacturing technologies defined for this stage in the template.</div>`;
                }
                stageGroup.innerHTML = stageHTML;
                phaseContent.appendChild(stageGroup);
            });
        } else {
            phaseContent.innerHTML = `<div class="empty-state">No process stages defined for this phase in the template.</div>`;
        }

        flowContainer.appendChild(phaseEl);
    });

    container.appendChild(flowContainer);
}

function showLoading(isLoading) {
    const container = document.getElementById('traceabilityVisualization');
    if (isLoading) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Building traceability flow...</p>
            </div>
        `;
    } 
}

function showError(message) {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i> ${message}
        </div>
    `;
}