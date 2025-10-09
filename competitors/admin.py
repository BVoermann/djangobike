from django.contrib import admin
from .models import AICompetitor, CompetitorProduction, CompetitorSale, MarketCompetition


@admin.register(AICompetitor)
class AICompetitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'strategy', 'financial_resources', 'market_presence', 'total_bikes_sold', 'total_revenue']
    list_filter = ['strategy', 'session']
    search_fields = ['name']
    readonly_fields = ['total_bikes_produced', 'total_bikes_sold', 'total_revenue', 'created_at']


@admin.register(CompetitorProduction)
class CompetitorProductionAdmin(admin.ModelAdmin):
    list_display = ['competitor', 'bike_type', 'price_segment', 'month', 'year', 'quantity_produced', 'production_cost_per_unit']
    list_filter = ['competitor', 'bike_type', 'price_segment', 'year', 'month']
    search_fields = ['competitor__name', 'bike_type__name']


@admin.register(CompetitorSale)
class CompetitorSaleAdmin(admin.ModelAdmin):
    list_display = ['competitor', 'market', 'bike_type', 'month', 'year', 'quantity_sold', 'sale_price', 'total_revenue']
    list_filter = ['competitor', 'market', 'bike_type', 'year', 'month']
    search_fields = ['competitor__name', 'market__name', 'bike_type__name']


@admin.register(MarketCompetition)
class MarketCompetitionAdmin(admin.ModelAdmin):
    list_display = ['market', 'bike_type', 'price_segment', 'month', 'year', 'total_supply', 'estimated_demand', 'saturation_level']
    list_filter = ['market', 'bike_type', 'price_segment', 'year', 'month']
    search_fields = ['market__name', 'bike_type__name']
