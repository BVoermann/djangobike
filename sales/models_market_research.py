"""
Market Research models for the sales app.

Players can invest in market research to get more accurate demand estimates.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid


class MarketResearch(models.Model):
    """
    Represents market research investment by a player for a specific market/bike combination.

    Research levels:
    - None (0€): Very wide range (±60% of actual demand)
    - Basic (500€): Medium range (±30% of actual demand)
    - Advanced (2000€): Narrow range (±15% of actual demand)
    - Premium (5000€): Precise range (±5% of actual demand)
    """

    RESEARCH_LEVEL_CHOICES = [
        ('none', 'No Research'),
        ('basic', 'Basic Research'),
        ('advanced', 'Advanced Research'),
        ('premium', 'Premium Research'),
    ]

    RESEARCH_COSTS = {
        'basic': Decimal('500.00'),
        'advanced': Decimal('2000.00'),
        'premium': Decimal('5000.00'),
    }

    RESEARCH_PRECISION = {
        'none': 0.60,      # ±60% range
        'basic': 0.30,     # ±30% range
        'advanced': 0.15,  # ±15% range
        'premium': 0.05,   # ±5% range
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to game session (multiplayer or singleplayer)
    session = models.ForeignKey(
        'bikeshop.GameSession',
        on_delete=models.CASCADE,
        related_name='market_research'
    )

    # What is being researched
    market = models.ForeignKey(
        'sales.Market',
        on_delete=models.CASCADE,
        related_name='research'
    )
    bike_type = models.ForeignKey(
        'bikeshop.BikeType',
        on_delete=models.CASCADE,
        related_name='market_research'
    )

    # Research details
    research_level = models.CharField(
        max_length=20,
        choices=RESEARCH_LEVEL_CHOICES,
        default='none'
    )
    invested_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Timestamps
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Research results (cached for performance)
    actual_demand = models.IntegerField(
        default=0,
        help_text="Actual monthly demand (hidden from player)"
    )
    estimated_min = models.IntegerField(
        default=0,
        help_text="Minimum estimated demand shown to player"
    )
    estimated_max = models.IntegerField(
        default=0,
        help_text="Maximum estimated demand shown to player"
    )

    class Meta:
        unique_together = ['session', 'market', 'bike_type']
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.research_level.title()} research: {self.market.name} - {self.bike_type.name}"

    def is_expired(self):
        """Check if research has expired."""
        return timezone.now() > self.expires_at

    def get_precision_modifier(self):
        """Get the precision modifier for this research level."""
        return self.RESEARCH_PRECISION.get(self.research_level, 0.60)

    def calculate_estimates(self, actual_demand):
        """
        Calculate min/max estimates based on research level.

        Args:
            actual_demand: The true monthly demand

        Returns:
            tuple: (estimated_min, estimated_max)
        """
        precision = self.get_precision_modifier()

        # Calculate range
        range_size = int(actual_demand * precision)

        # Add some randomness so it's not perfectly centered
        import random
        offset = random.randint(-range_size // 4, range_size // 4)

        estimated_min = max(0, actual_demand - range_size + offset)
        estimated_max = actual_demand + range_size + offset

        return estimated_min, estimated_max

    @classmethod
    def get_research_cost(cls, level):
        """Get the cost for a research level."""
        return cls.RESEARCH_COSTS.get(level, Decimal('0.00'))

    @classmethod
    def get_default_estimates(cls, actual_demand):
        """
        Get default estimates when no research has been purchased.
        Returns a very wide range (±60%).
        """
        precision = cls.RESEARCH_PRECISION['none']
        range_size = int(actual_demand * precision)

        estimated_min = max(0, actual_demand - range_size)
        estimated_max = actual_demand + range_size

        return estimated_min, estimated_max


class MarketResearchTransaction(models.Model):
    """Track market research purchases for accounting."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    session = models.ForeignKey(
        'bikeshop.GameSession',
        on_delete=models.CASCADE,
        related_name='research_transactions'
    )

    market_research = models.ForeignKey(
        MarketResearch,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    research_level = models.CharField(max_length=20)

    purchased_at = models.DateTimeField(auto_now_add=True)
    month = models.IntegerField()
    year = models.IntegerField()

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.research_level} research - {self.amount}€ ({self.month}/{self.year})"
