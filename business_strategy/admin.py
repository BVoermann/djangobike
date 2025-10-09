from django.contrib import admin
from .models import (
    ResearchProject, ResearchBenefit, MarketingCampaign, CampaignEffect,
    SustainabilityProfile, SustainabilityInitiative, BusinessStrategy,
    CompetitiveAnalysis
)


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'project_type', 'status', 'session', 'progress_percentage', 'months_remaining']
    list_filter = ['project_type', 'status', 'session']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage']
    
    fieldsets = (
        (None, {
            'fields': ('session', 'name', 'project_type', 'description', 'status')
        }),
        ('Investment & Timeline', {
            'fields': ('total_investment_required', 'invested_amount', 'monthly_investment', 
                      'duration_months', 'months_remaining', 'start_month', 'start_year',
                      'completion_month', 'completion_year')
        }),
        ('Benefits', {
            'fields': ('production_efficiency_bonus', 'quality_bonus', 'cost_reduction_bonus', 
                      'sustainability_bonus')
        }),
        ('Targets', {
            'fields': ('target_bike_types', 'target_components'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'progress_percentage'),
            'classes': ('collapse',)
        })
    )


@admin.register(ResearchBenefit)
class ResearchBenefitAdmin(admin.ModelAdmin):
    list_display = ['research_project', 'session', 'activation_month', 'activation_year', 'is_active']
    list_filter = ['session', 'is_active', 'activation_year']
    readonly_fields = ['created_at']


@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'target_segment', 'status', 'session', 'months_remaining']
    list_filter = ['campaign_type', 'target_segment', 'status', 'session']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('session', 'name', 'campaign_type', 'target_segment', 'description', 'status')
        }),
        ('Budget & Timeline', {
            'fields': ('total_budget', 'spent_amount', 'monthly_spend', 'duration_months', 
                      'months_remaining', 'start_month', 'start_year', 'end_month', 'end_year')
        }),
        ('Effects', {
            'fields': ('immediate_demand_boost', 'brand_awareness_boost', 'customer_loyalty_bonus', 
                      'price_premium_tolerance')
        }),
        ('Targets', {
            'fields': ('target_markets', 'target_bike_types'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CampaignEffect)
class CampaignEffectAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'session', 'month', 'year', 'demand_boost', 'brand_awareness_boost']
    list_filter = ['session', 'year', 'month']
    readonly_fields = ['created_at']


@admin.register(SustainabilityProfile)
class SustainabilityProfileAdmin(admin.ModelAdmin):
    list_display = ['session', 'sustainability_score', 'eco_certification_level', 'eco_customer_appeal']
    list_filter = ['session', 'eco_certification_level']
    readonly_fields = ['created_at', 'updated_at', 'eco_customer_appeal', 'premium_eco_pricing', 'brand_reputation_bonus']
    
    fieldsets = (
        (None, {
            'fields': ('session', 'sustainability_score', 'eco_certification_level')
        }),
        ('Material Choices', {
            'fields': ('sustainable_materials_percentage', 'recycled_materials_usage', 'local_supplier_percentage')
        }),
        ('Production Practices', {
            'fields': ('renewable_energy_usage', 'waste_reduction_level', 'carbon_footprint_reduction')
        }),
        ('Customer Effects (Auto-calculated)', {
            'fields': ('eco_customer_appeal', 'premium_eco_pricing', 'brand_reputation_bonus'),
            'classes': ('collapse',)
        }),
        ('Costs', {
            'fields': ('sustainability_investment_monthly', 'compliance_costs')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SustainabilityInitiative)
class SustainabilityInitiativeAdmin(admin.ModelAdmin):
    list_display = ['name', 'initiative_type', 'status', 'session', 'months_remaining']
    list_filter = ['initiative_type', 'status', 'session']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('session', 'sustainability_profile', 'name', 'initiative_type', 'description', 'status')
        }),
        ('Investment & Timeline', {
            'fields': ('total_cost', 'invested_amount', 'monthly_cost', 'implementation_months', 
                      'months_remaining', 'start_month', 'start_year', 'completion_month', 'completion_year')
        }),
        ('Benefits', {
            'fields': ('sustainability_score_bonus', 'renewable_energy_bonus', 'waste_reduction_bonus',
                      'sustainable_materials_bonus', 'local_sourcing_bonus', 'certification_level_bonus')
        }),
        ('Ongoing Requirements', {
            'fields': ('requires_ongoing_investment', 'penalty_if_neglected')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(BusinessStrategy)
class BusinessStrategyAdmin(admin.ModelAdmin):
    list_display = ['session', 'innovation_advantage', 'brand_strength', 'sustainability_reputation']
    list_filter = ['session']
    readonly_fields = ['created_at', 'updated_at', 'total_rd_investment', 'total_marketing_investment', 
                      'total_sustainability_investment', 'innovation_advantage', 'brand_strength', 
                      'sustainability_reputation']
    
    fieldsets = (
        (None, {
            'fields': ('session',)
        }),
        ('Strategy Focus (should sum to 100%)', {
            'fields': ('rd_focus_percentage', 'marketing_focus_percentage', 'sustainability_focus_percentage', 
                      'operational_focus_percentage')
        }),
        ('Monthly Budgets', {
            'fields': ('rd_monthly_budget', 'marketing_monthly_budget', 'sustainability_monthly_budget')
        }),
        ('Performance Tracking (Auto-calculated)', {
            'fields': ('total_rd_investment', 'total_marketing_investment', 'total_sustainability_investment',
                      'innovation_advantage', 'brand_strength', 'sustainability_reputation'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CompetitiveAnalysis)
class CompetitiveAnalysisAdmin(admin.ModelAdmin):
    list_display = ['session', 'month', 'year', 'market_share_estimate', 'brand_recognition_level', 
                   'customer_satisfaction_score']
    list_filter = ['session', 'year', 'month']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('session', 'month', 'year')
        }),
        ('Market Position', {
            'fields': ('market_share_estimate', 'brand_recognition_level', 'customer_satisfaction_score')
        }),
        ('Competitive Advantages', {
            'fields': ('price_competitiveness', 'quality_competitiveness', 'innovation_competitiveness', 
                      'sustainability_competitiveness')
        }),
        ('Market Intelligence', {
            'fields': ('competitor_rd_activity', 'competitor_marketing_intensity', 'market_sustainability_trend')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )