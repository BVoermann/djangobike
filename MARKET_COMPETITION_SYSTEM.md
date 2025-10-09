# Enhanced Market Competition System

## Overview

The bike shop simulation now includes a comprehensive market competition system that implements realistic competitive dynamics between AI competitors and the player. The system replaces simple probability-based sales with volume-constrained competitive market allocation.

## Key Features Implemented

### 1. Price-Sales Function Model
- **Demand curves**: Higher prices reduce sales volume based on price elasticity
- **Price elasticity**: Configurable per market and bike type/segment
- **Segment sensitivity**: Premium segments are less price-sensitive than budget segments

### 2. Market Volume Constraints
- **Maximum market capacity**: Each market has a monthly volume capacity limit
- **Segment distribution**: Different capacity allocation for cheap/standard/premium segments
- **Total sales constraint**: Combined player + AI sales cannot exceed market volume

### 3. Dynamic Market Competition
- **Competitive bidding**: Multiple sellers compete for the same market segments
- **Market share allocation**: Better price/quality combinations win larger market shares
- **Real-time saturation**: Market saturation affects pricing pressure and sales success

### 4. Inventory Carryover System
- **Aging effects**: Older inventory suffers price penalties (5-15% based on age)
- **Storage costs**: 2% of production cost per month for unsold inventory
- **Carryover sales**: Unsold bikes remain available for future sales periods

### 5. Enhanced Sales Processing
- **Market-volume-constrained allocation**: Replaces simple probability-based system
- **Competitive pricing**: Sellers with better prices/quality get higher allocation
- **Monthly inventory updates**: Track aging and storage costs continuously

## Technical Implementation

### New Models and Fields

#### Market Model Enhancements
```python
monthly_volume_capacity = models.IntegerField(default=200)
price_elasticity_factor = models.FloatField(default=1.0)
```

#### ProducedBike Model Enhancements
```python
months_in_inventory = models.IntegerField(default=0)
storage_cost_accumulated = models.DecimalField(max_digits=8, decimal_places=2, default=0)

def get_age_penalty_factor(self):
    """Returns price penalty factor based on inventory age (0.85-1.0)"""
    
def update_inventory_age(self, current_month, current_year):
    """Updates age and calculates storage costs"""
```

#### CompetitorProduction Model Enhancements
```python
quantity_in_inventory = models.IntegerField(default=0)
months_in_inventory = models.IntegerField(default=0)

def get_inventory_age_penalty(self):
    """Returns price penalty for aged competitor inventory"""
```

#### MarketCompetition Model Enhancements
```python
maximum_market_volume = models.IntegerField(default=0)
actual_sales_volume = models.IntegerField(default=0)
demand_curve_elasticity = models.FloatField(default=1.0)
optimal_price_point = models.DecimalField(max_digits=8, decimal_places=2, default=0)
```

### New Engine Classes

#### MarketVolumeEngine
- **Location**: `simulation/market_volume_engine.py`
- **Purpose**: Calculate market volume constraints and demand curves
- **Key methods**:
  - `calculate_market_volume_for_period()`: Set volume limits for all market segments
  - `calculate_demand_at_price()`: Apply demand curve to determine sales volume
  - `distribute_market_demand()`: Allocate sales among competing offers

#### CompetitiveSalesEngine
- **Location**: `simulation/competitive_sales_engine.py` 
- **Purpose**: Process competitive sales with market constraints
- **Key methods**:
  - `process_competitive_sales()`: Main sales processing with competition
  - `_collect_player_offers()`: Gather player sales offers
  - `_collect_competitor_offers()`: Gather AI competitor offers
  - `_execute_sale()`: Complete successful sales transactions

### Enhanced AI Competitor Behavior

#### Inventory Management
- **Age tracking**: Competitors track inventory age and apply price penalties
- **Clearance strategies**: Aggressive competitors liquidate old inventory
- **Strategic quantity offers**: Offer size based on strategy and inventory age

#### Dynamic Pricing
- **Market competition factors**: Adjust prices based on market saturation
- **Strategy-based pricing**: Different price strategies per competitor type
- **Inventory age discounts**: Automatic discounts for aging inventory

#### Production Planning
- **Capacity constraints**: Realistic production limits based on resources
- **Strategy preferences**: Different bike type and segment preferences
- **Market feedback**: Adjust production based on sales performance

## Market Dynamics

### Demand Curve Implementation
```python
demand_at_price = base_demand * (optimal_price / actual_price) ^ elasticity
```

### Market Share Allocation
```python
competitiveness_score = price_competitiveness + quality_bonus
market_share = individual_score / total_competitiveness
allocated_quantity = min(demand * market_share, offered_quantity, remaining_capacity)
```

### Price Pressure Calculation
```python
if saturation > 1.0:
    price_pressure = -min(0.5, (saturation - 1.0) * 0.3)  # Negative = downward pressure
else:
    price_pressure = (1.0 - saturation) * 0.2  # Positive = upward pressure
```

## Usage in Simulation Engine

### Monthly Processing
```python
if self.session.current_month % 3 == 0:
    self._process_competitive_sales()  # Full competitive sales every 3 months
else:
    self._update_inventory_ages()      # Update aging monthly
```

### Dashboard Integration
The system provides enhanced dashboard data including:
- Market competition status per segment
- Inventory aging summary with storage costs
- Competitor performance metrics
- Market saturation levels

## Testing

A comprehensive test suite (`test_market_competition.py`) validates:
- Market volume calculation accuracy
- Competitive sales allocation fairness  
- Inventory aging mechanics
- AI competitor behavior
- Integration with existing simulation engine

## Benefits

### Realistic Market Dynamics
- **Supply/demand balance**: Markets have realistic capacity constraints
- **Price competition**: Better pricing strategies are rewarded
- **Market saturation effects**: Oversupply creates pricing pressure

### Strategic Depth
- **Inventory management**: Players must consider storage costs and aging
- **Pricing strategy**: Price optimization becomes crucial for market share
- **Market timing**: Understanding seasonal and competitive cycles

### AI Intelligence
- **Adaptive competitors**: AI adjusts strategies based on market conditions
- **Realistic behavior**: Competitors have distinct strategies and limitations
- **Dynamic interaction**: AI responds to player actions and market changes

## Performance Considerations

- **Optimized queries**: Efficient database access patterns
- **Batch processing**: Inventory updates processed in batches
- **Caching strategy**: Market competition data cached appropriately
- **Scalable design**: System handles multiple markets and competitors efficiently

## Migration Path

The system is backward compatible:
- **Database migrations**: Automatic schema updates for existing installations  
- **Legacy support**: Old sales processing preserved as fallback
- **Gradual rollout**: Can be enabled per game session
- **Data preservation**: Existing game data remains intact

## Configuration Options

Markets can be configured with:
- **Volume capacity**: Monthly sales limits per market
- **Price elasticity**: Demand curve sensitivity
- **Transport costs**: Shipping cost differentials
- **Seasonal factors**: Built-in seasonal demand adjustments

The enhanced market competition system transforms the bike shop simulation into a realistic business strategy game where market dynamics, competitive positioning, and inventory management are crucial for success.