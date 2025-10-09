from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import math
import random
from datetime import date
from enum import Enum

from bikeshop.models import BikeType
from multiplayer.models import MultiplayerGame, PlayerSession


class MarketStructure(models.TextChoices):
    """Market structure types for bicycle market simulation"""
    PERFECT_COMPETITION = 'perfect', 'Perfect Competition'
    MONOPOLISTIC_COMPETITION = 'monopolistic', 'Monopolistic Competition'
    OLIGOPOLY = 'oligopoly', 'Oligopoly'
    DUOPOLY = 'duopoly', 'Duopoly'


class BusinessCyclePhase(models.TextChoices):
    """Business cycle phases affecting economic conditions"""
    EXPANSION = 'expansion', 'Expansion'
    PEAK = 'peak', 'Peak'
    CONTRACTION = 'contraction', 'Contraction'
    TROUGH = 'trough', 'Trough'


class IncomeClass(models.TextChoices):
    """Income classes for customer segmentation"""
    LOW_INCOME = 'low', 'Low Income (€0-30k)'
    LOWER_MIDDLE = 'lower_middle', 'Lower Middle (€30-50k)'
    MIDDLE = 'middle', 'Middle Class (€50-80k)'
    UPPER_MIDDLE = 'upper_middle', 'Upper Middle (€80-120k)'
    HIGH_INCOME = 'high', 'High Income (€120k+)'


class AgeGroup(models.TextChoices):
    """Age groups for customer segmentation"""
    CHILDREN = 'children', 'Children (5-12)'
    TEENAGERS = 'teenagers', 'Teenagers (13-17)'
    YOUNG_ADULTS = 'young_adults', 'Young Adults (18-30)'
    ADULTS = 'adults', 'Adults (31-50)'
    MIDDLE_AGED = 'middle_aged', 'Middle Aged (51-65)'
    SENIORS = 'seniors', 'Seniors (65+)'


class CustomerSegment(models.TextChoices):
    """Customer segments with different buying behaviors"""
    COMMUTERS = 'commuters', 'Urban Commuters'
    RECREATIONAL = 'recreational', 'Recreational Riders'
    SPORTS_ENTHUSIASTS = 'sports', 'Sports Enthusiasts'
    FAMILIES = 'families', 'Families with Children'
    ECO_CONSCIOUS = 'eco_conscious', 'Environmentally Conscious'
    LUXURY_BUYERS = 'luxury', 'Luxury/Premium Buyers'
    BUDGET_CONSCIOUS = 'budget', 'Budget-Conscious Buyers'


class EconomicCondition(models.Model):
    """Economic conditions affecting the bicycle market"""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='economic_conditions')
    month = models.IntegerField()
    year = models.IntegerField()
    
    # GDP and economic indicators
    gdp_growth_rate = models.FloatField(
        default=2.5,
        validators=[MinValueValidator(-10.0), MaxValueValidator(15.0)],
        help_text="Annual GDP growth rate percentage"
    )
    inflation_rate = models.FloatField(
        default=2.0,
        validators=[MinValueValidator(-5.0), MaxValueValidator(20.0)],
        help_text="Annual inflation rate percentage"
    )
    unemployment_rate = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(25.0)],
        help_text="Unemployment rate percentage"
    )
    interest_rate = models.FloatField(
        default=3.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(15.0)],
        help_text="Central bank interest rate percentage"
    )
    
    # Business cycle
    business_cycle_phase = models.CharField(
        max_length=20,
        choices=BusinessCyclePhase.choices,
        default=BusinessCyclePhase.EXPANSION
    )
    cycle_duration_months = models.IntegerField(default=0)
    cycle_intensity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Intensity multiplier for business cycle effects"
    )
    
    # Consumer confidence and spending
    consumer_confidence_index = models.FloatField(
        default=100.0,
        validators=[MinValueValidator(50.0), MaxValueValidator(150.0)],
        help_text="Consumer confidence index (100 = neutral)"
    )
    disposable_income_index = models.FloatField(
        default=100.0,
        validators=[MinValueValidator(70.0), MaxValueValidator(130.0)],
        help_text="Disposable income index (100 = baseline)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.multiplayer_game.name} - {self.year}/{self.month:02d} ({self.business_cycle_phase})"
    
    @property
    def economic_strength(self):
        """Calculate overall economic strength score (0-2)"""
        gdp_score = max(0, min(2, (self.gdp_growth_rate + 5) / 10))
        unemployment_score = max(0, min(2, (15 - self.unemployment_rate) / 10))
        confidence_score = max(0, min(2, self.consumer_confidence_index / 100))
        
        return (gdp_score + unemployment_score + confidence_score) / 3


class MarketFactors(models.Model):
    """Dynamic market factors affecting bicycle demand"""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='market_factors')
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Trend factors
    retro_trend_strength = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        help_text="Strength of retro/vintage bicycle trends"
    )
    electric_bike_trend = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(3.0)],
        help_text="Strength of electric bike adoption trend"
    )
    health_fitness_trend = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.7), MaxValueValidator(2.0)],
        help_text="Health and fitness consciousness trend"
    )
    
    # Environmental factors
    environmental_consciousness = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.8), MaxValueValidator(1.8)],
        help_text="Environmental consciousness level"
    )
    gas_price_index = models.FloatField(
        default=100.0,
        validators=[MinValueValidator(50.0), MaxValueValidator(200.0)],
        help_text="Gas price index (100 = baseline)"
    )
    carbon_tax_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(50.0)],
        help_text="Carbon tax per ton CO2"
    )
    
    # Weather and seasonal factors
    weather_favorability = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.3), MaxValueValidator(1.5)],
        help_text="Weather favorability for cycling"
    )
    seasonal_factor = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.4), MaxValueValidator(1.6)],
        help_text="Seasonal demand factor"
    )
    
    # Infrastructure and policy
    cycling_infrastructure_index = models.FloatField(
        default=100.0,
        validators=[MinValueValidator(80.0), MaxValueValidator(150.0)],
        help_text="Cycling infrastructure quality index"
    )
    government_bike_incentives = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1000.0)],
        help_text="Government incentives per bicycle purchase"
    )
    
    # Technology factors
    smart_bike_adoption = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.8), MaxValueValidator(2.5)],
        help_text="Smart bike technology adoption rate"
    )
    bike_sharing_competition = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.7), MaxValueValidator(1.3)],
        help_text="Competition from bike sharing services"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"Market Factors - {self.multiplayer_game.name} {self.year}/{self.month:02d}"
    
    @property
    def overall_demand_multiplier(self):
        """Calculate overall demand multiplier from all factors"""
        trend_factor = (self.retro_trend_strength + self.electric_bike_trend + self.health_fitness_trend) / 3
        env_factor = (self.environmental_consciousness + (self.gas_price_index / 100)) / 2
        infrastructure_factor = self.cycling_infrastructure_index / 100
        
        return (trend_factor + env_factor + infrastructure_factor + self.weather_favorability + self.seasonal_factor) / 5


class CustomerDemographics(models.Model):
    """Customer demographics for market segmentation"""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='customer_demographics')
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Income distribution (percentages should sum to 100)
    low_income_percentage = models.FloatField(
        default=20.0,
        validators=[MinValueValidator(10.0), MaxValueValidator(40.0)]
    )
    lower_middle_percentage = models.FloatField(
        default=25.0,
        validators=[MinValueValidator(15.0), MaxValueValidator(35.0)]
    )
    middle_percentage = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(20.0), MaxValueValidator(40.0)]
    )
    upper_middle_percentage = models.FloatField(
        default=20.0,
        validators=[MinValueValidator(10.0), MaxValueValidator(30.0)]
    )
    high_income_percentage = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(2.0), MaxValueValidator(15.0)]
    )
    
    # Age distribution (percentages should sum to 100)
    children_percentage = models.FloatField(default=10.0)
    teenagers_percentage = models.FloatField(default=8.0)
    young_adults_percentage = models.FloatField(default=25.0)
    adults_percentage = models.FloatField(default=35.0)
    middle_aged_percentage = models.FloatField(default=15.0)
    seniors_percentage = models.FloatField(default=7.0)
    
    # Customer segment distribution
    commuters_percentage = models.FloatField(default=20.0)
    recreational_percentage = models.FloatField(default=30.0)
    sports_percentage = models.FloatField(default=15.0)
    families_percentage = models.FloatField(default=20.0)
    eco_conscious_percentage = models.FloatField(default=10.0)
    luxury_percentage = models.FloatField(default=3.0)
    budget_percentage = models.FloatField(default=2.0)
    
    # Market size
    total_potential_customers = models.IntegerField(
        default=1000000,
        validators=[MinValueValidator(100000), MaxValueValidator(10000000)],
        help_text="Total potential bicycle customers in the market"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"Demographics - {self.multiplayer_game.name} {self.year}/{self.month:02d}"


class BikeMarketSegment(models.Model):
    """Market segment preferences for different bike types"""
    
    customer_demographics = models.ForeignKey(CustomerDemographics, on_delete=models.CASCADE, related_name='bike_segments')
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    
    # Price sensitivity by income class (0 = price insensitive, 1 = very price sensitive)
    low_income_price_sensitivity = models.FloatField(default=0.8)
    lower_middle_price_sensitivity = models.FloatField(default=0.7)
    middle_price_sensitivity = models.FloatField(default=0.5)
    upper_middle_price_sensitivity = models.FloatField(default=0.3)
    high_income_price_sensitivity = models.FloatField(default=0.1)
    
    # Age group preferences (0-1 preference score)
    children_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    teenagers_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    young_adults_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    adults_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    middle_aged_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    seniors_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Customer segment preferences
    commuters_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    recreational_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    sports_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    families_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    eco_conscious_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    luxury_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    budget_preference = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Base demand for this bike type (monthly units)
    base_monthly_demand = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(10), MaxValueValidator(100000)]
    )
    
    # Market elasticity (how responsive demand is to price changes)
    price_elasticity = models.FloatField(
        default=-1.5,
        validators=[MinValueValidator(-5.0), MaxValueValidator(-0.1)],
        help_text="Price elasticity of demand (negative value)"
    )
    
    class Meta:
        unique_together = ['customer_demographics', 'bike_type']
    
    def __str__(self):
        return f"{self.bike_type.name} - {self.customer_demographics}"


class MarketConfiguration(models.Model):
    """Overall market configuration and structure"""
    
    multiplayer_game = models.OneToOneField(MultiplayerGame, on_delete=models.CASCADE, related_name='market_config')
    
    # Market structure
    market_structure = models.CharField(
        max_length=20,
        choices=MarketStructure.choices,
        default=MarketStructure.MONOPOLISTIC_COMPETITION
    )
    
    # Market size and competition
    total_market_size = models.IntegerField(
        default=5000000,
        validators=[MinValueValidator(100000), MaxValueValidator(50000000)],
        help_text="Total annual bicycle market size in units"
    )
    market_concentration_ratio = models.FloatField(
        default=0.4,
        validators=[MinValueValidator(0.1), MaxValueValidator(0.9)],
        help_text="Market concentration ratio (top 4 firms)"
    )
    
    # Competition intensity
    price_competition_intensity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        help_text="Intensity of price competition"
    )
    quality_competition_intensity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        help_text="Intensity of quality competition"
    )
    innovation_competition_intensity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        help_text="Intensity of innovation competition"
    )
    
    # Market entry and exit
    entry_barriers = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Height of entry barriers"
    )
    exit_barriers = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Height of exit barriers"
    )
    
    # Price discovery mechanism
    price_transparency = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        help_text="Level of price transparency in market"
    )
    information_asymmetry = models.FloatField(
        default=0.2,
        validators=[MinValueValidator(0.0), MaxValueValidator(0.8)],
        help_text="Level of information asymmetry"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Market Config - {self.multiplayer_game.name} ({self.market_structure})"


class PlayerMarketSubmission(models.Model):
    """Player's monthly bicycle market submission"""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='market_submissions')
    player_session = models.ForeignKey(PlayerSession, on_delete=models.CASCADE, related_name='market_submissions')
    month = models.IntegerField()
    year = models.IntegerField()
    
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    
    # Submission details
    quantity_offered = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        help_text="Number of bicycles offered for sale"
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Price per bicycle"
    )
    
    # Product attributes
    quality_rating = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)],
        help_text="Quality rating (1-10 scale)"
    )
    innovation_level = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)],
        help_text="Innovation level (1-10 scale)"
    )
    brand_strength = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)],
        help_text="Brand strength (1-10 scale)"
    )
    
    # Marketing and positioning
    marketing_spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Marketing spend for this submission"
    )
    target_segments = models.JSONField(
        default=list,
        help_text="Target customer segments for this submission"
    )
    
    # Results (filled after market clearing)
    units_sold = models.IntegerField(default=0)
    market_share_percentage = models.FloatField(default=0.0)
    revenue_generated = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    demand_elasticity_applied = models.FloatField(default=0.0)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['multiplayer_game', 'player_session', 'month', 'year', 'bike_type']
        ordering = ['-year', '-month', 'player_session']
    
    def __str__(self):
        return f"{self.player_session.company_name} - {self.bike_type.name} ({self.year}/{self.month:02d})"


class MarketClearingResult(models.Model):
    """Results of monthly market clearing process"""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='market_results')
    month = models.IntegerField()
    year = models.IntegerField()
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    
    # Market totals
    total_quantity_supplied = models.IntegerField(default=0)
    total_quantity_demanded = models.IntegerField(default=0)
    total_quantity_sold = models.IntegerField(default=0)
    
    # Price discovery
    market_clearing_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    average_price_offered = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    price_dispersion = models.FloatField(default=0.0, help_text="Coefficient of variation in prices")
    
    # Market dynamics
    excess_supply = models.IntegerField(default=0)
    excess_demand = models.IntegerField(default=0)
    market_efficiency = models.FloatField(default=1.0, help_text="Market efficiency score (0-1)")
    
    # Competitive metrics
    herfindahl_index = models.FloatField(default=0.0, help_text="Market concentration measure")
    number_of_competitors = models.IntegerField(default=0)
    
    # Economic factors applied
    economic_multiplier = models.FloatField(default=1.0)
    market_factors_multiplier = models.FloatField(default=1.0)
    seasonal_adjustment = models.FloatField(default=1.0)
    
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'month', 'year', 'bike_type']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"Market Result - {self.bike_type.name} {self.year}/{self.month:02d}"


class PriceDemandFunction(models.Model):
    """Price-demand function parameters for different market segments"""
    
    market_config = models.ForeignKey(MarketConfiguration, on_delete=models.CASCADE, related_name='price_demand_functions')
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    customer_segment = models.CharField(max_length=20, choices=CustomerSegment.choices)
    
    # Linear demand function: Q = a - b*P + c*Income + d*Substitutes + e*Trends
    demand_intercept = models.FloatField(
        default=1000.0,
        help_text="Base demand level (a parameter)"
    )
    price_coefficient = models.FloatField(
        default=-0.5,
        help_text="Price sensitivity coefficient (b parameter)"
    )
    income_coefficient = models.FloatField(
        default=0.3,
        help_text="Income effect coefficient (c parameter)"
    )
    substitute_coefficient = models.FloatField(
        default=-0.2,
        help_text="Substitute goods effect (d parameter)"
    )
    trend_coefficient = models.FloatField(
        default=0.1,
        help_text="Market trend effect (e parameter)"
    )
    
    # Non-linear components
    price_elasticity = models.FloatField(
        default=-1.5,
        validators=[MinValueValidator(-5.0), MaxValueValidator(-0.1)],
        help_text="Price elasticity of demand"
    )
    saturation_point = models.IntegerField(
        default=10000,
        help_text="Market saturation point for this segment"
    )
    
    # Quality and innovation factors
    quality_sensitivity = models.FloatField(
        default=0.2,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Sensitivity to quality improvements"
    )
    innovation_sensitivity = models.FloatField(
        default=0.15,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Sensitivity to innovation"
    )
    brand_loyalty = models.FloatField(
        default=0.1,
        validators=[MinValueValidator(0.0), MaxValueValidator(0.5)],
        help_text="Brand loyalty factor"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['market_config', 'bike_type', 'customer_segment']
    
    def __str__(self):
        return f"PAF - {self.bike_type.name} / {self.customer_segment}"
    
    def calculate_demand(self, price, economic_condition, market_factors, player_attributes=None):
        """Calculate demand based on price and market conditions"""
        
        # Base demand calculation
        base_demand = self.demand_intercept
        
        # Price effect (with elasticity)
        price_effect = self.price_coefficient * (float(price) ** abs(self.price_elasticity))
        
        # Economic factors
        income_effect = self.income_coefficient * economic_condition.disposable_income_index
        
        # Market factors
        trend_effect = self.trend_coefficient * market_factors.overall_demand_multiplier
        
        # Quality and innovation effects (if player attributes provided)
        quality_effect = 0
        innovation_effect = 0
        brand_effect = 0
        
        if player_attributes:
            quality_effect = self.quality_sensitivity * player_attributes.get('quality_rating', 5.0)
            innovation_effect = self.innovation_sensitivity * player_attributes.get('innovation_level', 5.0)
            brand_effect = self.brand_loyalty * player_attributes.get('brand_strength', 5.0)
        
        # Calculate total demand
        total_demand = (base_demand + price_effect + income_effect + trend_effect + 
                       quality_effect + innovation_effect + brand_effect)
        
        # Apply saturation constraint
        total_demand = min(total_demand, self.saturation_point)
        
        # Ensure non-negative demand
        return max(0, total_demand)
