"""
Utility functions for applying game parameters to multiplayer sessions.

This module provides functions to retrieve and apply GameParameters multipliers
to various game mechanics.
"""

from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_game_parameters(session):
    """
    Get GameParameters for a given GameSession.

    Returns the GameParameters object if the session is part of a multiplayer game,
    otherwise returns None (for singleplayer games).

    Args:
        session: GameSession object

    Returns:
        GameParameters object or None
    """
    try:
        from multiplayer.models import GameParameters

        # Handle None case
        if session is None:
            return None

        # Use direct link from GameSession to MultiplayerGame (Fix for Issue #1)
        if not session.multiplayer_game:
            # This is a singleplayer session
            return None

        # Get GameParameters for this multiplayer game
        try:
            return GameParameters.objects.get(multiplayer_game=session.multiplayer_game)
        except GameParameters.DoesNotExist:
            logger.warning(f"No GameParameters found for game {session.multiplayer_game.name}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving game parameters: {e}")
        return None


def get_game_parameters_for_multiplayer_game(multiplayer_game):
    """
    Get GameParameters directly for a MultiplayerGame.

    Args:
        multiplayer_game: MultiplayerGame object

    Returns:
        GameParameters object or None
    """
    try:
        from multiplayer.models import GameParameters
        return GameParameters.objects.get(multiplayer_game=multiplayer_game)
    except GameParameters.DoesNotExist:
        logger.warning(f"No GameParameters found for game {multiplayer_game.name}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving game parameters: {e}")
        return None


def apply_worker_hours_multiplier(base_hours, session):
    """Apply worker hours multiplier from game parameters."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.worker_hours_multiplier)
        return base_hours * multiplier
    return base_hours


def apply_worker_cost_multiplier(base_wage, session):
    """Apply worker cost multiplier from game parameters."""
    params = get_game_parameters(session)
    if params:
        multiplier = Decimal(str(params.worker_cost_multiplier))
        return base_wage * multiplier
    return base_wage


def apply_worker_productivity_multiplier(base_hours, session):
    """Apply worker productivity multiplier (reduces hours needed)."""
    params = get_game_parameters(session)
    if params:
        # Higher productivity = fewer hours needed
        multiplier = float(params.worker_productivity_multiplier)
        return base_hours / multiplier
    return base_hours


def apply_supplier_payment_terms_multiplier(base_days, session):
    """Apply supplier payment terms multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.supplier_payment_terms_multiplier)
        return int(base_days * multiplier)
    return base_days


def apply_supplier_delivery_time_multiplier(base_days, session):
    """Apply supplier delivery time multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.supplier_delivery_time_multiplier)
        return int(base_days * multiplier)
    return base_days


def apply_supplier_complaint_probability_multiplier(base_probability, session):
    """Apply supplier complaint probability multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.supplier_complaint_probability_multiplier)
        return base_probability * multiplier
    return base_probability


def apply_supplier_complaint_quantity_multiplier(base_quantity, session):
    """Apply supplier complaint quantity multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.supplier_complaint_quantity_multiplier)
        return base_quantity * multiplier
    return base_quantity


def apply_component_cost_multiplier(base_price, session):
    """Apply component cost multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = Decimal(str(params.component_cost_multiplier))
        return base_price * multiplier
    return base_price


def apply_bike_skilled_worker_hours_multiplier(base_hours, session):
    """Apply bike skilled worker hours multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.bike_skilled_worker_hours_multiplier)
        return base_hours * multiplier
    return base_hours


def apply_bike_unskilled_worker_hours_multiplier(base_hours, session):
    """Apply bike unskilled worker hours multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.bike_unskilled_worker_hours_multiplier)
        return base_hours * multiplier
    return base_hours


def apply_bike_storage_space_multiplier(base_space, session):
    """Apply bike storage space multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.bike_storage_space_multiplier)
        return base_space * multiplier
    return base_space


def apply_bike_price_multiplier(base_price, price_segment, session):
    """Apply bike price multiplier based on segment."""
    params = get_game_parameters(session)
    if params:
        if price_segment == 'cheap':
            multiplier = Decimal(str(params.bike_price_cheap_multiplier))
        elif price_segment == 'standard':
            multiplier = Decimal(str(params.bike_price_standard_multiplier))
        elif price_segment == 'premium':
            multiplier = Decimal(str(params.bike_price_premium_multiplier))
        else:
            multiplier = Decimal('1.0')
        return base_price * multiplier
    return base_price


def apply_warehouse_cost_multiplier(base_cost, session):
    """Apply warehouse cost multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = Decimal(str(params.warehouse_cost_multiplier))
        return base_cost * multiplier
    return base_cost


def apply_warehouse_capacity_multiplier(base_capacity, session):
    """Apply warehouse capacity multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.warehouse_capacity_multiplier)
        return base_capacity * multiplier
    return base_capacity


def apply_component_storage_space_multiplier(base_space, session):
    """Apply component storage space multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.component_storage_space_multiplier)
        return base_space * multiplier
    return base_space


def apply_market_demand_multiplier(base_demand, session):
    """Apply market demand multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = float(params.market_demand_multiplier)
        return base_demand * multiplier
    return base_demand


def apply_transport_cost_multiplier(base_cost, session):
    """Apply transport cost multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = Decimal(str(params.transport_cost_multiplier))
        return base_cost * multiplier
    return base_cost


def apply_start_capital_multiplier(base_capital, session):
    """Apply start capital multiplier."""
    params = get_game_parameters(session)
    if params:
        multiplier = Decimal(str(params.start_capital_multiplier))
        return base_capital * multiplier
    return base_capital


def get_interest_rate(session):
    """Get interest rate from game parameters."""
    params = get_game_parameters(session)
    if params:
        return float(params.interest_rate)
    return 0.05  # Default 5%


def get_inflation_rate(session):
    """Get inflation rate from game parameters."""
    params = get_game_parameters(session)
    if params:
        return float(params.inflation_rate)
    return 0.02  # Default 2%


def are_seasonal_effects_enabled(session):
    """Check if seasonal effects are enabled."""
    params = get_game_parameters(session)
    if params:
        return params.seasonal_effects_enabled
    return True  # Default enabled
