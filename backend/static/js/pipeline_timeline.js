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
        this.zoomLevel = 1;
        this.zoomLevels = [0.5, 0.75, 1, 1.25, 1.5];
    }

    /**
     * Returns the default configuration for the timeline
     */
    getDefaultConfig() {
        return {
            dateSource: 'launch',
            yearSegmentPreset: 'individual',
            customSegments: [],
            groupingMode: 'modality',
            elementType: 'product',
            colorBy: 'modality',
            filters: {}
        };
    }

    /**
     * Gets the current configuration from the UI controls
     */
    getCurrentConfig() {
        const config = {
            dateSource: document.getElementById('dateSource').value,
            groupingMode: document.getElementById('groupingMode').value,
            elementType: document.getElementById('elementType').value,
            colorBy: 'modality',
            filters: {}
        };

        config.filters.include_line_extensions = document.getElementById('includeLineExtensions').checked;
        config.filters.exclude_discontinued = document.getElementById('excludeDiscontinued').checked;

        // Year range filters
        const yearFrom = document.getElementById('yearFrom');
        const yearTo = document.getElementById('yearTo');
        if (yearFrom && yearFrom.value) {
            config.filters.year_from = parseInt(yearFrom.value, 10);
        }
        if (yearTo && yearTo.value) {
            config.filters.year_to = parseInt(yearTo.value, 10);
        }

        // Year segment configuration (always year-based now with different milestones)
        const activePreset = document.querySelector('[data-preset].active');
        config.yearSegmentPreset = activePreset ?
            activePreset.dataset.preset : 'individual';

        if (config.yearSegmentPreset === 'custom') {
            config.customSegments = this.getCustomSegments();
        }

        return config;
    }

    /**
     * Gets custom segment configuration from UI
     */
    getCustomSegments() {
        return [];
    }

    /**
     * Main method to load data and render the timeline
     */
    async loadAndRender() {
        try {
            this.showLoading(true);
            
            this.config = this.getCurrentConfig();
            
            this.data = await this.fetchTimelineData(this.config);
            
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

        this.container.innerHTML = '';

        this.renderTimelineHeader();

        this.renderSwimLanes();

        this.attachEventListeners();

        if (this.data && this.data.metadata) {
            this.displayMetadata(this.data.metadata);
        }
    }

    /**
     * Displays metadata about filtered products
     */
    displayMetadata(metadata) {
        if (!metadata) return;
        
        const statusDiv = document.getElementById('filterStatus');
        const statusText = document.getElementById('filterStatusText');
        
        if (!statusDiv || !statusText) return;
        
        let parts = [];
        
        if (metadata.nme_count > 0 || metadata.line_extension_count > 0) {
            let productInfo = `${metadata.total_products} product${metadata.total_products !== 1 ? 's' : ''}`;
            
            if (metadata.nme_count > 0 && metadata.line_extension_count > 0) {
                productInfo += ` (${metadata.nme_count} NMEs, ${metadata.line_extension_count} Line-Extensions)`;
            } else if (metadata.nme_count > 0) {
                productInfo += ` (${metadata.nme_count} NMEs only)`;
            } else if (metadata.line_extension_count > 0) {
                productInfo += ` (${metadata.line_extension_count} Line-Extensions only)`;
            }
            
            parts.push(`Showing ${productInfo}`);
        }
        
        if (metadata.discontinued_count > 0) {
            if (metadata.active_filters.exclude_discontinued) {
                parts.push(`${metadata.discontinued_count} discontinued hidden`);
            } else {
                parts.push(`${metadata.discontinued_count} discontinued included`);
            }
        }
        
        if (parts.length > 0) {
            statusDiv.style.display = 'block';
            statusText.innerHTML = `<strong>${parts[0]}</strong>${parts.length > 1 ? ' — ' + parts.slice(1).join(', ') : ''}`;
        } else {
            statusDiv.style.display = 'none';
        }
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
            lanesContainer.appendChild(this.renderSwimLane({
                group_name: 'All Products',
                elements: this.data.elements || []
            }));
        } else {
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

        const grid = document.createElement('div');
        grid.className = 'timeline-grid';
        
        this.data.timeline_units.forEach(unit => {
            const cell = document.createElement('div');
            cell.className = 'timeline-cell';
            cell.dataset.unit = unit;

            const elementsInCell = laneData.elements.filter(el => 
                this.isElementInTimelineUnit(el, unit)
            );

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
     * Renders a single element (product or modality box) with visual distinction
     */
    renderElement(element) {
        const box = document.createElement('div');
        
        box.className = `timeline-element ${element.type}`;
        
        if (element.data && element.type === 'product') {
            if (element.data.is_nme) {
                box.classList.add('nme');
                box.setAttribute('data-is-nme', 'true');
            }
            
            if (element.data.is_line_extension) {
                box.classList.add('line-extension');
                box.setAttribute('data-is-line-extension', 'true');
            }
            
            if (element.data.project_status === 'Discontinued') {
                box.classList.add('discontinued');
            }
        }
        
        box.dataset.id = element.id;
        box.dataset.type = element.type;
        
        if (element.visual) {
            box.style.backgroundColor = element.visual.color || '#6c757d';
            box.style.borderColor = this.darkenColor(element.visual.color || '#6c757d');
        }

        let labelHtml = element.visual ? element.visual.label : element.id;
        
        if (element.data && element.data.is_line_extension && element.data.line_extension_indication) {
            labelHtml += ` <small>(${element.data.line_extension_indication})</small>`;
        }

        box.innerHTML = `
            <div class="element-content">
                ${element.visual && element.visual.icon ? 
                    `<i class="${element.visual.icon}"></i>` : ''}
                <span class="element-label">${labelHtml}</span>
                ${element.count > 1 ? 
                    `<span class="element-count badge">${element.count}</span>` : ''}
            </div>
        `;

        box.title = this.generateTooltip(element);

        return box;
    }

    /**
     * Determines if an element belongs in a specific timeline unit
     */
    isElementInTimelineUnit(element, unit) {
        return element.position === unit;
    }

    /**
     * Formats a timeline unit for display
     */
    formatTimelineUnit(unit) {
        return unit.toString();
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
     * Enhanced tooltip generation with NME/LE info
     */
    generateTooltip(element) {
        let tooltip = element.data.product_name || element.data.modality_name || element.id;
        
        if (element.type === 'product') {
            if (element.data.is_nme) {
                tooltip += '\n🔹 NME (New Molecular Entity)';
            } else if (element.data.is_line_extension) {
                tooltip += '\n🔸 Line-Extension';
                if (element.data.line_extension_indication) {
                    tooltip += ` - ${element.data.line_extension_indication}`;
                }
            }
            
            tooltip += `\nPhase: ${element.data.current_phase || 'N/A'}`;
            tooltip += `\nLaunch: ${element.data.expected_launch_year || 'TBD'}`;
            
            if (element.data.project_status) {
                tooltip += `\nStatus: ${element.data.project_status}`;
            }
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

        if (type === 'project') {
            window.location.href = `/projects/${id}`;
        } else if (type === 'modality') {
            window.location.href = `/modalities`;
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
                    this.showLoadViewDialog();
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

        this.applyConfigToUI(view.config);

        this.loadAndRender();
    }

    /**
     * Applies a configuration to the UI controls
     */
    applyConfigToUI(config) {
        document.getElementById('dateSource').value = config.dateSource || 'launch';
        document.getElementById('groupingMode').value = config.groupingMode;
        document.getElementById('elementType').value = config.elementType;

        if (config.yearSegmentPreset) {
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

    /**
     * Zoom in the timeline
     */
    zoomIn() {
        const currentIndex = this.zoomLevels.indexOf(this.zoomLevel);
        if (currentIndex < this.zoomLevels.length - 1) {
            this.setZoom(this.zoomLevels[currentIndex + 1]);
        }
    }

    /**
     * Zoom out the timeline
     */
    zoomOut() {
        const currentIndex = this.zoomLevels.indexOf(this.zoomLevel);
        if (currentIndex > 0) {
            this.setZoom(this.zoomLevels[currentIndex - 1]);
        }
    }

    /**
     * Set zoom level
     */
    setZoom(level) {
        this.zoomLevel = level;
        document.documentElement.style.setProperty('--timeline-zoom', level);

        // Update zoom display
        const zoomDisplay = document.getElementById('zoomLevel');
        if (zoomDisplay) {
            zoomDisplay.textContent = Math.round(level * 100) + '%';
        }
    }
}