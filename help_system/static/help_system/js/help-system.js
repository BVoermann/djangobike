/**
 * Comprehensive Help System for Django Bike Shop Simulation
 * 
 * This system provides multiple help delivery methods:
 * - Tooltips on interface elements
 * - Interactive popup guides
 * - Context-sensitive help
 * - Tutorial videos
 */

class HelpSystem {
    constructor() {
        this.currentGuide = null;
        this.currentStep = 0;
        this.tooltips = new Map();
        this.contextualHelp = [];
        this.isInitialized = false;
        
        this.init();
    }
    
    async init() {
        if (this.isInitialized) return;
        
        console.log('Initializing Help System...');
        
        // Load CSS dependencies
        this.loadCSS();
        
        // Initialize components
        this.setupEventListeners();
        await this.loadTooltips();
        await this.loadContextualHelp();
        
        // Setup help button
        this.setupHelpButton();
        
        this.isInitialized = true;
        console.log('Help System initialized successfully');
        
        // Trigger contextual help check
        this.checkContextualHelp();
    }
    
    loadCSS() {
        // Load Shepherd.js CSS for guided tours
        // Shepherd.js and Tippy.js disabled - using custom guide system
        // (These were causing MIME type errors)
        /*
        if (!document.querySelector('link[href*="shepherd"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://cdn.jsdelivr.net/npm/shepherd.js@11.2.0/dist/css/shepherd.css';
            document.head.appendChild(link);
        }

        // Load Tippy.js CSS for tooltips
        if (!document.querySelector('link[href*="tippy"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/tippy.js@6/dist/tippy.css';
            document.head.appendChild(link);
        }
        */
        
        // Load our custom CSS
        const customCSS = `
            .help-system-tooltip {
                max-width: 300px;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .help-system-tooltip.info { background: #007bff; }
            .help-system-tooltip.tip { background: #28a745; }
            .help-system-tooltip.warning { background: #ffc107; color: #000; }
            .help-system-tooltip.definition { background: #6f42c1; }
            
            .contextual-help-modal {
                position: fixed;
                top: 20px;
                right: 20px;
                max-width: 400px;
                z-index: 9999;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                border: 1px solid #ddd;
            }
            
            .contextual-help-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 9998;
                background: #007bff;
                color: white;
                padding: 12px 20px;
                text-align: center;
            }
            
            .help-button-floating {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9997;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
            }
            
            .help-button-floating:hover {
                background: #0056b3;
                transform: scale(1.1);
            }
            
            .help-quick-search {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10000;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                width: 500px;
                max-width: 90vw;
                max-height: 70vh;
                overflow: hidden;
            }
            
            .shepherd-element {
                z-index: 10001 !important;
            }
            
            .question-mark-icon {
                display: inline-block;
                width: 16px;
                height: 16px;
                background: #007bff;
                color: white;
                border-radius: 50%;
                text-align: center;
                font-size: 12px;
                font-weight: bold;
                line-height: 16px;
                margin-left: 5px;
                cursor: pointer;
                vertical-align: middle;
            }
            
            .question-mark-icon:hover {
                background: #0056b3;
            }
            
            @keyframes helpPulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .help-attention {
                animation: helpPulse 2s infinite;
            }
        `;
        
        const style = document.createElement('style');
        style.textContent = customCSS;
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // F1 key opens help
            if (e.key === 'F1') {
                e.preventDefault();
                this.openHelpDashboard();
            }
            
            // Ctrl+/ opens quick search
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                this.openQuickSearch();
            }
            
            // Escape closes current guide
            if (e.key === 'Escape' && this.currentGuide) {
                this.currentGuide.cancel();
            }
        });
        
        // Page visibility change - pause/resume guides
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.currentGuide) {
                // Pause guide when page is hidden
                console.log('Page hidden - pausing guide');
            }
        });
    }
    
    async loadTooltips() {
        try {
            const response = await fetch(`/help/api/tooltip-help/?page_url=${encodeURIComponent(window.location.pathname)}`);
            const data = await response.json();
            
            if (data.tooltips) {
                this.setupTooltips(data.tooltips);
            }
        } catch (error) {
            console.error('Failed to load tooltips:', error);
        }
    }
    
    setupTooltips(tooltips) {
        // Tippy.js disabled - tooltips not needed for custom guide system
        console.log('Tooltips disabled to avoid library conflicts');
        return;
        /* DISABLED
        // Load Tippy.js if not already loaded
        if (typeof tippy === 'undefined') {
            this.loadScript('https://unpkg.com/tippy.js@6/dist/tippy-bundle.umd.min.js', () => {
                this.createTooltips(tooltips);
            });
        } else {
            this.createTooltips(tooltips);
        }
        */
    }
    
    createTooltips(tooltips) {
        tooltips.forEach(tooltip => {
            const elements = document.querySelectorAll(tooltip.element_selector);
            
            elements.forEach(element => {
                // Add question mark icon if not already present
                this.addQuestionMarkIcon(element, tooltip);
                
                // Create tippy tooltip
                const tippyInstance = tippy(element, {
                    content: `
                        <div class="help-system-tooltip ${tooltip.tooltip_type}">
                            <strong>${tooltip.title}</strong>
                            <div style="margin-top: 5px;">${tooltip.content}</div>
                        </div>
                    `,
                    allowHTML: true,
                    placement: tooltip.position,
                    interactive: true,
                    theme: tooltip.tooltip_type,
                    trigger: this.getTippyTrigger(tooltip),
                    delay: [200, 0],
                    hideOnClick: true,
                    onShow: () => {
                        this.recordInteraction('tooltip_viewed', 'tooltip', tooltip.id);
                    }
                });
                
                if (tooltip.auto_hide_delay > 0) {
                    tippyInstance.setProps({
                        hideOnClick: false,
                        trigger: 'manual'
                    });
                    
                    setTimeout(() => {
                        tippyInstance.hide();
                    }, tooltip.auto_hide_delay * 1000);
                }
                
                this.tooltips.set(tooltip.id, tippyInstance);
            });
        });
    }
    
    addQuestionMarkIcon(element, tooltip) {
        // Check if element already has a question mark
        if (element.querySelector('.question-mark-icon')) return;
        
        const icon = document.createElement('span');
        icon.className = 'question-mark-icon';
        icon.innerHTML = '?';
        icon.title = tooltip.title;
        
        // Position the icon appropriately
        if (element.tagName === 'LABEL') {
            element.appendChild(icon);
        } else {
            // Try to find a good spot to place the icon
            const parent = element.parentElement;
            if (parent) {
                parent.style.position = 'relative';
                icon.style.position = 'absolute';
                icon.style.top = '5px';
                icon.style.right = '5px';
                parent.appendChild(icon);
            }
        }
        
        // Make the icon trigger the tooltip
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            const tippyInstance = this.tooltips.get(tooltip.id);
            if (tippyInstance) {
                tippyInstance.show();
            }
        });
    }
    
    getTippyTrigger(tooltip) {
        const triggers = [];
        if (tooltip.show_on_hover) triggers.push('mouseenter focus');
        if (tooltip.show_on_click) triggers.push('click');
        return triggers.join(' ') || 'mouseenter focus';
    }
    
    async loadContextualHelp() {
        try {
            const response = await fetch(`/help/api/contextual-help/?page_url=${encodeURIComponent(window.location.pathname)}`);
            const data = await response.json();
            
            if (data.help_items && data.help_items.length > 0) {
                this.contextualHelp = data.help_items;
            }
        } catch (error) {
            console.error('Failed to load contextual help:', error);
        }
    }
    
    checkContextualHelp() {
        if (this.contextualHelp.length === 0) return;
        
        // Show the highest priority contextual help
        const helpItem = this.contextualHelp[0];
        
        setTimeout(() => {
            this.showContextualHelp(helpItem);
        }, 1000); // Delay to let page load completely
    }
    
    showContextualHelp(helpItem) {
        this.recordInteraction('contextual_help_shown', 'contextual', helpItem.id);
        
        switch (helpItem.format) {
            case 'popup':
                this.showHelpPopup(helpItem);
                break;
            case 'banner':
                this.showHelpBanner(helpItem);
                break;
            case 'sidebar':
                this.showHelpSidebar(helpItem);
                break;
            case 'guide':
                if (helpItem.related_guide_id) {
                    this.startGuide(helpItem.related_guide_id);
                }
                break;
            default:
                this.showHelpPopup(helpItem);
        }
    }
    
    showHelpPopup(helpItem) {
        const modal = document.createElement('div');
        modal.className = 'contextual-help-modal';
        modal.innerHTML = `
            <div class="card border-0">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${helpItem.title}</h6>
                    <button type="button" class="btn-close btn-close-white" onclick="this.closest('.contextual-help-modal').remove()"></button>
                </div>
                <div class="card-body">
                    <p class="mb-3">${helpItem.content}</p>
                    <div class="d-flex gap-2">
                        ${helpItem.related_video_id ? `
                            <button class="btn btn-sm btn-outline-primary" onclick="helpSystem.openVideo(${helpItem.related_video_id})">
                                <i class="fas fa-play me-1"></i>Tutorial ansehen
                            </button>
                        ` : ''}
                        ${helpItem.related_guide_id ? `
                            <button class="btn btn-sm btn-outline-success" onclick="helpSystem.startGuide(${helpItem.related_guide_id})">
                                <i class="fas fa-route me-1"></i>Guide starten
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-secondary" onclick="this.closest('.contextual-help-modal').remove()">
                            Schließen
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
                this.recordInteraction('contextual_help_dismissed', 'contextual', helpItem.id);
            }
        }, 30000);
    }
    
    showHelpBanner(helpItem) {
        const banner = document.createElement('div');
        banner.className = 'contextual-help-banner';
        banner.innerHTML = `
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <strong>${helpItem.title}:</strong> ${helpItem.content}
                </div>
                <div>
                    ${helpItem.related_video_id ? `
                        <button class="btn btn-sm btn-light me-2" onclick="helpSystem.openVideo(${helpItem.related_video_id})">
                            Tutorial
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-light" onclick="this.closest('.contextual-help-banner').remove()">
                        ×
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        // Adjust body padding to account for banner
        document.body.style.paddingTop = (document.body.style.paddingTop || 0) + 'px';
        
        // Auto-remove after 15 seconds
        setTimeout(() => {
            if (banner.parentElement) {
                banner.remove();
                document.body.style.paddingTop = '0px';
                this.recordInteraction('contextual_help_dismissed', 'contextual', helpItem.id);
            }
        }, 15000);
    }
    
    setupHelpButton() {
        // Add floating help button
        const helpButton = document.createElement('button');
        helpButton.className = 'help-button-floating';
        helpButton.innerHTML = '?';
        helpButton.title = 'Hilfe (F1)';
        
        helpButton.addEventListener('click', () => {
            this.openHelpDashboard();
        });
        
        document.body.appendChild(helpButton);
    }
    
    async startGuide(guideId) {
        console.log('Starting guide with ID:', guideId);
        
        try {
            // Load Shepherd.js if not already loaded
            if (typeof Shepherd === 'undefined') {
                console.log('Loading Shepherd.js...');
                await this.loadScriptPromise('https://cdn.jsdelivr.net/npm/shepherd.js@11.2.0/dist/js/shepherd.min.js');
                console.log('Shepherd.js loaded successfully');
            }
            
            console.log('Fetching guide data...');
            const response = await fetch(`/help/api/guides/${guideId}/start/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                }
            });
            
            console.log('API response status:', response.status);
            const data = await response.json();
            console.log('API response data:', data);
            
            if (data.success) {
                console.log('Creating Shepherd tour...');
                this.createShepherdTour(data.guide);
            } else {
                console.error('API returned success=false');
                alert('Die Anleitung konnte nicht gestartet werden. Bitte versuchen Sie es später erneut.');
            }
        } catch (error) {
            console.error('Failed to start guide:', error);
            alert(`Fehler beim Starten der Anleitung: ${error.message}`);
        }
    }
    
    createShepherdTour(guide) {
        try {
            console.log('Creating Shepherd tour for guide:', guide.title);
            
            this.currentGuide = new Shepherd.Tour({
                useModalOverlay: true,
                defaultStepOptions: {
                    cancelIcon: {
                        enabled: guide.is_skippable
                    },
                    scrollTo: {
                        behavior: 'smooth',
                        block: 'center'
                    },
                    when: {
                        show: () => {
                            // Add progress indicator if enabled
                            if (guide.show_progress) {
                                this.updateGuideProgress(guide);
                            }
                        }
                    }
                }
            });
            
            guide.steps.forEach((step, index) => {
                console.log(`Adding step ${index + 1}:`, step.title);
                this.currentGuide.addStep({
                    title: step.title,
                    text: step.content,
                    attachTo: step.target ? {
                        element: step.target,
                        on: step.placement || 'bottom'
                    } : undefined,
                    buttons: this.createGuideButtons(guide, index, step),
                    id: `step-${index}`
                });
            });
            
            this.currentGuide.on('complete', () => {
                console.log('Guide completed');
                this.completeGuide(guide.id);
            });
            
            this.currentGuide.on('cancel', () => {
                if (confirm('Möchten Sie diese Anleitung wirklich beenden?')) {
                    this.skipGuide(guide.id);
                } else {
                    return false;
                }
            });
            
            console.log('Starting Shepherd tour...');
            this.currentGuide.start();
            
        } catch (error) {
            console.error('Error creating Shepherd tour:', error);
            // Fallback to simple modal-based guide
            this.createFallbackGuide(guide);
        }
    }
    
    createFallbackGuide(guide) {
        console.log('Using fallback guide system');
        alert(`Anleitung: ${guide.title}\n\nDiese vereinfachte Version führt Sie durch die ${guide.steps.length} Schritte der Anleitung.\n\nKlicken Sie OK um zu beginnen.`);
        
        let currentStep = 0;
        
        const showStep = () => {
            if (currentStep >= guide.steps.length) {
                alert('Anleitung abgeschlossen! Herzlichen Glückwunsch.');
                this.completeGuide(guide.id);
                return;
            }
            
            const step = guide.steps[currentStep];
            const result = confirm(`Schritt ${currentStep + 1} von ${guide.steps.length}\n\n${step.title}\n\n${step.content}\n\nKlicken Sie OK für den nächsten Schritt oder Abbrechen zum Beenden.`);
            
            if (result) {
                this.completeStep(guide.id, currentStep);
                currentStep++;
                showStep();
            } else {
                if (confirm('Möchten Sie die Anleitung wirklich beenden?')) {
                    this.skipGuide(guide.id);
                } else {
                    showStep(); // Continue with current step
                }
            }
        };
        
        showStep();
    }
    
    createGuideButtons(guide, stepIndex, step) {
        const buttons = [];
        
        // Previous button (except for first step)
        if (stepIndex > 0) {
            buttons.push({
                text: 'Zurück',
                classes: 'btn btn-outline-secondary',
                action: () => {
                    this.currentGuide.back();
                }
            });
        }
        
        // Skip button (if guide is skippable)
        if (guide.is_skippable) {
            buttons.push({
                text: 'Überspringen',
                classes: 'btn btn-outline-warning',
                action: () => {
                    if (confirm('Möchten Sie diese Anleitung überspringen?')) {
                        this.currentGuide.cancel();
                    }
                }
            });
        }
        
        // Next/Complete button
        const isLastStep = stepIndex === guide.steps.length - 1;
        buttons.push({
            text: isLastStep ? 'Abschließen' : 'Weiter',
            classes: `btn ${isLastStep ? 'btn-success' : 'btn-primary'}`,
            action: () => {
                this.completeStep(guide.id, stepIndex);
                if (isLastStep) {
                    this.currentGuide.complete();
                } else {
                    this.currentGuide.next();
                }
            }
        });
        
        return buttons;
    }
    
    updateGuideProgress(guide) {
        const currentStep = this.currentGuide.getCurrentStep();
        if (currentStep) {
            const stepIndex = parseInt(currentStep.id.replace('step-', ''));
            const progress = ((stepIndex + 1) / guide.steps.length) * 100;
            
            // Add progress bar to current step
            const progressHTML = `
                <div class="progress mb-3" style="height: 5px;">
                    <div class="progress-bar" role="progressbar" style="width: ${progress}%"></div>
                </div>
                <div class="text-muted small mb-2">Schritt ${stepIndex + 1} von ${guide.steps.length}</div>
            `;
            
            const stepContent = currentStep.getElement().querySelector('.shepherd-text');
            if (stepContent && !stepContent.querySelector('.progress')) {
                stepContent.insertAdjacentHTML('afterbegin', progressHTML);
            }
        }
    }
    
    async completeStep(guideId, stepIndex) {
        try {
            await fetch(`/help/api/guides/${guideId}/progress/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    step_number: stepIndex,
                    action: 'complete'
                })
            });
        } catch (error) {
            console.error('Failed to update guide progress:', error);
        }
    }
    
    async completeGuide(guideId) {
        try {
            await fetch(`/help/api/guides/${guideId}/progress/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'finish'
                })
            });
            
            this.currentGuide = null;
            
            // Show completion message
            this.showCompletionMessage('Anleitung erfolgreich abgeschlossen!');
        } catch (error) {
            console.error('Failed to complete guide:', error);
        }
    }
    
    async skipGuide(guideId) {
        try {
            await fetch(`/help/api/guides/${guideId}/progress/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'skip'
                })
            });
            
            this.currentGuide = null;
        } catch (error) {
            console.error('Failed to skip guide:', error);
        }
    }
    
    openHelpDashboard() {
        window.open('/help/', '_blank');
    }
    
    openVideo(videoId) {
        window.open(`/help/videos/${videoId}/`, '_blank');
    }
    
    openQuickSearch() {
        const searchModal = document.createElement('div');
        searchModal.className = 'help-quick-search';
        searchModal.innerHTML = `
            <div class="p-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0">Hilfe durchsuchen</h5>
                    <button type="button" class="btn-close" onclick="this.closest('.help-quick-search').remove()"></button>
                </div>
                <input type="text" class="form-control mb-3" placeholder="Suchbegriff eingeben..." id="help-search-input">
                <div id="help-search-results" class="overflow-auto" style="max-height: 300px;">
                    <div class="text-muted text-center">Beginnen Sie mit der Eingabe, um zu suchen...</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(searchModal);
        
        const searchInput = searchModal.querySelector('#help-search-input');
        const resultsDiv = searchModal.querySelector('#help-search-results');
        
        searchInput.focus();
        
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(searchInput.value, resultsDiv);
            }, 300);
        });
        
        // Close on escape
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchModal.remove();
            }
        });
    }
    
    async performSearch(query, resultsDiv) {
        if (query.length < 2) {
            resultsDiv.innerHTML = '<div class="text-muted text-center">Mindestens 2 Zeichen eingeben</div>';
            return;
        }
        
        try {
            const response = await fetch(`/help/api/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div class="text-muted text-center">Keine Ergebnisse gefunden</div>';
                return;
            }
            
            const resultsHTML = data.results.map(result => `
                <div class="border-bottom py-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <a href="${result.url}" target="_blank" class="text-decoration-none">
                                    ${result.title}
                                </a>
                            </h6>
                            <p class="text-muted small mb-1">${result.description}</p>
                            <span class="badge bg-secondary me-1">${result.category}</span>
                            ${result.difficulty ? `<span class="badge bg-info">${result.difficulty}</span>` : ''}
                            ${result.guide_type ? `<span class="badge bg-success">${result.guide_type}</span>` : ''}
                        </div>
                        <small class="text-muted">${result.type === 'video' ? 'Video' : 'Anleitung'}</small>
                    </div>
                </div>
            `).join('');
            
            resultsDiv.innerHTML = resultsHTML;
        } catch (error) {
            console.error('Search failed:', error);
            resultsDiv.innerHTML = '<div class="text-danger text-center">Suche fehlgeschlagen</div>';
        }
    }
    
    showCompletionMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'position-fixed top-0 start-50 translate-middle-x mt-3';
        toast.style.zIndex = '10002';
        toast.innerHTML = `
            <div class="toast show" role="alert">
                <div class="toast-body bg-success text-white">
                    <i class="fas fa-check-circle me-2"></i>${message}
                </div>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    async recordInteraction(eventType, contentType, contentId, interactionData = {}) {
        try {
            await fetch('/help/api/interactions/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_type: eventType,
                    content_type: contentType,
                    content_id: contentId,
                    page_url: window.location.pathname,
                    interaction_data: interactionData
                })
            });
        } catch (error) {
            console.error('Failed to record interaction:', error);
        }
    }
    
    loadScript(src, callback) {
        const script = document.createElement('script');
        script.src = src;
        script.onload = callback;
        document.head.appendChild(script);
    }
    
    loadScriptPromise(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    getCSRFToken() {
        // Try multiple methods to get CSRF token
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.content ||
                     document.querySelector('[name="csrftoken"]')?.value ||
                     '';
        
        if (!token) {
            console.warn('CSRF token not found');
        }
        
        return token;
    }
}

// Initialize help system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.helpSystem = new HelpSystem();
});

// Global functions for templates
window.startHelpGuide = (guideId) => {
    if (window.helpSystem) {
        window.helpSystem.startGuide(guideId);
    }
};

window.openHelpVideo = (videoId) => {
    if (window.helpSystem) {
        window.helpSystem.openVideo(videoId);
    }
};