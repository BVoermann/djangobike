from django.contrib import admin
from .models import Market, MarketDemand, MarketPriceSensitivity, SalesOrder, SalesDecision


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'location_type', 'monthly_volume_capacity', 'session']
    list_filter = ['location_type', 'session']
    search_fields = ['name', 'location']


@admin.register(MarketDemand)
class MarketDemandAdmin(admin.ModelAdmin):
    list_display = ['market', 'bike_type', 'demand_percentage', 'session']
    list_filter = ['market', 'bike_type', 'session']


@admin.register(MarketPriceSensitivity)
class MarketPriceSensitivityAdmin(admin.ModelAdmin):
    list_display = ['market', 'price_segment', 'percentage', 'session']
    list_filter = ['market', 'price_segment', 'session']


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['session', 'market', 'bike', 'sale_month', 'sale_year', 'sale_price', 'is_completed']
    list_filter = ['is_completed', 'sale_year', 'sale_month', 'market', 'session']
    search_fields = ['bike__bike_type__name', 'market__name']


@admin.register(SalesDecision)
class SalesDecisionAdmin(admin.ModelAdmin):
    list_display = ['session', 'market', 'bike_type', 'price_segment', 'quantity', 'desired_price', 'is_processed', 'quantity_sold', 'decision_month', 'decision_year']
    list_filter = ['is_processed', 'price_segment', 'market', 'decision_year', 'decision_month', 'session']
    search_fields = ['bike_type__name', 'market__name']
    readonly_fields = ['created_at', 'actual_revenue']

    fieldsets = (
        ('Decision Info', {
            'fields': ('session', 'market', 'bike_type', 'price_segment', 'quantity')
        }),
        ('Pricing', {
            'fields': ('desired_price', 'transport_cost')
        }),
        ('Timing', {
            'fields': ('decision_month', 'decision_year', 'created_at')
        }),
        ('Results', {
            'fields': ('is_processed', 'quantity_sold', 'actual_revenue', 'unsold_reason')
        }),
    )
