from django.db import models
from django.contrib.auth.models import User
from bikeshop.models import GameSession
from decimal import Decimal
from django.utils import timezone
import json


class GameMode(models.Model):
    """Different game modes with different objectives"""
    
    MODE_TYPES = [
        ('profit_maximization', 'Gewinnmaximierung'),
        ('market_dominance', 'Marktdominanz'),
        ('survival', 'Überleben'),
        ('growth_focused', 'Wachstumsorientiert'),
        ('balanced_scorecard', 'Balanced Scorecard'),
        ('time_challenge', 'Zeitherausforderung'),
        ('efficiency_master', 'Effizienz-Meister'),
    ]
    
    name = models.CharField(max_length=100)
    mode_type = models.CharField(max_length=30, choices=MODE_TYPES)
    description = models.TextField()
    
    # Game settings
    duration_months = models.IntegerField(default=24, help_text="Game duration in months")
    starting_balance = models.DecimalField(max_digits=12, decimal_places=2, default=80000.00)
    bankruptcy_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=-10000.00)
    
    # Victory conditions configuration
    victory_conditions = models.JSONField(
        default=dict,
        help_text="JSON configuration for victory conditions"
    )
    
    # Difficulty settings
    difficulty_multipliers = models.JSONField(
        default=dict,
        help_text="Multipliers for costs, prices, competition intensity, etc."
    )
    
    is_active = models.BooleanField(default=True)
    is_multiplayer_compatible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_mode_type_display()})"


class GameObjective(models.Model):
    """Individual objectives within a game mode"""
    
    OBJECTIVE_TYPES = [
        ('profit_total', 'Gesamtgewinn erreichen'),
        ('profit_monthly', 'Monatlicher Gewinn'),
        ('revenue_total', 'Gesamtumsatz'),
        ('revenue_monthly', 'Monatlicher Umsatz'),
        ('market_share', 'Marktanteil'),
        ('bikes_produced', 'Fahrräder produziert'),
        ('bikes_sold', 'Fahrräder verkauft'),
        ('quality_rating', 'Qualitätsbewertung'),
        ('efficiency_score', 'Effizienz-Score'),
        ('customer_satisfaction', 'Kundenzufriedenheit'),
        ('balance_minimum', 'Mindest-Kontostand'),
        ('inventory_turnover', 'Lagerumschlag'),
        ('cost_per_unit', 'Kosten pro Einheit'),
        ('sustainability_score', 'Nachhaltigkeits-Score'),
    ]
    
    COMPARISON_OPERATORS = [
        ('gte', 'Größer oder gleich'),
        ('lte', 'Kleiner oder gleich'),
        ('eq', 'Gleich'),
        ('gt', 'Größer als'),
        ('lt', 'Kleiner als'),
    ]
    
    game_mode = models.ForeignKey(GameMode, on_delete=models.CASCADE, related_name='objectives')
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    objective_type = models.CharField(max_length=30, choices=OBJECTIVE_TYPES)
    
    # Target values
    target_value = models.DecimalField(max_digits=15, decimal_places=2)
    comparison_operator = models.CharField(max_length=5, choices=COMPARISON_OPERATORS, default='gte')
    
    # Objective importance
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Weight for scoring")
    is_primary = models.BooleanField(default=False, help_text="Primary objectives must be met for victory")
    is_failure_condition = models.BooleanField(default=False, help_text="Failing this causes immediate game over")
    
    # Timing
    evaluation_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monatlich'),
            ('quarterly', 'Quartalsweise'),
            ('end_game', 'Spielende'),
            ('continuous', 'Kontinuierlich')
        ],
        default='end_game'
    )
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['game_mode', 'order', 'name']
    
    def __str__(self):
        return f"{self.game_mode.name}: {self.name}"
    
    def evaluate(self, session):
        """Evaluate this objective for a given session"""
        current_value = self.get_current_value(session)
        target = float(self.target_value)
        
        if self.comparison_operator == 'gte':
            return current_value >= target
        elif self.comparison_operator == 'lte':
            return current_value <= target
        elif self.comparison_operator == 'eq':
            return abs(current_value - target) < 0.01  # Allow small floating point differences
        elif self.comparison_operator == 'gt':
            return current_value > target
        elif self.comparison_operator == 'lt':
            return current_value < target
        
        return False
    
    def get_current_value(self, session):
        """Get the current value for this objective type"""
        from sales.models import SalesOrder
        from production.models import ProducedBike
        from competitors.models import CompetitorSale
        from django.db.models import Sum, Avg, Count
        
        if self.objective_type == 'profit_total':
            return self.calculate_total_profit(session)
        
        elif self.objective_type == 'profit_monthly':
            return self.calculate_monthly_profit(session)
        
        elif self.objective_type == 'revenue_total':
            total_revenue = SalesOrder.objects.filter(
                session=session
            ).aggregate(total=Sum('sale_price'))['total'] or 0
            return float(total_revenue)
        
        elif self.objective_type == 'revenue_monthly':
            monthly_revenue = SalesOrder.objects.filter(
                session=session,
                sale_month=session.current_month,
                sale_year=session.current_year
            ).aggregate(total=Sum('sale_price'))['total'] or 0
            return float(monthly_revenue)
        
        elif self.objective_type == 'market_share':
            return self.calculate_market_share(session)
        
        elif self.objective_type == 'bikes_produced':
            produced = ProducedBike.objects.filter(session=session).count()
            return float(produced)
        
        elif self.objective_type == 'bikes_sold':
            sold = SalesOrder.objects.filter(session=session).count()
            return float(sold)
        
        elif self.objective_type == 'quality_rating':
            # Since there's no quality score field, calculate based on price segment
            total_bikes = ProducedBike.objects.filter(session=session).count()
            if total_bikes == 0:
                return 0.0
            
            premium_bikes = ProducedBike.objects.filter(session=session, price_segment='premium').count()
            standard_bikes = ProducedBike.objects.filter(session=session, price_segment='standard').count()
            cheap_bikes = ProducedBike.objects.filter(session=session, price_segment='cheap').count()
            
            # Calculate weighted quality score (premium=10, standard=7, cheap=4)
            if total_bikes > 0:
                quality_score = (premium_bikes * 10 + standard_bikes * 7 + cheap_bikes * 4) / total_bikes
                return float(quality_score)
            return 0.0
        
        elif self.objective_type == 'balance_minimum':
            return float(session.balance)
        
        elif self.objective_type == 'efficiency_score':
            return self.calculate_efficiency_score(session)
        
        elif self.objective_type == 'inventory_turnover':
            return self.calculate_inventory_turnover(session)
        
        elif self.objective_type == 'cost_per_unit':
            return self.calculate_cost_per_unit(session)
        
        # Default return
        return 0.0
    
    def calculate_total_profit(self, session):
        """Calculate total profit (revenue - costs)"""
        from sales.models import SalesOrder
        from procurement.models import ProcurementOrder
        from django.db.models import Sum
        
        total_revenue = SalesOrder.objects.filter(session=session).aggregate(
            total=Sum('sale_price')
        )['total'] or 0
        
        total_procurement_cost = ProcurementOrder.objects.filter(session=session).aggregate(
            total=Sum('total_cost')
        )['total'] or 0
        
        return float(total_revenue - total_procurement_cost)
    
    def calculate_monthly_profit(self, session):
        """Calculate profit for current month"""
        from sales.models import SalesOrder
        from procurement.models import ProcurementOrder
        from django.db.models import Sum
        
        monthly_revenue = SalesOrder.objects.filter(
            session=session,
            sale_month=session.current_month,
            sale_year=session.current_year
        ).aggregate(total=Sum('sale_price'))['total'] or 0
        
        monthly_costs = ProcurementOrder.objects.filter(
            session=session,
            order_month=session.current_month,
            order_year=session.current_year
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        return float(monthly_revenue - monthly_costs)
    
    def calculate_market_share(self, session):
        """Calculate market share percentage"""
        from sales.models import SalesOrder
        from competitors.models import CompetitorSale
        from django.db.models import Sum
        
        player_sales = SalesOrder.objects.filter(session=session).count()
        
        competitor_sales = CompetitorSale.objects.filter(
            competitor__session=session
        ).aggregate(total=Sum('quantity_sold'))['total'] or 0
        
        total_market = player_sales + competitor_sales
        
        if total_market > 0:
            return (float(player_sales) / float(total_market)) * 100
        return 0.0
    
    def calculate_efficiency_score(self, session):
        """Calculate efficiency score based on profit per unit produced"""
        from production.models import ProducedBike
        
        total_profit = self.calculate_total_profit(session)
        bikes_produced = ProducedBike.objects.filter(session=session).count()
        
        if bikes_produced > 0:
            return total_profit / bikes_produced
        return 0.0
    
    def calculate_inventory_turnover(self, session):
        """Calculate inventory turnover ratio"""
        from warehouse.models import StockLevel
        from sales.models import SalesOrder
        from django.db.models import Avg, Sum
        
        avg_inventory_value = StockLevel.objects.filter(session=session).aggregate(
            avg=Avg('quantity')
        )['avg'] or 1
        
        cost_of_goods_sold = SalesOrder.objects.filter(session=session).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        if avg_inventory_value > 0:
            return float(cost_of_goods_sold) / float(avg_inventory_value)
        return 0.0
    
    def calculate_cost_per_unit(self, session):
        """Calculate average cost per bike produced"""
        from production.models import ProducedBike, ProductionCost
        from django.db.models import Sum
        
        total_cost = ProductionCost.objects.filter(session=session).aggregate(
            total=Sum('total_cost')
        )['total'] or 0
        
        bikes_produced = ProducedBike.objects.filter(session=session).count()
        
        if bikes_produced > 0:
            return float(total_cost) / bikes_produced
        return 0.0


class SessionGameMode(models.Model):
    """Assigns a game mode to a session and tracks progress"""
    
    session = models.OneToOneField(GameSession, on_delete=models.CASCADE, related_name='game_mode_config')
    game_mode = models.ForeignKey(GameMode, on_delete=models.CASCADE)
    
    # Game state
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    
    # Results
    final_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    objective_progress = models.JSONField(default=dict, help_text="Progress on each objective")
    monthly_scores = models.JSONField(default=list, help_text="Score history by month")
    
    class Meta:
        verbose_name = "Session Game Mode"
        verbose_name_plural = "Session Game Modes"
    
    def __str__(self):
        return f"{self.session.name} - {self.game_mode.name}"
    
    def check_victory_conditions(self):
        """Check if victory conditions are met"""
        if self.is_completed or self.is_failed:
            return
        
        # Check if game duration exceeded
        if self.session.current_month > self.game_mode.duration_months:
            self.complete_game()
            return
        
        # Check bankruptcy
        if self.session.balance < self.game_mode.bankruptcy_threshold:
            self.fail_game("Bankrott")
            return
        
        # Check failure conditions
        for objective in self.game_mode.objectives.filter(is_failure_condition=True, is_active=True):
            if not objective.evaluate(self.session):
                self.fail_game(f"Fehlschlag bei: {objective.name}")
                return
        
        # Check victory conditions (all primary objectives must be met)
        primary_objectives = self.game_mode.objectives.filter(is_primary=True, is_active=True)
        if primary_objectives.exists():
            all_primary_met = all(obj.evaluate(self.session) for obj in primary_objectives)
            if all_primary_met:
                self.complete_game()
                return
    
    def complete_game(self):
        """Mark game as completed and calculate final score"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.final_score = self.calculate_final_score()
        self.completion_percentage = self.calculate_completion_percentage()
        self.save()
        
        # Create game result
        GameResult.objects.create(
            session_game_mode=self,
            result_type='victory',
            final_score=self.final_score,
            completion_percentage=self.completion_percentage,
            summary=self.generate_victory_summary()
        )
    
    def fail_game(self, reason):
        """Mark game as failed"""
        self.is_failed = True
        self.is_active = False
        self.completed_at = timezone.now()
        self.final_score = self.calculate_final_score()
        self.completion_percentage = self.calculate_completion_percentage()
        self.save()
        
        # Create game result
        GameResult.objects.create(
            session_game_mode=self,
            result_type='defeat',
            final_score=self.final_score,
            completion_percentage=self.completion_percentage,
            summary=f"Spiel beendet: {reason}",
            failure_reason=reason
        )
    
    def calculate_final_score(self):
        """Calculate weighted final score based on objectives"""
        total_score = Decimal('0.0')
        total_weight = Decimal('0.0')
        
        for objective in self.game_mode.objectives.filter(is_active=True):
            current_value = objective.get_current_value(self.session)
            target_value = float(objective.target_value)
            
            # Calculate achievement percentage
            if target_value > 0:
                achievement_pct = min(current_value / target_value, 2.0)  # Cap at 200%
            else:
                achievement_pct = 1.0 if objective.evaluate(self.session) else 0.0
            
            weighted_score = Decimal(str(achievement_pct)) * objective.weight
            total_score += weighted_score
            total_weight += objective.weight
        
        if total_weight > 0:
            return (total_score / total_weight) * Decimal('100.0')
        return Decimal('0.0')
    
    def calculate_completion_percentage(self):
        """Calculate percentage of objectives completed"""
        objectives = self.game_mode.objectives.filter(is_active=True)
        if not objectives.exists():
            return Decimal('100.0')
        
        completed = sum(1 for obj in objectives if obj.evaluate(self.session))
        return Decimal(str(completed)) / Decimal(str(objectives.count())) * Decimal('100.0')
    
    def generate_victory_summary(self):
        """Generate a summary of the victory"""
        summary_parts = []
        
        for objective in self.game_mode.objectives.filter(is_primary=True, is_active=True):
            current = objective.get_current_value(self.session)
            target = float(objective.target_value)
            summary_parts.append(f"{objective.name}: {current:.2f} (Ziel: {target:.2f})")
        
        return "Gratulation! Alle Hauptziele erreicht:\n" + "\n".join(summary_parts)
    
    def update_monthly_progress(self):
        """Update progress tracking for the current month"""
        current_progress = {}
        
        for objective in self.game_mode.objectives.filter(is_active=True):
            current_value = objective.get_current_value(self.session)
            target_value = float(objective.target_value)
            is_met = objective.evaluate(self.session)
            
            current_progress[str(objective.id)] = {
                'name': objective.name,
                'current_value': current_value,
                'target_value': target_value,
                'is_met': is_met,
                'progress_percentage': min((current_value / target_value) * 100, 200) if target_value > 0 else (100 if is_met else 0)
            }
        
        self.objective_progress = current_progress
        
        # Add monthly score
        monthly_score = {
            'month': self.session.current_month,
            'year': self.session.current_year,
            'score': float(self.calculate_final_score()),
            'completion_pct': float(self.calculate_completion_percentage()),
            'balance': float(self.session.balance)
        }
        
        monthly_scores = self.monthly_scores or []
        monthly_scores.append(monthly_score)
        self.monthly_scores = monthly_scores
        
        self.save()


class GameResult(models.Model):
    """Final results and statistics for completed games"""
    
    RESULT_TYPES = [
        ('victory', 'Sieg'),
        ('defeat', 'Niederlage'),
        ('timeout', 'Zeitüberschreitung'),
        ('bankruptcy', 'Bankrott'),
        ('elimination', 'Eliminiert'),
    ]
    
    session_game_mode = models.OneToOneField(SessionGameMode, on_delete=models.CASCADE, related_name='result')
    
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES)
    final_score = models.DecimalField(max_digits=10, decimal_places=2)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Game statistics
    total_months_played = models.IntegerField()
    final_balance = models.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bikes_produced = models.IntegerField(default=0)
    bikes_sold = models.IntegerField(default=0)
    market_share_final = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Detailed results
    objective_results = models.JSONField(default=dict, help_text="Results for each objective")
    performance_metrics = models.JSONField(default=dict, help_text="Additional performance metrics")
    
    # Text summaries
    summary = models.TextField()
    failure_reason = models.CharField(max_length=200, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Rankings (for multiplayer)
    rank = models.IntegerField(null=True, blank=True)
    total_players = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-final_score', '-completion_percentage']
    
    def __str__(self):
        return f"{self.session_game_mode.session.name} - {self.get_result_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # First time saving
            self.calculate_statistics()
        super().save(*args, **kwargs)
    
    def calculate_statistics(self):
        """Calculate all game statistics"""
        session = self.session_game_mode.session
        
        self.total_months_played = session.current_month
        self.final_balance = session.balance
        
        # Calculate revenue and profit
        from sales.models import SalesOrder
        from procurement.models import ProcurementOrder
        from django.db.models import Sum
        
        self.total_revenue = SalesOrder.objects.filter(session=session).aggregate(
            total=Sum('sale_price')
        )['total'] or 0
        
        total_costs = ProcurementOrder.objects.filter(session=session).aggregate(
            total=Sum('total_cost')
        )['total'] or 0
        
        self.total_profit = self.total_revenue - total_costs
        
        # Calculate bikes
        from production.models import ProducedBike
        
        self.bikes_produced = ProducedBike.objects.filter(session=session).count()
        self.bikes_sold = SalesOrder.objects.filter(session=session).count()
        
        # Calculate market share
        from competitors.models import CompetitorSale
        
        competitor_sales = CompetitorSale.objects.filter(
            competitor__session=session
        ).aggregate(total=Sum('quantity_sold'))['total'] or 0
        
        total_market = self.bikes_sold + competitor_sales
        if total_market > 0:
            self.market_share_final = (Decimal(str(self.bikes_sold)) / Decimal(str(total_market))) * Decimal('100')
        
        # Generate recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate improvement recommendations based on performance"""
        recommendations = []
        
        if self.final_balance < 0:
            recommendations.append("Verbessern Sie Ihr Finanzmanagement - überwachen Sie die Liquidität genauer.")
        
        if self.market_share_final < 10:
            recommendations.append("Erhöhen Sie Ihren Marktanteil durch bessere Produktpositionierung oder Preisstrategien.")
        
        if self.bikes_sold > 0 and self.total_profit / self.bikes_sold < 100:
            recommendations.append("Optimieren Sie Ihre Gewinnmargen durch effizientere Produktion oder höhere Preise.")
        
        if self.bikes_produced > self.bikes_sold and (self.bikes_produced - self.bikes_sold) > self.bikes_produced * 0.2:
            recommendations.append("Reduzieren Sie Überproduktion - produzieren Sie nachfrageorientierter.")
        
        self.recommendations = "\n".join(recommendations) if recommendations else "Gute Leistung! Versuchen Sie, Ihre Strategien weiter zu verfeinern."


class BankruptcyEvent(models.Model):
    """Track bankruptcy events and elimination from games"""
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='bankruptcy_events')
    session_game_mode = models.ForeignKey(SessionGameMode, on_delete=models.CASCADE, null=True, blank=True)
    
    # Bankruptcy details
    balance_at_bankruptcy = models.DecimalField(max_digits=12, decimal_places=2)
    bankruptcy_threshold = models.DecimalField(max_digits=12, decimal_places=2)
    trigger_month = models.IntegerField()
    trigger_year = models.IntegerField()
    
    # Cause analysis
    primary_cause = models.CharField(
        max_length=50,
        choices=[
            ('excessive_spending', 'Übermäßige Ausgaben'),
            ('low_sales', 'Niedrige Verkäufe'),
            ('high_costs', 'Hohe Kosten'),
            ('market_downturn', 'Marktabschwung'),
            ('poor_planning', 'Schlechte Planung'),
            ('external_event', 'Externes Ereignis'),
            ('competition', 'Konkurrenz'),
        ]
    )
    
    contributing_factors = models.JSONField(default=list, help_text="List of contributing factors")
    
    # Recovery options (if any)
    recovery_attempted = models.BooleanField(default=False)
    recovery_successful = models.BooleanField(default=False)
    bailout_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Elimination
    player_eliminated = models.BooleanField(default=True)
    elimination_reason = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bankrott: {self.session.name} - Monat {self.trigger_month}/{self.trigger_year}"
