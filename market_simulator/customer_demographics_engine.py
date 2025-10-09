import random
import math
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

from django.db import transaction

from .models import (
    CustomerDemographics, BikeMarketSegment, EconomicCondition, MarketFactors,
    CustomerSegment, IncomeClass, AgeGroup
)
from bikeshop.models import BikeType
from multiplayer.models import MultiplayerGame


class CustomerDemographicsEngine:
    """Engine for managing customer demographics and segmentation"""
    
    # Age-specific bike preferences (preference scores 0-1)
    AGE_BIKE_PREFERENCES = {
        'children': {
            'Kinderfahrrad': 0.9,
            'BMX': 0.7,
            'Mountain Bike': 0.3,
            'Cityrad': 0.1,
            'E-Bike': 0.1,
            'Rennrad': 0.1,
            'Trekkingrad': 0.2
        },
        'teenagers': {
            'BMX': 0.9,
            'Mountain Bike': 0.8,
            'Rennrad': 0.6,
            'Cityrad': 0.4,
            'E-Bike': 0.2,
            'Trekkingrad': 0.5,
            'Kinderfahrrad': 0.1
        },
        'young_adults': {
            'Mountain Bike': 0.8,
            'Rennrad': 0.8,
            'Cityrad': 0.7,
            'E-Bike': 0.6,
            'Trekkingrad': 0.7,
            'BMX': 0.4,
            'Kinderfahrrad': 0.1
        },
        'adults': {
            'Cityrad': 0.9,
            'E-Bike': 0.8,
            'Trekkingrad': 0.8,
            'Mountain Bike': 0.6,
            'Rennrad': 0.5,
            'BMX': 0.2,
            'Kinderfahrrad': 0.2
        },
        'middle_aged': {
            'E-Bike': 0.9,
            'Cityrad': 0.8,
            'Trekkingrad': 0.7,
            'Mountain Bike': 0.4,
            'Rennrad': 0.3,
            'BMX': 0.1,
            'Kinderfahrrad': 0.1
        },
        'seniors': {
            'E-Bike': 0.9,
            'Cityrad': 0.6,
            'Trekkingrad': 0.5,
            'Mountain Bike': 0.2,
            'Rennrad': 0.1,
            'BMX': 0.1,
            'Kinderfahrrad': 0.1
        }
    }
    
    # Customer segment bike preferences
    SEGMENT_BIKE_PREFERENCES = {
        'commuters': {
            'Cityrad': 0.9,
            'E-Bike': 0.8,
            'Trekkingrad': 0.6,
            'Mountain Bike': 0.3,
            'Rennrad': 0.4,
            'BMX': 0.1,
            'Kinderfahrrad': 0.1
        },
        'recreational': {
            'Trekkingrad': 0.9,
            'Cityrad': 0.7,
            'Mountain Bike': 0.6,
            'E-Bike': 0.5,
            'Rennrad': 0.4,
            'BMX': 0.3,
            'Kinderfahrrad': 0.2
        },
        'sports': {
            'Rennrad': 0.9,
            'Mountain Bike': 0.9,
            'BMX': 0.6,
            'Trekkingrad': 0.4,
            'Cityrad': 0.2,
            'E-Bike': 0.3,
            'Kinderfahrrad': 0.1
        },
        'families': {
            'Kinderfahrrad': 0.9,
            'Cityrad': 0.7,
            'Trekkingrad': 0.6,
            'E-Bike': 0.5,
            'Mountain Bike': 0.4,
            'Rennrad': 0.2,
            'BMX': 0.3
        },
        'eco_conscious': {
            'E-Bike': 0.9,
            'Cityrad': 0.8,
            'Trekkingrad': 0.7,
            'Mountain Bike': 0.4,
            'Rennrad': 0.3,
            'BMX': 0.2,
            'Kinderfahrrad': 0.2
        },
        'luxury': {
            'E-Bike': 0.8,  # Premium e-bikes
            'Rennrad': 0.8,  # High-end racing bikes
            'Mountain Bike': 0.7,  # Premium mountain bikes
            'Trekkingrad': 0.5,
            'Cityrad': 0.4,
            'BMX': 0.3,
            'Kinderfahrrad': 0.2
        },
        'budget': {
            'Cityrad': 0.8,
            'Trekkingrad': 0.7,
            'Mountain Bike': 0.6,
            'BMX': 0.6,
            'Kinderfahrrad': 0.8,
            'Rennrad': 0.4,
            'E-Bike': 0.2  # E-bikes typically expensive
        }
    }
    
    # Price sensitivity by income class (0 = price insensitive, 1 = very price sensitive)
    INCOME_PRICE_SENSITIVITY = {
        'low': 0.9,
        'lower_middle': 0.7,
        'middle': 0.5,
        'upper_middle': 0.3,
        'high': 0.1
    }
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.current_demographics = None
        
    def initialize_customer_demographics(self, starting_month: int, starting_year: int) -> CustomerDemographics:
        """Initialize customer demographics for a new game"""
        
        # Create base demographics
        demographics = CustomerDemographics.objects.create(
            multiplayer_game=self.game,
            month=starting_month,
            year=starting_year,
            
            # Income distribution (based on European averages)
            low_income_percentage=20.0,
            lower_middle_percentage=25.0,
            middle_percentage=30.0,
            upper_middle_percentage=20.0,
            high_income_percentage=5.0,
            
            # Age distribution (based on demographic data)
            children_percentage=10.0,
            teenagers_percentage=8.0,
            young_adults_percentage=25.0,
            adults_percentage=35.0,
            middle_aged_percentage=15.0,
            seniors_percentage=7.0,
            
            # Customer segment distribution
            commuters_percentage=20.0,
            recreational_percentage=30.0,
            sports_percentage=15.0,
            families_percentage=20.0,
            eco_conscious_percentage=10.0,
            luxury_percentage=3.0,
            budget_percentage=2.0,
            
            # Market size
            total_potential_customers=1000000
        )
        
        # Create bike market segments for all bike types
        self._create_bike_market_segments(demographics)
        
        self.current_demographics = demographics
        return demographics
    
    def advance_customer_demographics(self, target_month: int, target_year: int,
                                    economic_condition: EconomicCondition,
                                    market_factors: MarketFactors) -> CustomerDemographics:
        """Advance customer demographics to target month/year"""
        
        # Get current demographics or create initial ones
        try:
            current_demographics = CustomerDemographics.objects.filter(
                multiplayer_game=self.game
            ).latest('year', 'month')
        except CustomerDemographics.DoesNotExist:
            current_demographics = self.initialize_customer_demographics(target_month, target_year)
            return current_demographics
        
        # Check if we need to advance
        if (current_demographics.year == target_year and 
            current_demographics.month == target_month):
            return current_demographics
        
        # Generate new demographics
        new_demographics = self._generate_next_month_demographics(
            current_demographics, target_month, target_year, economic_condition, market_factors
        )
        
        self.current_demographics = new_demographics
        return new_demographics
    
    def _generate_next_month_demographics(self, previous_demographics: CustomerDemographics,
                                        month: int, year: int,
                                        economic_condition: EconomicCondition,
                                        market_factors: MarketFactors) -> CustomerDemographics:
        """Generate demographics for the next month"""
        
        with transaction.atomic():
            # Create new demographics with evolved distributions
            new_demographics = CustomerDemographics.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year,
                
                # Evolve income distribution
                **self._evolve_income_distribution(previous_demographics, economic_condition),
                
                # Evolve age distribution (slower changes)
                **self._evolve_age_distribution(previous_demographics),
                
                # Evolve customer segments
                **self._evolve_customer_segments(previous_demographics, market_factors),
                
                # Evolve market size
                total_potential_customers=self._evolve_market_size(
                    previous_demographics.total_potential_customers, economic_condition
                )
            )
            
            # Update bike market segments
            self._update_bike_market_segments(new_demographics, market_factors)
        
        return new_demographics
    
    def _evolve_income_distribution(self, previous_demographics: CustomerDemographics,
                                  economic_condition: EconomicCondition) -> Dict:
        """Evolve income class distribution based on economic conditions"""
        
        # Economic conditions affect income distribution
        economic_strength = economic_condition.economic_strength
        
        # Get previous distribution
        prev_low = previous_demographics.low_income_percentage
        prev_lower_middle = previous_demographics.lower_middle_percentage
        prev_middle = previous_demographics.middle_percentage
        prev_upper_middle = previous_demographics.upper_middle_percentage
        prev_high = previous_demographics.high_income_percentage
        
        # Economic expansion/contraction effects
        if economic_condition.business_cycle_phase == 'expansion':
            # Economic growth: some people move up income brackets
            mobility = 0.5 * economic_strength
            
            # Shift people upward
            shift_from_low = min(mobility * 0.3, prev_low * 0.05)
            shift_from_lower_middle = min(mobility * 0.2, prev_lower_middle * 0.03)
            shift_from_middle = min(mobility * 0.15, prev_middle * 0.02)
            shift_from_upper_middle = min(mobility * 0.1, prev_upper_middle * 0.02)
            
            new_low = prev_low - shift_from_low
            new_lower_middle = prev_lower_middle - shift_from_lower_middle + shift_from_low
            new_middle = prev_middle - shift_from_middle + shift_from_lower_middle
            new_upper_middle = prev_upper_middle - shift_from_upper_middle + shift_from_middle
            new_high = prev_high + shift_from_upper_middle
            
        elif economic_condition.business_cycle_phase == 'contraction':
            # Economic downturn: some people move down income brackets
            severity = 2.0 - economic_strength
            
            # Shift people downward
            shift_from_high = min(severity * 0.1, prev_high * 0.1)
            shift_from_upper_middle = min(severity * 0.15, prev_upper_middle * 0.05)
            shift_from_middle = min(severity * 0.2, prev_middle * 0.03)
            shift_from_lower_middle = min(severity * 0.25, prev_lower_middle * 0.02)
            
            new_high = prev_high - shift_from_high
            new_upper_middle = prev_upper_middle - shift_from_upper_middle + shift_from_high
            new_middle = prev_middle - shift_from_middle + shift_from_upper_middle
            new_lower_middle = prev_lower_middle - shift_from_lower_middle + shift_from_middle
            new_low = prev_low + shift_from_lower_middle
            
        else:
            # Peak or trough: minimal changes
            new_low = prev_low + random.gauss(0, 0.1)
            new_lower_middle = prev_lower_middle + random.gauss(0, 0.1)
            new_middle = prev_middle + random.gauss(0, 0.1)
            new_upper_middle = prev_upper_middle + random.gauss(0, 0.1)
            new_high = prev_high + random.gauss(0, 0.1)
        
        # Normalize to ensure percentages sum to 100
        total = new_low + new_lower_middle + new_middle + new_upper_middle + new_high
        
        return {
            'low_income_percentage': max(10.0, min(40.0, (new_low / total) * 100)),
            'lower_middle_percentage': max(15.0, min(35.0, (new_lower_middle / total) * 100)),
            'middle_percentage': max(20.0, min(40.0, (new_middle / total) * 100)),
            'upper_middle_percentage': max(10.0, min(30.0, (new_upper_middle / total) * 100)),
            'high_income_percentage': max(2.0, min(15.0, (new_high / total) * 100))
        }
    
    def _evolve_age_distribution(self, previous_demographics: CustomerDemographics) -> Dict:
        """Evolve age distribution (very slow demographic changes)"""
        
        # Age distribution changes very slowly - mostly random variation
        return {
            'children_percentage': max(8.0, min(12.0, 
                previous_demographics.children_percentage + random.gauss(0, 0.05))),
            'teenagers_percentage': max(6.0, min(10.0, 
                previous_demographics.teenagers_percentage + random.gauss(0, 0.05))),
            'young_adults_percentage': max(20.0, min(30.0, 
                previous_demographics.young_adults_percentage + random.gauss(0, 0.1))),
            'adults_percentage': max(30.0, min(40.0, 
                previous_demographics.adults_percentage + random.gauss(0, 0.1))),
            'middle_aged_percentage': max(12.0, min(18.0, 
                previous_demographics.middle_aged_percentage + random.gauss(0, 0.05))),
            'seniors_percentage': max(5.0, min(10.0, 
                previous_demographics.seniors_percentage + random.gauss(0, 0.05)))
        }
    
    def _evolve_customer_segments(self, previous_demographics: CustomerDemographics,
                                market_factors: MarketFactors) -> Dict:
        """Evolve customer segment distribution based on market trends"""
        
        # Market factors influence customer segment preferences
        changes = {}
        
        # Commuters influenced by urban infrastructure and gas prices
        commuter_change = (market_factors.cycling_infrastructure_index - 100) / 1000
        commuter_change += (market_factors.gas_price_index - 100) / 2000
        changes['commuters_percentage'] = max(15.0, min(30.0, 
            previous_demographics.commuters_percentage + commuter_change + random.gauss(0, 0.2)))
        
        # Recreational riders influenced by weather and fitness trends
        recreational_change = (market_factors.health_fitness_trend - 1.0) * 2
        recreational_change += (market_factors.weather_favorability - 1.0) * 1
        changes['recreational_percentage'] = max(25.0, min(40.0, 
            previous_demographics.recreational_percentage + recreational_change + random.gauss(0, 0.3)))
        
        # Sports enthusiasts influenced by fitness trends
        sports_change = (market_factors.health_fitness_trend - 1.0) * 3
        changes['sports_percentage'] = max(10.0, min(25.0, 
            previous_demographics.sports_percentage + sports_change + random.gauss(0, 0.2)))
        
        # Families influenced by infrastructure and safety
        family_change = (market_factors.cycling_infrastructure_index - 100) / 2000
        changes['families_percentage'] = max(15.0, min(30.0, 
            previous_demographics.families_percentage + family_change + random.gauss(0, 0.2)))
        
        # Eco-conscious influenced by environmental consciousness
        eco_change = (market_factors.environmental_consciousness - 1.0) * 5
        changes['eco_conscious_percentage'] = max(5.0, min(20.0, 
            previous_demographics.eco_conscious_percentage + eco_change + random.gauss(0, 0.3)))
        
        # Luxury buyers influenced by economic conditions (from context)
        changes['luxury_percentage'] = max(1.0, min(8.0, 
            previous_demographics.luxury_percentage + random.gauss(0, 0.1)))
        
        # Budget buyers (counter-cyclical to luxury)
        changes['budget_percentage'] = max(1.0, min(5.0, 
            previous_demographics.budget_percentage + random.gauss(0, 0.1)))
        
        # Normalize to ensure reasonable total (should be close to 100%)
        total = sum(changes.values())
        if total > 0:
            normalization_factor = 100 / total
            for key in changes:
                changes[key] *= normalization_factor
        
        return changes
    
    def _evolve_market_size(self, previous_size: int, economic_condition: EconomicCondition) -> int:
        """Evolve total market size based on economic conditions"""
        
        # Market size grows/shrinks with economic conditions
        growth_rate = economic_condition.gdp_growth_rate / 100  # Convert percentage to decimal
        
        # Consumer confidence affects market participation
        confidence_effect = (economic_condition.consumer_confidence_index - 100) / 1000
        
        # Calculate growth
        total_growth_rate = growth_rate + confidence_effect
        new_size = int(previous_size * (1 + total_growth_rate))
        
        # Add some randomness
        new_size += random.randint(-5000, 5000)
        
        # Ensure reasonable bounds
        return max(100000, min(10000000, new_size))
    
    def _create_bike_market_segments(self, demographics: CustomerDemographics):
        """Create bike market segments for all bike types"""
        
        bike_types = BikeType.objects.all()
        
        for bike_type in bike_types:
            self._create_bike_segment(demographics, bike_type)
    
    def _create_bike_segment(self, demographics: CustomerDemographics, bike_type: BikeType):
        """Create a bike market segment for a specific bike type"""
        
        bike_name = bike_type.name
        
        # Calculate preferences and sensitivities
        age_prefs = self._calculate_age_preferences(bike_name)
        segment_prefs = self._calculate_segment_preferences(bike_name)
        price_sensitivities = self.INCOME_PRICE_SENSITIVITY
        
        # Calculate base demand
        base_demand = self._calculate_base_demand(bike_name, demographics)
        
        # Calculate price elasticity
        price_elasticity = self._calculate_price_elasticity(bike_name)
        
        BikeMarketSegment.objects.create(
            customer_demographics=demographics,
            bike_type=bike_type,
            
            # Price sensitivity by income
            low_income_price_sensitivity=price_sensitivities['low'],
            lower_middle_price_sensitivity=price_sensitivities['lower_middle'],
            middle_price_sensitivity=price_sensitivities['middle'],
            upper_middle_price_sensitivity=price_sensitivities['upper_middle'],
            high_income_price_sensitivity=price_sensitivities['high'],
            
            # Age preferences
            children_preference=age_prefs.get('children', 0.5),
            teenagers_preference=age_prefs.get('teenagers', 0.5),
            young_adults_preference=age_prefs.get('young_adults', 0.5),
            adults_preference=age_prefs.get('adults', 0.5),
            middle_aged_preference=age_prefs.get('middle_aged', 0.5),
            seniors_preference=age_prefs.get('seniors', 0.5),
            
            # Customer segment preferences
            commuters_preference=segment_prefs.get('commuters', 0.5),
            recreational_preference=segment_prefs.get('recreational', 0.5),
            sports_preference=segment_prefs.get('sports', 0.5),
            families_preference=segment_prefs.get('families', 0.5),
            eco_conscious_preference=segment_prefs.get('eco_conscious', 0.5),
            luxury_preference=segment_prefs.get('luxury', 0.5),
            budget_preference=segment_prefs.get('budget', 0.5),
            
            # Market characteristics
            base_monthly_demand=base_demand,
            price_elasticity=price_elasticity
        )
    
    def _update_bike_market_segments(self, demographics: CustomerDemographics, market_factors: MarketFactors):
        """Update bike market segments for changing market conditions"""
        
        # Update demand based on market factors for each bike type
        segments = BikeMarketSegment.objects.filter(customer_demographics=demographics)
        
        for segment in segments:
            # Recalculate base demand based on current demographics
            new_base_demand = self._calculate_base_demand(segment.bike_type.name, demographics)
            
            # Apply market factor adjustments
            market_multiplier = self._get_market_factor_multiplier(segment.bike_type.name, market_factors)
            adjusted_demand = int(new_base_demand * market_multiplier)
            
            segment.base_monthly_demand = max(10, min(100000, adjusted_demand))
            segment.save()
    
    def _calculate_age_preferences(self, bike_name: str) -> Dict:
        """Calculate age group preferences for a bike type"""
        
        return self.AGE_BIKE_PREFERENCES.get('young_adults', {}).copy()  # Default fallback
        
        # Try to match bike name to preferences
        for age_group, prefs in self.AGE_BIKE_PREFERENCES.items():
            if bike_name in prefs:
                return {age_group: prefs[bike_name] for age_group in self.AGE_BIKE_PREFERENCES.keys()}
        
        # Fallback to default preferences
        return {age_group: 0.5 for age_group in self.AGE_BIKE_PREFERENCES.keys()}
    
    def _calculate_segment_preferences(self, bike_name: str) -> Dict:
        """Calculate customer segment preferences for a bike type"""
        
        # Extract preferences for this bike from all segments
        preferences = {}
        for segment, bikes in self.SEGMENT_BIKE_PREFERENCES.items():
            preferences[segment] = bikes.get(bike_name, 0.5)
        
        return preferences
    
    def _calculate_base_demand(self, bike_name: str, demographics: CustomerDemographics) -> int:
        """Calculate base monthly demand for a bike type"""
        
        # Start with total potential customers
        total_customers = demographics.total_potential_customers
        
        # Monthly purchase rate (assume 1% of potential customers buy a bike per year)
        monthly_purchase_rate = 0.01 / 12
        
        # Calculate how much of that demand goes to this bike type
        bike_market_share = self._estimate_bike_type_market_share(bike_name)
        
        base_demand = int(total_customers * monthly_purchase_rate * bike_market_share)
        
        return max(10, min(100000, base_demand))
    
    def _estimate_bike_type_market_share(self, bike_name: str) -> float:
        """Estimate market share for a bike type"""
        
        bike_name_lower = bike_name.lower()
        
        # Rough market share estimates based on bike type
        if 'city' in bike_name_lower or 'cityrad' in bike_name_lower:
            return 0.25  # City bikes are popular
        elif 'e-bike' in bike_name_lower or 'electric' in bike_name_lower:
            return 0.15  # Growing segment
        elif 'mountain' in bike_name_lower:
            return 0.15
        elif 'trekking' in bike_name_lower:
            return 0.20
        elif 'rennrad' in bike_name_lower or 'racing' in bike_name_lower:
            return 0.08
        elif 'kinder' in bike_name_lower or 'children' in bike_name_lower:
            return 0.10
        elif 'bmx' in bike_name_lower:
            return 0.05
        else:
            return 0.02  # Other/specialty bikes
    
    def _calculate_price_elasticity(self, bike_name: str) -> float:
        """Calculate price elasticity for a bike type"""
        
        bike_name_lower = bike_name.lower()
        
        # Price elasticity by bike type (more negative = more elastic)
        if 'luxury' in bike_name_lower or 'premium' in bike_name_lower:
            return -0.8  # Luxury bikes less price sensitive
        elif 'budget' in bike_name_lower or 'basic' in bike_name_lower:
            return -2.5  # Budget bikes very price sensitive
        elif 'e-bike' in bike_name_lower:
            return -1.2  # E-bikes moderately price sensitive
        elif 'children' in bike_name_lower or 'kinder' in bike_name_lower:
            return -2.0  # Family purchases price sensitive
        else:
            return -1.5  # Standard elasticity
    
    def _get_market_factor_multiplier(self, bike_name: str, market_factors: MarketFactors) -> float:
        """Get market factor multiplier for bike demand"""
        
        bike_name_lower = bike_name.lower()
        multiplier = 1.0
        
        # Apply market factor effects by bike type
        if 'electric' in bike_name_lower or 'e-bike' in bike_name_lower:
            multiplier *= market_factors.electric_bike_trend
            multiplier *= market_factors.environmental_consciousness
        
        if 'city' in bike_name_lower or 'urban' in bike_name_lower:
            multiplier *= (market_factors.cycling_infrastructure_index / 100)
        
        if 'mountain' in bike_name_lower or 'sport' in bike_name_lower:
            multiplier *= market_factors.health_fitness_trend
        
        # Universal seasonal effects
        multiplier *= market_factors.seasonal_factor
        multiplier *= market_factors.weather_favorability
        
        return max(0.1, min(3.0, multiplier))
    
    def get_customer_segment_analysis(self) -> Dict:
        """Get analysis of current customer segments"""
        
        if not self.current_demographics:
            return {}
        
        return {
            'total_market_size': self.current_demographics.total_potential_customers,
            'income_distribution': {
                'low_income': self.current_demographics.low_income_percentage,
                'lower_middle': self.current_demographics.lower_middle_percentage,
                'middle': self.current_demographics.middle_percentage,
                'upper_middle': self.current_demographics.upper_middle_percentage,
                'high_income': self.current_demographics.high_income_percentage
            },
            'age_distribution': {
                'children': self.current_demographics.children_percentage,
                'teenagers': self.current_demographics.teenagers_percentage,
                'young_adults': self.current_demographics.young_adults_percentage,
                'adults': self.current_demographics.adults_percentage,
                'middle_aged': self.current_demographics.middle_aged_percentage,
                'seniors': self.current_demographics.seniors_percentage
            },
            'customer_segments': {
                'commuters': self.current_demographics.commuters_percentage,
                'recreational': self.current_demographics.recreational_percentage,
                'sports': self.current_demographics.sports_percentage,
                'families': self.current_demographics.families_percentage,
                'eco_conscious': self.current_demographics.eco_conscious_percentage,
                'luxury': self.current_demographics.luxury_percentage,
                'budget': self.current_demographics.budget_percentage
            },
            'market_insights': self._generate_market_insights()
        }
    
    def _generate_market_insights(self) -> List[str]:
        """Generate insights about current customer demographics"""
        
        if not self.current_demographics:
            return []
        
        insights = []
        
        # Income insights
        if self.current_demographics.high_income_percentage > 6:
            insights.append("High-income segment is growing - good opportunity for premium bikes")
        elif self.current_demographics.low_income_percentage > 25:
            insights.append("Budget-conscious segment is dominant - focus on affordable options")
        
        # Age insights
        if self.current_demographics.seniors_percentage > 8:
            insights.append("Senior segment is growing - e-bikes and comfortable designs in demand")
        if self.current_demographics.young_adults_percentage > 27:
            insights.append("Young adult market is strong - sports and urban bikes popular")
        
        # Segment insights
        if self.current_demographics.commuters_percentage > 22:
            insights.append("Commuter segment is expanding - focus on urban and e-bikes")
        if self.current_demographics.eco_conscious_percentage > 12:
            insights.append("Environmental consciousness is rising - e-bikes and sustainable features valued")
        if self.current_demographics.sports_percentage > 17:
            insights.append("Sports segment is active - performance and racing bikes in demand")
        
        return insights