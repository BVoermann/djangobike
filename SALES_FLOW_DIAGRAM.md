# Deferred Sales System Flow

## Old System (Immediate Sales)
```
Player submits sales form
        ↓
    Validation
        ↓
Mark bikes as SOLD immediately
        ↓
Update balance immediately
        ↓
Create Transaction records
        ↓
Show success message
        ↓
    Page reload
```

## New System (Deferred Sales with Market Simulation)

### Phase 1: Decision Making
```
Player visits Sales page
        ↓
See: Available bikes
     Pending decisions (if any)
     Recent sales results (feedback)
        ↓
Select bikes, markets, prices, quantities
        ↓
    Submit form
        ↓
    Validation
        ↓
Create SalesDecision records
(bikes NOT marked as sold yet)
        ↓
Show preview message:
  "Decisions saved! Will process next month"
  Expected revenue: XXX€
  Pending quantity: YYY bikes
        ↓
    Page reload
        ↓
See pending decisions section
(yellow/warning themed)
```

### Phase 2: Month Processing (when player clicks "Next Month")
```
Player clicks "Advance Month"
        ↓
simulation/engine.py: process_month()
        ↓
    ... other monthly tasks ...
        ↓
Every 3rd month: _process_competitive_sales()
        ↓
┌─────────────────────────────────────────────┐
│  MarketSimulator.process_pending_sales_decisions()
│
│  For each Market/BikeType/Segment:
│    1. Calculate market demand
│       - Base capacity
│       - × Location multiplier (e.g., 1.5 for e-bikes in green city)
│       - × Segment factor (40% cheap, 40% standard, 20% premium)
│       - × Seasonal factor (e.g., 1.3 for mountain bikes in summer)
│
│    2. Collect all offers
│       - Player offers (from SalesDecisions)
│         • Apply aging penalty to price
│         • Add quality factor
│       - Competitor offers (from CompetitorProduction)
│         • Calculate competitive pricing
│         • Add quality factor
│
│    3. Apply price elasticity
│       - Calculate average price
│       - Adjust demand: high prices = lower demand
│
│    4. Sort offers by effective price
│       - Lower prices sell first
│       - Add 10% random variance
│       - Divide by quality factor
│
│    5. Allocate sales (up to demand)
│       For top N offers (where N = adjusted demand):
│         - Mark bike as SOLD
│         - Update session balance
│         - Create SalesOrder record
│         - Create Transaction record
│         - Increment decision.quantity_sold
│         - Add to decision.actual_revenue
│
│    6. Handle unsold bikes
│       For remaining offers:
│         - Keep bike in inventory (is_sold=False)
│         - Set decision.unsold_reason = "market_oversaturated"
│
│    7. Mark decision as processed
│       - is_processed = True
│       - Save all results
└─────────────────────────────────────────────┘
        ↓
Continue with rest of month processing
        ↓
Month advances
```

### Phase 3: Feedback
```
Player visits Sales page again
        ↓
See "Recent Sales Results" section
(blue/info themed)
        ↓
Table shows:
  - What was planned
  - What actually sold
  - Success rate (color-coded)
  - Revenue generated
  - Reasons for unsold bikes
        ↓
Player can analyze and adjust strategy
for next sales decisions
```

## Market Demand Calculation

```
Base Demand = Market.monthly_volume_capacity
              × Market.get_bike_type_demand_multiplier(bike_type)
              × segment_factor (cheap=0.4, standard=0.4, premium=0.2)
              × seasonal_factor (varies by month and bike type)

Price Elasticity Adjustment:
  avg_price = average of all offers
  price_ratio = avg_price / base_price_for_segment
  elasticity_adjustment = 1.0 - (price_ratio - 1.0) × market.price_elasticity_factor × 0.5
  elasticity_adjustment = clamp(0.3, 1.5)  # Between 30% and 150%

Adjusted Demand = Base Demand × elasticity_adjustment
```

## Example Scenario

### Setup:
- Market: Copenhagen (urban, green_city_factor=1.5)
- Bike Type: E-Bike
- Segment: Standard
- Month: September (seasonal_factor for e-bikes = 1.2)
- Market capacity: 200 bikes/month
- Player wants to sell: 30 e-bikes @ 800€
- Competitor offers: 25 e-bikes @ 750€

### Calculation:
```
Base Demand = 200 × 1.5 (green city) × 0.4 (standard segment) × 1.2 (Sept.) = 144 bikes

All offers:
  - 30 player e-bikes @ 800€ (avg age 1 month → no penalty)
  - 25 competitor e-bikes @ 750€

Price elasticity:
  avg_price = (30×800 + 25×750) / 55 = 777€
  base_price_standard = 700€
  price_ratio = 777/700 = 1.11
  elasticity = 1.0 - (1.11-1.0) × 1.0 × 0.5 = 0.945

Adjusted Demand = 144 × 0.945 = 136 bikes

Sort offers by price (with 10% random):
  1. Competitor bikes @ ~750€ × random(0.95-1.05)
  2. Player bikes @ ~800€ × random(0.95-1.05)

Allocation:
  - First 25 competitor bikes sell (750€)
  - Next 30 player bikes sell (800€)
  - Total: 55 bikes (well below 136 demand)
  - Result: ALL bikes sell! ✓

Player sees:
  Planned: 30 bikes
  Sold: 30 bikes
  Success: 100%
  Revenue: 30 × (800 - transport_cost)
  Status: ✓ Fully sold
```

## Key Differences from Old System

| Aspect | Old System | New System |
|--------|-----------|------------|
| **Timing** | Immediate | Deferred (next month) |
| **Execution** | Always sells | May not sell if oversaturated |
| **Competition** | Ignored | Integrated with AI competitors |
| **Market Dynamics** | None | Supply/demand, elasticity, seasons |
| **Feedback** | Simple success | Detailed results with reasons |
| **Location** | Not considered | Affects demand by bike type |
| **Pricing Strategy** | No impact | Affects sales probability |
| **Realism** | Low | High |
| **Player Strategy** | Simple | Complex, requires planning |

## Benefits

1. **Strategic Depth**: Players must consider timing, pricing, and market conditions
2. **Market Awareness**: Different locations favor different bike types
3. **Risk/Reward**: Higher prices = higher revenue but lower sell chance
4. **Seasonal Strategy**: Plan production around peak demand months
5. **Competitive Edge**: Players see their performance vs. AI competitors
6. **Learning Feedback**: Clear reasons why sales succeeded/failed
7. **Realistic Simulation**: Mirrors real-world market dynamics
8. **Engagement**: More interesting than guaranteed sales

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (sales.html)                     │
│  - Form for sales decisions                                  │
│  - Pending decisions display                                 │
│  - Recent results feedback                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓ POST /sales/{session_id}/
┌─────────────────────────────────────────────────────────────┐
│                    Views (sales/views.py)                    │
│  - Validate input                                            │
│  - Create SalesDecision records                              │
│  - Return preview summary                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Data stored in DB
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Models (sales/models.py)                   │
│  - SalesDecision (pending decisions)                         │
│  - Market (with location characteristics)                    │
│  - SalesOrder (completed sales)                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ When month advances
                           ↓
┌─────────────────────────────────────────────────────────────┐
│             Engine (simulation/engine.py)                    │
│  process_month() → _process_competitive_sales()              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         Market Simulator (sales/market_simulator.py)         │
│  - Process pending decisions                                 │
│  - Calculate market demand                                   │
│  - Collect player + competitor offers                        │
│  - Apply supply/demand dynamics                              │
│  - Execute successful sales                                  │
│  - Mark decisions as processed with results                  │
└─────────────────────────────────────────────────────────────┘
```
