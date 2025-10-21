/**
 * Procurement Tutorial System
 * A comprehensive, standalone interactive tutorial for the procurement process
 */

// Tutorial State Manager
class ProcurementTutorialManager {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 0;
        this.isActive = false;
        this.spotlight = null;
        this.notificationBox = null;
        this.currentTargetElement = null;

        // Define tutorial steps
        this.steps = [
            {
                target: '#supplierDropdown',
                title: 'Schritt 1: Lieferant auswählen',
                description: 'Klicken Sie auf dieses Dropdown-Menü, um einen Lieferanten auszuwählen. Jeder Lieferant bietet unterschiedliche Qualitätsstufen, Lieferzeiten und Zahlungsbedingungen.',
                placement: 'bottom',
                preActions: async () => {
                    // No pre-actions needed for first step
                }
            },
            {
                target: '.supplier-option:first-child',
                title: 'Schritt 2: Lieferant wählen',
                description: 'Wählen Sie einen beliebigen Lieferanten aus der Liste aus. Achten Sie auf die Qualitätsstufe, Lieferzeit und Zahlungsbedingungen.',
                placement: 'right',
                preActions: async () => {
                    // Open dropdown if not already open
                    const dropdown = document.getElementById('supplierDropdown');
                    if (dropdown && !dropdown.nextElementSibling.classList.contains('show')) {
                        dropdown.click();
                        await this.wait(300);
                    }
                }
            },
            {
                target: '.col-lg-3:first-child .card',
                title: 'Schritt 3: Budget überprüfen',
                description: 'Hier sehen Sie Ihr verfügbares Budget. Achten Sie darauf, dass Sie nicht mehr ausgeben als verfügbar ist!',
                placement: 'right',
                preActions: async () => {
                    // Ensure a supplier is selected
                    await this.ensureSupplierSelected();
                    // Scroll to budget card
                    const target = document.querySelector('.col-lg-3:first-child .card');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '#supplier-badges',
                title: 'Schritt 4: Lieferanten-Informationen',
                description: 'Diese Badges zeigen wichtige Informationen: Qualitätsstufe, Lieferzeit und Zahlungsziel des ausgewählten Lieferanten.',
                placement: 'bottom',
                preActions: async () => {
                    const target = document.querySelector('#supplier-badges');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '#bikeTypeDropdown',
                title: 'Schritt 5: Komponenten filtern (optional)',
                description: 'Mit diesem Dropdown können Sie die Komponenten nach Fahrradtyp filtern. Dies zeigt nur die Teile, die Sie für einen bestimmten Fahrradtyp benötigen.',
                placement: 'bottom',
                preActions: async () => {
                    const target = document.querySelector('#bikeTypeDropdown');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.table-responsive',
                title: 'Schritt 6: Komponenten bestellen',
                description: 'In dieser Tabelle sehen Sie alle verfügbaren Komponenten. Geben Sie die gewünschte Menge in die Eingabefelder ein und beobachten Sie, wie sich der Gesamtpreis ändert.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.table-responsive');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.procurement-input:first-child',
                title: 'Schritt 7: Menge eingeben',
                description: 'Geben Sie hier eine Menge ein (z.B. 10). Sie können dies für mehrere Komponenten tun. Beobachten Sie, wie sich der Gesamtpreis aktualisiert.',
                placement: 'right',
                preActions: async () => {
                    const target = document.querySelector('.procurement-input:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '#grand-total',
                title: 'Schritt 8: Gesamtkosten prüfen',
                description: 'Hier sehen Sie den Gesamtbetrag Ihrer Bestellung. Stellen Sie sicher, dass dieser Betrag Ihr verfügbares Budget nicht überschreitet.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('#grand-total');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.btn-primary.btn-lg.px-4',
                title: 'Schritt 9: Bestellung aufgeben',
                description: 'Wenn Sie mit Ihrer Auswahl zufrieden sind, klicken Sie auf diesen Button, um die Bestellung aufzugeben. Die Komponenten werden zu Ihrem Lagerbestand hinzugefügt.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.btn-primary.btn-lg.px-4');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            }
        ];

        this.totalSteps = this.steps.length;
    }

    // Helper function to wait
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Ensure a supplier is selected for the tutorial
    async ensureSupplierSelected() {
        const supplierDetails = document.getElementById('supplier-details');
        if (supplierDetails && supplierDetails.style.display === 'none') {
            // Auto-select first supplier
            const firstSupplierOption = document.querySelector('.supplier-option:first-child');
            if (firstSupplierOption) {
                firstSupplierOption.click();
                await this.wait(500);
            }
        }
    }

    // Start the tutorial
    async start() {
        console.log('🎓 Starting Procurement Tutorial');
        this.isActive = true;
        this.currentStep = 0;

        // Create spotlight (no overlay - grey veil removed)
        this.createSpotlight();

        // Create notification box
        this.createNotificationBox();

        // Show first step
        await this.showStep(0);
    }

    // Create spotlight effect
    createSpotlight() {
        this.spotlight = document.createElement('div');
        this.spotlight.id = 'tutorial-spotlight';
        this.spotlight.style.cssText = `
            position: absolute;
            background: transparent;
            border: 3px solid #007bff;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 123, 255, 0.8);
            z-index: 999999;
            pointer-events: auto;
            transition: all 0.3s ease;
            display: none;
        `;

        // Add pulsing animation (without grey overlay)
        if (!document.getElementById('tutorial-animations')) {
            const style = document.createElement('style');
            style.id = 'tutorial-animations';
            style.textContent = `
                @keyframes tutorialPulse {
                    0% {
                        box-shadow: 0 0 20px rgba(0, 123, 255, 0.8);
                        border-color: #007bff;
                    }
                    50% {
                        box-shadow: 0 0 40px rgba(0, 123, 255, 1);
                        border-color: #0056b3;
                    }
                    100% {
                        box-shadow: 0 0 20px rgba(0, 123, 255, 0.8);
                        border-color: #007bff;
                    }
                }
                #tutorial-spotlight {
                    animation: tutorialPulse 2s infinite;
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(this.spotlight);
    }

    // Create notification box
    createNotificationBox() {
        this.notificationBox = document.createElement('div');
        this.notificationBox.id = 'tutorial-notification';
        this.notificationBox.style.cssText = `
            position: absolute;
            width: 400px;
            max-width: 90vw;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 1000000;
            font-family: Arial, sans-serif;
            pointer-events: auto;
        `;
        document.body.appendChild(this.notificationBox);
    }

    // Show a specific step
    async showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.totalSteps) {
            return;
        }

        this.currentStep = stepIndex;
        const step = this.steps[stepIndex];

        console.log(`📍 Showing step ${stepIndex + 1}: ${step.title}`);

        // Execute pre-actions
        if (step.preActions) {
            console.log('⚙️ Executing pre-actions...');
            await step.preActions();
        }

        // Find target element
        const targetElement = document.querySelector(step.target);
        if (!targetElement) {
            console.error(`❌ Target element not found: ${step.target}`);
            // Skip to next step or show error
            return;
        }

        this.currentTargetElement = targetElement;

        // Scroll element into view
        targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });

        await this.wait(600);

        // Position spotlight on target
        this.positionSpotlight(targetElement);

        // Position notification box
        this.positionNotificationBox(targetElement, step.placement);

        // Update notification content
        this.updateNotificationContent(step);
    }

    // Position spotlight on target element
    positionSpotlight(element) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        this.spotlight.style.display = 'block';
        this.spotlight.style.top = `${rect.top + scrollTop - 8}px`;
        this.spotlight.style.left = `${rect.left + scrollLeft - 8}px`;
        this.spotlight.style.width = `${rect.width + 16}px`;
        this.spotlight.style.height = `${rect.height + 16}px`;
    }

    // Position notification box adjacent to target
    positionNotificationBox(element, placement) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        const boxWidth = 400;
        const boxHeight = this.notificationBox.offsetHeight || 200;
        const margin = 20;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let top, left;
        let finalPlacement = placement;

        // Calculate position based on placement
        switch (placement) {
            case 'top':
                top = rect.top + scrollTop - boxHeight - margin;
                left = rect.left + scrollLeft + (rect.width / 2) - (boxWidth / 2);
                break;
            case 'bottom':
                top = rect.bottom + scrollTop + margin;
                left = rect.left + scrollLeft + (rect.width / 2) - (boxWidth / 2);
                break;
            case 'left':
                top = rect.top + scrollTop + (rect.height / 2) - (boxHeight / 2);
                left = rect.left + scrollLeft - boxWidth - margin;
                break;
            case 'right':
            default:
                top = rect.top + scrollTop + (rect.height / 2) - (boxHeight / 2);
                left = rect.right + scrollLeft + margin;
                break;
        }

        // Adjust if going off-screen
        if (left + boxWidth > scrollLeft + viewportWidth - margin) {
            left = rect.left + scrollLeft - boxWidth - margin;
            finalPlacement = 'left';
        }
        if (left < scrollLeft + margin) {
            left = rect.right + scrollLeft + margin;
            finalPlacement = 'right';
            if (left + boxWidth > scrollLeft + viewportWidth - margin) {
                left = Math.max(scrollLeft + margin, (viewportWidth - boxWidth) / 2 + scrollLeft);
                top = rect.bottom + scrollTop + margin;
                finalPlacement = 'bottom';
            }
        }

        if (top < scrollTop + margin) {
            top = rect.bottom + scrollTop + margin;
            finalPlacement = 'bottom';
        }
        if (top + boxHeight > scrollTop + viewportHeight - margin) {
            top = Math.max(scrollTop + margin, scrollTop + viewportHeight - boxHeight - margin);
        }

        this.notificationBox.style.top = top + 'px';
        this.notificationBox.style.left = left + 'px';
    }

    // Update notification box content
    updateNotificationContent(step) {
        const progress = Math.round(((this.currentStep + 1) / this.totalSteps) * 100);
        const isFirstStep = this.currentStep === 0;
        const isLastStep = this.currentStep === this.totalSteps - 1;

        this.notificationBox.innerHTML = `
            <div style="padding: 25px;">
                <!-- Progress bar -->
                <div style="margin-bottom: 20px;">
                    <div style="background: #e9ecef; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #007bff 0%, #0056b3 100%); height: 100%; width: ${progress}%; transition: width 0.3s ease;"></div>
                    </div>
                    <div style="text-align: center; font-size: 13px; color: #6c757d; margin-top: 8px; font-weight: 500;">
                        Schritt ${this.currentStep + 1} von ${this.totalSteps}
                    </div>
                </div>

                <!-- Title -->
                <h4 style="margin: 0 0 12px 0; color: #212529; font-size: 20px; font-weight: 700;">
                    ${step.title}
                </h4>

                <!-- Description -->
                <p style="margin: 0 0 25px 0; color: #495057; line-height: 1.6; font-size: 15px;">
                    ${step.description}
                </p>

                <!-- Navigation buttons -->
                <div style="display: flex; gap: 10px; justify-content: space-between;">
                    <div style="display: flex; gap: 10px; flex: 1;">
                        ${!isFirstStep ? `
                            <button id="tutorial-prev-btn" style="flex: 1; padding: 12px 20px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease;">
                                ← Zurück
                            </button>
                        ` : ''}
                        <button id="tutorial-next-btn" style="flex: 2; padding: 12px 20px; background: ${isLastStep ? '#28a745' : '#007bff'}; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease;">
                            ${isLastStep ? '🎉 Fertig' : 'Weiter →'}
                        </button>
                    </div>
                    <button id="tutorial-exit-btn" style="padding: 12px 16px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s ease;">
                        ✕
                    </button>
                </div>
            </div>
        `;

        // Add hover effects
        const style = document.createElement('style');
        style.textContent = `
            #tutorial-prev-btn:hover, #tutorial-next-btn:hover, #tutorial-exit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            #tutorial-prev-btn:active, #tutorial-next-btn:active, #tutorial-exit-btn:active {
                transform: translateY(0);
            }
        `;
        if (!document.getElementById('tutorial-button-styles')) {
            style.id = 'tutorial-button-styles';
            document.head.appendChild(style);
        }

        // Attach event listeners
        const prevBtn = document.getElementById('tutorial-prev-btn');
        const nextBtn = document.getElementById('tutorial-next-btn');
        const exitBtn = document.getElementById('tutorial-exit-btn');

        if (prevBtn) {
            prevBtn.onclick = () => this.previousStep();
        }

        if (nextBtn) {
            nextBtn.onclick = () => {
                if (isLastStep) {
                    this.finish();
                } else {
                    this.nextStep();
                }
            };
        }

        if (exitBtn) {
            exitBtn.onclick = () => this.exit();
        }
    }

    // Navigate to previous step
    async previousStep() {
        if (this.currentStep > 0) {
            await this.showStep(this.currentStep - 1);
        }
    }

    // Navigate to next step
    async nextStep() {
        if (this.currentStep < this.totalSteps - 1) {
            await this.showStep(this.currentStep + 1);
        }
    }

    // Exit tutorial early
    exit() {
        if (confirm('Möchten Sie das Tutorial wirklich beenden?')) {
            this.cleanup();

            // Close window if opened as popup
            if (window.opener && !window.opener.closed) {
                window.close();
            }
        }
    }

    // Finish tutorial
    finish() {
        alert('🎉 Glückwunsch!\n\nSie haben das Einkaufs-Tutorial erfolgreich abgeschlossen.\n\nSie wissen nun, wie Sie Komponenten von Lieferanten bestellen können.');
        this.cleanup();

        // Close window if opened as popup
        if (window.opener && !window.opener.closed) {
            window.close();
        }
    }

    // Clean up tutorial elements
    cleanup() {
        console.log('🧹 Cleaning up tutorial');
        this.isActive = false;

        if (this.spotlight) {
            this.spotlight.remove();
            this.spotlight = null;
        }

        if (this.notificationBox) {
            this.notificationBox.remove();
            this.notificationBox = null;
        }

        // Remove animations
        const animations = document.getElementById('tutorial-animations');
        if (animations) {
            animations.remove();
        }

        const buttonStyles = document.getElementById('tutorial-button-styles');
        if (buttonStyles) {
            buttonStyles.remove();
        }
    }

    // Handle window resize
    handleResize() {
        if (this.isActive && this.currentTargetElement) {
            this.positionSpotlight(this.currentTargetElement);
            const step = this.steps[this.currentStep];
            this.positionNotificationBox(this.currentTargetElement, step.placement);
        }
    }

    // Handle scroll
    handleScroll() {
        if (this.isActive && this.currentTargetElement) {
            this.positionSpotlight(this.currentTargetElement);
            const step = this.steps[this.currentStep];
            this.positionNotificationBox(this.currentTargetElement, step.placement);
        }
    }
}

// Export for global use
window.ProcurementTutorialManager = ProcurementTutorialManager;

// Auto-start if tutorial flag is set
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tutorial') === 'true') {
        console.log('🎓 Tutorial mode detected, starting in 2 seconds...');
        setTimeout(() => {
            const tutorial = new ProcurementTutorialManager();
            tutorial.start();

            // Add resize and scroll listeners
            window.addEventListener('resize', () => tutorial.handleResize());
            window.addEventListener('scroll', () => tutorial.handleScroll());
        }, 2000);
    }
});
