from django.db import models
from decimal import Decimal
import math
import random
from sales.models import Market, MarketDemand, MarketPriceSensitivity
from competitors.models import MarketCompetition, AICompetitor, CompetitorSale
from production.models import ProducedBike
from sales.models import SalesOrder


class MarketVolumeEngine:
    """Engine for calculating market volume constraints and demand curves"""
    
    def __init__(self, session):
        self.session = session
    
    def calculate_market_volume_for_period(self, month, year):
        """Calculate market volumes for all markets and bike types for a given period"""
        markets = Market.objects.filter(session=self.session)
        from bikeshop.models import BikeType
        bike_types = BikeType.objects.filter(session=self.session)
        
        for market in markets:
            for bike_type in bike_types:
                for segment in ['cheap', 'standard', 'premium']:
                    self._calculate_segment_volume(market, bike_type, segment, month, year)
    
    def _calculate_segment_volume(self, market, bike_type, segment, month, year):
        """Calculate volume constraints for a specific market/bike/segment combination"""
        # Get or create market competition record
        competition, created = MarketCompetition.objects.get_or_create(
            session=self.session,
            market=market,
            bike_type=bike_type,
            price_segment=segment,
            month=month,
            year=year,
            defaults={
                'estimated_demand': 0,
                'maximum_market_volume': 0,
                'demand_curve_elasticity': 1.0,
                'optimal_price_point': Decimal('500.00')
            }
        )
        
        # Calculate base demand
        base_demand = self._calculate_base_demand(market, bike_type, segment, month)
        
        # Calculate maximum market volume (capacity constraint)
        max_volume = self._calculate_maximum_volume(market, bike_type, segment)
        
        # Calculate demand curve parameters
        elasticity = self._calculate_demand_elasticity(market, bike_type, segment)
        optimal_price = self._calculate_optimal_price(bike_type, segment)
        
        # Update competition record
        competition.estimated_demand = base_demand
        competition.maximum_market_volume = max_volume
        competition.demand_curve_elasticity = elasticity
        competition.optimal_price_point = optimal_price
        competition.save()
        
        return competition
    
    def _calculate_base_demand(self, market, bike_type, segment, month):
        """Calculate base demand considering seasonal, preference, and business strategy factors"""
        # Start with market demand if available
        try:
            market_demand = MarketDemand.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type
            )
            base_demand_percentage = market_demand.demand_percentage
        except MarketDemand.DoesNotExist:
            # Fallback to default values
            base_demand_percentage = 0.3
        
        # Market capacity as baseline
        market_capacity = market.monthly_volume_capacity
        
        # Apply bike type demand percentage
        type_demand = int(market_capacity * base_demand_percentage)
        
        # Segment distribution
        segment_factors = {
            'cheap': 0.5,    # 50% of demand is price-sensitive
            'standard': 0.35, # 35% standard segment
            'premium': 0.15   # 15% premium segment
        }
        
        segment_demand = int(type_demand * segment_factors.get(segment, 0.3))
        
        # Seasonal adjustments
        seasonal_factor = self._get_seasonal_demand_factor(bike_type.name, month)
        seasonal_demand = int(segment_demand * seasonal_factor)
        
        # Apply business strategy effects (marketing and sustainability)
        business_strategy_factor = self._get_business_strategy_demand_factor(market, bike_type, segment)
        strategy_adjusted_demand = int(seasonal_demand * business_strategy_factor)
        
        # Add random variation (±20%)
        variation = random.uniform(0.8, 1.2)
        final_demand = int(strategy_adjusted_demand * variation)
        
        return max(1, final_demand)
    
    def _calculate_maximum_volume(self, market, bike_type, segment):
        """Calculate absolute maximum sales volume for this market segment"""
        # Market capacity constraint
        market_capacity = market.monthly_volume_capacity
        
        # Segment capacity distribution (cheap has more capacity)
        segment_capacity_factors = {
            'cheap': 0.6,     # 60% of market capacity for cheap
            'standard': 0.3,  # 30% for standard
            'premium': 0.1    # 10% for premium
        }
        
        segment_capacity = int(market_capacity * segment_capacity_factors.get(segment, 0.3))
        
        # Bike type popularity factor
        bike_popularity_factors = self._get_bike_type_popularity(bike_type.name)
        type_capacity = int(segment_capacity * bike_popularity_factors)
        
        return max(1, type_capacity)
    
    def _calculate_demand_elasticity(self, market, bike_type, segment):
        """Calculate price elasticity of demand"""
        # Get market price sensitivity if available
        try:
            price_sensitivity = MarketPriceSensitivity.objects.filter(
                session=self.session,
                market=market,
                price_segment=segment
            ).first()
            if price_sensitivity:
                base_elasticity = price_sensitivity.percentage / 100.0
            else:
                raise MarketPriceSensitivity.DoesNotExist
        except MarketPriceSensitivity.DoesNotExist:
            # Default elasticity values
            segment_elasticities = {
                'cheap': 1.5,     # Very price sensitive
                'standard': 1.0,  # Normal sensitivity
                'premium': 0.7    # Less price sensitive
            }
            base_elasticity = segment_elasticities.get(segment, 1.0)
        
        # Apply market elasticity factor
        market_elasticity = market.price_elasticity_factor
        final_elasticity = base_elasticity * market_elasticity
        
        # Bike type adjustments
        bike_elasticity_factors = {
            'city': 1.2,      # City bikes are more price sensitive
            'mountain': 0.8,  # Mountain bikes less sensitive (enthusiasts)
            'e-': 0.6         # E-bikes least sensitive (premium product)
        }
        
        bike_name_lower = bike_type.name.lower()
        for bike_key, factor in bike_elasticity_factors.items():
            if bike_key in bike_name_lower:
                final_elasticity *= factor
                break
        
        return max(0.1, min(3.0, final_elasticity))
    
    def _calculate_optimal_price(self, bike_type, segment):
        """Calculate the optimal price point for maximum volume"""
        from bikeshop.models import BikePrice
        
        # Try to get configured price
        try:
            bike_price = BikePrice.objects.get(
                session=self.session,
                bike_type=bike_type,
                price_segment=segment
            )
            return bike_price.price
        except BikePrice.DoesNotExist:
            # Estimate based on segment and bike complexity
            base_prices = {
                'cheap': Decimal('300.00'),
                'standard': Decimal('600.00'),
                'premium': Decimal('1200.00')
            }
            
            base_price = base_prices.get(segment, Decimal('600.00'))
            
            # Adjust for bike type complexity
            bike_name_lower = bike_type.name.lower()
            if 'e-' in bike_name_lower:
                base_price *= Decimal('1.8')  # E-bikes are more expensive
            elif 'mountain' in bike_name_lower:
                base_price *= Decimal('1.3')  # Mountain bikes cost more
            elif 'racing' in bike_name_lower:
                base_price *= Decimal('1.5')  # Racing bikes are premium
            
            return base_price
    
    def _get_seasonal_demand_factor(self, bike_type_name, month):
        """Get seasonal demand multiplier"""
        name_lower = bike_type_name.lower()
        
        # Spring/Summer peaks
        if month in [4, 5, 6, 7, 8]:
            if 'mountain' in name_lower or 'racing' in name_lower:
                return 1.4  # High demand for outdoor bikes
            elif 'city' in name_lower:
                return 1.2  # Moderate increase for city bikes
            else:
                return 1.1  # General increase
        
        # Autumn moderate
        elif month in [3, 9, 10]:
            if 'e-' in name_lower:
                return 1.3  # E-bikes popular in milder weather
            else:
                return 1.0
        
        # Winter low
        elif month in [11, 12, 1, 2]:
            return 0.7  # Lower demand in winter
        
        return 1.0
    
    def _get_business_strategy_demand_factor(self, market, bike_type, segment):
        """Get demand multiplier from business strategy effects (marketing and sustainability)"""
        try:
            from business_strategy.business_engine import BusinessStrategyEngine
            engine = BusinessStrategyEngine(self.session)
            
            # Get marketing effects
            marketing_effects = engine.get_marketing_demand_bonuses()
            marketing_boost = marketing_effects.get('demand_boost', 0.0) / 100.0  # Convert percentage to decimal
            
            # Get sustainability effects
            sustainability_effects = engine.get_sustainability_effects()
            sustainability_modifier = sustainability_effects.get('demand_modifier', 1.0)
            
            # Combine effects
            # Marketing provides additive boost, sustainability provides multiplicative modifier
            combined_factor = (1.0 + marketing_boost) * sustainability_modifier
            
            # Apply segment-specific modifiers
            if segment == 'premium':
                # Premium customers are more responsive to marketing and sustainability
                combined_factor = 1.0 + (combined_factor - 1.0) * 1.3
            elif segment == 'cheap':
                # Budget customers are less responsive to marketing, more to price
                combined_factor = 1.0 + (combined_factor - 1.0) * 0.7
            
            # Cap the total effect to prevent unrealistic boosts
            return max(0.5, min(2.0, combined_factor))
            
        except ImportError:
            # Fallback if business strategy is not available
            return 1.0
        except Exception:
            # Handle any other errors gracefully
            return 1.0
    
    def _get_bike_type_popularity(self, bike_type_name):
        """Get bike type popularity factor"""
        name_lower = bike_type_name.lower()
        
        if 'city' in name_lower:
            return 0.4  # Very popular general purpose
        elif 'e-' in name_lower:
            return 0.3  # Growing segment
        elif 'mountain' in name_lower:
            return 0.2  # Niche but profitable
        elif 'racing' in name_lower:
            return 0.1  # Small niche market
        else:
            return 0.3  # Default
    
    def calculate_demand_at_price(self, competition, price):
        """Calculate demand quantity at a specific price using demand curve"""
        if not competition.optimal_price_point or competition.optimal_price_point == 0:
            return competition.estimated_demand
        
        # Simple demand curve: Q = Q_max * (P_optimal / P) ^ elasticity
        price_ratio = float(competition.optimal_price_point) / max(float(price), 1.0)
        elasticity = competition.demand_curve_elasticity
        
        demand_multiplier = math.pow(price_ratio, elasticity)
        demand_at_price = int(competition.estimated_demand * demand_multiplier)
        
        # Constrain to maximum volume
        return min(demand_at_price, competition.maximum_market_volume)
    
    def get_available_market_capacity(self, competition, current_sales=0):
        """Get remaining market capacity after current sales"""
        remaining_capacity = competition.maximum_market_volume - current_sales
        return max(0, remaining_capacity)
    
    def distribute_market_demand(self, competition, offers):
        """
        Distribute market demand among competing offers
        
        Args:
            competition: MarketCompetition instance
            offers: List of dicts with keys: 'seller', 'quantity', 'price', 'quality_factor'
        
        Returns:
            List of allocation results: [{'seller': seller, 'quantity_allocated': int, 'price': price}, ...]
        """
        if not offers:
            return []
        
        # Calculate demand at each price point
        total_demand = 0
        for offer in offers:
            demand_at_price = self.calculate_demand_at_price(competition, offer['price'])
            offer['demand_at_price'] = demand_at_price
            total_demand += demand_at_price
        
        # Calculate market share based on competitiveness
        allocations = []
        remaining_capacity = competition.maximum_market_volume
        
        # Sort offers by competitiveness (price and quality)
        sorted_offers = sorted(offers, key=lambda x: self._calculate_competitiveness_score(x), reverse=True)
        
        for offer in sorted_offers:
            if remaining_capacity <= 0:
                allocation = offer.copy()
                allocation['quantity_allocated'] = 0
                allocations.append(allocation)
                continue
            
            # Calculate market share based on competitiveness
            competitiveness = self._calculate_competitiveness_score(offer)
            total_competitiveness = sum(self._calculate_competitiveness_score(o) for o in offers)
            
            if total_competitiveness > 0:
                market_share = competitiveness / total_competitiveness
            else:
                market_share = 1.0 / len(offers)
            
            # Allocate quantity based on market share and demand
            base_allocation = int(competition.estimated_demand * market_share)
            
            # Constrain by offer quantity and remaining capacity
            allocated_quantity = min(
                offer['quantity'],
                base_allocation,
                remaining_capacity
            )
            
            # Copy all offer data and add allocation result
            allocation = offer.copy()
            allocation['quantity_allocated'] = allocated_quantity
            allocations.append(allocation)
            
            remaining_capacity -= allocated_quantity
        
        return allocations
    
    def _calculate_competitiveness_score(self, offer):
        """Calculate competitiveness score for market share allocation"""
        # Base score from price competitiveness (lower price = higher score)
        price = float(offer['price'])
        price_score = 1000.0 / max(price, 1.0)  # Inverse relationship
        
        # Quality factor bonus
        quality_factor = offer.get('quality_factor', 1.0)
        quality_score = quality_factor * 100
        
        # Combine scores
        total_score = price_score + quality_score
        
        return total_score