# Quick Reference: Deferred Sales System

## For Developers

### Key Files Modified/Created
- `sales/models.py` - Added SalesDecision model, updated Market model
- `sales/market_simulator.py` - NEW: Market simulation engine
- `sales/views.py` - Modified to store decisions instead of immediate sales
- `sales/admin.py` - Added admin interfaces
- `simulation/engine.py` - Integrated market simulator
- `templates/sales/sales.html` - Added pending/feedback sections
- `sales/migrations/0003_*.py` - Database migration

### Quick Commands
```bash
# Check for errors
python3 manage.py check

# View pending decisions
python3 manage.py shell -c "from sales.models import SalesDecision; print(SalesDecision.objects.filter(is_processed=False).count())"

# View sales results
python3 manage.py shell -c "from sales.models import SalesDecision; [print(f'{d.bike_type.name}: {d.quantity_sold}/{d.quantity} sold') for d in SalesDecision.objects.filter(is_processed=True)[:5]]"

# Access admin
python3 manage.py runserver
# Navigate to: http://localhost:8000/admin/sales/salesdecision/
```

### Key Model Fields

#### SalesDecision
```python
session          # Which game session
market           # Target market
bike_type        # Type of bike
price_segment    # cheap/standard/premium
quantity         # How many to sell
desired_price    # Player's asking price
transport_cost   # Cost per bike
decision_month   # When decided
is_processed     # Has simulator run?
quantity_sold    # How many actually sold
actual_revenue   # Money received
unsold_reason    # Why didn't sell
```

#### Market (new fields)
```python
location_type          # urban/suburban/rural/mountainous/coastal
green_city_factor      # E-bike demand multiplier
mountain_bike_factor   # Mountain bike demand multiplier
road_bike_factor       # Road bike demand multiplier
city_bike_factor       # City bike demand multiplier
```

### Integration Points

#### In simulation/engine.py
```python
def _process_competitive_sales(self):
    # Player sales decisions processed first
    self.market_simulator.process_pending_sales_decisions(
        self.session.current_month,
        self.session.current_year
    )

    # Then existing competitive engine
    self.competitive_sales_engine.process_competitive_sales(...)
```

#### In sales/views.py
```python
# Old way (immediate):
bike.is_sold = True
session.balance += revenue

# New way (deferred):
SalesDecision.objects.create(
    session=session,
    market=market,
    bike_type=bike_type,
    quantity=quantity,
    desired_price=price,
    ...
)
# Execution happens later in market simulator
```

## For Gameplay Designers

### Market Location Characteristics

| Location Type | E-bikes | Mountain | Road | City |
|--------------|---------|----------|------|------|
| Urban | 1.2 | 0.7 | 1.0 | 1.5 |
| Suburban | 1.0 | 0.9 | 1.1 | 1.2 |
| Rural | 0.7 | 1.1 | 1.3 | 0.8 |
| Mountainous | 0.8 | 1.8 | 0.7 | 0.6 |
| Coastal | 1.1 | 0.8 | 1.3 | 1.1 |

*Values are multipliers for base demand*

### Seasonal Factors

| Bike Type | Peak Season | Factor | Low Season | Factor |
|-----------|-------------|--------|------------|--------|
| Mountain | May-Aug | 1.3× | Nov-Feb | 0.7× |
| Road | Apr-Aug | 1.2× | Nov-Feb | 0.8× |
| E-Bike | Sep-Oct | 1.2× | Dec-Feb | 0.9× |
| City | Year-round | 1.0× | Year-round | 1.0× |

### Segment Distribution

| Segment | Base Demand % | Typical Price | Quality Factor |
|---------|---------------|---------------|----------------|
| Cheap | 40% | 400€ | 0.8 |
| Standard | 40% | 700€ | 1.0 |
| Premium | 20% | 1200€ | 1.3 |

### Price Elasticity

Formula: `demand_adjustment = 1.0 - (price_ratio - 1.0) × elasticity × 0.5`

Example:
- Base price: 700€
- Your price: 800€
- Elasticity: 1.0
- Ratio: 800/700 = 1.14
- Adjustment: 1.0 - (1.14-1.0) × 1.0 × 0.5 = 0.93
- Result: 7% demand reduction

### Aging Penalties

| Inventory Age | Price Penalty |
|---------------|---------------|
| 0-1 months | 100% (no penalty) |
| 2-3 months | 95% |
| 4-6 months | 90% |
| 7+ months | 85% |

## For Players

### Strategy Tips

1. **Timing**
   - Plan sales 3 months ahead (sales process quarterly)
   - Produce mountain bikes before summer
   - E-bikes sell best in fall

2. **Pricing**
   - Lower prices = higher chance to sell
   - But also lower profit margins
   - Check competitor prices (visible in dashboard)
   - Don't price too high or demand drops

3. **Location Selection**
   - Sell e-bikes to green cities (Copenhagen, Amsterdam)
   - Sell mountain bikes to mountainous regions (Alps, Rockies)
   - Sell road bikes to coastal/suburban areas
   - City bikes work everywhere

4. **Segment Strategy**
   - Cheap/Standard segments have 40% demand each
   - Premium only has 20% demand
   - Don't overproduce premium bikes

5. **Inventory Management**
   - Old inventory sells for less (aging penalty)
   - Better to sell at lower price than hold too long
   - Monitor "months in inventory" stat

### Reading Feedback

#### Success Rates
- **Green (80-100%)**: Excellent pricing and timing
- **Yellow (50-79%)**: Okay, but could improve
- **Red (0-49%)**: Poor - adjust strategy

#### Unsold Reasons
- **"Market oversaturated"**: Too much supply, not enough demand
  - Solution: Lower prices, sell to different market, wait
- **"Price too high"**: Your pricing isn't competitive
  - Solution: Reduce prices
- **"Partially sold"**: Some sold, some didn't
  - Solution: Check what sold and adjust

## For Testing

### Test Scenarios

#### 1. Basic Sales Decision
```python
from sales.models import SalesDecision, Market
from bikeshop.models import GameSession, BikeType

session = GameSession.objects.first()
market = Market.objects.filter(session=session).first()
bike_type = BikeType.objects.filter(session=session).first()

decision = SalesDecision.objects.create(
    session=session,
    market=market,
    bike_type=bike_type,
    price_segment='standard',
    quantity=5,
    desired_price=700,
    transport_cost=20,
    decision_month=session.current_month,
    decision_year=session.current_year
)

print(f"Created decision: {decision.id}")
```

#### 2. Process Decisions Manually
```python
from simulation.engine import SimulationEngine

session = GameSession.objects.first()
engine = SimulationEngine(session)

# This processes the entire month, including sales
engine.process_month()

# Check results
from sales.models import SalesDecision
decisions = SalesDecision.objects.filter(
    session=session,
    is_processed=True
).order_by('-created_at')[:5]

for d in decisions:
    print(f"{d.bike_type.name}: {d.quantity_sold}/{d.quantity} sold for {d.actual_revenue}€")
```

#### 3. Test Market Demand Calculation
```python
from sales.market_simulator import MarketSimulator
from sales.models import Market
from bikeshop.models import BikeType

session = GameSession.objects.first()
simulator = MarketSimulator(session)

market = Market.objects.filter(session=session).first()
bike_type = BikeType.objects.filter(session=session, name__icontains='E-').first()

demand = simulator._calculate_market_demand(
    market=market,
    bike_type=bike_type,
    price_segment='standard',
    month=9  # September
)

print(f"Calculated demand: {demand} bikes")
```

#### 4. View Pending Summary
```python
from sales.market_simulator import MarketSimulator

session = GameSession.objects.first()
simulator = MarketSimulator(session)

summary = simulator.get_pending_decisions_summary()

print(f"Total pending: {summary['total_quantity']} bikes")
print(f"Expected revenue: {summary['total_expected_revenue']}€")
for market, data in summary['by_market'].items():
    print(f"  {market}: {data['quantity']} bikes for {data['expected_revenue']}€")
```

## Troubleshooting

### Problem: Sales not processing
**Check:**
1. Are decisions marked as `is_processed=False`?
2. Is the decision month <= current month?
3. Are you advancing to a month divisible by 3? (sales process quarterly)
4. Check logs for errors during `process_month()`

### Problem: All bikes showing as unsold
**Check:**
1. Are prices way too high? (check elasticity adjustment)
2. Is market capacity very low?
3. Are competitors flooding the market?
4. Check actual demand calculation in logs

### Problem: Pending decisions not showing in UI
**Check:**
1. Is `pending_decisions` in context? (views.py)
2. Are there actually unprocessed decisions?
3. Check template if-condition: `{% if pending_decisions.total_quantity > 0 %}`

### Problem: Recent results not showing
**Check:**
1. Have any decisions been processed recently?
2. Is `recent_sales_results` in context?
3. Check filter: decisions from last month only

## Performance Notes

- Market simulation runs in O(n×m) where n=decisions, m=markets
- Uses `select_related()` for efficient queries
- All operations are in a transaction
- For 100 decisions across 5 markets: ~1-2 seconds
- Logging can be disabled for production performance

## Maintenance

### Adding New Location Type
1. Add to `Market.LOCATION_TYPE_CHOICES`
2. Set appropriate bike type factors in market instances
3. Update documentation

### Adjusting Demand Factors
All factors are in `sales/market_simulator.py`:
- Segment distribution: `_calculate_market_demand()`
- Seasonal factors: `_get_seasonal_factor()`
- Quality factors: `_get_quality_factor()`
- Base prices: `_get_base_price_for_segment()`

### Changing Processing Frequency
Currently sales process every 3 months. To change:
```python
# In simulation/engine.py, line ~54
if self.session.current_month % 3 == 0:  # Change this
    self._process_competitive_sales()
```

## References

- Full documentation: `DEFERRED_SALES_IMPLEMENTATION.md`
- Flow diagram: `SALES_FLOW_DIAGRAM.md`
- Models: `sales/models.py`
- Simulator: `sales/market_simulator.py`
- Views: `sales/views.py`
- Template: `templates/sales/sales.html`
