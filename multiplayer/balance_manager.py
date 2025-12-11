"""
Balance Manager for Multiplayer Games

This module provides centralized balance management to ensure that player balances
are always stored correctly and synchronized between PlayerSession and GameSession.

In multiplayer games:
- PlayerSession.balance is the SOURCE OF TRUTH
- GameSession.balance is synchronized for compatibility with existing singleplayer code
"""

from decimal import Decimal
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class BalanceManager:
    """Manages player balance in multiplayer games with proper synchronization."""

    def __init__(self, player_session, game_session=None):
        """
        Initialize balance manager.

        Args:
            player_session: PlayerSession object (multiplayer model)
            game_session: GameSession object (optional, will be fetched if needed)
        """
        self.player_session = player_session
        self._game_session = game_session

    @property
    def game_session(self):
        """Lazy load game session if needed."""
        if self._game_session is None:
            from .player_state_manager import PlayerStateManager
            state_mgr = PlayerStateManager(self.player_session.multiplayer_game)
            self._game_session = state_mgr.get_player_game_session(self.player_session)
        return self._game_session

    def get_balance(self):
        """
        Get current balance.
        Always returns PlayerSession.balance as source of truth.
        """
        self.player_session.refresh_from_db()
        return self.player_session.balance

    @transaction.atomic
    def set_balance(self, new_balance, reason="balance_update"):
        """
        Set balance to a specific value.
        Updates both PlayerSession and GameSession atomically.

        Args:
            new_balance: New balance value (Decimal)
            reason: Reason for balance change (for logging)
        """
        old_balance = self.player_session.balance
        new_balance = Decimal(str(new_balance))

        # Update PlayerSession (source of truth)
        self.player_session.balance = new_balance
        self.player_session.save(update_fields=['balance'])

        # Sync with GameSession
        if self.game_session:
            self.game_session.balance = new_balance
            self.game_session.save(update_fields=['balance'])

        logger.info(
            f"Balance updated for {self.player_session.company_name}: "
            f"{old_balance}€ -> {new_balance}€ (reason: {reason})"
        )

        return new_balance

    @transaction.atomic
    def add_to_balance(self, amount, reason="credit"):
        """
        Add amount to balance.

        Args:
            amount: Amount to add (positive for credit, negative for debit)
            reason: Reason for transaction (for logging)
        """
        amount = Decimal(str(amount))
        current_balance = self.get_balance()
        new_balance = current_balance + amount

        return self.set_balance(new_balance, reason=reason)

    @transaction.atomic
    def subtract_from_balance(self, amount, reason="debit"):
        """
        Subtract amount from balance.

        Args:
            amount: Amount to subtract (should be positive)
            reason: Reason for transaction (for logging)
        """
        amount = Decimal(str(amount))
        if amount < 0:
            raise ValueError("Amount to subtract must be positive")

        return self.add_to_balance(-amount, reason=reason)

    @transaction.atomic
    def sync_balances(self):
        """
        Force synchronization between PlayerSession and GameSession.
        Uses PlayerSession.balance as source of truth.
        """
        # PlayerSession is source of truth
        self.player_session.refresh_from_db()
        source_balance = self.player_session.balance

        # Update GameSession to match
        if self.game_session:
            self.game_session.balance = source_balance
            self.game_session.save(update_fields=['balance'])

            logger.info(
                f"Synchronized balance for {self.player_session.company_name}: "
                f"PlayerSession={source_balance}€"
            )

        return source_balance

    @transaction.atomic
    def check_and_fix_balance_mismatch(self):
        """
        Check for balance mismatch and fix if found.
        Returns tuple: (had_mismatch: bool, current_balance: Decimal)
        """
        self.player_session.refresh_from_db()
        player_balance = self.player_session.balance

        if self.game_session:
            self.game_session.refresh_from_db()
            session_balance = self.game_session.balance

            if player_balance != session_balance:
                logger.warning(
                    f"Balance mismatch detected for {self.player_session.company_name}: "
                    f"PlayerSession={player_balance}€, GameSession={session_balance}€. "
                    f"Fixing by using PlayerSession as source of truth."
                )

                # Fix by syncing
                self.game_session.balance = player_balance
                self.game_session.save(update_fields=['balance'])

                return (True, player_balance)

        return (False, player_balance)


def get_balance_manager(player_session, game_session=None):
    """
    Factory function to get a BalanceManager instance.

    Args:
        player_session: PlayerSession object
        game_session: Optional GameSession object

    Returns:
        BalanceManager instance
    """
    return BalanceManager(player_session, game_session)


def sync_all_player_balances(multiplayer_game):
    """
    Utility function to sync balances for all players in a game.
    Useful for fixing inconsistencies.

    Args:
        multiplayer_game: MultiplayerGame object
    """
    from .models import PlayerSession
    from .player_state_manager import PlayerStateManager

    players = PlayerSession.objects.filter(multiplayer_game=multiplayer_game)
    state_mgr = PlayerStateManager(multiplayer_game)

    fixed_count = 0
    for player in players:
        game_session = state_mgr.get_player_game_session(player)
        balance_mgr = BalanceManager(player, game_session)

        had_mismatch, current_balance = balance_mgr.check_and_fix_balance_mismatch()
        if had_mismatch:
            fixed_count += 1

    if fixed_count > 0:
        logger.info(f"Fixed balance mismatches for {fixed_count} players in game {multiplayer_game.name}")
    else:
        logger.info(f"All balances synchronized in game {multiplayer_game.name}")

    return fixed_count
