from django.contrib import admin
from .models import GameMode, GameObjective, SessionGameMode, GameResult, BankruptcyEvent


@admin.register(GameMode)
class GameModeAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode_type', 'duration_months', 'starting_balance', 'bankruptcy_threshold', 'is_active', 'is_multiplayer_compatible']
    list_filter = ['mode_type', 'is_active', 'is_multiplayer_compatible']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_multiplayer_compatible']
    ordering = ['name']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('name', 'mode_type', 'description')
        }),
        ('Spieleinstellungen', {
            'fields': ('duration_months', 'starting_balance', 'bankruptcy_threshold')
        }),
        ('Konfiguration', {
            'fields': ('victory_conditions', 'difficulty_multipliers')
        }),
        ('Optionen', {
            'fields': ('is_active', 'is_multiplayer_compatible')
        }),
    )


class GameObjectiveInline(admin.TabularInline):
    model = GameObjective
    extra = 1
    fields = ['name', 'objective_type', 'target_value', 'comparison_operator', 'weight', 'is_primary', 'is_failure_condition', 'order', 'is_active']
    ordering = ['order', 'name']


@admin.register(GameObjective)
class GameObjectiveAdmin(admin.ModelAdmin):
    list_display = ['name', 'game_mode', 'objective_type', 'target_value', 'comparison_operator', 'weight', 'is_primary', 'is_failure_condition', 'is_active']
    list_filter = ['game_mode', 'objective_type', 'is_primary', 'is_failure_condition', 'is_active', 'evaluation_frequency']
    search_fields = ['name', 'description']
    list_editable = ['weight', 'is_primary', 'is_failure_condition', 'is_active']
    ordering = ['game_mode', 'order', 'name']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('game_mode', 'name', 'description', 'order')
        }),
        ('Zielwerte', {
            'fields': ('objective_type', 'target_value', 'comparison_operator')
        }),
        ('Wichtigkeit', {
            'fields': ('weight', 'is_primary', 'is_failure_condition')
        }),
        ('Timing', {
            'fields': ('evaluation_frequency',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# Add inline to GameMode admin
GameModeAdmin.inlines = [GameObjectiveInline]


@admin.register(SessionGameMode)
class SessionGameModeAdmin(admin.ModelAdmin):
    list_display = ['session', 'game_mode', 'is_active', 'is_completed', 'is_failed', 'final_score', 'completion_percentage', 'started_at']
    list_filter = ['game_mode', 'is_active', 'is_completed', 'is_failed', 'started_at']
    search_fields = ['session__name', 'session__user__username', 'game_mode__name']
    readonly_fields = ['started_at', 'completed_at', 'final_score', 'completion_percentage', 'objective_progress', 'monthly_scores']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session', 'game_mode')
        }),
        ('Game State', {
            'fields': ('is_active', 'is_completed', 'is_failed')
        }),
        ('Results', {
            'fields': ('final_score', 'completion_percentage'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Progress Data', {
            'fields': ('objective_progress', 'monthly_scores'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active games
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'game_mode_name', 'result_type', 'final_score', 'completion_percentage', 'total_months_played', 'final_balance', 'created_at']
    list_filter = ['result_type', 'session_game_mode__game_mode', 'created_at']
    search_fields = ['session_game_mode__session__name', 'session_game_mode__session__user__username']
    readonly_fields = ['session_game_mode', 'result_type', 'final_score', 'completion_percentage', 'total_months_played', 'final_balance', 'total_revenue', 'total_profit', 'bikes_produced', 'bikes_sold', 'market_share_final', 'objective_results', 'performance_metrics', 'created_at']
    ordering = ['-final_score', '-created_at']
    
    fieldsets = (
        ('Game Information', {
            'fields': ('session_game_mode', 'result_type')
        }),
        ('Scores', {
            'fields': ('final_score', 'completion_percentage')
        }),
        ('Game Statistics', {
            'fields': ('total_months_played', 'final_balance', 'total_revenue', 'total_profit', 'bikes_produced', 'bikes_sold', 'market_share_final')
        }),
        ('Results Data', {
            'fields': ('objective_results', 'performance_metrics'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('summary', 'failure_reason', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Multiplayer', {
            'fields': ('rank', 'total_players'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def session_name(self, obj):
        return obj.session_game_mode.session.name
    session_name.short_description = 'Session'
    
    def game_mode_name(self, obj):
        return obj.session_game_mode.game_mode.name
    game_mode_name.short_description = 'Game Mode'
    
    def has_add_permission(self, request):
        return False  # Results are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Results should not be modified


@admin.register(BankruptcyEvent)
class BankruptcyEventAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'trigger_month', 'trigger_year', 'balance_at_bankruptcy', 'primary_cause', 'player_eliminated', 'recovery_attempted', 'created_at']
    list_filter = ['primary_cause', 'player_eliminated', 'recovery_attempted', 'recovery_successful', 'trigger_year', 'created_at']
    search_fields = ['session__name', 'session__user__username', 'elimination_reason']
    readonly_fields = ['session', 'session_game_mode', 'balance_at_bankruptcy', 'bankruptcy_threshold', 'trigger_month', 'trigger_year', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Bankruptcy Details', {
            'fields': ('session', 'session_game_mode', 'trigger_month', 'trigger_year')
        }),
        ('Financial Information', {
            'fields': ('balance_at_bankruptcy', 'bankruptcy_threshold')
        }),
        ('Cause Analysis', {
            'fields': ('primary_cause', 'contributing_factors')
        }),
        ('Recovery', {
            'fields': ('recovery_attempted', 'recovery_successful', 'bailout_amount')
        }),
        ('Elimination', {
            'fields': ('player_eliminated', 'elimination_reason')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def session_name(self, obj):
        return obj.session.name
    session_name.short_description = 'Session'
    
    def has_add_permission(self, request):
        return False  # Bankruptcy events are created automatically
    
    def has_change_permission(self, request, obj=None):
        # Allow modification of recovery fields only
        return True
