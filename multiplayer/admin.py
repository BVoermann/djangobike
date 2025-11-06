from django.contrib import admin
from .models import (
    MultiplayerGame, PlayerSession, TurnState, GameEvent,
    MultiplayerGameInvitation, PlayerCommunication
)


@admin.register(MultiplayerGame)
class MultiplayerGameAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'max_players', 'current_turn', 'created_by', 'created_at')
    list_filter = ('status', 'difficulty', 'created_at')
    search_fields = ('name', 'created_by__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_turn_processed_at')
    actions = ['delete_selected_games']

    def current_turn(self, obj):
        return f"{obj.current_year}/{obj.current_month:02d}"
    current_turn.short_description = 'Current Turn'

    def delete_selected_games(self, request, queryset):
        """Delete selected multiplayer games and all associated data."""
        count = queryset.count()
        # Get the names of games being deleted for the message
        game_names = list(queryset.values_list('name', flat=True))

        # Django will automatically cascade delete related objects due to ForeignKey on_delete=CASCADE
        # This includes PlayerSession, TurnState, GameEvent, etc.
        queryset.delete()

        self.message_user(
            request,
            f"Successfully deleted {count} game(s): {', '.join(game_names)}. "
            f"All player sessions and related data have been removed."
        )
    delete_selected_games.short_description = "Delete selected games (and all player data)"

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'created_by', 'status')
        }),
        ('Game Configuration', {
            'fields': ('max_players', 'human_players_count', 'ai_players_count', 'difficulty')
        }),
        ('Timing', {
            'fields': ('current_month', 'current_year', 'max_months', 'turn_deadline_hours',
                      'turn_duration_minutes', 'last_turn_processed_at')
        }),
        ('Financial Settings', {
            'fields': ('starting_balance', 'bankruptcy_threshold')
        }),
        ('Features', {
            'fields': ('allow_bankruptcy', 'enable_real_time_updates', 'enable_player_chat', 'enable_market_intelligence')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'ended_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PlayerSession)
class PlayerSessionAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'multiplayer_game', 'player_type', 'balance', 'is_bankrupt', 'joined_at')
    list_filter = ('player_type', 'is_bankrupt', 'is_active', 'ai_strategy')
    search_fields = ('company_name', 'user__username')
    readonly_fields = ('id', 'joined_at', 'last_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'multiplayer_game', 'user', 'company_name', 'player_type')
        }),
        ('Game State', {
            'fields': ('balance', 'is_bankrupt', 'is_active', 'bankruptcy_month', 'bankruptcy_year')
        }),
        ('Performance Metrics', {
            'fields': ('total_revenue', 'total_profit', 'bikes_produced', 'bikes_sold', 'market_share')
        }),
        ('AI Configuration', {
            'fields': ('ai_strategy', 'ai_difficulty', 'ai_aggressiveness', 'ai_risk_tolerance'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'last_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(TurnState)
class TurnStateAdmin(admin.ModelAdmin):
    list_display = ('player_session', 'turn_display', 'decisions_submitted', 'submitted_at', 'auto_submitted')
    list_filter = ('decisions_submitted', 'auto_submitted', 'year', 'month')
    search_fields = ('player_session__company_name', 'multiplayer_game__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def turn_display(self, obj):
        return f"{obj.year}/{obj.month:02d}"
    turn_display.short_description = 'Turn'
    
    fieldsets = (
        ('Turn Information', {
            'fields': ('multiplayer_game', 'player_session', 'month', 'year')
        }),
        ('Submission Status', {
            'fields': ('decisions_submitted', 'submitted_at', 'auto_submitted')
        }),
        ('Performance', {
            'fields': ('revenue_this_turn', 'profit_this_turn', 'bikes_produced_this_turn', 'bikes_sold_this_turn')
        }),
        ('Decisions', {
            'fields': ('production_decisions', 'procurement_decisions', 'sales_decisions', 'hr_decisions', 'finance_decisions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ('multiplayer_game', 'event_type', 'message_preview', 'timestamp', 'visible_to_all')
    list_filter = ('event_type', 'visible_to_all', 'timestamp')
    search_fields = ('multiplayer_game__name', 'message')
    readonly_fields = ('timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('multiplayer_game', 'event_type', 'message', 'data')
        }),
        ('Visibility', {
            'fields': ('visible_to_all', 'visible_to', 'created_by')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        })
    )


@admin.register(MultiplayerGameInvitation)
class MultiplayerGameInvitationAdmin(admin.ModelAdmin):
    list_display = ('multiplayer_game', 'invited_user', 'invited_by', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('multiplayer_game__name', 'invited_user__username', 'invited_by__username')
    readonly_fields = ('created_at', 'responded_at')


@admin.register(PlayerCommunication)
class PlayerCommunicationAdmin(admin.ModelAdmin):
    list_display = ('multiplayer_game', 'sender', 'message_type', 'content_preview', 'is_public', 'created_at')
    list_filter = ('message_type', 'is_public', 'is_read', 'created_at')
    search_fields = ('multiplayer_game__name', 'sender__company_name', 'content')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = 'Content'
