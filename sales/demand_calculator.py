"""
Demand Calculator for Sales

Calculates actual and estimated market demand for bikes.
Handles market research precision to provide better estimates to players.
"""

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random


class DemandCalculator:
    """Calculate market demand with research-based precision."""

    def __init__(self, session):
        self.session = session

    def calculate_actual_demand(self, market, bike_type, month, year):
        """
        Calculate the actual monthly demand for a bike type in a market.

        This is the "true" demand that players don't see directly.

        Args:
            market: Market object
            bike_type: BikeType object
            month: Current month
            year: Current year

        Returns:
            int: Actual monthly demand in bikes
        """
        from .models import MarketDemand

        # Get base demand from MarketDemand model
        try:
            market_demand = MarketDemand.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type
            )
            demand_percentage = market_demand.demand_percentage
        except MarketDemand.DoesNotExist:
            # Default to equal distribution if not configured
            from bikeshop.models import BikeType
            bike_types_count = BikeType.objects.filter(session=self.session).count()
            demand_percentage = 100.0 / bike_types_count if bike_types_count > 0 else 0

        # Calculate base demand from market capacity
        base_demand = int(market.monthly_volume_capacity * (demand_percentage / 100.0))

        # Apply location-based modifiers
        location_modifier = self._get_location_modifier(market, bike_type)
        actual_demand = int(base_demand * location_modifier)

        # Add seasonal variation (±15%)
        seasonal_modifier = self._get_seasonal_modifier(month)
        actual_demand = int(actual_demand * seasonal_modifier)

        # Add some randomness (±10%) to keep it interesting
        random_modifier = random.uniform(0.90, 1.10)
        actual_demand = int(actual_demand * random_modifier)

        return max(0, actual_demand)

    def get_demand_estimate(self, market, bike_type, month, year):
        """
        Get demand estimate for a player based on their market research.

        Args:
            market: Market object
            bike_type: BikeType object
            month: Current month
            year: Current year

        Returns:
            dict: {
                'actual': int,  # Hidden from player
                'estimated_min': int,
                'estimated_max': int,
                'research_level': str,
                'precision': float
            }
        """
        from .models_market_research import MarketResearch

        # Calculate actual demand
        actual_demand = self.calculate_actual_demand(market, bike_type, month, year)

        # Check if player has research for this market/bike combination
        try:
            research = MarketResearch.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type
            )

            # Check if research is expired
            if research.is_expired():
                # Research expired - use default estimates
                estimated_min, estimated_max = MarketResearch.get_default_estimates(actual_demand)
                research_level = 'none'
                precision = MarketResearch.RESEARCH_PRECISION['none']
            else:
                # Use research-based estimates
                estimated_min, estimated_max = research.calculate_estimates(actual_demand)
                research_level = research.research_level
                precision = research.get_precision_modifier()

        except MarketResearch.DoesNotExist:
            # No research - use default (very wide) estimates
            estimated_min, estimated_max = MarketResearch.get_default_estimates(actual_demand)
            research_level = 'none'
            precision = MarketResearch.RESEARCH_PRECISION['none']

        return {
            'actual': actual_demand,  # Hidden from player in UI
            'estimated_min': estimated_min,
            'estimated_max': estimated_max,
            'research_level': research_level,
            'precision': precision,
            'precision_percentage': int(precision * 100)
        }

    def get_all_market_estimates(self, month, year):
        """
        Get demand estimates for all markets and bike types.

        Returns:
            dict: Nested dict of estimates by market and bike type
        """
        from .models import Market
        from bikeshop.models import BikeType

        markets = Market.objects.filter(session=self.session)
        bike_types = BikeType.objects.filter(session=self.session)

        estimates = {}

        for market in markets:
            estimates[market.id] = {
                'market': market,
                'bike_types': {}
            }

            for bike_type in bike_types:
                estimate = self.get_demand_estimate(market, bike_type, month, year)
                estimates[market.id]['bike_types'][bike_type.id] = {
                    'bike_type': bike_type,
                    **estimate
                }

        return estimates

    def _get_location_modifier(self, market, bike_type):
        """Calculate demand modifier based on location and bike type."""
        bike_name = bike_type.name.lower()

        # E-bikes benefit from green cities
        if 'e-' in bike_name or 'ebike' in bike_name:
            return market.green_city_factor

        # Mountain bikes benefit from mountainous areas
        if 'mountain' in bike_name or 'mtb' in bike_name:
            return market.mountain_bike_factor

        # Road/racing bikes
        if 'renn' in bike_name or 'road' in bike_name or 'racing' in bike_name:
            return market.road_bike_factor

        # City/commuter bikes
        if any(word in bike_name for word in ['damen', 'herren', 'city', 'commuter']):
            return market.city_bike_factor

        # Default
        return 1.0

    def _get_seasonal_modifier(self, month):
        """Calculate seasonal demand modifier."""
        # Higher demand in spring/summer (months 3-9)
        # Lower demand in fall/winter (months 10-12, 1-2)

        seasonal_factors = {
            1: 0.85,   # January - low
            2: 0.90,   # February - low
            3: 1.05,   # March - rising
            4: 1.15,   # April - high
            5: 1.20,   # May - peak
            6: 1.15,   # June - high
            7: 1.10,   # July - good
            8: 1.05,   # August - good
            9: 1.00,   # September - neutral
            10: 0.95,  # October - declining
            11: 0.90,  # November - low
            12: 0.85,  # December - low
        }

        return seasonal_factors.get(month, 1.0)


def purchase_market_research(session, market, bike_type, research_level, current_month, current_year):
    """
    Purchase market research for a specific market and bike type.

    Args:
        session: GameSession object
        market: Market object
        bike_type: BikeType object
        research_level: 'basic', 'advanced', or 'premium'
        current_month: Current game month
        current_year: Current game year

    Returns:
        tuple: (MarketResearch object, cost)

    Raises:
        ValueError: If research_level is invalid or player can't afford it
    """
    from .models_market_research import MarketResearch, MarketResearchTransaction
    from multiplayer.balance_manager import BalanceManager

    # Get cost
    cost = MarketResearch.get_research_cost(research_level)
    if cost == 0:
        raise ValueError(f"Invalid research level: {research_level}")

    # Check if player can afford it
    if session.balance < cost:
        raise ValueError(f"Insufficient funds. Cost: {cost}€, Balance: {session.balance}€")

    # Calculate expiration (research lasts 3 months)
    expires_at = timezone.now() + timedelta(days=90)

    # Calculate actual demand for this market/bike
    calculator = DemandCalculator(session)
    actual_demand = calculator.calculate_actual_demand(market, bike_type, current_month, current_year)

    # Create or update research
    research, created = MarketResearch.objects.update_or_create(
        session=session,
        market=market,
        bike_type=bike_type,
        defaults={
            'research_level': research_level,
            'invested_amount': cost,
            'expires_at': expires_at,
            'actual_demand': actual_demand,
        }
    )

    # Calculate and store estimates
    estimated_min, estimated_max = research.calculate_estimates(actual_demand)
    research.estimated_min = estimated_min
    research.estimated_max = estimated_max
    research.save()

    # Deduct cost from balance
    # Check if this is a multiplayer session
    if hasattr(session, 'multiplayer_game') and session.multiplayer_game:
        # Multiplayer - use BalanceManager
        from multiplayer.models import PlayerSession
        player_session = PlayerSession.objects.filter(
            multiplayer_game=session.multiplayer_game,
            user=session.user
        ).first()

        if player_session:
            balance_mgr = BalanceManager(player_session, session)
            balance_mgr.subtract_from_balance(cost, reason=f"market_research_{research_level}")
    else:
        # Singleplayer - direct balance update
        session.balance -= cost
        session.save()

    # Record transaction
    MarketResearchTransaction.objects.create(
        session=session,
        market_research=research,
        amount=cost,
        research_level=research_level,
        month=current_month,
        year=current_year
    )

    return research, cost
