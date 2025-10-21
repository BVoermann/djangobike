/**
 * Warehouse Tutorial System
 * A comprehensive, standalone interactive tutorial for the warehouse management process
 */

// Tutorial State Manager
class WarehouseTutorialManager {
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
                target: '.display-4',
                title: 'Schritt 1: Willkommen im Lager',
                description: 'Im Lager-Tab sehen Sie eine Übersicht über alle Ihre Lagerhallen, die gelagerten Komponenten und fertigen Fahrräder sowie die verfügbare Kapazität.',
                placement: 'bottom',
                preActions: async () => {
                    // No pre-actions needed for first step
                }
            },
            {
                target: '.col-lg-3:nth-child(1) .card',
                title: 'Schritt 2: Anzahl Lagerhallen',
                description: 'Diese Karte zeigt, wie viele Lagerhallen Sie besitzen. Jede Lagerhalle bietet Lagerkapazität für Komponenten und Fahrräder.',
                placement: 'right',
                preActions: async () => {
                    const target = document.querySelector('.col-lg-3:nth-child(1) .card');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.col-lg-3:nth-child(2) .card',
                title: 'Schritt 3: Gesamtkapazität',
                description: 'Hier sehen Sie die gesamte Lagerkapazität in Quadratmetern (m²). Dies ist die Summe aller Ihrer Lagerhallen.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('.col-lg-3:nth-child(2) .card');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.col-lg-3:nth-child(3) .card',
                title: 'Schritt 4: Komponententypen',
                description: 'Diese Zahl zeigt die Anzahl unterschiedlicher Komponententypen, die Sie im Lager haben.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('.col-lg-3:nth-child(3) .card');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.col-lg-3:nth-child(4) .card',
                title: 'Schritt 5: Monatliche Miete',
                description: 'Hier sehen Sie die gesamten monatlichen Mietkosten für alle Ihre Lagerhallen. Diese Kosten werden jeden Monat automatisch abgebucht.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('.col-lg-3:nth-child(4) .card');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.btn-success.btn-lg',
                title: 'Schritt 6: Neues Lager kaufen',
                description: 'Mit diesem Button können Sie zusätzliche Lagerhallen erwerben, wenn Sie mehr Lagerkapazität benötigen.',
                placement: 'bottom',
                preActions: async () => {
                    const target = document.querySelector('.btn-success.btn-lg');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .card-header',
                title: 'Schritt 7: Lager-Information',
                description: 'Jede Lagerhalle hat einen Namen, einen Standort und monatliche Mietkosten. Diese Informationen finden Sie hier im Header.',
                placement: 'bottom',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .card-header');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .progress',
                title: 'Schritt 8: Kapazitätsanzeige',
                description: 'Dieser Balken zeigt die Auslastung der Lagerhalle. Grün = wenig belegt, Gelb = mittel belegt, Rot = fast voll. Achten Sie darauf, dass Sie nicht über 100% gehen!',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .progress');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .col-lg-6:first-child',
                title: 'Schritt 9: Gelagerte Komponenten',
                description: 'In diesem Bereich sehen Sie alle Komponenten, die in dieser Lagerhalle gelagert sind. Jede Zeile zeigt den Komponententyp, die Menge und den Platzbedarf in m².',
                placement: 'right',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .col-lg-6:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .col-lg-6:first-child tbody tr:first-child',
                title: 'Schritt 10: Komponenten-Details',
                description: 'Jede Komponente zeigt: Name, Menge (in Stück) und den Platzbedarf (in m²). Die Farbcodierung der Badges zeigt den Bestandsstatus: Grün = viel, Gelb = mittel, Rot = wenig.',
                placement: 'right',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .col-lg-6:first-child tbody tr:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .col-lg-6:last-child',
                title: 'Schritt 11: Gelagerte Fahrräder',
                description: 'Auf der rechten Seite sehen Sie alle fertigen Fahrräder, die bereit zum Verkauf sind. Die Fahrräder sind nach Typ und Preissegment gruppiert.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .col-lg-6:last-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .col-lg-6:last-child tbody tr:first-child',
                title: 'Schritt 12: Fahrrad-Details',
                description: 'Für jede Fahrradgruppe sehen Sie: Fahrradtyp, Preissegment (Günstig/Standard/Premium), Anzahl und Platzbedarf. Diese Fahrräder können im Verkaufs-Tab verkauft werden.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .col-lg-6:last-child tbody tr:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .card-footer .col-6:first-child',
                title: 'Schritt 13: Auslastung im Detail',
                description: 'Hier sehen Sie die prozentuale Auslastung der Lagerhalle. Dies hilft Ihnen zu entscheiden, ob Sie ein neues Lager benötigen.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .card-footer .col-6:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.warehouse-card:first-child .card-footer .col-6:last-child',
                title: 'Schritt 14: Monatliche Kosten',
                description: 'Hier sehen Sie die monatlichen Mietkosten für diese spezifische Lagerhalle. Diese Kosten werden automatisch von Ihrem Konto abgebucht.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.warehouse-card:first-child .card-footer .col-6:last-child');
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

    // Start the tutorial
    async start() {
        console.log('🎓 Starting Warehouse Tutorial');
        this.isActive = true;
        this.currentStep = 0;

        // Create spotlight (no overlay)
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
            border: 3px solid #17a2b8;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(23, 162, 184, 0.8);
            z-index: 999999;
            pointer-events: auto;
            transition: all 0.3s ease;
            display: none;
        `;

        // Add pulsing animation (with teal/cyan color for warehouse)
        if (!document.getElementById('tutorial-animations')) {
            const style = document.createElement('style');
            style.id = 'tutorial-animations';
            style.textContent = `
                @keyframes tutorialPulse {
                    0% {
                        box-shadow: 0 0 20px rgba(23, 162, 184, 0.8);
                        border-color: #17a2b8;
                    }
                    50% {
                        box-shadow: 0 0 40px rgba(23, 162, 184, 1);
                        border-color: #138496;
                    }
                    100% {
                        box-shadow: 0 0 20px rgba(23, 162, 184, 0.8);
                        border-color: #17a2b8;
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
                        <div style="background: linear-gradient(90deg, #17a2b8 0%, #138496 100%); height: 100%; width: ${progress}%; transition: width 0.3s ease;"></div>
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
                        <button id="tutorial-next-btn" style="flex: 2; padding: 12px 20px; background: ${isLastStep ? '#28a745' : '#17a2b8'}; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease;">
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
        alert('🎉 Glückwunsch!\n\nSie haben das Lager-Tutorial erfolgreich abgeschlossen.\n\nSie wissen nun, wie Sie Ihren Lagerbestand überwachen und verwalten können.');
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
window.WarehouseTutorialManager = WarehouseTutorialManager;

// Auto-start if tutorial flag is set
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tutorial') === 'true') {
        console.log('🎓 Tutorial mode detected, starting in 2 seconds...');
        setTimeout(() => {
            const tutorial = new WarehouseTutorialManager();
            tutorial.start();

            // Add resize and scroll listeners
            window.addEventListener('resize', () => tutorial.handleResize());
            window.addEventListener('scroll', () => tutorial.handleScroll());
        }, 2000);
    }
});
