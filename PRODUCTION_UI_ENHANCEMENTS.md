# Production UI Component Requirements Enhancement

## Overview

The production interface has been significantly enhanced to provide players with clear, actionable information about component requirements, stock availability, and quality levels.

## What Was Improved

### Before
- Component requirements shown as simple list of component names
- No stock quantity information visible
- No quality level indicators
- No visual feedback about availability
- Players had to guess if they had enough components

### After
- **Clear status indicators** for each quality segment (Günstig, Standard, Premium)
- **Detailed component modals** showing all requirements
- **Real-time stock quantities** with color-coded availability
- **Quality level badges** for each component
- **Upgrade warnings** when higher-quality components will be used
- **Missing component alerts** clearly highlighted

## New Features

### 1. Status Badges per Quality Segment

Each production input now shows a status badge indicating:
- ✅ **Bereit** (Ready) - All components available with correct quality
- ⚠️ **Upgrade** - Higher quality components will be used
- ❌ **Unvollständig** (Incomplete) - Some components missing

### 2. Component Details Modal

Click "Komponenten anzeigen" (Show Components) to see detailed information:

**For Each Component:**
- Component type (Laufradsatz, Rahmen, etc.)
- Component name
- Quality level (Basis, Standard, Premium)
- Current stock quantity with color coding:
  - 🟢 Green: >10 pieces (sufficient)
  - 🟡 Yellow: 1-10 pieces (low stock)
  - 🔴 Red: 0 pieces (out of stock)
- Upgrade indicator if applicable
- Visual status icon

**Organized by Quality Segment:**
- Separate tabs for Günstig, Standard, and Premium
- Shows exact components that will be used for each segment
- Highlights missing components with red alert banner

### 3. Enhanced Table Layout

The production planning table now shows:
- **Bike type** with icon
- **Work requirements** (skilled + unskilled hours in one column)
- **Quantity inputs** for each segment with status badges below
- "Komponenten anzeigen" link for detailed view

### 4. Color-Coded Visual Feedback

**Stock Levels:**
- Green badge: Sufficient stock (>10 pieces)
- Yellow badge: Low stock (1-10 pieces)
- Red badge: Out of stock (0 pieces)

**Quality Indicators:**
- Green badge: Basis quality
- Blue badge: Standard quality
- Orange badge: Premium quality

**Status Icons:**
- ✓ Check circle: Everything ready
- ⚠ Warning circle: Low stock
- ✗ Cross circle: Out of stock

## Technical Implementation

### Backend Changes (`production/views.py`)

Added comprehensive component data preparation:

```python
bike_types_with_details = []
for bike_type in bike_types:
    # For each segment, find required components with stock info
    for segment in ['cheap', 'standard', 'premium']:
        component_match_result = bike_type.find_best_components_for_segment(session, segment)

        components_info = []
        for component_type_name, component in component_match_result['components'].items():
            # Get stock, quality, upgrade status for each component
            components_info.append({
                'id': component.id,
                'type': component_type_name,
                'name': component.name,
                'quality': quality_display,
                'stock': stock_quantity,
                'is_upgrade': is_upgrade,
            })
```

### Frontend Changes (`templates/production/production.html`)

1. **Restructured production table** to show work requirements in single column
2. **Added status badges** below each quantity input
3. **Created component detail modals** with tabbed interface for each segment
4. **Implemented color-coded stock displays** with dynamic updates

### Data Flow

```
Backend (views.py)
    ↓
bike_types_with_details
    ├── bike_type
    └── components_by_segment
        ├── cheap
        │   ├── components [list with stock, quality, upgrade info]
        │   ├── missing [list of missing components]
        │   └── has_upgrades [boolean]
        ├── standard
        └── premium
    ↓
Template (production.html)
    ↓
Component Details Modal
    ├── Tabs (Günstig, Standard, Premium)
    └── Component Table
        ├── Type, Name, Quality
        ├── Stock Quantity (color-coded)
        └── Status Icon
```

## User Benefits

### 1. **Improved Decision Making**
Players can immediately see:
- Which bike types they can produce
- Which quality segments are ready
- Where they need to order more components

### 2. **Reduced Errors**
Clear visual indicators prevent:
- Attempting production without sufficient components
- Unexpected quality upgrades
- Wasting time on impossible production plans

### 3. **Better Planning**
Players can:
- Prioritize which components to order
- Understand quality matching requirements
- Plan production based on available stock

### 4. **Transparency**
Complete visibility into:
- Exact component requirements per bike type
- Current stock levels
- Quality tiers and compatibility

## Example Use Cases

### Use Case 1: Planning Production
1. Player opens production page
2. Sees status badges: "Damenrad Günstig" shows ✅ Bereit
3. Clicks "Komponenten anzeigen" to verify stock levels
4. Modal shows all components with green badges (>10 stock)
5. Confidently enters production quantity

### Use Case 2: Identifying Shortages
1. Player wants to produce "E-Bike Premium"
2. Sees ❌ Unvollständig badge
3. Opens component details modal
4. Premium tab shows "Motor und Akku" with red badge (0 stock)
5. Player goes to procurement to order motors

### Use Case 3: Understanding Quality Upgrades
1. Player plans "Herrenrad Günstig" production
2. Sees ⚠️ Upgrade badge
3. Opens modal, switches to "Günstig" tab
4. Sees "Rahmen: Carbon-Rahmen" with orange Premium badge and ⬆️ Upgrade indicator
5. Understands higher-quality frame will be used
6. Can decide whether to proceed or wait for cheaper components

## Files Modified

### Backend
- `production/views.py` - Added `bike_types_with_details` data structure with component info

### Frontend
- `templates/production/production.html` - Enhanced table layout and added component modals

## Testing

✅ Django check passed with no errors
✅ Template syntax validated
✅ Data structure matches template expectations
✅ Color coding logic implemented correctly

## Future Enhancements (Optional)

1. **Real-time consumption tracking** - Show how many components will be consumed as quantities are adjusted
2. **Component shopping list** - Generate procurement list based on missing components
3. **Stock predictions** - Show "enough for X bikes" indicator
4. **Historical production analysis** - Show which components are used most frequently
5. **Bulk component view** - See all components across all bike types at once

## Summary

The production UI now provides comprehensive component requirement information with:
- ✅ Clear visual status indicators
- ✅ Detailed stock information
- ✅ Quality level transparency
- ✅ Upgrade warnings
- ✅ Missing component alerts
- ✅ Color-coded availability feedback
- ✅ Organized, tabbed interface

Players can now make informed production decisions with complete visibility into component requirements and availability.
