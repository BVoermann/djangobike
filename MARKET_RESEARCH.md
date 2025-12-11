# Market Research System

## Overview

Players can now invest in market research to get more accurate demand estimates. Instead of showing vague percentages, the system displays **gross estimated demand ranges** (e.g., "45-75 bikes/month") that become more precise with research investment.

## How It Works

### 1. Demand Display (New System)

**Before:** Vague percentage-based demand
**After:** Clear bike quantity ranges

| Research Level | Cost | Precision | Example Range | Duration |
|----------------|------|-----------|---------------|----------|
| **None** (Default) | 0€ | ±60% | 24-92 bikes | - |
| **Basic** | 500€ | ±30% | 38-72 bikes | 3 months |
| **Advanced** | 2,000€ | ±15% | 48-68 bikes | 3 months |
| **Premium** | 5,000€ | ±5% | 55-61 bikes | 3 months |

### 2. Strategic Value

**Without Research:**
- Very wide ranges (±60%)
- Example: "Damenrad in Domestic Market: 24-92 bikes"
- High uncertainty - risky sales decisions

**With Basic Research (500€):**
- Medium ranges (±30%)
- Example: "Damenrad in Domestic Market: 38-72 bikes"
- Better planning, reduced risk

**With Premium Research (5,000€):**
- Narrow ranges (±5%)
- Example: "Damenrad in Domestic Market: 55-61 bikes"
- Near-perfect planning, minimal waste

## Implementation Details

### New Models

**`MarketResearch`**
- Tracks research investment per market/bike type combination
- Stores precision level and expiration date
- Calculates min/max demand estimates

**`MarketResearchTransaction`**
- Accounting record of research purchases
- Links to finance system

### Key Features

1. **Per-Market, Per-Bike Specificity**
   - Research for "Damenrad in Domestic Market" doesn't help with "Herrenrad in EU Market"
   - Players must strategically choose what to research
   - Creates interesting spending decisions

2. **Time-Limited Research**
   - Research expires after 3 months
   - Must re-purchase to maintain precision
   - Simulates real-world market volatility

3. **Dynamic Demand Calculation**
   - Base demand from market capacity and demand percentages
   - Location modifiers (e.g., mountain bikes sell better in mountainous areas)
   - Seasonal variations (higher demand in spring/summer)
   - Random fluctuations (±10%) for realism

4. **Integrated with Balance System**
   - Uses BalanceManager for multiplayer
   - Direct balance updates for singleplayer
   - Proper transaction logging

## API Endpoints

### Get Demand Estimates
```http
GET /sales/<session_id>/market-research/estimates/
```

**Response:**
```json
{
  "success": true,
  "estimates": [
    {
      "market_id": "...",
      "market_name": "Domestic Market",
      "bike_types": [
        {
          "bike_type_id": "...",
          "bike_type_name": "Damenrad",
          "estimated_min": 38,
          "estimated_max": 72,
          "research_level": "basic",
          "precision_percentage": 30
        }
      ]
    }
  ],
  "current_month": 2,
  "current_year": 2024
}
```

### Purchase Market Research
```http
POST /sales/<session_id>/market-research/purchase/
Content-Type: application/json

{
  "market_id": "...",
  "bike_type_id": "...",
  "research_level": "basic"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Basic research purchased",
  "cost": 500.0,
  "new_balance": 79500.0,
  "estimated_min": 38,
  "estimated_max": 72,
  "expires_at": "2026-03-11T...",
  "research_costs": {
    "basic": 500.0,
    "advanced": 2000.0,
    "premium": 5000.0
  }
}
```

## UI Integration Example

### Sales Overview Display

```
=== MARKET DEMAND ESTIMATES ===

Domestic Market:
  🔬 Damenrad: 38-72 bikes/month (Basic Research - expires March 2026)
  ❓ Herrenrad: 22-86 bikes/month (No Research)
  ❓ Mountainbike: 25-95 bikes/month (No Research)

  [Purchase Research] button

EU Market:
  ❓ Damenrad: 38-152 bikes/month (No Research)
  ❓ Herrenrad: 35-139 bikes/month (No Research)

  [Purchase Research] button

=== RESEARCH OPTIONS ===

Damenrad in Domestic Market:
  Current: 38-72 bikes (±30%)

  [ ] Basic (500€) - ±30% precision ← Already purchased
  [ ] Advanced (2,000€) - ±15% precision → Upgrade: 48-68 bikes
  [ ] Premium (5,000€) - ±5% precision → Upgrade: 55-61 bikes

  [Purchase] button
```

### Benefits Display

```
WHY INVEST IN MARKET RESEARCH?

WITHOUT RESEARCH:
❌ Wide uncertainty: 24-92 bikes (68 bike range!)
❌ Risk of overproduction or stockouts
❌ Hard to plan inventory
❌ Wasted resources

WITH BASIC RESEARCH (500€):
✓ Better accuracy: 38-72 bikes (34 bike range)
✓ Reduced risk
✓ Smarter production planning
✓ Worth the investment if selling 10+ bikes

WITH PREMIUM RESEARCH (5,000€):
✓✓ Near-perfect: 55-61 bikes (6 bike range)
✓✓ Minimal waste
✓✓ Optimal production
✓✓ Best for high-volume products
```

## Strategic Considerations

### When to Buy Research?

**Buy Basic Research (500€) when:**
- Planning to produce 10+ bikes
- Market is critical to your strategy
- Uncertain about demand
- Want to reduce inventory risk

**Buy Advanced Research (2,000€) when:**
- High-value bikes (e-bikes, premium models)
- Large production runs (20+ bikes)
- Tight profit margins
- Precision is crucial

**Buy Premium Research (5,000€) when:**
- Very high-value products
- Mass production (50+ bikes)
- Market dominance strategy
- Maximum efficiency needed

**Skip Research when:**
- Small test batches (1-5 bikes)
- Experimental products
- Cash-strapped early game
- Multiple markets to explore

## Economic Balance

### Costs vs. Benefits

**Basic Research (500€):**
- Narrows range by 50%
- Pays for itself if prevents 2-3 unsold bikes
- ROI: ~3-5 bikes sold

**Advanced Research (2,000€):**
- Narrows range by 75%
- Pays for itself if prevents 8-10 unsold bikes
- ROI: ~10-15 bikes sold

**Premium Research (5,000€):**
- Narrows range by 92%
- Pays for itself if prevents 20-25 unsold bikes
- ROI: ~25-30 bikes sold

### Competitive Advantage

In multiplayer:
- Players with research have **information advantage**
- Can price more competitively
- Less inventory waste
- Higher margins
- Faster growth

## Testing Results

✅ **All Tests Passed:**

1. **Default Estimates** - Wide ranges (±60%) without research
2. **Purchase Research** - Balance correctly deducted (79,500€ after 500€ purchase)
3. **Improved Precision** - Narrower ranges (±30%) with basic research
4. **Multi-Market Support** - Different precision per market/bike combination
5. **Research Indicators** - Clear visual distinction (🔬 vs ❓)

## Files Created/Modified

### New Files:
- `sales/models_market_research.py` - MarketResearch and MarketResearchTransaction models
- `sales/demand_calculator.py` - Demand calculation and research logic
- `sales/migrations/0005_add_market_research.py` - Database migration
- `MARKET_RESEARCH.md` - This documentation

### Modified Files:
- `sales/models.py` - Import market research models
- `sales/views.py` - Add API endpoints
- `sales/urls.py` - Add URL routes

## Next Steps for Full Implementation

1. **UI Integration:**
   - Add market research widget to sales page
   - Show demand ranges instead of percentages
   - Add "Purchase Research" buttons
   - Display research expiration dates

2. **Visual Design:**
   - Color-code precision levels (red → yellow → green)
   - Show research status icons
   - Animate range narrowing
   - Add tooltips explaining benefits

3. **Multiplayer Integration:**
   - Add market research to multiplayer views
   - Include research costs in monthly reports
   - Show competitor research levels (if visible)

4. **Tutorial/Help:**
   - Add tutorial explaining market research
   - Show example calculations
   - Recommend when to buy research
   - Explain ROI

## Summary

The market research system transforms vague percentage-based demand into **clear, actionable bike quantity ranges** that players can use to make smart production and sales decisions. By investing in research, players reduce uncertainty and gain competitive advantage, creating interesting strategic choices about where to allocate their research budget.

**Key Innovation:** Demand is now displayed as **"38-72 bikes/month"** instead of **"33.33% demand"** - immediately understandable and actionable!
