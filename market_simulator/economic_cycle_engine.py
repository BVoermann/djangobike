import math
import random
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from django.utils import timezone
from django.db import transaction

from .models import (
    EconomicCondition, MarketFactors, CustomerDemographics, 
    BusinessCyclePhase, MarketConfiguration
)
from multiplayer.models import MultiplayerGame


class EconomicCycleEngine:
    """Engine for simulating realistic economic cycles and GDP fluctuations"""
    
    # Business cycle parameters (in months)
    CYCLE_LENGTHS = {
        'expansion': (12, 36),      # 1-3 years
        'peak': (1, 6),             # 1-6 months
        'contraction': (6, 18),     # 6-18 months  
        'trough': (1, 6)            # 1-6 months
    }
    
    # GDP growth rate ranges by cycle phase
    GDP_RANGES = {
        'expansion': (1.5, 6.0),
        'peak': (0.5, 3.0),
        'contraction': (-8.0, 1.0),
        'trough': (-5.0, 0.5)
    }
    
    # Unemployment rate ranges by cycle phase
    UNEMPLOYMENT_RANGES = {
        'expansion': (3.0, 8.0),
        'peak': (3.0, 6.0),
        'contraction': (6.0, 15.0),
        'trough': (8.0, 12.0)
    }
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.current_conditions = None
        
    def initialize_economic_conditions(self, starting_month: int, starting_year: int) -> EconomicCondition:
        """Initialize economic conditions for a new game"""
        
        # Start in expansion phase with moderate conditions
        conditions = EconomicCondition.objects.create(
            multiplayer_game=self.game,
            month=starting_month,
            year=starting_year,
            gdp_growth_rate=2.5,
            inflation_rate=2.0,
            unemployment_rate=5.0,
            interest_rate=3.5,
            business_cycle_phase=BusinessCyclePhase.EXPANSION,
            cycle_duration_months=0,
            cycle_intensity=1.0,
            consumer_confidence_index=100.0,
            disposable_income_index=100.0
        )
        
        self.current_conditions = conditions
        return conditions
    
    def advance_economic_cycle(self, target_month: int, target_year: int) -> EconomicCondition:
        """Advance the economic cycle to the target month/year"""
        
        # Get current conditions or create initial ones
        try:
            current_conditions = EconomicCondition.objects.filter(
                multiplayer_game=self.game
            ).latest('year', 'month')
        except EconomicCondition.DoesNotExist:
            current_conditions = self.initialize_economic_conditions(target_month, target_year)
            return current_conditions
        
        # Check if we need to advance
        if (current_conditions.year == target_year and 
            current_conditions.month == target_month):
            return current_conditions
        
        # Calculate months elapsed
        months_elapsed = self._calculate_months_difference(
            current_conditions.month, current_conditions.year,
            target_month, target_year
        )
        
        # Advance conditions month by month
        new_conditions = current_conditions
        for month_step in range(1, months_elapsed + 1):
            new_month, new_year = self._add_months(
                current_conditions.month, current_conditions.year, month_step
            )
            new_conditions = self._generate_next_month_conditions(new_conditions, new_month, new_year)
        
        self.current_conditions = new_conditions
        return new_conditions
    
    def _generate_next_month_conditions(self, previous_conditions: EconomicCondition, 
                                      month: int, year: int) -> EconomicCondition:
        """Generate economic conditions for the next month"""
        
        # Determine if we should transition to next cycle phase
        current_phase = previous_conditions.business_cycle_phase
        cycle_duration = previous_conditions.cycle_duration_months + 1
        
        # Check for phase transition
        new_phase, new_duration = self._check_phase_transition(current_phase, cycle_duration)
        
        # Generate new economic indicators based on phase
        new_indicators = self._generate_economic_indicators(
            new_phase, new_duration, previous_conditions
        )
        
        # Create new economic condition
        with transaction.atomic():
            new_conditions = EconomicCondition.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year,
                business_cycle_phase=new_phase,
                cycle_duration_months=new_duration,
                **new_indicators
            )
        
        return new_conditions
    
    def _check_phase_transition(self, current_phase: str, duration: int) -> Tuple[str, int]:
        """Check if business cycle should transition to next phase"""
        
        min_duration, max_duration = self.CYCLE_LENGTHS[current_phase]
        
        # Forced transition if at maximum duration
        if duration >= max_duration:
            return self._get_next_phase(current_phase), 1
        
        # Random transition chance if past minimum duration
        if duration >= min_duration:
            transition_probability = self._calculate_transition_probability(current_phase, duration)
            if random.random() < transition_probability:
                return self._get_next_phase(current_phase), 1
        
        # Stay in current phase
        return current_phase, duration + 1
    
    def _get_next_phase(self, current_phase: str) -> str:
        """Get the next phase in the business cycle"""
        cycle_order = ['expansion', 'peak', 'contraction', 'trough']
        current_index = cycle_order.index(current_phase)
        next_index = (current_index + 1) % len(cycle_order)
        return cycle_order[next_index]
    
    def _calculate_transition_probability(self, phase: str, duration: int) -> float:
        """Calculate probability of transitioning to next phase"""
        min_duration, max_duration = self.CYCLE_LENGTHS[phase]
        
        # Probability increases linearly from 0 at min_duration to 1 at max_duration
        if duration <= min_duration:
            return 0.0
        
        progress = (duration - min_duration) / (max_duration - min_duration)
        
        # Base probability with some randomness
        base_probability = min(0.3, progress * 0.2)
        
        # Phase-specific adjustments
        phase_adjustments = {
            'expansion': 0.1,   # Expansions can last longer
            'peak': 0.4,        # Peaks are typically brief
            'contraction': 0.2, # Contractions have moderate duration
            'trough': 0.3       # Troughs are typically brief
        }
        
        return min(1.0, base_probability + phase_adjustments.get(phase, 0.2))
    
    def _generate_economic_indicators(self, phase: str, duration: int, 
                                    previous_conditions: EconomicCondition) -> Dict:
        """Generate economic indicators for the given phase"""
        
        # Get base ranges for this phase
        gdp_min, gdp_max = self.GDP_RANGES[phase]
        unemployment_min, unemployment_max = self.UNEMPLOYMENT_RANGES[phase]
        
        # Add momentum from previous period (trending)
        momentum_factor = 0.7  # How much previous values influence current
        volatility = self._get_phase_volatility(phase)
        
        # GDP Growth Rate
        target_gdp = random.uniform(gdp_min, gdp_max)
        new_gdp = (momentum_factor * previous_conditions.gdp_growth_rate + 
                  (1 - momentum_factor) * target_gdp)
        new_gdp += random.gauss(0, volatility)
        new_gdp = max(gdp_min, min(gdp_max, new_gdp))
        
        # Unemployment Rate (inversely related to GDP growth)
        unemployment_target = unemployment_max - ((new_gdp - gdp_min) / (gdp_max - gdp_min)) * (unemployment_max - unemployment_min)
        new_unemployment = (momentum_factor * previous_conditions.unemployment_rate + 
                           (1 - momentum_factor) * unemployment_target)
        new_unemployment += random.gauss(0, volatility * 0.5)
        new_unemployment = max(unemployment_min, min(unemployment_max, new_unemployment))
        
        # Inflation Rate (related to economic activity)
        inflation_base = 2.0
        if phase in ['expansion', 'peak']:
            inflation_adjustment = (new_gdp / 4.0) * 0.5  # Higher GDP → higher inflation
        else:
            inflation_adjustment = (new_gdp / 4.0) * 0.3  # Lower GDP → deflationary pressure
        
        new_inflation = inflation_base + inflation_adjustment + random.gauss(0, 0.3)
        new_inflation = max(-2.0, min(8.0, new_inflation))
        
        # Interest Rate (central bank response to economic conditions)
        target_interest_rate = self._calculate_target_interest_rate(new_gdp, new_inflation, new_unemployment)
        new_interest_rate = (momentum_factor * previous_conditions.interest_rate + 
                           (1 - momentum_factor) * target_interest_rate)
        new_interest_rate = max(0.0, min(15.0, new_interest_rate))
        
        # Consumer Confidence (leading indicator)
        confidence_base = 100.0
        if phase == 'expansion':
            confidence_target = random.uniform(105, 130)
        elif phase == 'peak':
            confidence_target = random.uniform(115, 135)
        elif phase == 'contraction':
            confidence_target = random.uniform(70, 95)
        else:  # trough
            confidence_target = random.uniform(60, 85)
        
        new_confidence = (momentum_factor * previous_conditions.consumer_confidence_index + 
                         (1 - momentum_factor) * confidence_target)
        new_confidence += random.gauss(0, 5)
        new_confidence = max(50.0, min(150.0, new_confidence))
        
        # Disposable Income Index
        income_factor = 1.0 + (new_gdp / 100)  # GDP growth affects disposable income
        unemployment_factor = 1.0 - ((new_unemployment - 5.0) / 100)  # Unemployment reduces income
        
        new_income_index = previous_conditions.disposable_income_index * income_factor * unemployment_factor
        new_income_index += random.gauss(0, 2)
        new_income_index = max(70.0, min(130.0, new_income_index))
        
        # Cycle intensity (how strongly this cycle affects the economy)
        intensity_base = previous_conditions.cycle_intensity
        if duration == 1:  # New phase, reset intensity
            intensity_base = random.uniform(0.8, 1.5)
        
        new_intensity = intensity_base + random.gauss(0, 0.1)
        new_intensity = max(0.1, min(3.0, new_intensity))
        
        return {
            'gdp_growth_rate': round(new_gdp, 2),
            'inflation_rate': round(new_inflation, 2),
            'unemployment_rate': round(new_unemployment, 2),
            'interest_rate': round(new_interest_rate, 2),
            'consumer_confidence_index': round(new_confidence, 1),
            'disposable_income_index': round(new_income_index, 1),
            'cycle_intensity': round(new_intensity, 2)
        }
    
    def _get_phase_volatility(self, phase: str) -> float:
        """Get volatility level for economic indicators by phase"""
        volatility_map = {
            'expansion': 0.5,
            'peak': 0.8,
            'contraction': 1.2,
            'trough': 1.0
        }
        return volatility_map.get(phase, 0.5)
    
    def _calculate_target_interest_rate(self, gdp_growth: float, inflation: float, unemployment: float) -> float:
        """Calculate target interest rate based on economic conditions (Taylor Rule inspired)"""
        
        # Base rate
        real_rate = 2.0
        
        # Inflation targeting
        inflation_gap = inflation - 2.0  # Target 2% inflation
        
        # Output gap (using GDP growth as proxy)
        output_gap = gdp_growth - 2.5  # Assume 2.5% trend growth
        
        # Taylor rule: nominal rate = real rate + inflation + 0.5*(inflation gap) + 0.5*(output gap)
        target_rate = real_rate + inflation + 0.5 * inflation_gap + 0.5 * output_gap
        
        # Unemployment adjustment (Okun's law consideration)
        unemployment_adjustment = (unemployment - 5.0) * -0.2  # Higher unemployment → lower rates
        
        return target_rate + unemployment_adjustment
    
    def _calculate_months_difference(self, month1: int, year1: int, month2: int, year2: int) -> int:
        """Calculate the number of months between two dates"""
        return (year2 - year1) * 12 + (month2 - month1)
    
    def _add_months(self, month: int, year: int, months_to_add: int) -> Tuple[int, int]:
        """Add months to a given month/year"""
        total_months = year * 12 + month - 1 + months_to_add
        new_year = total_months // 12
        new_month = (total_months % 12) + 1
        return new_month, new_year
    
    def get_economic_impact_multiplier(self, bike_type_name: str = None) -> float:
        """Get economic impact multiplier for bicycle demand"""
        
        if not self.current_conditions:
            return 1.0
        
        # Base multiplier from economic strength
        economic_strength = self.current_conditions.economic_strength
        base_multiplier = 0.5 + economic_strength  # Range: 0.5 to 2.5
        
        # Consumer confidence effect
        confidence_effect = self.current_conditions.consumer_confidence_index / 100
        
        # Disposable income effect
        income_effect = self.current_conditions.disposable_income_index / 100
        
        # Unemployment effect (higher unemployment reduces bicycle purchases)
        unemployment_effect = max(0.3, 1.0 - ((self.current_conditions.unemployment_rate - 5.0) / 20))
        
        # Interest rate effect (higher rates reduce big purchases)
        interest_effect = max(0.7, 1.0 - ((self.current_conditions.interest_rate - 3.0) / 20))
        
        # Combine effects
        total_multiplier = base_multiplier * confidence_effect * income_effect * unemployment_effect * interest_effect
        
        # Apply cycle intensity
        total_multiplier *= self.current_conditions.cycle_intensity
        
        # Bike type specific adjustments
        if bike_type_name:
            total_multiplier *= self._get_bike_type_economic_sensitivity(bike_type_name)
        
        return max(0.1, min(3.0, total_multiplier))
    
    def _get_bike_type_economic_sensitivity(self, bike_type_name: str) -> float:
        """Get economic sensitivity multiplier for different bike types"""
        
        bike_type_lower = bike_type_name.lower()
        
        # Economic sensitivity by bike type
        if 'luxury' in bike_type_lower or 'premium' in bike_type_lower:
            # Luxury bikes are more sensitive to economic conditions
            if self.current_conditions.business_cycle_phase in ['contraction', 'trough']:
                return 0.6  # Luxury demand drops significantly
            elif self.current_conditions.business_cycle_phase in ['expansion', 'peak']:
                return 1.4  # Luxury demand increases significantly
        
        elif 'budget' in bike_type_lower or 'basic' in bike_type_lower:
            # Budget bikes are counter-cyclical
            if self.current_conditions.business_cycle_phase in ['contraction', 'trough']:
                return 1.3  # Budget demand increases during tough times
            elif self.current_conditions.business_cycle_phase in ['expansion', 'peak']:
                return 0.8  # Budget demand decreases when economy is good
        
        elif 'electric' in bike_type_lower or 'e-bike' in bike_type_lower:
            # E-bikes are somewhat luxury but also utilitarian
            if self.current_conditions.business_cycle_phase in ['contraction', 'trough']:
                return 0.8
            elif self.current_conditions.business_cycle_phase in ['expansion', 'peak']:
                return 1.2
        
        # Default for standard bikes (less economic sensitivity)
        return 1.0
    
    def generate_economic_forecast(self, months_ahead: int = 12) -> List[Dict]:
        """Generate economic forecast for planning purposes"""
        
        if not self.current_conditions:
            return []
        
        forecast = []
        current_conditions = self.current_conditions
        
        for month_offset in range(1, months_ahead + 1):
            # Calculate target month/year
            target_month, target_year = self._add_months(
                current_conditions.month, current_conditions.year, month_offset
            )
            
            # Generate forecasted conditions (simplified)
            forecasted_phase = self._forecast_business_cycle_phase(
                current_conditions.business_cycle_phase,
                current_conditions.cycle_duration_months + month_offset
            )
            
            # Estimate economic indicators
            gdp_range = self.GDP_RANGES[forecasted_phase]
            unemployment_range = self.UNEMPLOYMENT_RANGES[forecasted_phase]
            
            forecast_data = {
                'month': target_month,
                'year': target_year,
                'business_cycle_phase': forecasted_phase,
                'gdp_growth_estimate': sum(gdp_range) / 2,
                'unemployment_estimate': sum(unemployment_range) / 2,
                'economic_impact_multiplier': self._estimate_future_multiplier(forecasted_phase),
                'confidence_level': self._get_forecast_confidence(month_offset)
            }
            
            forecast.append(forecast_data)
        
        return forecast
    
    def _forecast_business_cycle_phase(self, current_phase: str, future_duration: int) -> str:
        """Forecast likely business cycle phase"""
        
        # Simple heuristic: assume phase transitions at expected durations
        min_duration, max_duration = self.CYCLE_LENGTHS[current_phase]
        avg_duration = (min_duration + max_duration) / 2
        
        if future_duration > avg_duration:
            return self._get_next_phase(current_phase)
        else:
            return current_phase
    
    def _estimate_future_multiplier(self, forecasted_phase: str) -> float:
        """Estimate future economic impact multiplier"""
        
        phase_multipliers = {
            'expansion': 1.2,
            'peak': 1.3,
            'contraction': 0.7,
            'trough': 0.6
        }
        
        return phase_multipliers.get(forecasted_phase, 1.0)
    
    def _get_forecast_confidence(self, months_ahead: int) -> float:
        """Get confidence level for forecast (decreases with time)"""
        
        # Confidence decreases exponentially with time
        base_confidence = 0.9
        decay_rate = 0.05
        
        confidence = base_confidence * math.exp(-decay_rate * months_ahead)
        return max(0.1, confidence)