# Interactive Tutorial System - Procurement Guide

## 🎯 System Overview

Your BikeShop simulation already has a **fully functional interactive tutorial system** implemented! Here's how it works:

### Current Implementation

✅ **Popup Window System** - Opens procurement tab in a new browser window
✅ **Grey Overlay** - Semi-transparent veil over popup content
✅ **Step-by-Step Guide** - Interactive tooltips positioned next to UI elements
✅ **Navigation Controls** - Next/Previous buttons with progress indicator
✅ **Auto-Expand** - Automatically opens dropdowns/collapses when needed
✅ **Element Highlighting** - Blue pulsing border around target elements

## 📍 File Structure

```
help_system/
├── models.py                           # InteractiveGuide model definition
├── views.py                            # API endpoints for guides
├── templates/help_system/
│   └── interactive_guides.html        # Main guide interface with startGuide()
└── management/commands/
    └── create_interactive_guides.py   # Creates default guides

templates/procurement/
└── procurement.html                    # Procurement tab with guide targets

Static files:
- help_system/js/help-system.js        # Guide system logic
- help_system/js/guide-continuation.js # Cross-page navigation
```

## 🚀 How to Use

### Starting a Guide

1. Navigate to: `/help/interactive-guides/`
2. Find the "Einkauf: Komponenten bestellen" guide card
3. Click the "Guide starten" button
4. A popup window opens with the procurement tab
5. The guide automatically starts with grey overlay

### What Happens Internally

```javascript
// In interactive_guides.html (line 309-476)
window.startGuide(guideId) {
    1. Fetches guide data via API: /help/api/guides/{id}/start/
    2. Gets user's active session ID
    3. Opens procurement page in popup: window.open(url, '_blank', ...)
    4. Waits for page load
    5. Injects guide script into popup
    6. Calls createInteractiveGuide(guideData)
}

// Guide execution (line 491-1008)
createInteractiveGuide(guide, startStep, isPopup) {
    1. Creates grey overlay (rgba(0,0,0,0.7))
    2. Creates guide notification box
    3. For each step:
       - Finds target element
       - Auto-expands if needed (dropdowns, collapses)
       - Highlights element with blue border
       - Positions notification box
       - Shows content with navigation
}
```

## 📋 Current Procurement Guide Steps

**Guide ID: 30** | **11 Steps Total**

1. **Welcome** (target: body)
   - Introduction to procurement tab

2. **Budget Display** (target: `.col-lg-3:nth-child(1) .card`)
   - Shows available balance

3. **Supplier Count** (target: `.col-lg-3:nth-child(2) .card`)
   - Number of available suppliers

4. **Component Count** (target: `.col-lg-3:nth-child(3) .card`)
   - Available components from supplier

5. **Order Total** (target: `.col-lg-3:nth-child(4) .card`)
   - Real-time order value

6. **Supplier Selection** (target: `#supplierDropdown`)
   - How to choose a supplier

7. **Supplier Details** (target: `.dropdown-row:first-child .card`)
   - Quality, delivery time, payment terms

8. **Bike Type Filter** (target: `#bike-type-filter-row`)
   - Filter components by bike type

9. **Components Table** (target: `#supplier-components`)
   - View and order components

10. **Order Summary** (target: `.card.border-0:has(#grand-total)`)
    - Review total and submit order

11. **Completion** (target: body)
    - Success message

## 🔧 How to Modify Guide Steps

### Via Django Admin

1. Go to: `/admin/help_system/interactiveguide/`
2. Find "Einkauf: Komponenten bestellen"
3. Edit the `steps` JSON field

### Via Python Shell

```python
python3 manage.py shell

from help_system.models import InteractiveGuide

guide = InteractiveGuide.objects.get(title='Einkauf: Komponenten bestellen')

# Add a new step
new_step = {
    'title': 'New Step Title',
    'content': 'Detailed explanation of this feature...',
    'target': '#element-id',  # CSS selector
    'placement': 'right'      # 'top', 'bottom', 'left', 'right'
}

guide.steps.append(new_step)
guide.save()
```

### Step Configuration

Each step is a dictionary with:

```python
{
    'title': 'Step Title',              # Required
    'content': 'Step description',      # Required
    'target': '#element-id',            # CSS selector (use 'body' for centered)
    'placement': 'right',               # Position: top/bottom/left/right
    'navigate_to': '/other/page/'      # Optional: navigate to different page
}
```

## 🎨 Styling & Appearance

### Grey Overlay
```javascript
// Line 495-506 in interactive_guides.html
position: fixed;
background: rgba(0, 0, 0, 0.7);  // 70% opacity black
z-index: 9999;
pointer-events: none;  // Allow clicks through
```

### Notification Box
```javascript
// Line 510-521
position: absolute;
width: 350px;
background: white;
border-radius: 10px;
box-shadow: 0 8px 30px rgba(0,0,0,0.3);
z-index: 10001;  // Above overlay
```

### Element Highlighting
```javascript
// Line 918-933
border: 3px solid #007bff;  // Blue border
border-radius: 8px;
box-shadow: 0 0 20px rgba(0, 123, 255, 0.5);  // Blue glow
animation: guidePulse 2s infinite;  // Pulsing effect
```

## 🔄 Dynamic Content Expansion

The system automatically expands hidden elements:

```javascript
// Line 529-594: expandElementIfNeeded()
async function expandElementIfNeeded(targetElement) {
    // 1. Check if element is in collapsed dropdown
    if (dropdownMenu) {
        dropdown.click();  // Open dropdown
        await delay(300);   // Wait for animation
    }

    // 2. Check if element is a dropdown toggle
    if (element.classList.contains('dropdown-toggle')) {
        element.click();   // Open dropdown
    }

    // 3. Check if element is in Bootstrap collapse
    if (collapseParent) {
        collapseToggle.click();  // Expand collapse
    }

    // 4. Check if element has display:none
    if (styles.display === 'none') {
        parent.style.display = 'block';  // Show parent
    }
}
```

## 🎯 Targeting Elements in Procurement Tab

### Available Selectors

```html
<!-- Header -->
.display-4                              /* "Einkauf" title */

<!-- Statistics Cards -->
.col-lg-3:nth-child(1) .card           /* Budget */
.col-lg-3:nth-child(2) .card           /* Suppliers */
.col-lg-3:nth-child(3) .card           /* Components */
.col-lg-3:nth-child(4) .card           /* Order total */

<!-- Dropdowns -->
#supplierDropdown                       /* Supplier selector */
#bikeTypeDropdown                       /* Bike type filter */
.dropdown-row:first-child .card        /* Supplier dropdown container */
#bike-type-filter-row                   /* Bike filter section */

<!-- Supplier Details -->
#supplier-details                       /* Details section */
#supplier-name                          /* Supplier name */
#supplier-badges                        /* Quality/delivery badges */
#supplier-components                    /* Components table */
.table-responsive                       /* Table container */

<!-- Order Summary -->
.card.border-0:has(#grand-total)       /* Order summary card */
#grand-total                            /* Total amount */
.btn-primary.btn-lg.px-4               /* Submit button */
```

## 📊 Analytics & Tracking

The system tracks:

```python
# In InteractiveGuide model
- start_count          # Times guide started
- completion_count     # Times completed
- completion_rate      # Percentage (completion/start * 100)

# In UserHelpProgress model
- guides_started       # Guides user has begun
- guides_completed     # Guides user finished
- total_help_interactions
```

## 🐛 Troubleshooting

### Guide doesn't start
1. Check guide is active: `guide.is_active = True`
2. Verify URL pattern matches: `/procurement/*`
3. Check browser allows popups
4. Open browser console for errors

### Element not highlighted
1. Verify CSS selector is correct
2. Element must be visible when step loads
3. Check z-index conflicts
4. Use browser DevTools to test selector

### Positioning issues
1. Element must have dimensions (not display:none)
2. Guide auto-adjusts if off-screen
3. Check placement: 'top', 'bottom', 'left', 'right'
4. Use 'body' target for centered notifications

## 🚀 Adding New Guides

### For Other Tabs

```python
python3 manage.py shell

from help_system.models import HelpCategory, InteractiveGuide

# Get category
cat = HelpCategory.objects.get(category_type='production')

# Create guide
guide = InteractiveGuide.objects.create(
    title='Produktion: Fahrräder herstellen',
    description='Lernen Sie die Fahrradproduktion',
    category=cat,
    guide_type='walkthrough',
    target_url_pattern='/production/*',
    user_level_required='beginner',
    steps=[
        {
            'title': 'Welcome',
            'content': 'Welcome to production!',
            'target': 'h1',
            'placement': 'bottom'
        },
        # ... more steps
    ],
    is_active=True
)
```

## 🎨 Customization Options

### Change Overlay Opacity
```javascript
// Line 503 in interactive_guides.html
background: rgba(0, 0, 0, 0.7);  // Change 0.7 to 0.5 for lighter
```

### Change Notification Size
```javascript
// Line 514
width: 350px;  // Make wider: 450px
```

### Change Colors
```javascript
// Blue highlight -> Green
border: 3px solid #28a745;  // Line 925
box-shadow: 0 0 20px rgba(40, 167, 69, 0.5);  // Line 930
```

### Add Custom Animations
```javascript
// Line 936-944
@keyframes guidePulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}
```

## 📱 API Endpoints

```
GET  /help/interactive-guides/              # List all guides
POST /help/api/guides/{id}/start/           # Start guide (returns guide data)
GET  /help/api/guides/{id}/preview/         # Preview guide
POST /help/api/guides/{id}/complete/        # Mark complete
```

## 🎯 Next Steps

To enhance the procurement guide:

1. **Review step order** - Ensure logical flow
2. **Test with real users** - Gather feedback
3. **Add more detail** - Explain complex features
4. **Include tips** - Best practices and strategies
5. **Track analytics** - Monitor completion rate

## 💡 Pro Tips

- **Keep steps short** - 1-2 sentences per step
- **Use action verbs** - "Click", "Select", "Enter"
- **Highlight benefits** - "This helps you save money"
- **Progressive disclosure** - Start simple, add complexity
- **Test thoroughly** - Try all paths and edge cases

## 📞 Support

For issues or questions:
- Check browser console for JavaScript errors
- Verify element selectors in DevTools
- Test guide in incognito mode
- Review help_system/views.py for API logic
