// Guide continuation system for cross-page navigation
// This should be included on all simulation pages

document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to continue a guide from another page
    const continueGuideData = sessionStorage.getItem('continueGuide');
    if (continueGuideData) {
        try {
            const guideInfo = JSON.parse(continueGuideData);
            sessionStorage.removeItem('continueGuide'); // Clean up
            
            console.log('🔄 Continuing guide from navigation:', guideInfo);
            
            // Small delay to let page settle
            setTimeout(() => {
                if (typeof createInteractiveGuide === 'function') {
                    createInteractiveGuide(guideInfo.guide, guideInfo.stepIndex);
                } else {
                    // Fallback: load the guide system
                    loadGuideSystem().then(() => {
                        createInteractiveGuide(guideInfo.guide, guideInfo.stepIndex);
                    });
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error continuing guide:', error);
            sessionStorage.removeItem('continueGuide');
        }
    }
});

async function loadGuideSystem() {
    // Load the main interactive guide JavaScript if not already loaded
    if (typeof createInteractiveGuide !== 'function') {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = '/static/help_system/js/interactive-guides.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    return Promise.resolve();
}

// Make createInteractiveGuide available globally for cross-page guides
window.createInteractiveGuide = async function(guide, startStep = 0) {
    console.log('🎬 Creating interactive guide:', guide.title, 'starting at step', startStep);
    
    // Create grey overlay that covers entire page
    const overlay = document.createElement('div');
    overlay.id = 'guide-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 9999;
        pointer-events: none;
    `;
    document.body.appendChild(overlay);
    
    // Create guide container
    const guideContainer = document.createElement('div');
    guideContainer.id = 'guide-container';
    guideContainer.style.cssText = `
        position: absolute;
        width: 350px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        z-index: 10001;
        font-family: Arial, sans-serif;
        pointer-events: auto;
    `;
    document.body.appendChild(guideContainer);
    
    let currentStep = startStep;
    let currentHighlight = null;
    let currentTargetElement = null;
    let currentPlacement = 'right';
    
    const positionGuideContainer = (targetElement, placement = 'right') => {
        if (!targetElement) {
            // Default position if no target element
            guideContainer.style.top = '20px';
            guideContainer.style.right = '20px';
            guideContainer.style.left = 'auto';
            guideContainer.style.bottom = 'auto';
            return;
        }
        
        const rect = targetElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        const containerWidth = 350;
        const containerHeight = 300; // Approximate height
        const margin = 15; // Space between target and container
        
        let top, left;
        
        switch (placement) {
            case 'top':
                top = rect.top + scrollTop - containerHeight - margin;
                left = rect.left + scrollLeft + (rect.width / 2) - (containerWidth / 2);
                break;
            case 'bottom':
                top = rect.bottom + scrollTop + margin;
                left = rect.left + scrollLeft + (rect.width / 2) - (containerWidth / 2);
                break;
            case 'left':
                top = rect.top + scrollTop + (rect.height / 2) - (containerHeight / 2);
                left = rect.left + scrollLeft - containerWidth - margin;
                break;
            case 'right':
            default:
                top = rect.top + scrollTop + (rect.height / 2) - (containerHeight / 2);
                left = rect.right + scrollLeft + margin;
                break;
        }
        
        // Ensure container stays within viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Adjust horizontal position
        if (left < 0) {
            left = margin;
        } else if (left + containerWidth > viewportWidth) {
            left = viewportWidth - containerWidth - margin;
        }
        
        // Adjust vertical position
        if (top < scrollTop) {
            top = scrollTop + margin;
        } else if (top + containerHeight > scrollTop + viewportHeight) {
            top = scrollTop + viewportHeight - containerHeight - margin;
        }
        
        guideContainer.style.top = top + 'px';
        guideContainer.style.left = left + 'px';
        guideContainer.style.right = 'auto';
        guideContainer.style.bottom = 'auto';
        
        // Add pointer arrow
        addPointerArrow(placement);
    };
    
    const addPointerArrow = (placement) => {
        // Remove existing arrow
        const existingArrow = guideContainer.querySelector('.guide-arrow');
        if (existingArrow) {
            existingArrow.remove();
        }
        
        // Create new arrow
        const arrow = document.createElement('div');
        arrow.className = 'guide-arrow';
        
        const arrowSize = 12;
        let arrowStyles = `
            position: absolute;
            width: 0;
            height: 0;
            z-index: 10002;
        `;
        
        switch (placement) {
            case 'top':
                arrowStyles += `
                    bottom: -${arrowSize}px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-left: ${arrowSize}px solid transparent;
                    border-right: ${arrowSize}px solid transparent;
                    border-top: ${arrowSize}px solid white;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
                `;
                break;
            case 'bottom':
                arrowStyles += `
                    top: -${arrowSize}px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-left: ${arrowSize}px solid transparent;
                    border-right: ${arrowSize}px solid transparent;
                    border-bottom: ${arrowSize}px solid white;
                    filter: drop-shadow(0 -2px 4px rgba(0,0,0,0.1));
                `;
                break;
            case 'left':
                arrowStyles += `
                    right: -${arrowSize}px;
                    top: 50%;
                    transform: translateY(-50%);
                    border-top: ${arrowSize}px solid transparent;
                    border-bottom: ${arrowSize}px solid transparent;
                    border-left: ${arrowSize}px solid white;
                    filter: drop-shadow(2px 0 4px rgba(0,0,0,0.1));
                `;
                break;
            case 'right':
            default:
                arrowStyles += `
                    left: -${arrowSize}px;
                    top: 50%;
                    transform: translateY(-50%);
                    border-top: ${arrowSize}px solid transparent;
                    border-bottom: ${arrowSize}px solid transparent;
                    border-right: ${arrowSize}px solid white;
                    filter: drop-shadow(-2px 0 4px rgba(0,0,0,0.1));
                `;
                break;
        }
        
        arrow.style.cssText = arrowStyles;
        guideContainer.appendChild(arrow);
    };
    
    const showStep = async (stepIndex) => {
        if (stepIndex >= guide.steps.length) {
            // Guide completed
            endGuide();
            alert('🎉 Anleitung erfolgreich abgeschlossen!\\n\\nSie haben alle Schritte durchlaufen. Viel Erfolg bei der Simulation!');
            return;
        }
        
        const step = guide.steps[stepIndex];
        console.log(`📍 Showing step ${stepIndex + 1}: ${step.title}`);
        
        // Remove previous highlight
        if (currentHighlight) {
            currentHighlight.remove();
        }
        
        // Navigate to target page if specified
        if (step.navigate_to) {
            console.log(`🧭 Navigating to: ${step.navigate_to}`);
            
            // Check if we're in mock simulation
            if (window.location.pathname.includes('/help/mock-simulation/')) {
                // Handle navigation within mock simulation
                let targetView = step.navigate_to;
                
                // Extract view name from various formats
                if (typeof targetView === 'string') {
                    if (targetView.includes('/')) {
                        // Extract from URL patterns
                        const patterns = ['procurement', 'production', 'sales', 'finance', 'warehouse'];
                        for (const pattern of patterns) {
                            if (targetView.includes(pattern)) {
                                targetView = pattern;
                                break;
                            }
                        }
                    }
                }
                
                // Switch view in mock simulation
                if (window.switchMockView && typeof targetView === 'string') {
                    console.log(`🔄 Switching to mock view: ${targetView}`);
                    window.switchMockView(targetView);
                    
                    // Small delay to let view switch complete
                    setTimeout(() => {
                        showStep(stepIndex + 1);
                    }, 500);
                    return;
                }
            } else {
                // Original navigation logic for real simulation
                let navigationUrl = step.navigate_to;
                const currentUrl = window.location.pathname;
                const sessionIdMatch = currentUrl.match(/([a-f0-9-]{36})/);
                
                if (sessionIdMatch && navigationUrl.includes('{{ session_id }}')) {
                    navigationUrl = navigationUrl.replace('{{ session_id }}', sessionIdMatch[1]);
                    console.log(`🔄 Replaced session ID: ${navigationUrl}`);
                }
                
                // Store guide continuation data
                sessionStorage.setItem('continueGuide', JSON.stringify({
                    guideId: guide.id,
                    stepIndex: stepIndex + 1,
                    guide: guide
                }));
                
                window.location.href = navigationUrl;
                return; // Let the page load and continue guide there
            }
        }
        
        // Find and highlight target element
        let targetElement = null;
        if (step.target && step.target !== 'body') {
            targetElement = document.querySelector(step.target);
            if (targetElement) {
                currentTargetElement = targetElement;
                currentPlacement = step.placement || 'right';
                highlightElement(targetElement);
                // Position guide container next to target element
                positionGuideContainer(targetElement, currentPlacement);
            } else {
                console.warn(`⚠️ Target element not found: ${step.target}`);
                currentTargetElement = null;
                // Use default positioning if target not found
                positionGuideContainer(null);
            }
        } else {
            // Center the guide for body/general steps
            currentTargetElement = null;
            guideContainer.style.top = '50%';
            guideContainer.style.left = '50%';
            guideContainer.style.transform = 'translate(-50%, -50%)';
            guideContainer.style.right = 'auto';
            guideContainer.style.bottom = 'auto';
            
            // Remove arrow for centered guides
            const existingArrow = guideContainer.querySelector('.guide-arrow');
            if (existingArrow) {
                existingArrow.remove();
            }
        }
        
        // Update guide container content
        const isLastStep = stepIndex === guide.steps.length - 1;
        const progress = Math.round(((stepIndex + 1) / guide.steps.length) * 100);
        
        guideContainer.innerHTML = `
            <div style="padding: 20px;">
                <!-- Progress bar -->
                <div style="margin-bottom: 15px;">
                    <div style="background: #f0f0f0; height: 4px; border-radius: 2px; overflow: hidden;">
                        <div style="background: #007bff; height: 100%; width: ${progress}%; transition: width 0.3s ease;"></div>
                    </div>
                    <div style="text-align: center; font-size: 12px; color: #666; margin-top: 5px;">
                        Schritt ${stepIndex + 1} von ${guide.steps.length}
                    </div>
                </div>
                
                <!-- Guide content -->
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">
                        ${step.title}
                    </h4>
                    <p style="margin: 0; color: #555; line-height: 1.5; font-size: 14px;">
                        ${step.content}
                    </p>
                    ${step.target && step.target !== 'body' ? `
                        <div style="margin-top: 10px; padding: 8px; background: #e3f2fd; border-radius: 4px; font-size: 12px; color: #1976d2;">
                            💡 <strong>Schauen Sie sich an:</strong> ${step.target}
                        </div>
                    ` : ''}
                </div>
                
                <!-- Buttons -->
                <div style="display: flex; gap: 8px;">
                    ${stepIndex > 0 ? `
                        <button onclick="previousStep()" style="flex: 1; padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                            ← Zurück
                        </button>
                    ` : ''}
                    <button onclick="nextStep()" style="flex: 2; padding: 8px 16px; background: ${isLastStep ? '#28a745' : '#007bff'}; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        ${isLastStep ? '🎉 Fertig' : 'Weiter →'}
                    </button>
                    <button onclick="endGuide()" style="padding: 8px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        ✕
                    </button>
                </div>
            </div>
        `;
    };
    
    const highlightElement = (element) => {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        // Create highlight box
        currentHighlight = document.createElement('div');
        currentHighlight.style.cssText = `
            position: absolute;
            top: ${rect.top + scrollTop - 5}px;
            left: ${rect.left + scrollLeft - 5}px;
            width: ${rect.width + 10}px;
            height: ${rect.height + 10}px;
            border: 3px solid #007bff;
            border-radius: 8px;
            background: rgba(0, 123, 255, 0.1);
            z-index: 10000;
            pointer-events: none;
            box-shadow: 0 0 20px rgba(0, 123, 255, 0.5);
            animation: guidePulse 2s infinite;
        `;
        
        // Add pulsing animation
        if (!document.getElementById('guide-animations')) {
            const style = document.createElement('style');
            style.id = 'guide-animations';
            style.textContent = `
                @keyframes guidePulse {
                    0% { box-shadow: 0 0 20px rgba(0, 123, 255, 0.5); }
                    50% { box-shadow: 0 0 30px rgba(0, 123, 255, 0.8); }
                    100% { box-shadow: 0 0 20px rgba(0, 123, 255, 0.5); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(currentHighlight);
        
        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };
    
    // Global functions for buttons
    window.nextStep = () => {
        currentStep++;
        showStep(currentStep);
    };
    
    window.previousStep = () => {
        currentStep--;
        showStep(currentStep);
    };
    
    window.endGuide = () => {
        console.log('🏁 Ending guide');
        if (overlay) overlay.remove();
        if (guideContainer) guideContainer.remove();
        if (currentHighlight) currentHighlight.remove();
        
        // Remove resize listener
        window.removeEventListener('resize', window.repositionGuide);
        window.removeEventListener('scroll', window.repositionGuide);
        
        // Clean up global functions
        delete window.nextStep;
        delete window.previousStep;
        delete window.endGuide;
        delete window.repositionGuide;
        
        // Clear any stored guide data
        sessionStorage.removeItem('continueGuide');
        
        // If this is a mock window (opened for guided tour), close it automatically
        if (window.location.pathname.includes('/help/mock-simulation/')) {
            setTimeout(() => {
                window.close();
            }, 1000);
        }
    };
    
    // Reposition guide when window resizes or scrolls
    window.repositionGuide = () => {
        if (currentTargetElement) {
            positionGuideContainer(currentTargetElement, currentPlacement);
            // Also update highlight position
            if (currentHighlight) {
                currentHighlight.remove();
                highlightElement(currentTargetElement);
            }
        }
    };
    
    // Add event listeners for repositioning
    window.addEventListener('resize', window.repositionGuide);
    window.addEventListener('scroll', window.repositionGuide);
    
    // Start with first step
    showStep(currentStep);
};