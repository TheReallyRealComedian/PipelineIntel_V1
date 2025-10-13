// Global state
let traceabilityData = null;
let selectedNode = null;
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
        // Template will be populated when modality is selected
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

function populateFilterDropdown(elementId, items) {
    const select = document.getElementById(elementId);
    // Clear existing options except the first placeholder
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        select.appendChild(option);
    });
}

// Setup all event listeners
function setupEventListeners() {
    // Modality change - cascade to template dropdown
    document.getElementById('modalityFilter').addEventListener('change', async (e) => {
        const modalityId = e.target.value;
        const templateSelect = document.getElementById('templateFilter');
        const visualizeBtn = document.getElementById('visualizeButton');
        
        if (modalityId) {
            // Enable template dropdown and fetch templates for this modality
            templateSelect.disabled = false;
            
            try {
                const response = await fetch(`/challenge-traceability/api/templates-by-modality/${modalityId}`);
                const templates = await response.json();
                
                populateFilterDropdown('templateFilter', templates);
                
                // Update stored modality
                currentModality = {
                    id: modalityId,
                    name: e.target.options[e.target.selectedIndex].text
                };
            } catch (error) {
                console.error('Error loading templates:', error);
            }
        } else {
            // Reset template dropdown
            templateSelect.disabled = true;
            templateSelect.value = '';
            visualizeBtn.disabled = true;
            currentModality = null;
            currentTemplate = null;
            clearVisualization();
        }
    });
    
    // Template change - enable visualize button
    document.getElementById('templateFilter').addEventListener('change', (e) => {
        const templateId = e.target.value;
        const visualizeBtn = document.getElementById('visualizeButton');
        
        if (templateId && currentModality) {
            visualizeBtn.disabled = false;
            currentTemplate = {
                id: templateId,
                name: e.target.options[e.target.selectedIndex].text
            };
        } else {
            visualizeBtn.disabled = true;
            currentTemplate = null;
        }
    });
    
    // Visualize button - load and render data
    document.getElementById('visualizeButton').addEventListener('click', () => {
        if (currentModality && currentTemplate) {
            loadTraceabilityData();
        }
    });
    
    // Close details panel
    const closeBtn = document.getElementById('closeDetails');
    if (closeBtn) {
        closeBtn.addEventListener('click', clearSelection);
    }
}

// Fetch data from API
async function loadTraceabilityData() {
    try {
        showLoading(true);
        
        const params = new URLSearchParams({
            modality_id: currentModality.id,
            template_id: currentTemplate.id
        });
        
        const response = await fetch(`/challenge-traceability/api/data?${params}`);
        traceabilityData = await response.json();
        
        if (traceabilityData.error) {
            showError(traceabilityData.error);
            return;
        }
        
        // Show context display
        updateContextDisplay();
        
        renderVisualization();
        showLoading(false);
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load traceability data');
    }
}

function updateContextDisplay() {
    const display = document.getElementById('contextDisplay');
    document.getElementById('selectedModalityName').textContent = currentModality.name;
    document.getElementById('selectedTemplateName').textContent = currentTemplate.name;
    display.style.display = 'block';
}

// Main rendering function
function renderVisualization() {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = '';
    
    if (!traceabilityData || !traceabilityData.nodes || traceabilityData.nodes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h5>No Data Available</h5>
                <p>No challenge traceability data found for this selection.</p>
            </div>
        `;
        return;
    }
    
    // Create wrapper with horizontal layout
    const wrapper = document.createElement('div');
    wrapper.className = 'traceability-container';
    
    // Create three columns: Stage, Technology, Challenge
    const columns = createColumnStructure();
    const nodesByLevel = groupNodesByLevel(traceabilityData.nodes);
    
    columns.forEach((columnConfig) => {
        const column = createColumn(columnConfig, nodesByLevel[columnConfig.level] || []);
        wrapper.appendChild(column);
    });
    
    container.appendChild(wrapper);
    
    // Render connections as SVG overlay
    renderConnections();
}

function createColumnStructure() {
    return [
        { id: 'stage', title: 'Process Stage', level: 0 },
        { id: 'technology', title: 'Manufacturing Technology', level: 1 },
        { id: 'challenge', title: 'Manufacturing Challenge', level: 2 }
    ];
}

function groupNodesByLevel(nodes) {
    const grouped = {};
    nodes.forEach(node => {
        if (!grouped[node.level]) grouped[node.level] = [];
        grouped[node.level].push(node);
    });
    return grouped;
}

function createColumn(config, nodes) {
    const column = document.createElement('div');
    column.className = 'traceability-column';
    column.dataset.level = config.level;
    
    const header = document.createElement('div');
    header.className = 'column-header';
    header.textContent = config.title;
    column.appendChild(header);
    
    const nodesContainer = document.createElement('div');
    nodesContainer.className = 'nodes-container';
    
    nodes.forEach(node => {
        const nodeElement = createNodeElement(node);
        nodesContainer.appendChild(nodeElement);
    });
    
    column.appendChild(nodesContainer);
    return column;
}

function createNodeElement(node) {
    const nodeEl = document.createElement('div');
    nodeEl.className = 'trace-node';
    nodeEl.dataset.nodeId = node.id;
    nodeEl.dataset.nodeType = node.type;
    
    nodeEl.innerHTML = `
        <div class="node-name">${node.name}</div>
        ${node.badge ? `<div class="node-badge">${node.badge}</div>` : ''}
    `;
    
    nodeEl.addEventListener('click', () => handleNodeClick(node));
    
    return nodeEl;
}

// Connection rendering (horizontal flow)
function renderConnections() {
    const container = document.querySelector('.traceability-container');
    if (!container) return;
    
    const existingSvg = document.getElementById('connectionsSvg');
    if (existingSvg) existingSvg.remove();
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'connectionsSvg';
    container.appendChild(svg);
    
    traceabilityData.links.forEach(link => {
        drawConnection(svg, link);
    });
}

function drawConnection(svg, link) {
    const sourceEl = document.querySelector(`[data-node-id="${link.source}"]`);
    const targetEl = document.querySelector(`[data-node-id="${link.target}"]`);
    
    if (!sourceEl || !targetEl) return;
    
    const containerRect = svg.parentElement.getBoundingClientRect();
    const sourceRect = sourceEl.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    
    // Calculate connection points (horizontal flow: right side of source to left side of target)
    const sourceX = sourceRect.right - containerRect.left;
    const sourceY = sourceRect.top + sourceRect.height / 2 - containerRect.top;
    const targetX = targetRect.left - containerRect.left;
    const targetY = targetRect.top + targetRect.height / 2 - containerRect.top;
    
    // Create horizontal curved path
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const midX = (sourceX + targetX) / 2;
    const d = `M ${sourceX} ${sourceY} C ${midX} ${sourceY}, ${midX} ${targetY}, ${targetX} ${targetY}`;
    
    path.setAttribute('d', d);
    path.classList.add('connection-line');
    path.dataset.linkId = `${link.source}-${link.target}`;
    
    svg.appendChild(path);
}

// Node interaction
function handleNodeClick(node) {
    if (selectedNode && selectedNode.id === node.id) {
        clearSelection();
        return;
    }
    
    selectedNode = node;
    highlightConnectedPaths(node);
    showNodeDetails(node);
}

function highlightConnectedPaths(node) {
    document.querySelectorAll('.trace-node').forEach(el => {
        el.classList.add('dimmed');
        el.classList.remove('selected');
    });
    
    const connectedNodes = findConnectedNodes(node.id);
    
    connectedNodes.forEach(nodeId => {
        const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeEl) {
            nodeEl.classList.remove('dimmed');
            if (nodeId === node.id) {
                nodeEl.classList.add('selected');
            }
        }
    });
    
    document.querySelectorAll('.connection-line').forEach(line => {
        const linkId = line.dataset.linkId;
        const [source, target] = linkId.split('-');
        
        if (connectedNodes.includes(source) && connectedNodes.includes(target)) {
            line.classList.add('highlighted');
        } else {
            line.style.opacity = '0.1';
        }
    });
}

function findConnectedNodes(nodeId) {
    const connected = new Set([nodeId]);
    
    const findConnections = (currentId) => {
        traceabilityData.links.forEach(link => {
            if (link.source === currentId && !connected.has(link.target)) {
                connected.add(link.target);
                findConnections(link.target);
            }
            if (link.target === currentId && !connected.has(link.source)) {
                connected.add(link.source);
                findConnections(link.source);
            }
        });
    };
    
    findConnections(nodeId);
    return Array.from(connected);
}

async function showNodeDetails(node) {
    const panel = document.getElementById('detailsPanel');
    const content = document.getElementById('detailsContent');
    
    panel.style.display = 'block';
    content.innerHTML = '<div class="spinner-border"></div>';
    
    try {
        const nodeIdNum = node.id.split('_')[1];
        const response = await fetch(`/challenge-traceability/api/node-details/${node.type}/${nodeIdNum}`);
        const details = await response.json();
        
        content.innerHTML = renderNodeDetails(node, details);
    } catch (error) {
        content.innerHTML = '<div class="alert alert-danger">Failed to load details</div>';
    }
}

function renderNodeDetails(node, details) {
    return `
        <h4>${node.name}</h4>
        <p class="text-muted">${node.type}</p>
        <hr>
        <pre>${JSON.stringify(details, null, 2)}</pre>
    `;
}

function clearSelection() {
    selectedNode = null;
    
    document.querySelectorAll('.trace-node').forEach(el => {
        el.classList.remove('dimmed', 'selected');
    });
    
    document.querySelectorAll('.connection-line').forEach(line => {
        line.classList.remove('highlighted');
        line.style.opacity = '';
    });
    
    document.getElementById('detailsPanel').style.display = 'none';
}

function clearVisualization() {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = '';
    document.getElementById('contextDisplay').style.display = 'none';
}

function showLoading(show) {
    const container = document.getElementById('traceabilityVisualization');
    if (show) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading traceability data...</p>
            </div>
        `;
    }
}

function showError(message) {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
}