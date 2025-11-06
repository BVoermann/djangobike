/**
 * Sales Tutorial System
 * A comprehensive, standalone interactive tutorial for the sales process
 */

// Tutorial State Manager
class SalesTutorialManager {
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
                title: 'Schritt 1: Willkommen im Verkauf',
                description: 'Im Verkaufs-Tab können Sie Ihre produzierten Fahrräder an verschiedene Märkte verkaufen. Hier legen Sie Verkaufspreise fest und wählen die besten Märkte für Ihre Produkte.',
                placement: 'bottom',
                preActions: async () => {
                    // No pre-actions needed for first step
                }
            },
            {
                target: '.col-lg-3:nth-child(1) .card',
                title: 'Schritt 2: Verfügbare Fahrräder',
                description: 'Diese Zahl zeigt, wie viele Fahrräder Sie insgesamt zum Verkauf verfügbar haben. Dies sind alle produzierten Fahrräder in Ihrem Lager.',
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
                title: 'Schritt 3: Verfügbare Märkte',
                description: 'Hier sehen Sie, wie viele verschiedene Märkte für den Verkauf zur Verfügung stehen. Jeder Markt hat unterschiedliche Eigenschaften und Transportkosten.',
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
                title: 'Schritt 4: Geplanter Umsatz',
                description: 'Diese Anzeige zeigt den geplanten Gesamtumsatz basierend auf Ihren Verkaufspreisen und -mengen. Sie aktualisiert sich automatisch.',
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
                title: 'Schritt 5: Transportkosten',
                description: 'Hier sehen Sie die gesamten Transportkosten, die vom Umsatz abgezogen werden. Unterschiedliche Märkte haben unterschiedliche Transportkosten.',
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
                target: '.table-responsive',
                title: 'Schritt 6: Fahrrad-Verkaufsübersicht',
                description: 'In dieser Tabelle sehen Sie alle verfügbaren Fahrräder. Für jedes Fahrrad können Sie einen Markt wählen, einen Verkaufspreis festlegen und die Verkaufsmenge bestimmen.',
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
                target: 'tbody tr:first-child .bike-icon',
                title: 'Schritt 7: Fahrradtyp und Segment',
                description: 'Hier sehen Sie den Fahrradtyp und das Preissegment (Günstig/Standard/Premium). Verschiedene Segmente haben unterschiedliche Preisspannen.',
                placement: 'right',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child .bike-icon');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child td:nth-child(2)',
                title: 'Schritt 8: Verfügbare Menge',
                description: 'Diese Zahl zeigt, wie viele Fahrräder dieses Typs und Segments Sie auf Lager haben und verkaufen können.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child td:nth-child(2)');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child td:nth-child(3)',
                title: 'Schritt 9: Produktionskosten',
                description: 'Dies sind die durchschnittlichen Produktionskosten pro Fahrrad. Ihr Verkaufspreis sollte höher sein, um Gewinn zu erzielen!',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child td:nth-child(3)');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child .market-select',
                title: 'Schritt 10: Markt auswählen',
                description: 'Wählen Sie hier den Zielmarkt für den Verkauf. Jeder Markt hat unterschiedliche Standorte und Transportkosten. Wählen Sie einen Markt aus, um die Preis- und Mengeneingabe zu aktivieren.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child .market-select');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child .transport-cost-display',
                title: 'Schritt 11: Transportkosten pro Einheit',
                description: 'Hier sehen Sie die Transportkosten pro Fahrrad für den gewählten Markt. Diese werden vom Verkaufspreis abgezogen.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child .transport-cost-display');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child .price-input',
                title: 'Schritt 12: Verkaufspreis festlegen',
                description: 'Geben Sie hier den gewünschten Verkaufspreis pro Fahrrad ein. Beachten Sie den erlaubten Preisbereich (unter dem Eingabefeld angezeigt). Grün = gültiger Preis, Rot = zu niedrig, Orange = zu hoch.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child .price-input');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: 'tbody tr:first-child .quantity-input',
                title: 'Schritt 13: Verkaufsmenge eingeben',
                description: 'Geben Sie hier ein, wie viele Fahrräder Sie verkaufen möchten. Die maximale Menge entspricht Ihrem Lagerbestand.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('tbody tr:first-child .quantity-input');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.market-card:first-child',
                title: 'Schritt 14: Markt-Übersicht',
                description: 'Diese Karten zeigen eine Zusammenfassung für jeden Markt: Standort, Transportkosten pro Fahrrad und eine Liste aller für diesen Markt geplanten Verkäufe.',
                placement: 'top',
                preActions: async () => {
                    const target = document.querySelector('.market-card:first-child');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '.market-card:first-child .market-info',
                title: 'Schritt 15: Markt-Details',
                description: 'Hier sehen Sie den Standort des Marktes und die Transportkosten pro Fahrrad. Märkte mit niedrigeren Transportkosten sind profitabler!',
                placement: 'bottom',
                preActions: async () => {
                    const target = document.querySelector('.market-card:first-child .market-info');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.wait(500);
                    }
                }
            },
            {
                target: '#grand-total',
                title: 'Schritt 16: Nettoertrag',
                description: 'Dies ist Ihr gesamter Nettoertrag: Umsatz minus Transportkosten. Dies ist der Betrag, der Ihrem Konto gutgeschrieben wird.',
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
                target: 'button[type="submit"]',
                title: 'Schritt 17: Verkaufsaufträge erstellen',
                description: 'Wenn Sie alle Verkaufspreise und -mengen festgelegt haben, klicken Sie hier, um die Verkaufsaufträge zu erstellen. Die Fahrräder werden verkauft und der Erlös wird Ihrem Konto gutgeschrieben.',
                placement: 'left',
                preActions: async () => {
                    const target = document.querySelector('button[type="submit"]');
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
        console.log('🎓 Starting Sales Tutorial');
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
            border: 3px solid #28a745;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(40, 167, 69, 0.8);
            z-index: 999999;
            pointer-events: auto;
            transition: all 0.3s ease;
            display: none;
        `;

        // Add pulsing animation (with green color for sales)
        if (!document.getElementById('tutorial-animations')) {
            const style = document.createElement('style');
            style.id = 'tutorial-animations';
            style.textContent = `
                @keyframes tutorialPulse {
                    0% {
                        box-shadow: 0 0 20px rgba(40, 167, 69, 0.8);
                        border-color: #28a745;
                    }
                    50% {
                        box-shadow: 0 0 40px rgba(40, 167, 69, 1);
                        border-color: #1e7e34;
                    }
                    100% {
                        box-shadow: 0 0 20px rgba(40, 167, 69, 0.8);
                        border-color: #28a745;
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
                        <div style="background: linear-gradient(90deg, #28a745 0%, #1e7e34 100%); height: 100%; width: ${progress}%; transition: width 0.3s ease;"></div>
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
                        <button id="tutorial-next-btn" style="flex: 2; padding: 12px 20px; background: ${isLastStep ? '#28a745' : '#28a745'}; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease;">
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
        alert('🎉 Glückwunsch!\n\nSie haben das Verkaufs-Tutorial erfolgreich abgeschlossen.\n\nSie wissen nun, wie Sie Ihre Fahrräder gewinnbringend an verschiedene Märkte verkaufen können.');
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
window.SalesTutorialManager = SalesTutorialManager;

// Auto-start if tutorial flag is set
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tutorial') === 'true') {
        console.log('🎓 Tutorial mode detected, starting in 2 seconds...');
        setTimeout(() => {
            const tutorial = new SalesTutorialManager();
            tutorial.start();

            // Add resize and scroll listeners
            window.addEventListener('resize', () => tutorial.handleResize());
            window.addEventListener('scroll', () => tutorial.handleScroll());
        }, 2000);
    }
});
