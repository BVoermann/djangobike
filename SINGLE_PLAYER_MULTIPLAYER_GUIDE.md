# Single-Player Multiplayer Auto-Processing Guide

## Overview

When a multiplayer game has only **one human player** (with AI opponents), the turn now processes **automatically** as soon as the human player submits their decisions. This eliminates waiting for turn deadlines and provides immediate feedback.

## How It Works

### Detection
The system automatically detects single-player scenarios:
- Counts active, non-bankrupt **human players**
- If count = 1 → Single-player mode activated
- Works transparently - no configuration needed

### Auto-Processing Flow

```
Player submits sales decisions
         ↓
System checks: Is this a single human player game?
         ↓
    YES → Process turn immediately
         ↓
    AI competitors make decisions
         ↓
    Market simulation runs
         ↓
    Results calculated with rich feedback
         ↓
    Player sees results instantly
```

### What Gets Auto-Processed

When you submit decisions in a single-player multiplayer game:
- **Sales decisions** → Turn processes immediately
- **Procurement decisions** → Turn processes immediately
- **Production decisions** → Turn processes immediately

All AI competitors automatically submit their decisions and compete with you in the market.

## Enhanced Sales Feedback

### Summary Cards (4 cards at top)

1. **Success Rate** (color-coded)
   - Green ≥80%: Excellent performance
   - Yellow ≥50%: Moderate success
   - Red <50%: Needs improvement

2. **Bikes Sold**
   - Total quantity successfully sold

3. **Unsold (In Stock)**
   - Quantity remaining in warehouse

4. **Revenue**
   - Actual money earned from sales

### Detailed Results Table

For each sales decision, you see:

#### Outcome Column
- **Sold/Planned ratio**: "8/10 sold"
- **Success percentage badge**: "80%"
- **Progress bar** (color-coded by performance)
- **Narrative message**: Educational feedback without formulas

#### Market Insight Column
- **Market condition badge**: "Competitive market"
- **Description**: What happened in the market
- **Competitive position**: How your pricing compared

### Example Outcome Messages

**100% Success:**
- "Outstanding performance! Every bike was sold."
- "Perfect timing! Complete sell-out achieved."

**80%+ Success:**
- "Strong sales! 8 out of 10 bikes sold. The market was receptive to your offering."

**50-80% Success:**
- "Moderate success. 5 bikes sold, 5 remain in inventory. Consider adjusting your strategy."

**20-50% Success:**
- "Limited sales. 2 of 10 sold. Your pricing may not have matched market expectations."
- "Competitive market. 3 of 10 sold. Many competitors were targeting the same customers."

**<20% Success:**
- "Very limited success. Only 1 of 10 bikes sold. Significant inventory remains."
- "No sales completed. Your bikes didn't find buyers this turn. Consider revising your market approach."

### Market Condition Descriptions

**High demand, low competition:**
- "The market had strong appetite for bikes with limited competition."

**Healthy market:**
- "Good market conditions with balanced supply and demand."

**Competitive market:**
- "Many sellers competed for available customers."

**Oversaturated market:**
- "The market was flooded with offerings, limiting individual success."

**Location-specific insights:**
- "This city's eco-conscious population favored e-bikes." (for green cities)
- "The mountainous terrain increased demand for mountain bikes." (for mountain regions)

### Competitive Position Feedback

**Pricing Feedback:**
- "Your competitive pricing gave you an advantage in the market." (15%+ below average)
- "Your pricing was slightly below market average, helping sales." (5-15% below)
- "Your pricing aligned with market expectations." (±5% of average)
- "Your pricing was slightly higher than competitors, which may have affected sales." (5-15% above)
- "Your premium pricing positioned you at the higher end of the market." (15%+ above)

## What You Learn (Without Seeing Formulas)

The feedback system helps you understand:

1. **Market Dynamics**
   - Was the market crowded or open?
   - Did many competitors target the same segment?

2. **Pricing Strategy**
   - Were you priced competitively?
   - Did pricing affect your sales?

3. **Location Effects**
   - Does this city prefer certain bike types?
   - Are you selling the right bikes in the right places?

4. **Timing**
   - Seasonal factors (implied through demand descriptions)
   - Market saturation levels

## Strategic Insights

### If Success Rate is Low

**Check:**
- Your pricing vs. competitors
- Market condition (was it oversaturated?)
- Location match (e.g., selling mountain bikes in flat cities?)
- Inventory age (old bikes harder to sell)

**Actions:**
- Lower prices to be more competitive
- Target different markets
- Sell bikes that match location preferences
- Don't let inventory age too long

### If Market Was "Oversaturated"

**Means:**
- Too many sellers targeting same segment
- Limited customer capacity
- Strong competition

**Actions:**
- Try different price segments
- Target underserved markets
- Differentiate through quality
- Time your sales better

### If Pricing Feedback Indicates "Premium"

**Means:**
- You're priced higher than competitors
- May limit sales volume
- But maximizes profit per bike sold

**Decision:**
- High price, low volume strategy OK?
- Or lower price for more sales?

## Multi-Player vs Single-Player Games

| Feature | Single Human Player | Multiple Human Players |
|---------|-------------------|----------------------|
| **Turn Processing** | Instant when you submit | Waits for all players or deadline |
| **AI Decisions** | Auto-submitted immediately | Auto-submitted at deadline |
| **Feedback** | Immediate results | Results when turn processes |
| **Wait Time** | None | Up to turn deadline |
| **Competition** | You vs AI | You vs AI + other humans |

## Tips for Success

### 1. Use Location Characteristics
- Green cities (high green_city_factor) → Sell e-bikes
- Mountain regions (high mountain_bike_factor) → Sell mountain bikes
- Match your bikes to city preferences

### 2. Watch Market Conditions
- "High demand" → Safe to set higher prices
- "Oversaturated" → Lower prices to compete
- "Competitive" → Middle ground pricing

### 3. Learn from Feedback
- Read the outcome messages carefully
- Adjust strategy based on competitive position
- Track which markets work best for you

### 4. Manage Inventory
- Old bikes harder to sell (aging penalty)
- Don't produce more than you can sell
- Use warehouse space wisely

### 5. Price Strategically
- Too high → No sales
- Too low → Lost profit
- Watch feedback to find sweet spot

## Technical Details (For Reference)

### Game Detection
```python
@property
def is_single_human_player_game(self):
    human_players = self.players.filter(
        is_active=True,
        is_bankrupt=False,
        player_type='human'
    ).count()
    return human_players == 1
```

### Auto-Process Trigger Points
- `multiplayer_sales()` view → After storing sales decisions
- `multiplayer_procurement()` view → After storing procurement decisions
- `multiplayer_production()` view → After storing production decisions

### Results Storage
Results stored in `TurnState.sales_results` with structure:
```json
{
    "total_sold": 25,
    "total_revenue": 15000.0,
    "total_unsold": 5,
    "success_rate": 83.3,
    "decisions": [
        {
            "market_name": "Berlin",
            "bike_type_name": "E-Bike City",
            "price_segment": "standard",
            "quantity_planned": 10,
            "quantity_sold": 8,
            "success_rate": 80.0,
            "outcome_message": "Strong sales! 8 out of 10...",
            "market_condition": {
                "condition": "Healthy market",
                "description": "Good market conditions..."
            },
            "competitive_position": "Your pricing aligned with..."
        }
    ]
}
```

## Troubleshooting

### "Turn not processing automatically"
**Check:**
- Is there more than 1 human player?
- Are you in a multiplayer game (not singleplayer)?
- Did you submit ALL decision types?

### "No feedback showing"
**Check:**
- Have you completed at least one turn?
- Did sales actually process?
- Check "Previous Turn Results" section

### "Feedback seems incorrect"
**Remember:**
- Feedback is narrative, not exact formulas
- Market simulation includes randomness
- Multiple factors affect outcomes

## Summary

Single-player multiplayer mode now provides:
- ✅ **Instant turn processing** - No waiting!
- ✅ **Rich narrative feedback** - Learn without formulas
- ✅ **Market insights** - Understand what happened
- ✅ **Strategic guidance** - Improve your decisions
- ✅ **Competitive analysis** - See how you compare
- ✅ **Location awareness** - Match bikes to cities

The system educates you about market dynamics while keeping the exact mechanics appropriately opaque for gameplay balance.
