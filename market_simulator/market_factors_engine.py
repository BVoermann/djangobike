import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from django.utils import timezone
from django.db import transaction

from .models import MarketFactors, EconomicCondition
from multiplayer.models import MultiplayerGame


class MarketFactorsEngine:
    """Engine for simulating dynamic market factors affecting bicycle demand"""
    
    # Seasonal patterns for different factors (12 months)
    SEASONAL_PATTERNS = {
        'weather_favorability': [0.3, 0.4, 0.6, 0.8, 1.2, 1.4, 1.5, 1.4, 1.2, 0.9, 0.5, 0.3],
        'seasonal_factor': [0.6, 0.7, 0.9, 1.1, 1.3, 1.5, 1.6, 1.5, 1.3, 1.0, 0.7, 0.6],
        'health_fitness_trend': [1.4, 1.3, 1.2, 1.0, 0.9, 0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]  # New Year effect
    }
    
    # Trend evolution parameters
    TREND_EVOLUTION = {
        'retro_trend_strength': {
            'base_volatility': 0.05,
            'cycle_length': 24,  # months
            'amplitude': 0.3
        },
        'electric_bike_trend': {
            'base_volatility': 0.03,
            'growth_rate': 0.02,  # monthly growth
            'saturation_point': 2.5
        },
        'health_fitness_trend': {
            'base_volatility': 0.04,
            'cycle_length': 36,
            'amplitude': 0.4
        },
        'environmental_consciousness': {
            'base_volatility': 0.02,
            'growth_rate': 0.01,
            'saturation_point': 1.6
        }
    }
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.current_factors = None
        
    def initialize_market_factors(self, starting_month: int, starting_year: int) -> MarketFactors:
        """Initialize market factors for a new game"""
        
        # Start with baseline conditions
        factors = MarketFactors.objects.create(
            multiplayer_game=self.game,
            month=starting_month,
            year=starting_year,
            retro_trend_strength=1.0,
            electric_bike_trend=1.2,  # Start with growing e-bike trend
            health_fitness_trend=1.0,
            environmental_consciousness=1.1,  # Slightly above baseline
            gas_price_index=100.0,
            carbon_tax_level=0.0,
            weather_favorability=self._get_seasonal_weather(starting_month),
            seasonal_factor=self._get_seasonal_factor(starting_month),
            cycling_infrastructure_index=100.0,
            government_bike_incentives=0.0,
            smart_bike_adoption=1.0,
            bike_sharing_competition=1.0
        )
        
        self.current_factors = factors
        return factors
    
    def advance_market_factors(self, target_month: int, target_year: int, 
                             economic_condition: EconomicCondition) -> MarketFactors:
        """Advance market factors to target month/year"""
        
        # Get current factors or create initial ones
        try:
            current_factors = MarketFactors.objects.filter(
                multiplayer_game=self.game
            ).latest('year', 'month')
        except MarketFactors.DoesNotExist:
            current_factors = self.initialize_market_factors(target_month, target_year)
            return current_factors
        
        # Check if we need to advance
        if (current_factors.year == target_year and 
            current_factors.month == target_month):
            return current_factors
        
        # Generate new market factors
        new_factors = self._generate_next_month_factors(current_factors, target_month, target_year, economic_condition)
        
        self.current_factors = new_factors
        return new_factors
    
    def _generate_next_month_factors(self, previous_factors: MarketFactors, 
                                   month: int, year: int,
                                   economic_condition: EconomicCondition) -> MarketFactors:
        """Generate market factors for the next month"""
        
        # Calculate months elapsed since game start
        months_elapsed = self._calculate_months_since_start(month, year)
        
        with transaction.atomic():
            new_factors = MarketFactors.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year,
                
                # Trend factors
                retro_trend_strength=self._evolve_retro_trend(previous_factors.retro_trend_strength, months_elapsed),
                electric_bike_trend=self._evolve_electric_bike_trend(previous_factors.electric_bike_trend, months_elapsed, economic_condition),
                health_fitness_trend=self._evolve_health_fitness_trend(previous_factors.health_fitness_trend, months_elapsed, month),
                
                # Environmental factors
                environmental_consciousness=self._evolve_environmental_consciousness(previous_factors.environmental_consciousness, months_elapsed, economic_condition),
                gas_price_index=self._evolve_gas_prices(previous_factors.gas_price_index, economic_condition),
                carbon_tax_level=self._evolve_carbon_tax(previous_factors.carbon_tax_level, months_elapsed),
                
                # Weather and seasonal
                weather_favorability=self._get_seasonal_weather(month),
                seasonal_factor=self._get_seasonal_factor(month),
                
                # Infrastructure and policy
                cycling_infrastructure_index=self._evolve_infrastructure(previous_factors.cycling_infrastructure_index, months_elapsed, economic_condition),
                government_bike_incentives=self._evolve_government_incentives(previous_factors.government_bike_incentives, economic_condition),
                
                # Technology factors
                smart_bike_adoption=self._evolve_smart_bike_adoption(previous_factors.smart_bike_adoption, months_elapsed),
                bike_sharing_competition=self._evolve_bike_sharing_competition(previous_factors.bike_sharing_competition, months_elapsed, economic_condition)
            )
        
        return new_factors
    
    def _evolve_retro_trend(self, current_value: float, months_elapsed: int) -> float:
        """Evolve retro/vintage bicycle trend strength"""
        
        params = self.TREND_EVOLUTION['retro_trend_strength']
        
        # Cyclical component (retro trends come and go)
        cycle_component = params['amplitude'] * math.sin(2 * math.pi * months_elapsed / params['cycle_length'])
        
        # Random volatility
        random_component = random.gauss(0, params['base_volatility'])
        
        # New value
        new_value = current_value + cycle_component * 0.1 + random_component
        
        return max(0.5, min(2.0, new_value))
    
    def _evolve_electric_bike_trend(self, current_value: float, months_elapsed: int, 
                                  economic_condition: EconomicCondition) -> float:
        """Evolve electric bike adoption trend"""
        
        params = self.TREND_EVOLUTION['electric_bike_trend']
        
        # Growth trend (with saturation)
        saturation_factor = 1.0 - (current_value / params['saturation_point'])
        growth_component = params['growth_rate'] * saturation_factor
        
        # Economic influence (good economy accelerates e-bike adoption)
        economic_multiplier = economic_condition.economic_strength
        growth_component *= economic_multiplier
        
        # Random volatility
        random_component = random.gauss(0, params['base_volatility'])
        
        # Technology adoption events (rare step changes)
        if random.random() < 0.02:  # 2% chance per month
            tech_breakthrough = random.uniform(0.1, 0.3)
            growth_component += tech_breakthrough
        
        new_value = current_value + growth_component + random_component
        
        return max(0.5, min(3.0, new_value))
    
    def _evolve_health_fitness_trend(self, current_value: float, months_elapsed: int, month: int) -> float:
        """Evolve health and fitness consciousness trend"""
        
        params = self.TREND_EVOLUTION['health_fitness_trend']
        
        # Seasonal component (New Year effect, summer preparation)
        seasonal_adjustment = self.SEASONAL_PATTERNS['health_fitness_trend'][month - 1]
        seasonal_component = (seasonal_adjustment - 1.0) * 0.05
        
        # Long-term cyclical trend
        cycle_component = params['amplitude'] * math.sin(2 * math.pi * months_elapsed / params['cycle_length'])
        
        # Random events (health campaigns, celebrity endorsements, etc.)
        if random.random() < 0.03:  # 3% chance per month
            event_impact = random.uniform(-0.1, 0.2)  # Usually positive
        else:
            event_impact = 0
        
        # Random volatility
        random_component = random.gauss(0, params['base_volatility'])
        
        new_value = current_value + seasonal_component + cycle_component * 0.05 + event_impact + random_component
        
        return max(0.7, min(2.0, new_value))
    
    def _evolve_environmental_consciousness(self, current_value: float, months_elapsed: int,
                                         economic_condition: EconomicCondition) -> float:
        """Evolve environmental consciousness level"""
        
        params = self.TREND_EVOLUTION['environmental_consciousness']
        
        # Long-term growth trend (with saturation)
        saturation_factor = 1.0 - (current_value / params['saturation_point'])
        growth_component = params['growth_rate'] * saturation_factor
        
        # Economic condition effect (good economy allows more environmental focus)
        if economic_condition.business_cycle_phase in ['expansion', 'peak']:
            economic_boost = 0.005
        else:
            economic_boost = -0.002  # Environmental concerns take backseat in recessions
        
        # Environmental events (disasters, agreements, etc.)
        if random.random() < 0.015:  # 1.5% chance per month
            event_impact = random.uniform(0.05, 0.15)  # Usually positive
        else:
            event_impact = 0
        
        # Random volatility
        random_component = random.gauss(0, params['base_volatility'])
        
        new_value = current_value + growth_component + economic_boost + event_impact + random_component
        
        return max(0.8, min(1.8, new_value))
    
    def _evolve_gas_prices(self, current_index: float, economic_condition: EconomicCondition) -> float:
        """Evolve gas price index"""
        
        # Economic activity affects gas prices
        if economic_condition.business_cycle_phase == 'expansion':
            base_change = random.uniform(0.5, 2.0)
        elif economic_condition.business_cycle_phase == 'peak':
            base_change = random.uniform(-1.0, 1.5)
        elif economic_condition.business_cycle_phase == 'contraction':
            base_change = random.uniform(-3.0, 0.5)
        else:  # trough
            base_change = random.uniform(-2.0, 1.0)
        
        # Random supply/demand shocks
        if random.random() < 0.05:  # 5% chance per month
            shock = random.uniform(-15, 20)  # Oil price shocks
            base_change += shock
        
        # Mean reversion (prices tend to return to baseline)
        mean_reversion = (100.0 - current_index) * 0.02
        
        new_index = current_index + base_change + mean_reversion
        
        return max(50.0, min(200.0, new_index))
    
    def _evolve_carbon_tax(self, current_level: float, months_elapsed: int) -> float:
        """Evolve carbon tax level"""
        
        # Policy changes are infrequent but significant
        if random.random() < 0.01:  # 1% chance per month
            policy_change = random.uniform(-5, 15)  # Usually increases over time
            new_level = current_level + policy_change
        else:
            # Small random variations
            new_level = current_level + random.gauss(0, 0.5)
        
        return max(0.0, min(50.0, new_level))
    
    def _get_seasonal_weather(self, month: int) -> float:
        """Get weather favorability for the given month"""
        return self.SEASONAL_PATTERNS['weather_favorability'][month - 1]
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal demand factor for the given month"""
        return self.SEASONAL_PATTERNS['seasonal_factor'][month - 1]
    
    def _evolve_infrastructure(self, current_index: float, months_elapsed: int,
                             economic_condition: EconomicCondition) -> float:
        """Evolve cycling infrastructure index"""
        
        # Infrastructure improves slowly over time
        base_improvement = 0.2  # 0.2 points per month
        
        # Economic conditions affect infrastructure spending
        if economic_condition.business_cycle_phase in ['expansion', 'peak']:
            economic_multiplier = 1.5
        else:
            economic_multiplier = 0.5  # Budget cuts during recessions
        
        # Random policy initiatives
        if random.random() < 0.02:  # 2% chance per month
            policy_boost = random.uniform(2, 8)
        else:
            policy_boost = 0
        
        monthly_change = base_improvement * economic_multiplier + policy_boost + random.gauss(0, 0.3)
        new_index = current_index + monthly_change
        
        return max(80.0, min(150.0, new_index))
    
    def _evolve_government_incentives(self, current_incentives: float, 
                                    economic_condition: EconomicCondition) -> float:
        """Evolve government bicycle purchase incentives"""
        
        # Policy changes based on economic conditions and environmental goals
        if economic_condition.business_cycle_phase in ['contraction', 'trough']:
            # Stimulus spending might include bike incentives
            if random.random() < 0.03:  # 3% chance per month
                new_program = random.uniform(50, 500)
                return min(1000.0, current_incentives + new_program)
        
        # Environmental policy changes
        if random.random() < 0.015:  # 1.5% chance per month
            policy_change = random.uniform(-100, 300)  # Usually positive
            new_incentives = current_incentives + policy_change
        else:
            # Gradual changes
            new_incentives = current_incentives + random.gauss(0, 10)
        
        return max(0.0, min(1000.0, new_incentives))
    
    def _evolve_smart_bike_adoption(self, current_value: float, months_elapsed: int) -> float:
        """Evolve smart bike technology adoption rate"""
        
        # Technology adoption follows S-curve
        growth_rate = 0.015  # 1.5% monthly growth
        saturation_point = 2.2
        
        saturation_factor = 1.0 - (current_value / saturation_point)
        growth_component = growth_rate * saturation_factor
        
        # Technology breakthrough events
        if random.random() < 0.02:  # 2% chance per month
            tech_advance = random.uniform(0.05, 0.2)
            growth_component += tech_advance
        
        new_value = current_value + growth_component + random.gauss(0, 0.02)
        
        return max(0.8, min(2.5, new_value))
    
    def _evolve_bike_sharing_competition(self, current_value: float, months_elapsed: int,
                                       economic_condition: EconomicCondition) -> float:
        """Evolve bike sharing service competition"""
        
        # Bike sharing affects private bike sales
        if economic_condition.business_cycle_phase in ['expansion', 'peak']:
            # Good economy → more bike sharing investment
            base_change = random.uniform(0.005, 0.02)
        else:
            # Poor economy → bike sharing struggles
            base_change = random.uniform(-0.02, 0.005)
        
        # Market saturation effects
        if current_value > 1.15:
            base_change -= 0.01  # Market saturation
        
        # Random events (new services, regulations, etc.)
        if random.random() < 0.02:  # 2% chance per month
            event_impact = random.uniform(-0.05, 0.1)
            base_change += event_impact
        
        new_value = current_value + base_change + random.gauss(0, 0.01)
        
        return max(0.7, min(1.3, new_value))
    
    def _calculate_months_since_start(self, month: int, year: int) -> int:
        """Calculate months since game start (assuming 2024/01 start)"""
        return (year - 2024) * 12 + month - 1
    
    def get_demand_multiplier_by_bike_type(self, bike_type_name: str) -> float:
        """Get demand multiplier for specific bike type based on current market factors"""
        
        if not self.current_factors:
            return 1.0
        
        bike_type_lower = bike_type_name.lower()
        multiplier = 1.0
        
        # Apply relevant market factors based on bike type
        if 'electric' in bike_type_lower or 'e-bike' in bike_type_lower:
            # E-bikes affected by electric bike trend, environmental consciousness, gas prices
            multiplier *= self.current_factors.electric_bike_trend
            multiplier *= self.current_factors.environmental_consciousness
            multiplier *= (self.current_factors.gas_price_index / 100)  # Higher gas prices boost e-bike demand
            multiplier *= self.current_factors.smart_bike_adoption
        
        elif 'vintage' in bike_type_lower or 'retro' in bike_type_lower or 'classic' in bike_type_lower:
            # Retro bikes affected by retro trends
            multiplier *= self.current_factors.retro_trend_strength
            multiplier *= (2.0 - self.current_factors.smart_bike_adoption)  # Counter to smart bike trend
        
        elif 'mountain' in bike_type_lower or 'sport' in bike_type_lower or 'racing' in bike_type_lower:
            # Sports bikes affected by health/fitness trends
            multiplier *= self.current_factors.health_fitness_trend
            multiplier *= (2.0 - self.current_factors.bike_sharing_competition)  # Less affected by sharing
        
        elif 'city' in bike_type_lower or 'urban' in bike_type_lower or 'commuter' in bike_type_lower:
            # City bikes affected by infrastructure, bike sharing competition
            multiplier *= (self.current_factors.cycling_infrastructure_index / 100)
            multiplier *= (2.0 - self.current_factors.bike_sharing_competition)  # Negatively affected by sharing
            multiplier *= self.current_factors.environmental_consciousness
        
        elif 'cargo' in bike_type_lower or 'family' in bike_type_lower:
            # Family/cargo bikes affected by environmental consciousness, infrastructure
            multiplier *= self.current_factors.environmental_consciousness
            multiplier *= (self.current_factors.cycling_infrastructure_index / 100)
        
        # Universal factors that affect all bike types
        multiplier *= self.current_factors.weather_favorability
        multiplier *= self.current_factors.seasonal_factor
        
        # Government incentives boost all types
        if self.current_factors.government_bike_incentives > 0:
            incentive_boost = 1.0 + (self.current_factors.government_bike_incentives / 1000)
            multiplier *= incentive_boost
        
        return max(0.1, min(5.0, multiplier))
    
    def get_market_trends_summary(self) -> Dict:
        """Get summary of current market trends for reporting"""
        
        if not self.current_factors:
            return {}
        
        return {
            'overall_demand_multiplier': self.current_factors.overall_demand_multiplier,
            'trending_up': [
                factor for factor, threshold in [
                    ('Electric bikes', self.current_factors.electric_bike_trend > 1.2),
                    ('Environmental consciousness', self.current_factors.environmental_consciousness > 1.1),
                    ('Health & fitness', self.current_factors.health_fitness_trend > 1.1),
                    ('Smart bike technology', self.current_factors.smart_bike_adoption > 1.1),
                    ('Retro/vintage styles', self.current_factors.retro_trend_strength > 1.1),
                ] if threshold
            ],
            'trending_down': [
                factor for factor, threshold in [
                    ('Electric bikes', self.current_factors.electric_bike_trend < 0.9),
                    ('Environmental consciousness', self.current_factors.environmental_consciousness < 0.95),
                    ('Health & fitness', self.current_factors.health_fitness_trend < 0.9),
                    ('Retro/vintage styles', self.current_factors.retro_trend_strength < 0.9),
                ] if threshold
            ],
            'seasonal_effect': 'favorable' if self.current_factors.seasonal_factor > 1.0 else 'unfavorable',
            'weather_effect': 'favorable' if self.current_factors.weather_favorability > 1.0 else 'unfavorable',
            'gas_price_impact': 'high' if self.current_factors.gas_price_index > 120 else 'normal' if self.current_factors.gas_price_index > 80 else 'low',
            'government_incentives': self.current_factors.government_bike_incentives > 0,
            'infrastructure_quality': 'excellent' if self.current_factors.cycling_infrastructure_index > 120 else 'good' if self.current_factors.cycling_infrastructure_index > 100 else 'poor'
        }