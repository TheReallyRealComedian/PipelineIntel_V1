/**
 * Pipeline Timeline Visualization
 * 
 * Interactive timeline for visualizing pharmaceutical pipeline with configurable
 * axes (year/phase), groupings (modality/therapeutic area), and display modes.
 */

class PipelineTimeline {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.config = this.getDefaultConfig();
        this.data = null;
        this.savedViews = this.loadSavedViews();
    }

    /**
     * Returns the default configuration for the timeline
     */
    getDefaultConfig() {
        return {
            timelineMode: 'year',           // 'year' | 'phase'
            yearSegmentPreset: 'individual', // 'individual' | 'grouped' | 'custom'
            customSegments: [],              // Array of {label, yearStart, yearEnd}
            groupingMode: 'modality',        // 'modality' | 'therapeutic_area' | 'product_type' | 'none'
            elementType: 'product',          // 'product' | 'modality'
            colorBy: 'modality',             // What determines color
            filters: {}                      // Additional filters
        };
    }

    /**
     * Gets the current configuration from the UI controls
     */
    getCurrentConfig() {
        const config = {
            timelineMode: document.getElementById('timelineMode').value,
            groupingMode: document.getElementById('groupingMode').value,
            elementType: document.getElementById('elementType').value,
            colorBy: 'modality', // We'll add this control later
            filters: {}
        };

        // Get year segment configuration if in year mode
        if (config.timelineMode === 'year') {
            const activePreset = document.querySelector('[data-preset].active');
            config.yearSegmentPreset = activePreset ? activePreset.dataset.preset : 'individual';
            
            if (config.yearSegmentPreset === 'custom') {
                config.customSegments = this.getCustomSegments();
            }
        }

        return config;
    }

    /**
     * Gets custom segment configuration from UI
     * (Placeholder for now - we'll implement the builder in next step)
     */
    getCustomSegments() {
        // For now, return empty array
        // We'll add the segment builder UI in the next step
        return [];
    }

    /**
     * Main method to load data and render the timeline
     */
    async loadAndRender() {
        try {
            this.showLoading(true);
            
            // Get current configuration
            this.config = this.getCurrentConfig();
            
            // Fetch data from backend
            this.data = await this.fetchTimelineData(this.config);
            
            // Render the timeline
            this.render();
            
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading timeline:', error);
            this.showError('Failed to load timeline data: ' + error.message);
            this.showLoading(false);
        }
    }

    /**
     * Fetches timeline data from the backend API
     */
    async fetchTimelineData(config) {
        const response = await fetch('/analytics/api/pipeline-timeline-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Main rendering method
     */
    render() {
        if (!this.data) {
            this.container.innerHTML = '<div class="alert alert-warning">No data to display</div>';
            return;
        }

        // Clear container
        this.container.innerHTML = '';

        // Render timeline header
        this.renderTimelineHeader();

        // Render swim lanes
        this.renderSwimLanes();

        // Attach interactivity
        this.attachEventListeners();
    }

    /**
     * Renders the timeline header (year/phase labels)
     */
    renderTimelineHeader() {
        const header = document.createElement('div');
        header.className = 'timeline-header';
        header.innerHTML = `
            <div class="timeline-header-container">
                <div class="timeline-label-column">
                    <span class="fw-bold">${this.getGroupingLabel()}</span>
                </div>
                <div class="timeline-axis-container">
                    ${this.data.timeline_units.map(unit => `
                        <div class="timeline-unit-header">
                            ${this.formatTimelineUnit(unit)}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        this.container.appendChild(header);
    }

    /**
     * Renders all swim lanes with their elements
     */
    renderSwimLanes() {
        const lanesContainer = document.createElement('div');
        lanesContainer.className = 'timeline-lanes-container';

        if (this.config.groupingMode === 'none') {
            // Single lane with all elements
            lanesContainer.appendChild(this.renderSwimLane({
                group_name: 'All Products',
                elements: this.data.elements || []
            }));
        } else {
            // Multiple swim lanes
            this.data.swim_lanes.forEach(lane => {
                lanesContainer.appendChild(this.renderSwimLane(lane));
            });
        }

        this.container.appendChild(lanesContainer);
    }

    /**
     * Renders a single swim lane
     */
    renderSwimLane(laneData) {
        const lane = document.createElement('div');
        lane.className = 'timeline-lane';
        
        const laneHeader = document.createElement('div');
        laneHeader.className = 'timeline-lane-header';
        laneHeader.innerHTML = `
            <div class="lane-label">
                <span class="lane-name">${laneData.group_name}</span>
                <span class="lane-count badge bg-secondary">${laneData.elements.length}</span>
            </div>
        `;

        const laneContent = document.createElement('div');
        laneContent.className = 'timeline-lane-content';

        // Create grid for timeline units
        const grid = document.createElement('div');
        grid.className = 'timeline-grid';
        
        // Create cells for each timeline unit
        this.data.timeline_units.forEach(unit => {
            const cell = document.createElement('div');
            cell.className = 'timeline-cell';
            cell.dataset.unit = unit;

            // Find elements that belong in this cell
            const elementsInCell = laneData.elements.filter(el => 
                this.isElementInTimelineUnit(el, unit)
            );

            // Render elements in this cell
            elementsInCell.forEach(element => {
                cell.appendChild(this.renderElement(element));
            });

            grid.appendChild(cell);
        });

        laneContent.appendChild(grid);
        lane.appendChild(laneHeader);
        lane.appendChild(laneContent);

        return lane;
    }

    /**
     * Renders a single element (product or modality box)
     */
    renderElement(element) {
        const box = document.createElement('div');
        box.className = `timeline-element ${element.type}`;
        box.dataset.id = element.id;
        box.dataset.type = element.type;
        
        // Apply visual styling from backend
        if (element.visual) {
            box.style.backgroundColor = element.visual.color || '#6c757d';
            box.style.borderColor = this.darkenColor(element.visual.color || '#6c757d');
        }

        box.innerHTML = `
            <div class="element-content">
                ${element.visual && element.visual.icon ? 
                    `<i class="${element.visual.icon}"></i>` : ''}
                <span class="element-label">${element.visual ? element.visual.label : element.id}</span>
                ${element.count > 1 ? 
                    `<span class="element-count badge">${element.count}</span>` : ''}
            </div>
        `;

        // Add tooltip
        box.title = this.generateTooltip(element);

        return box;
    }

    /**
     * Determines if an element belongs in a specific timeline unit
     */
    isElementInTimelineUnit(element, unit) {
        if (this.config.timelineMode === 'phase') {
            return element.position === unit;
        } else {
            // Year-based positioning
            return element.position === unit;
        }
    }

    /**
     * Formats a timeline unit for display
     */
    formatTimelineUnit(unit) {
        if (this.config.timelineMode === 'phase') {
            return unit; // e.g., "Phase I"
        } else {
            return unit.toString(); // e.g., "2025"
        }
    }

    /**
     * Gets the label for the grouping column
     */
    getGroupingLabel() {
        const labels = {
            'modality': 'Modality',
            'therapeutic_area': 'Therapeutic Area',
            'product_type': 'Product Type',
            'none': 'Products'
        };
        return labels[this.config.groupingMode] || 'Group';
    }

    /**
     * Generates tooltip text for an element
     */
    generateTooltip(element) {
        let tooltip = element.data.product_name || element.data.modality_name || element.id;
        
        if (element.type === 'product') {
            tooltip += `\nPhase: ${element.data.current_phase || 'N/A'}`;
            tooltip += `\nLaunch: ${element.data.expected_launch_year || 'TBD'}`;
        }
        
        if (element.count > 1) {
            tooltip += `\n(${element.count} products)`;
        }

        return tooltip;
    }

    /**
     * Attaches click handlers to elements
     */
    attachEventListeners() {
        this.container.querySelectorAll('.timeline-element').forEach(element => {
            element.addEventListener('click', (e) => {
                this.handleElementClick(e.currentTarget);
            });
        });
    }

    /**
     * Handles clicks on timeline elements
     */
    handleElementClick(element) {
        const type = element.dataset.type;
        const id = element.dataset.id;

        if (type === 'product') {
            // Navigate to product detail page
            window.location.href = `/products/${id}`;
        } else if (type === 'modality') {
            // Navigate to modality page (or open modal with product list)
            window.location.href = `/modalities`; // We could pass a filter here
        }
    }

    /**
     * Saves the current view configuration
     */
    saveCurrentView() {
        const viewName = prompt('Enter a name for this view:');
        if (!viewName) return;

        const view = {
            name: viewName,
            config: this.getCurrentConfig(),
            timestamp: new Date().toISOString()
        };

        this.savedViews[viewName] = view;
        this.persistSavedViews();

        alert(`View "${viewName}" saved successfully!`);
    }

    /**
     * Shows dialog to load a saved view
     */
    showLoadViewDialog() {
        const viewNames = Object.keys(this.savedViews);
        
        if (viewNames.length === 0) {
            alert('No saved views found. Save a view first!');
            return;
        }

        // Create a simple modal for view selection
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Load Saved View</h5>
                        <button type="button" class="btn-close" data-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="list-group">
                            ${viewNames.map(name => {
                                const view = this.savedViews[name];
                                return `
                                    <a href="#" class="list-group-item list-group-item-action" data-view="${name}">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${name}</strong>
                                                <br>
                                                <small class="text-muted">
                                                    Saved: ${new Date(view.timestamp).toLocaleString()}
                                                </small>
                                            </div>
                                            <button class="btn btn-sm btn-danger delete-view" data-view="${name}">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </a>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners for modal
        modal.querySelector('.btn-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                if (!e.target.classList.contains('delete-view') && 
                    !e.target.closest('.delete-view')) {
                    this.loadView(item.dataset.view);
                    modal.remove();
                }
            });
        });

        modal.querySelectorAll('.delete-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (confirm(`Delete view "${btn.dataset.view}"?`)) {
                    delete this.savedViews[btn.dataset.view];
                    this.persistSavedViews();
                    modal.remove();
                    this.showLoadViewDialog(); // Refresh the dialog
                }
            });
        });
    }

    /**
     * Loads a saved view
     */
    loadView(viewName) {
        const view = this.savedViews[viewName];
        if (!view) {
            alert(`View "${viewName}" not found`);
            return;
        }

        // Apply configuration to UI controls
        this.applyConfigToUI(view.config);

        // Load and render with the saved config
        this.loadAndRender();
    }

    /**
     * Applies a configuration to the UI controls
     */
    applyConfigToUI(config) {
        document.getElementById('timelineMode').value = config.timelineMode;
        document.getElementById('groupingMode').value = config.groupingMode;
        document.getElementById('elementType').value = config.elementType;

        // Trigger change events to update dependent UI elements
        document.getElementById('timelineMode').dispatchEvent(new Event('change'));

        if (config.timelineMode === 'year' && config.yearSegmentPreset) {
            const presetBtn = document.querySelector(`[data-preset="${config.yearSegmentPreset}"]`);
            if (presetBtn) {
                document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('active'));
                presetBtn.classList.add('active');
                presetBtn.dispatchEvent(new Event('click'));
            }
        }
    }

    /**
     * Loads saved views from localStorage
     */
    loadSavedViews() {
        try {
            const saved = localStorage.getItem('pipelineTimelineViews');
            return saved ? JSON.parse(saved) : {};
        } catch (e) {
            console.error('Error loading saved views:', e);
            return {};
        }
    }

    /**
     * Persists saved views to localStorage
     */
    persistSavedViews() {
        try {
            localStorage.setItem('pipelineTimelineViews', JSON.stringify(this.savedViews));
        } catch (e) {
            console.error('Error saving views:', e);
            alert('Failed to save view to browser storage');
        }
    }

    /**
     * Shows/hides loading indicator
     */
    showLoading(show) {
        if (show) {
            this.container.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3 text-muted">Loading timeline data...</p>
                </div>
            `;
        }
    }

    /**
     * Shows error message
     */
    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }

    /**
     * Utility: Gets CSRF token for POST requests
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    /**
     * Utility: Darkens a hex color for borders
     */
    darkenColor(hex, percent = 20) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + 
            (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
            (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
            (B < 255 ? (B < 1 ? 0 : B) : 255)
        ).toString(16).slice(1);
    }
}