from django.contrib import admin
from .models import (
    HelpCategory, TutorialVideo, InteractiveGuide, TooltipHelp, 
    ContextualHelp, UserHelpProgress, GuideProgress, HelpFeedback, HelpAnalytics
)


@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'order', 'is_active']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']


@admin.register(TutorialVideo)
class TutorialVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty_level', 'duration_minutes', 'view_count', 'is_featured', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active', 'is_featured']
    search_fields = ['title', 'description', 'tags']
    list_editable = ['is_featured', 'is_active']
    readonly_fields = ['view_count']
    ordering = ['category', 'order', 'title']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('title', 'description', 'category', 'order')
        }),
        ('Video Details', {
            'fields': ('video_url', 'video_embed_code', 'thumbnail_url', 'duration_minutes')
        }),
        ('Metadaten', {
            'fields': ('difficulty_level', 'prerequisites', 'learning_objectives', 'tags')
        }),
        ('Einstellungen', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Statistiken', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
    )


@admin.register(InteractiveGuide)
class InteractiveGuideAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'guide_type', 'user_level_required', 'start_count', 'completion_rate', 'is_active']
    list_filter = ['category', 'guide_type', 'user_level_required', 'is_active']
    search_fields = ['title', 'description', 'target_url_pattern']
    list_editable = ['is_active']
    readonly_fields = ['start_count', 'completion_count', 'completion_rate']
    ordering = ['category', 'order', 'title']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('title', 'description', 'category', 'order')
        }),
        ('Guide Konfiguration', {
            'fields': ('guide_type', 'target_url_pattern', 'trigger_condition', 'steps')
        }),
        ('Bedingungen', {
            'fields': ('prerequisites', 'user_level_required')
        }),
        ('Einstellungen', {
            'fields': ('is_skippable', 'show_progress', 'auto_advance', 'completion_required', 'is_active')
        }),
        ('Statistiken', {
            'fields': ('start_count', 'completion_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TooltipHelp)
class TooltipHelpAdmin(admin.ModelAdmin):
    list_display = ['title', 'element_selector', 'page_url_pattern', 'tooltip_type', 'view_count', 'is_active']
    list_filter = ['tooltip_type', 'category', 'is_active']
    search_fields = ['title', 'content', 'element_selector', 'page_url_pattern']
    list_editable = ['is_active']
    readonly_fields = ['view_count']
    ordering = ['category', 'order', 'title']
    
    fieldsets = (
        ('Ziel Element', {
            'fields': ('element_selector', 'page_url_pattern')
        }),
        ('Inhalt', {
            'fields': ('title', 'content', 'tooltip_type', 'category')
        }),
        ('Erscheinungsbild', {
            'fields': ('position', 'icon')
        }),
        ('Verhalten', {
            'fields': ('show_on_hover', 'show_on_click', 'auto_hide_delay')
        }),
        ('Organisation', {
            'fields': ('order', 'is_active')
        }),
        ('Statistiken', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContextualHelp)
class ContextualHelpAdmin(admin.ModelAdmin):
    list_display = ['title', 'context_type', 'help_format', 'user_experience_level', 'priority', 'trigger_count', 'is_active']
    list_filter = ['context_type', 'help_format', 'user_experience_level', 'category', 'is_active']
    search_fields = ['title', 'content']
    list_editable = ['priority', 'is_active']
    readonly_fields = ['trigger_count', 'interaction_count']
    ordering = ['priority', 'order', 'title']
    
    fieldsets = (
        ('Kontext Erkennung', {
            'fields': ('context_type', 'trigger_conditions')
        }),
        ('Inhalt', {
            'fields': ('title', 'content', 'help_format', 'category')
        }),
        ('Verwandte Inhalte', {
            'fields': ('related_video', 'related_guide')
        }),
        ('Targeting', {
            'fields': ('user_experience_level', 'session_month_range')
        }),
        ('Verhalten', {
            'fields': ('max_displays_per_user', 'cooldown_hours', 'priority')
        }),
        ('Organisation', {
            'fields': ('order', 'is_active')
        }),
        ('Statistiken', {
            'fields': ('trigger_count', 'interaction_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserHelpProgress)
class UserHelpProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'session', 'help_level', 'onboarding_completed', 'total_help_interactions']
    list_filter = ['help_level', 'onboarding_completed', 'show_tooltips', 'show_contextual_help']
    search_fields = ['user__username', 'session__id']
    readonly_fields = ['total_help_interactions', 'last_help_accessed']
    
    fieldsets = (
        ('Benutzer', {
            'fields': ('user', 'session')
        }),
        ('Fortschritt', {
            'fields': ('onboarding_completed', 'help_level')
        }),
        ('Präferenzen', {
            'fields': ('show_tooltips', 'show_contextual_help', 'auto_play_guides')
        }),
        ('Statistiken', {
            'fields': ('total_help_interactions', 'last_help_accessed'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GuideProgress)
class GuideProgressAdmin(admin.ModelAdmin):
    list_display = ['user_progress', 'guide', 'current_step', 'completion_percentage', 'was_skipped']
    list_filter = ['guide__category', 'was_skipped', 'completed_at']
    search_fields = ['user_progress__user__username', 'guide__title']
    readonly_fields = ['completion_percentage', 'time_spent_seconds']
    
    fieldsets = (
        ('Fortschritt', {
            'fields': ('user_progress', 'guide', 'current_step', 'total_steps', 'completion_percentage')
        }),
        ('Zeitstempel', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Interaktionsdaten', {
            'fields': ('steps_completed', 'time_spent_seconds', 'was_skipped')
        }),
    )


@admin.register(HelpFeedback)
class HelpFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_id', 'rating', 'would_recommend', 'created_at']
    list_filter = ['content_type', 'rating', 'would_recommend', 'user_experience_level']
    search_fields = ['user__username', 'comment', 'suggested_improvements']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Benutzer & Inhalt', {
            'fields': ('user', 'content_type', 'content_id', 'user_experience_level')
        }),
        ('Feedback', {
            'fields': ('rating', 'comment', 'would_recommend')
        }),
        ('Verbesserungen', {
            'fields': ('suggested_improvements', 'session_context')
        }),
        ('Zeitstempel', {
            'fields': ('created_at',)
        }),
    )


@admin.register(HelpAnalytics)
class HelpAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'content_type', 'content_id', 'page_url', 'timestamp']
    list_filter = ['event_type', 'content_type', 'user_experience_level', 'session_month']
    search_fields = ['user__username', 'page_url']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Benutzer & Ereignis', {
            'fields': ('user', 'session', 'event_type', 'content_type', 'content_id')
        }),
        ('Kontext', {
            'fields': ('page_url', 'session_month', 'user_experience_level')
        }),
        ('Interaktionsdaten', {
            'fields': ('interaction_data',)
        }),
        ('Zeitstempel', {
            'fields': ('timestamp',)
        }),
    )
