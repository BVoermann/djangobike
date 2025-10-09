from django.contrib import admin
from .models import (
    MarketConfiguration, EconomicCondition, MarketFactors, 
    CustomerDemographics, BikeMarketSegment, PlayerMarketSubmission,
    MarketClearingResult, PriceDemandFunction
)


@admin.register(MarketConfiguration)
class MarketConfigurationAdmin(admin.ModelAdmin):
    list_display = ['multiplayer_game', 'market_structure', 'total_market_size', 'price_competition_intensity']
    list_filter = ['market_structure']
    search_fields = ['multiplayer_game__name']


@admin.register(EconomicCondition)
class EconomicConditionAdmin(admin.ModelAdmin):
    list_display = ['multiplayer_game', 'month', 'gdp_growth_rate', 'unemployment_rate', 'business_cycle_phase']
    list_filter = ['business_cycle_phase']
    ordering = ['-month']


@admin.register(MarketFactors)
class MarketFactorsAdmin(admin.ModelAdmin):
    list_display = ['multiplayer_game', 'month', 'retro_trend_strength', 'environmental_consciousness']
    ordering = ['-month']


@admin.register(CustomerDemographics)
class CustomerDemographicsAdmin(admin.ModelAdmin):
    list_display = ['multiplayer_game', 'month', 'total_potential_customers']
    ordering = ['-month']


@admin.register(BikeMarketSegment)
class BikeMarketSegmentAdmin(admin.ModelAdmin):
    list_display = ['customer_demographics', 'bike_type', 'commuters_preference', 'recreational_preference']


@admin.register(PlayerMarketSubmission)
class PlayerMarketSubmissionAdmin(admin.ModelAdmin):
    list_display = ['player_session', 'month', 'bike_type', 'quantity_offered', 'price_per_unit', 'submitted_at']
    list_filter = ['bike_type', 'month']
    search_fields = ['player_session__user__username']
    ordering = ['-month', '-submitted_at']


@admin.register(MarketClearingResult)
class MarketClearingResultAdmin(admin.ModelAdmin):
    list_display = ['multiplayer_game', 'month', 'bike_type', 'total_quantity_sold', 'market_clearing_price']
    list_filter = ['month', 'bike_type']
    ordering = ['-month']


@admin.register(PriceDemandFunction)
class PriceDemandFunctionAdmin(admin.ModelAdmin):
    list_display = ['market_config', 'bike_type', 'demand_intercept', 'price_elasticity']
    list_filter = ['bike_type']
