// Global state
let traceabilityData = null;
let selectedNode = null;
let activeFilters = {
    modality: null,
    template: null,
    challenge: null
};
let pathwayView = 'both'; // 'both', 'process_derived', 'direct'

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    loadTraceabilityData();
    setupEventListeners();
});

// Fetch data from API
async function loadTraceabilityData() {
    try {
        showLoading(true);
        
        // Build query string from active filters
        const params = new URLSearchParams();
        if (activeFilters.modality) params.append('modality_id', activeFilters.modality);
        if (activeFilters.template) params.append('template_id', activeFilters.template);
        if (activeFilters.challenge) params.append('challenge_id', activeFilters.challenge);
        
        const response = await fetch(`/challenge-traceability/api/data?${params}`);
        traceabilityData = await response.json();
        
        renderVisualization();
        showLoading(false);
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load traceability data');
    }
}

// Initialize filter dropdowns
async function initializeFilters() {
    try {
        const response = await fetch('/challenge-traceability/api/filters');
        const filters = await response.json();
        
        populateFilterDropdown('modalityFilter', filters.modalities);
        populateFilterDropdown('templateFilter', filters.templates);
        populateFilterDropdown('challengeFilter', filters.challenges);
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

function populateFilterDropdown(elementId, items) {
    const select = document.getElementById(elementId);
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        select.appendChild(option);
    });
}

// Main rendering function
function renderVisualization() {
    const container = document.getElementById('traceabilityVisualization');
    container.innerHTML = '';
    
    // Create column structure
    const columns = createColumnStructure();
    
    // Group nodes by level
    const nodesByLevel = groupNodesByLevel(traceabilityData.nodes);
    
    // Render each column
    columns.forEach((columnConfig, index) => {
        const column = createColumn(columnConfig, nodesByLevel[index] || []);
        container.appendChild(column);
    });
    
    // Render connections as SVG overlay
    renderConnections();
}

function createColumnStructure() {
    return [
        { id: 'modality', title: 'Modality', level: 0 },
        { id: 'template', title: 'Process Template', level: 1 },
        { id: 'stage', title: 'Process Stage', level: 2 },
        { id: 'technology', title: 'Manufacturing Technology', level: 3 },
        { id: 'challenge', title: 'Manufacturing Challenge', level: 4 }
    ];
}

function groupNodesByLevel(nodes) {
    const grouped = {};
    nodes.forEach(node => {
        if (!grouped[node.level]) grouped[node.level] = [];
        
        // Filter by pathway view
        if (shouldShowNode(node)) {
            grouped[node.level].push(node);
        }
    });
    return grouped;
}

function shouldShowNode(node) {
    if (pathwayView === 'both') return true;
    // Add logic to filter nodes based on pathway type
    return true; // Simplified for now
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
        ${node.badge ? `<span class="node-badge">${node.badge}</span>` : ''}
        ${node.count ? `<div class="node-count text-muted small">${node.count} connections</div>` : ''}
    `;
    
    nodeEl.addEventListener('click', () => handleNodeClick(node));
    
    return nodeEl;
}

function renderConnections() {
    const container = document.getElementById('traceabilityVisualization');
    const containerRect = container.getBoundingClientRect();
    
    // Remove existing SVG if present
    const existingSvg = document.getElementById('connectionsSvg');
    if (existingSvg) existingSvg.remove();
    
    // Create SVG overlay
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'connectionsSvg';
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    container.style.position = 'relative';
    container.appendChild(svg);
    
    // Draw connections
    traceabilityData.links.forEach(link => {
        if (shouldShowLink(link)) {
            drawConnection(svg, link);
        }
    });
}

function shouldShowLink(link) {
    if (pathwayView === 'process_derived') {
        return link.pathway === 'process_derived';
    } else if (pathwayView === 'direct') {
        return link.pathway === 'direct';
    }
    return true; // 'both'
}

function drawConnection(svg, link) {
    const sourceEl = document.querySelector(`[data-node-id="${link.source}"]`);
    const targetEl = document.querySelector(`[data-node-id="${link.target}"]`);
    
    if (!sourceEl || !targetEl) return;
    
    const sourceRect = sourceEl.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    const containerRect = svg.parentElement.getBoundingClientRect();
    
    // Calculate connection points
    const sourceX = sourceRect.right - containerRect.left;
    const sourceY = sourceRect.top + sourceRect.height / 2 - containerRect.top;
    const targetX = targetRect.left - containerRect.left;
    const targetY = targetRect.top + targetRect.height / 2 - containerRect.top;
    
    // Create curved path (cubic bezier)
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const midX = (sourceX + targetX) / 2;
    const d = `M ${sourceX} ${sourceY} C ${midX} ${sourceY}, ${midX} ${targetY}, ${targetX} ${targetY}`;
    
    path.setAttribute('d', d);
    path.classList.add('connection-line');
    path.classList.add(`pathway-${link.pathway}`);
    path.dataset.linkId = `${link.source}-${link.target}`;
    
    svg.appendChild(path);
}

function handleNodeClick(node) {
    // Toggle selection
    if (selectedNode && selectedNode.id === node.id) {
        clearSelection();
        return;
    }
    
    selectedNode = node;
    highlightConnectedPaths(node);
    showNodeDetails(node);
}

function highlightConnectedPaths(node) {
    // Dim all nodes
    document.querySelectorAll('.trace-node').forEach(el => {
        el.classList.add('dimmed');
        el.classList.remove('selected');
    });
    
    // Find all connected nodes
    const connectedNodes = findConnectedNodes(node.id);
    
    // Highlight connected nodes
    connectedNodes.forEach(nodeId => {
        const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeEl) {
            nodeEl.classList.remove('dimmed');
            if (nodeId === node.id) {
                nodeEl.classList.add('selected');
            }
        }
    });
    
    // Highlight relevant connections
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
    
    // Find all nodes connected upstream and downstream
    const findConnections = (currentId, direction = 'both') => {
        traceabilityData.links.forEach(link => {
            if (direction !== 'upstream' && link.source === currentId && !connected.has(link.target)) {
                connected.add(link.target);
                findConnections(link.target, 'downstream');
            }
            if (direction !== 'downstream' && link.target === currentId && !connected.has(link.source)) {
                connected.add(link.source);
                findConnections(link.source, 'upstream');
            }
        });
    };
    
    findConnections(nodeId);
    return Array.from(connected);
}

function clearSelection() {
    selectedNode = null;
    
    // Remove dimmed state from all nodes
    document.querySelectorAll('.trace-node').forEach(el => {
        el.classList.remove('dimmed', 'selected');
    });
    
    // Reset all connections
    document.querySelectorAll('.connection-line').forEach(line => {
        line.classList.remove('highlighted');
        line.style.opacity = '';
    });
    
    // Hide details panel
    document.getElementById('detailsPanel').style.display = 'none';
}

async function showNodeDetails(node) {
    const panel = document.getElementById('detailsPanel');
    const content = document.getElementById('detailsContent');
    
    panel.style.display = 'block';
    content.innerHTML = '<div class="spinner-border"></div>';
    
    try {
        const response = await fetch(`/challenge-traceability/api/node-details/${node.type}/${node.id.split('_')[1]}`);
        const details = await response.json();
        
        content.innerHTML = renderNodeDetails(node, details);
    } catch (error) {
        content.innerHTML = '<div class="alert alert-danger">Failed to load details</div>';
    }
}

function renderNodeDetails(node, details) {
    let html = `
        <h4>${node.name}</h4>
        <p class="text-muted">${node.type}</p>
        <hr>
    `;
    
    // Type-specific details
    switch(node.type) {
        case 'modality':
            html += `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Category:</strong> ${details.category || 'N/A'}
                    </div>
                    <div class="col-md-6">
                        <strong>Process Templates:</strong> ${details.template_count || 0}
                    </div>
                </div>
                <div class="mt-3">
                    <strong>Description:</strong>
                    <p>${details.description || 'No description available'}</p>
                </div>
            `;
            break;
        
        case 'template':
            html += `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Modality:</strong> ${details.modality_name}
                    </div>
                    <div class="col-md-6">
                        <strong>Number of Stages:</strong> ${details.stage_count}
                    </div>
                </div>
            `;
            break;
        
        case 'challenge':
            html += `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Category:</strong> ${details.category}
                    </div>
                    <div class="col-md-6">
                        <strong>Severity:</strong> ${details.severity_level}
                    </div>
                </div>
                <div class="mt-3">
                    <strong>Affected Products:</strong> ${details.product_count || 0}
                </div>
            `;
            break;
        
        // Add cases for other node types
    }
    
    return html;
}

function setupEventListeners() {
    // Filter change handlers
    document.getElementById('modalityFilter').addEventListener('change', (e) => {
        activeFilters.modality = e.target.value || null;
        loadTraceabilityData();
    });
    
    document.getElementById('templateFilter').addEventListener('change', (e) => {
        activeFilters.template = e.target.value || null;
        loadTraceabilityData();
    });
    
    document.getElementById('challengeFilter').addEventListener('change', (e) => {
        activeFilters.challenge = e.target.value || null;
        loadTraceabilityData();
    });
    
    // Reset filters
    document.getElementById('resetFilters').addEventListener('click', () => {
        activeFilters = { modality: null, template: null, challenge: null };
        document.querySelectorAll('.form-select').forEach(select => select.value = '');
        loadTraceabilityData();
    });
    
    // Pathway view switcher
    document.querySelectorAll('input[name="pathwayView"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            pathwayView = e.target.id.replace('view', '').toLowerCase()
                .replace('processderived', 'process_derived')
                .replace('direct', 'direct')
                .replace('both', 'both');
            renderVisualization();
        });
    });
    
    // Close details panel
    document.getElementById('closeDetails').addEventListener('click', clearSelection);
}

// Helper functions
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const viz = document.getElementById('traceabilityVisualization');
    
    if (show) {
        spinner.style.display = 'block';
        viz.style.opacity = '0.5';
    } else {
        spinner.style.display = 'none';
        viz.style.opacity = '1';
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