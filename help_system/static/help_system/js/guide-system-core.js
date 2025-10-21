/**
 * Interactive Guide System - Core Functions
 * This file contains the core guide functionality that can be used on any page
 */

async function createInteractiveGuide(guide, startStep = 0, isPopup = false) {
    console.log('🎬 Creating interactive guide:', guide.title, 'starting at step', startStep, 'isPopup:', isPopup);

    // Create grey overlay that covers entire page
    const overlay = document.createElement('div');
    overlay.id = 'guide-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.75);
        z-index: 9999;
        pointer-events: none;
        transition: background 0.3s ease;
    `;
    document.body.appendChild(overlay);

    // Create a spotlight div that will cut through the overlay for highlighted elements
    const spotlight = document.createElement('div');
    spotlight.id = 'guide-spotlight';
    spotlight.style.cssText = `
        position: absolute;
        background: transparent;
        border: 3px solid #007bff;
        border-radius: 8px;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 20px rgba(0, 123, 255, 0.8);
        z-index: 10000;
        pointer-events: none;
        transition: all 0.3s ease;
        display: none;
    `;
    document.body.appendChild(spotlight);

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
    let currentTargetElement = null;
    let currentPlacement = 'right';

    const expandElementIfNeeded = async (targetElement) => {
        console.log('🔍 Checking if element needs expansion:', targetElement);
        let expansionsPerformed = 0;

        // Check if element is inside a tab pane
        const tabPane = targetElement.closest('.tab-pane');
        if (tabPane && !tabPane.classList.contains('active')) {
            const tabId = tabPane.id;
            if (tabId) {
                const tabButton = document.querySelector(`[data-bs-toggle="tab"][data-bs-target="#${tabId}"], [data-bs-toggle="pill"][data-bs-target="#${tabId}"]`);
                if (tabButton) {
                    console.log('🔄 Switching to tab:', tabId);
                    tabButton.click();
                    expansionsPerformed++;
                    await new Promise(resolve => setTimeout(resolve, 600)); // Increased for animation
                }
            }
        }

        // Check if element is inside a dropdown menu
        const dropdownMenu = targetElement.closest('.dropdown-menu');
        if (dropdownMenu) {
            // Find the dropdown toggle button
            const dropdown = dropdownMenu.previousElementSibling;
            if (dropdown && (dropdown.classList.contains('dropdown-toggle') || dropdown.hasAttribute('data-bs-toggle'))) {
                // Check if dropdown is not already shown
                if (!dropdownMenu.classList.contains('show')) {
                    console.log('📂 Opening dropdown menu for:', targetElement);
                    dropdown.click();
                    expansionsPerformed++;
                    // Wait for dropdown animation
                    await new Promise(resolve => setTimeout(resolve, 600)); // Increased
                }
            }
        }

        // Check if element is a dropdown toggle itself
        if (targetElement.classList.contains('dropdown-toggle') ||
            targetElement.hasAttribute('data-bs-toggle')) {
            const toggleType = targetElement.getAttribute('data-bs-toggle');

            if (toggleType === 'dropdown') {
                const nextElement = targetElement.nextElementSibling;
                if (nextElement && nextElement.classList.contains('dropdown-menu') &&
                    !nextElement.classList.contains('show')) {
                    console.log('📂 Opening dropdown toggle:', targetElement);
                    targetElement.click();
                    expansionsPerformed++;
                    await new Promise(resolve => setTimeout(resolve, 600)); // Increased
                }
            }
        }

        // Check if element is inside one or more collapse elements (can be nested)
        // We need to expand ALL parent collapses, starting from the outermost
        const collapseParents = [];
        let currentElement = targetElement;
        while (currentElement && currentElement !== document.body) {
            if (currentElement.classList && currentElement.classList.contains('collapse')) {
                collapseParents.unshift(currentElement); // Add to beginning (outermost first)
            }
            currentElement = currentElement.parentElement;
        }

        // Expand all collapse parents from outermost to innermost
        if (collapseParents.length > 0) {
            console.log(`📖 Found ${collapseParents.length} collapsed parent(s) to expand`);
        }
        for (const collapseParent of collapseParents) {
            if (!collapseParent.classList.contains('show')) {
                const collapseId = collapseParent.id;
                if (collapseId) {
                    const collapseToggle = document.querySelector(`[data-bs-toggle="collapse"][data-bs-target="#${collapseId}"], [data-bs-toggle="collapse"][href="#${collapseId}"]`);
                    if (collapseToggle) {
                        console.log('📖 Expanding collapse:', collapseId);
                        collapseToggle.click();
                        expansionsPerformed++;
                        await new Promise(resolve => setTimeout(resolve, 700)); // Wait for animation
                    }
                }
            }
        }

        // Check if element is inside a modal
        const modalParent = targetElement.closest('.modal');
        if (modalParent && !modalParent.classList.contains('show')) {
            const modalId = modalParent.id;
            if (modalId) {
                console.log('🪟 Opening modal:', modalId);
                const modal = new bootstrap.Modal(modalParent);
                modal.show();
                expansionsPerformed++;
                await new Promise(resolve => setTimeout(resolve, 700)); // Increased for modal
            }
        }

        // Check if element has display: none or visibility: hidden
        const styles = window.getComputedStyle(targetElement);
        if (styles.display === 'none' || styles.visibility === 'hidden') {
            console.log('👁️ Element is hidden, checking for show/hide mechanisms');

            // Try to find parent with display:none
            let parent = targetElement.parentElement;
            while (parent && parent !== document.body) {
                const parentStyles = window.getComputedStyle(parent);
                if (parentStyles.display === 'none') {
                    console.log('👁️ Making parent visible:', parent);
                    // Try to show the parent
                    parent.style.display = 'block';
                    await new Promise(resolve => setTimeout(resolve, 150));
                    break;
                }
                parent = parent.parentElement;
            }
        }

        // Extra wait to ensure everything is rendered and animations complete
        await new Promise(resolve => setTimeout(resolve, 300)); // Increased

        if (expansionsPerformed > 0) {
            console.log(`✅ Element expansion complete: ${expansionsPerformed} expansion(s) performed`);
        } else {
            console.log('✅ Element expansion check complete: No expansions needed');
        }
    };

    const showCenteredNotification = (title, message) => {
        return new Promise((resolve) => {
            // Create modal backdrop
            const backdrop = document.createElement('div');
            backdrop.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                z-index: 10001;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            // Create modal content
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                animation: modalFadeIn 0.3s ease;
            `;

            // Add animation keyframes
            if (!document.getElementById('modal-animations')) {
                const style = document.createElement('style');
                style.id = 'modal-animations';
                style.textContent = `
                    @keyframes modalFadeIn {
                        from {
                            opacity: 0;
                            transform: scale(0.9);
                        }
                        to {
                            opacity: 1;
                            transform: scale(1);
                        }
                    }
                `;
                document.head.appendChild(style);
            }

            modal.innerHTML = `
                <div style="text-align: center;">
                    <h3 style="margin: 0 0 20px 0; color: #333; font-size: 24px;">
                        ${title}
                    </h3>
                    <p style="margin: 0 0 25px 0; color: #555; line-height: 1.6; font-size: 16px; white-space: pre-line;">
                        ${message}
                    </p>
                    <button id="notification-ok-btn" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 12px 40px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s ease;
                    " onmouseover="this.style.background='#0056b3'; this.style.transform='translateY(-2px)'"
                       onmouseout="this.style.background='#007bff'; this.style.transform='translateY(0)'">
                        OK
                    </button>
                </div>
            `;

            backdrop.appendChild(modal);
            document.body.appendChild(backdrop);

            // Handle OK button click
            const okButton = document.getElementById('notification-ok-btn');
            okButton.addEventListener('click', () => {
                backdrop.remove();
                resolve();
            });

            // Also allow closing with Enter key
            const handleKeyPress = (e) => {
                if (e.key === 'Enter') {
                    backdrop.remove();
                    document.removeEventListener('keypress', handleKeyPress);
                    resolve();
                }
            };
            document.addEventListener('keypress', handleKeyPress);

            // Focus the OK button
            setTimeout(() => okButton.focus(), 100);
        });
    };

    const positionGuideContainer = async (targetElement, placement = 'right') => {
        if (!targetElement) {
            // Default position if no target element
            guideContainer.style.top = '20px';
            guideContainer.style.right = '20px';
            guideContainer.style.left = 'auto';
            guideContainer.style.bottom = 'auto';
            return Promise.resolve();
        }

        console.log('📍 Positioning guide for element:', targetElement);
        // Note: Scrolling is now handled in showStep() before this function is called

        const rect = targetElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        const containerWidth = 350;
        const containerHeight = guideContainer.offsetHeight || 300;
        const margin = 20;

        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let top, left;
        let finalPlacement = placement;

        // Calculate initial position based on placement
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

        // Adjust if going off-screen horizontally
        if (left + containerWidth > scrollLeft + viewportWidth - margin) {
            // Try left side instead
            left = rect.left + scrollLeft - containerWidth - margin;
            finalPlacement = 'left';
        }
        if (left < scrollLeft + margin) {
            // Try right side
            left = rect.right + scrollLeft + margin;
            finalPlacement = 'right';
            // If still off, center below
            if (left + containerWidth > scrollLeft + viewportWidth - margin) {
                left = Math.max(scrollLeft + margin, (viewportWidth - containerWidth) / 2 + scrollLeft);
                top = rect.bottom + scrollTop + margin;
                finalPlacement = 'bottom';
            }
        }

        // Adjust if going off-screen vertically
        if (top < scrollTop + margin) {
            top = rect.bottom + scrollTop + margin;
            finalPlacement = 'bottom';
        }
        if (top + containerHeight > scrollTop + viewportHeight - margin) {
            top = Math.max(scrollTop + margin, scrollTop + viewportHeight - containerHeight - margin);
        }

        // Apply positioning
        guideContainer.style.position = 'absolute';
        guideContainer.style.top = top + 'px';
        guideContainer.style.left = left + 'px';
        guideContainer.style.right = 'auto';
        guideContainer.style.bottom = 'auto';
        guideContainer.style.transform = 'none';

        // Add arrow
        addPointerArrow(finalPlacement);

        // Ensure guide box is visible - scroll if needed
        await new Promise(resolve => setTimeout(resolve, 100));
        const containerRect = guideContainer.getBoundingClientRect();

        console.log('📦 Guide box position:', {
            top: containerRect.top,
            bottom: containerRect.bottom,
            left: containerRect.left,
            right: containerRect.right,
            viewportHeight: viewportHeight,
            viewportWidth: viewportWidth
        });

        // Check if guide box extends beyond viewport
        const isGuideBoxVisible = (
            containerRect.top >= 0 &&
            containerRect.bottom <= viewportHeight &&
            containerRect.left >= 0 &&
            containerRect.right <= viewportWidth
        );

        if (!isGuideBoxVisible) {
            console.log('⚠️ Guide box not fully visible, adjusting scroll...');

            // Calculate how much to scroll to center both element and guide box
            const guideBoxCenterY = (containerRect.top + containerRect.bottom) / 2;
            const elementCenterY = (rect.top + rect.bottom) / 2;
            const avgCenterY = (guideBoxCenterY + elementCenterY) / 2;

            // Scroll to center the average point
            const scrollTargetY = window.pageYOffset + avgCenterY - (viewportHeight / 2);

            window.scrollTo({
                top: Math.max(0, scrollTargetY),
                left: window.pageXOffset, // Keep horizontal scroll
                behavior: 'smooth'
            });
            await new Promise(resolve => setTimeout(resolve, 400));

            console.log('✅ Scroll adjustment complete');

            // Recalculate guide box position after scroll
            const newRect = targetElement.getBoundingClientRect();
            const newScrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const newScrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

            // Recalculate top and left based on new scroll position
            switch (finalPlacement) {
                case 'top':
                    top = newRect.top + newScrollTop - containerHeight - margin;
                    left = newRect.left + newScrollLeft + (newRect.width / 2) - (containerWidth / 2);
                    break;
                case 'bottom':
                    top = newRect.bottom + newScrollTop + margin;
                    left = newRect.left + newScrollLeft + (newRect.width / 2) - (containerWidth / 2);
                    break;
                case 'left':
                    top = newRect.top + newScrollTop + (newRect.height / 2) - (containerHeight / 2);
                    left = newRect.left + newScrollLeft - containerWidth - margin;
                    break;
                case 'right':
                default:
                    top = newRect.top + newScrollTop + (newRect.height / 2) - (containerHeight / 2);
                    left = newRect.right + newScrollLeft + margin;
                    break;
            }

            // Update position
            guideContainer.style.top = top + 'px';
            guideContainer.style.left = left + 'px';

            console.log('✅ Guide box repositioned after scroll');
        } else {
            console.log('✅ Guide box is visible');
        }

        return Promise.resolve();
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

            // Check if we're in a popup window
            const isInPopup = window.opener && !window.opener.closed;

            if (isInPopup) {
                alert('🎉 Anleitung erfolgreich abgeschlossen!\n\nSie haben alle Schritte durchlaufen.\n\nDas Fenster wird nun geschlossen.');
                window.close();
            } else {
                alert('🎉 Anleitung erfolgreich abgeschlossen!\n\nSie haben alle Schritte durchlaufen. Viel Erfolg bei der Simulation!');
            }
            return;
        }

        const step = guide.steps[stepIndex];
        console.log(`📍 Showing step ${stepIndex + 1}: ${step.title}`);

        // Hide spotlight initially
        spotlight.style.display = 'none';

        // Update guide container content FIRST
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
                </div>

                <!-- Buttons -->
                <div style="display: flex; gap: 8px;">
                    ${stepIndex > 0 ? `
                        <button onclick="window.previousStep()" style="flex: 1; padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                            ← Zurück
                        </button>
                    ` : ''}
                    <button onclick="window.nextStep()" style="flex: 2; padding: 8px 16px; background: ${isLastStep ? '#28a745' : '#007bff'}; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        ${isLastStep ? '🎉 Fertig' : 'Weiter →'}
                    </button>
                    <button onclick="window.endGuide()" style="padding: 8px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        ✕
                    </button>
                </div>
            </div>
        `;

        // NOW position the guide container after content is set
        let targetElement = null;
        if (step.target && step.target !== 'body') {
            targetElement = document.querySelector(step.target);
            if (targetElement) {
                console.log(`🎯 Found target element for step ${stepIndex + 1}:`, step.target);
                currentTargetElement = targetElement;
                currentPlacement = step.placement || 'right';

                // STEP 1: Auto-expand elements if needed (this must happen FIRST)
                console.log('📂 STEP 1: Expanding any collapsed parents...');
                await expandElementIfNeeded(targetElement);

                // STEP 2: Extra wait to ensure DOM has updated after expansion
                console.log('⏳ STEP 2: Waiting for DOM to update after expansion...');
                await new Promise(resolve => setTimeout(resolve, 500));

                // STEP 3: Verify element is now visible
                console.log('👁️ STEP 3: Checking if element is visible...');
                const computedStyle = window.getComputedStyle(targetElement);
                if (computedStyle.display === 'none' || computedStyle.visibility === 'hidden') {
                    console.error('❌ Element is still hidden after expansion!');
                }

                // STEP 4: Force scroll element into center of viewport
                console.log('📜 STEP 4: Scrolling element into center of viewport...');
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
                await new Promise(resolve => setTimeout(resolve, 600));

                // STEP 5: Position the guide container next to element
                console.log('📍 STEP 5: Positioning guide container...');
                await positionGuideContainer(targetElement, currentPlacement);

                // STEP 6: Add highlight/spotlight
                console.log('✨ STEP 6: Adding highlight...');

                // Special handling for procurement guide dropdown steps
                // Remove veil and make dropdown clickable for step 2 (index 1) and step 6 (index 5)
                if ((stepIndex === 1 || stepIndex === 5) && guide.title === 'Einkauf: Komponenten bestellen') {
                    const dropdownElement = document.querySelector('#mockSupplierDropdown');
                    if (dropdownElement) {
                        console.log(`🎯 Special handling: Highlighting dropdown for step ${stepIndex + 1}`);
                        highlightElement(targetElement);
                        // Allow pointer events on the dropdown so users can click it
                        dropdownElement.style.pointerEvents = 'auto';
                        dropdownElement.style.position = 'relative';
                        dropdownElement.style.zIndex = '10002';
                    } else {
                        highlightElement(targetElement);
                    }
                } else {
                    highlightElement(targetElement);
                }

                console.log('✅ Step positioning complete!');
            } else {
                console.warn(`⚠️ Target element not found: ${step.target}`);
                currentTargetElement = null;
                // Use default positioning if target not found
                await positionGuideContainer(null);
            }
        } else {
            // Center the guide for body/general steps
            console.log('📍 Centering guide for general step');
            currentTargetElement = null;
            guideContainer.style.position = 'fixed';
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
    };

    const highlightElement = (element) => {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        // Position spotlight to cut through the overlay
        spotlight.style.display = 'block';
        spotlight.style.top = `${rect.top + scrollTop - 8}px`;
        spotlight.style.left = `${rect.left + scrollLeft - 8}px`;
        spotlight.style.width = `${rect.width + 16}px`;
        spotlight.style.height = `${rect.height + 16}px`;

        // Add pulsing animation
        if (!document.getElementById('guide-animations')) {
            const style = document.createElement('style');
            style.id = 'guide-animations';
            style.textContent = `
                @keyframes guidePulse {
                    0% {
                        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 20px rgba(0, 123, 255, 0.8);
                        border-color: #007bff;
                    }
                    50% {
                        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 40px rgba(0, 123, 255, 1);
                        border-color: #0056b3;
                    }
                    100% {
                        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 20px rgba(0, 123, 255, 0.8);
                        border-color: #007bff;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        spotlight.style.animation = 'guidePulse 2s infinite';
    };

    // Global functions for buttons
    window.nextStep = () => {
        console.log('Next step clicked, current:', currentStep);
        currentStep++;
        showStep(currentStep);
    };

    window.previousStep = () => {
        console.log('Previous step clicked, current:', currentStep);
        currentStep--;
        showStep(currentStep);
    };

    const endGuide = () => {
        console.log('🏁 Ending guide - X button clicked or guide completed');

        // Check if we're in a popup FIRST before removing anything
        const isInPopup = window.opener && !window.opener.closed;
        console.log('🔍 Is in popup window:', isInPopup);

        // Remove guide elements
        if (overlay) overlay.remove();
        if (spotlight) spotlight.remove();
        if (guideContainer) guideContainer.remove();

        // Remove event listeners
        window.removeEventListener('resize', repositionGuide);
        window.removeEventListener('scroll', repositionGuide);

        // Clean up global functions
        delete window.nextStep;
        delete window.previousStep;
        delete window.endGuide;
        delete window.repositionGuide;

        // If we're in a popup, ALWAYS close the window immediately
        if (isInPopup) {
            console.log('🚪 Closing popup window immediately...');
            setTimeout(() => {
                window.close();
            }, 100); // Small delay to ensure cleanup completes
        }
    };

    window.endGuide = endGuide;

    // Reposition guide when window resizes or scrolls
    const repositionGuide = () => {
        if (currentTargetElement) {
            positionGuideContainer(currentTargetElement, currentPlacement);
            // Also update spotlight position
            highlightElement(currentTargetElement);
        }
    };

    window.repositionGuide = repositionGuide;

    // Add event listeners for repositioning
    window.addEventListener('resize', repositionGuide);
    window.addEventListener('scroll', repositionGuide);

    // Start with first step
    showStep(0);
}

// Make function globally available
window.createInteractiveGuide = createInteractiveGuide;
