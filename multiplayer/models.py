from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Get the custom user model
User = settings.AUTH_USER_MODEL


class MultiplayerGame(models.Model):
    """Represents a multiplayer game session with multiple human and AI players."""
    
    GAME_STATUS_CHOICES = [
        ('setup', 'Setup'),
        ('waiting', 'Waiting for Players'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    max_players = models.IntegerField(
        default=6, 
        validators=[MinValueValidator(2), MaxValueValidator(10)]
    )
    human_players_count = models.IntegerField(default=1)
    ai_players_count = models.IntegerField(default=5)
    
    # Game timing
    current_month = models.IntegerField(default=1)
    current_year = models.IntegerField(default=2024)
    max_months = models.IntegerField(default=60)  # 5 years default
    turn_deadline_hours = models.IntegerField(
        default=24,
        validators=[MinValueValidator(0)],
        help_text="Hours to submit decisions. Set to 0 for instant turn advancement when all players submit."
    )
    turn_duration_minutes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum wait time in minutes before next turn can be processed (0 = instant)"
    )
    last_turn_processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the last turn was processed"
    )
    
    # Game settings
    status = models.CharField(max_length=20, choices=GAME_STATUS_CHOICES, default='setup')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    allow_bankruptcy = models.BooleanField(default=True)
    bankruptcy_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=-50000.00)
    starting_balance = models.DecimalField(max_digits=12, decimal_places=2, default=80000.00)
    
    # Meta information
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_games')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Game configuration
    enable_real_time_updates = models.BooleanField(default=True)
    enable_player_chat = models.BooleanField(default=True)
    enable_market_intelligence = models.BooleanField(default=False)  # Show competitor info

    # Admin-managed user assignment
    assigned_users = models.ManyToManyField(
        User,
        related_name='assigned_multiplayer_games',
        blank=True,
        help_text='Users assigned to this game by Spielleitung'
    )

    # Game parameters (uploaded by admin)
    parameters_uploaded = models.BooleanField(
        default=False,
        help_text='Whether game parameters have been uploaded and initialized'
    )
    parameters_file = models.FileField(
        upload_to='multiplayer_parameters/',
        null=True,
        blank=True,
        help_text='ZIP file containing game parameters (Excel files)'
    )
    parameters_uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When parameters were uploaded'
    )

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.status})"
        
    @property
    def is_full(self):
        return self.players.count() >= self.max_players
        
    @property
    def active_players_count(self):
        return self.players.filter(is_active=True, is_bankrupt=False).count()
        
    @property
    def game_progress_percentage(self):
        total_months = self.max_months
        current_progress = (self.current_year - 2024) * 12 + self.current_month - 1
        return min(100, (current_progress / total_months) * 100)

    def can_process_next_turn(self):
        """Check if enough time has passed to process the next turn."""
        # If turn_duration_minutes is 0, can process immediately
        if self.turn_duration_minutes == 0:
            return True, None

        # If this is the first turn, can process
        if not self.last_turn_processed_at:
            return True, None

        from django.utils import timezone
        from datetime import timedelta

        # Calculate when the next turn can be processed
        next_turn_time = self.last_turn_processed_at + timedelta(minutes=self.turn_duration_minutes)
        now = timezone.now()

        if now >= next_turn_time:
            return True, None
        else:
            # Return False and the remaining time
            remaining = next_turn_time - now
            return False, remaining

    def get_next_turn_countdown(self):
        """Get human-readable countdown until next turn can be processed."""
        can_process, remaining = self.can_process_next_turn()

        if can_process:
            return None

        if remaining:
            total_seconds = int(remaining.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        return None

    @property
    def is_single_human_player_game(self):
        """Check if this is a game with only one human player."""
        human_players = self.players.filter(
            is_active=True,
            is_bankrupt=False,
            player_type='human'
        ).count()
        return human_players == 1


class PlayerSession(models.Model):
    """Represents a player (human or AI) in a multiplayer game.

    IMPORTANT - Balance Management:
    ================================
    The `balance` field in this model is the SOURCE OF TRUTH for player finances
    in multiplayer games. Each player's balance is stored HERE, specific to this
    game instance.

    For compatibility with singleplayer code, each player also has a GameSession
    object where balance is synchronized. However, PlayerSession.balance should
    always be treated as the authoritative value.

    To update player balance, use the BalanceManager from multiplayer.balance_manager:
        from multiplayer.balance_manager import get_balance_manager
        balance_mgr = get_balance_manager(player_session, game_session)
        balance_mgr.subtract_from_balance(amount, reason="purchase")

    This ensures both PlayerSession.balance and GameSession.balance stay in sync.
    """

    PLAYER_TYPE_CHOICES = [
        ('human', 'Human Player'),
        ('ai', 'AI Player'),
    ]

    AI_STRATEGY_CHOICES = [
        ('cheap_only', 'Cost Leader'),
        ('balanced', 'Balanced'),
        ('premium_focus', 'Premium Focus'),
        ('e_bike_specialist', 'E-Bike Specialist'),
        ('innovative', 'Innovation Leader'),
        ('aggressive', 'Aggressive Competitor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE, related_name='players')

    # Player identification
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # None for AI
    company_name = models.CharField(max_length=100)
    player_type = models.CharField(max_length=10, choices=PLAYER_TYPE_CHOICES)
    ai_strategy = models.CharField(max_length=20, choices=AI_STRATEGY_CHOICES, null=True, blank=True)

    # Game state - BALANCE IS STORED HERE (source of truth for multiplayer)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=80000.00,
        help_text="Player's current balance in this specific game. This is the source of truth."
    )
    is_bankrupt = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    bankruptcy_month = models.IntegerField(null=True, blank=True)
    bankruptcy_year = models.IntegerField(null=True, blank=True)
    
    # Performance tracking
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bikes_produced = models.IntegerField(default=0)
    bikes_sold = models.IntegerField(default=0)
    market_share = models.FloatField(default=0.0)
    
    # AI-specific settings
    ai_difficulty = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(2.0)])
    ai_aggressiveness = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    ai_risk_tolerance = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'user']
        ordering = ['joined_at']
        
    def __str__(self):
        player_info = self.user.username if self.user else f"AI-{self.ai_strategy}"
        return f"{self.company_name} ({player_info})"
        
    @property
    def is_ai(self):
        return self.player_type == 'ai'
        
    @property
    def is_human(self):
        return self.player_type == 'human'
        
    def check_bankruptcy(self):
        """Check if player meets bankruptcy conditions."""
        if self.is_bankrupt:
            return True
            
        # Multiple bankruptcy conditions
        game = self.multiplayer_game
        if self.balance <= game.bankruptcy_threshold:
            return True
            
        # Additional conditions can be added here
        # e.g., consecutive losses, debt ratio, etc.
        return False
        
    def trigger_bankruptcy(self):
        """Mark player as bankrupt and handle consequences."""
        if not self.is_bankrupt:
            self.is_bankrupt = True
            self.bankruptcy_month = self.multiplayer_game.current_month
            self.bankruptcy_year = self.multiplayer_game.current_year
            self.is_active = False
            self.save()
            
            # Create bankruptcy event
            GameEvent.objects.create(
                multiplayer_game=self.multiplayer_game,
                event_type='player_bankruptcy',
                message=f"{self.company_name} has gone bankrupt",
                data={'player_id': str(self.id), 'company_name': self.company_name}
            )


class TurnState(models.Model):
    """Tracks decision submission state for each player in each turn."""
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE)
    player_session = models.ForeignKey(PlayerSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Decision submission tracking
    decisions_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    auto_submitted = models.BooleanField(default=False)  # AI or timeout auto-submission
    
    # Decision data (stored as JSON for flexibility)
    production_decisions = models.JSONField(default=dict)
    procurement_decisions = models.JSONField(default=dict)
    sales_decisions = models.JSONField(default=list, help_text="List of sales decisions: [{market_id, bike_type_id, price_segment, quantity, desired_price, transport_cost}, ...]")
    hr_decisions = models.JSONField(default=dict)
    finance_decisions = models.JSONField(default=dict)

    # Sales results after market simulation
    sales_results = models.JSONField(default=dict, help_text="Results of sales processing: {decisions: [...], total_sold: 0, total_revenue: 0, unsold: [...]}")

    # Performance data for this turn
    revenue_this_turn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_this_turn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bikes_produced_this_turn = models.IntegerField(default=0)
    bikes_sold_this_turn = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['multiplayer_game', 'player_session', 'month', 'year']
        ordering = ['-year', '-month', 'player_session']
        
    def __str__(self):
        status = "✓" if self.decisions_submitted else "⏳"
        return f"{self.player_session.company_name} - {self.year}/{self.month:02d} {status}"


class GameEvent(models.Model):
    """Represents events that occur during the game for logging and notifications."""
    
    EVENT_TYPE_CHOICES = [
        ('game_started', 'Game Started'),
        ('turn_processed', 'Turn Processed'),
        ('player_joined', 'Player Joined'),
        ('player_left', 'Player Left'),
        ('player_bankruptcy', 'Player Bankruptcy'),
        ('market_event', 'Market Event'),
        ('ai_action', 'AI Action'),
        ('system_message', 'System Message'),
        ('player_message', 'Player Message'),
        ('game_ended', 'Game Ended'),
    ]
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    message = models.TextField()
    data = models.JSONField(default=dict)
    
    # Visibility settings
    visible_to_all = models.BooleanField(default=True)
    visible_to = models.ManyToManyField(PlayerSession, blank=True, related_name='visible_events')
    created_by = models.ForeignKey(PlayerSession, on_delete=models.CASCADE, null=True, blank=True, related_name='created_events')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.event_type}: {self.message[:50]}"


class MultiplayerGameInvitation(models.Model):
    """Handles invitations to multiplayer games."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ['multiplayer_game', 'invited_user']
        
    def __str__(self):
        return f"Invitation to {self.invited_user.username} for {self.multiplayer_game.name}"
        
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class PlayerCommunication(models.Model):
    """Handles chat and communication between players."""

    MESSAGE_TYPE_CHOICES = [
        ('chat', 'Chat Message'),
        ('trade_offer', 'Trade Offer'),
        ('alliance_request', 'Alliance Request'),
        ('system_notification', 'System Notification'),
    ]

    multiplayer_game = models.ForeignKey(MultiplayerGame, on_delete=models.CASCADE)
    sender = models.ForeignKey(PlayerSession, on_delete=models.CASCADE, related_name='sent_messages')
    recipients = models.ManyToManyField(PlayerSession, related_name='received_messages', blank=True)

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='chat')
    content = models.TextField()
    data = models.JSONField(default=dict)  # For structured data like trade offers

    is_public = models.BooleanField(default=True)  # False for private messages
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        recipient_info = "All" if self.is_public else f"{self.recipients.count()} players"
        return f"{self.sender.company_name} → {recipient_info}: {self.content[:30]}"


class GameParameters(models.Model):
    """Stores editable simulation parameters for a multiplayer game.

    This allows Spielleitung to adjust game parameters in real-time during gameplay.
    Parameters are stored as JSON for flexibility.
    """

    multiplayer_game = models.OneToOneField(
        MultiplayerGame,
        on_delete=models.CASCADE,
        related_name='parameters'
    )

    # === SUPPLIER PARAMETERS (from lieferanten.xlsx) ===
    supplier_payment_terms_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for supplier payment terms in days (1.0 = normal, 0.5 = half payment terms) - HINWEIS: Aktuell werden Zahlungsziele nur angezeigt, Zahlung erfolgt sofort'
    )
    supplier_delivery_time_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for supplier delivery time in days (1.0 = normal, 2.0 = double delivery time) - HINWEIS: Aktuell werden Lieferzeiten nur angezeigt, Lieferung erfolgt sofort'
    )
    supplier_complaint_probability_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for supplier complaint probability (1.0 = normal, 0.5 = fewer complaints)'
    )
    supplier_complaint_quantity_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for quantity of defective components (1.0 = normal)'
    )
    component_cost_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for component costs from suppliers (1.0 = normal, 1.5 = 50% more expensive)'
    )

    # === BIKE PARAMETERS (from fahrraeder.xlsx) ===
    bike_skilled_worker_hours_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for skilled worker hours needed per bike (1.0 = normal, 0.8 = 20% faster)'
    )
    bike_unskilled_worker_hours_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for unskilled worker hours needed per bike (1.0 = normal, 0.8 = 20% faster)'
    )
    bike_storage_space_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for bike storage space requirements (1.0 = normal, 0.8 = 20% more compact)'
    )

    # === BIKE PRICE PARAMETERS (from preise_verkauf.xlsx) ===
    bike_price_cheap_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for cheap/budget bike segment base prices (1.0 = normal)'
    )
    bike_price_standard_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for standard bike segment base prices (1.0 = normal)'
    )
    bike_price_premium_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for premium bike segment base prices (1.0 = normal)'
    )

    # === WAREHOUSE PARAMETERS (from lager.xlsx) ===
    warehouse_cost_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for warehouse rental costs per month (1.0 = normal, 2.0 = double rent)'
    )
    warehouse_capacity_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for warehouse storage capacity (1.0 = normal, 1.5 = 50% more capacity)'
    )
    component_storage_space_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for component storage space requirements (1.0 = normal, 0.8 = 20% more compact)'
    )

    # === MARKET PARAMETERS (from maerkte.xlsx) ===
    market_demand_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for overall market demand (0.5 = 50% demand, 2.0 = 200% demand)'
    )
    market_distance_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for market distances (currently not used - transport costs are calculated from Excel distance data via transport_cost_multiplier)'
    )
    market_price_sensitivity_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for market price sensitivity (1.0 = normal, 1.5 = customers more price-sensitive)'
    )
    transport_cost_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for transport costs to markets (1.0 = normal, 1.5 = 50% more expensive)'
    )
    seasonal_effects_enabled = models.BooleanField(
        default=True,
        help_text='Enable seasonal demand fluctuations'
    )

    # === WORKER PARAMETERS (from personal.xlsx) ===
    worker_cost_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for worker wages (hourly wage, 1.0 = normal, 1.2 = 20% higher wages)'
    )
    worker_hours_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for available worker hours per month (1.0 = normal, 1.2 = 20% more hours)'
    )
    worker_productivity_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for worker productivity (1.0 = normal, 1.2 = 20% more productive)'
    )

    # === FINANCE PARAMETERS (from finanzen.xlsx) ===
    start_capital_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for starting capital (1.0 = normal, 1.5 = 50% more starting money)'
    )
    interest_rate = models.FloatField(
        default=0.05,
        help_text='Interest rate for loans (0.05 = 5% annual interest)'
    )
    loan_availability_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for maximum loan amounts available (1.0 = normal)'
    )
    other_costs_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for miscellaneous/overhead costs (currently applies to warehouse rent via warehouse_cost_multiplier - this parameter reserved for future use)'
    )
    inflation_rate = models.FloatField(
        default=0.02,
        help_text='Annual inflation rate affecting costs and prices (0.02 = 2%)'
    )

    # === COMPETITOR PARAMETERS (from konkurrenten.xlsx) ===
    competitor_aggressiveness = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(2.0)],
        help_text='How aggressive AI competitors are (0.1 = passive, 2.0 = very aggressive)'
    )
    competitor_financial_resources_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for competitor starting capital (1.0 = normal, 0.5 = weaker competitors)'
    )
    competitor_efficiency_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for competitor efficiency (1.0 = normal, 1.2 = competitors 20% more efficient)'
    )
    competitor_market_presence_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for competitor market share (1.0 = normal, 0.8 = competitors have less market share)'
    )
    competitor_marketing_budget_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiplier for competitor marketing budgets (1.0 = normal)'
    )

    # Advanced parameters (stored as JSON for flexibility)
    custom_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional custom parameters in JSON format'
    )

    # Audit fields
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modified_game_parameters'
    )
    last_modified_at = models.DateTimeField(auto_now=True)
    modification_history = models.JSONField(
        default=list,
        help_text='History of parameter changes'
    )

    def __str__(self):
        return f"Parameters for {self.multiplayer_game.name}"

    def log_change(self, user, field_name, old_value, new_value):
        """Log a parameter change to history"""
        from django.utils import timezone

        change_entry = {
            'timestamp': timezone.now().isoformat(),
            'user': user.username if user else 'System',
            'field': field_name,
            'old_value': str(old_value),
            'new_value': str(new_value)
        }

        if not isinstance(self.modification_history, list):
            self.modification_history = []

        self.modification_history.append(change_entry)
        self.save()
