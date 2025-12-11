"""
Management command to synchronize player balances in multiplayer games.

Usage:
    python manage.py sync_multiplayer_balances [--game-id GAME_ID] [--check-only]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from multiplayer.models import MultiplayerGame, PlayerSession
from multiplayer.balance_manager import sync_all_player_balances, BalanceManager
from multiplayer.player_state_manager import PlayerStateManager


class Command(BaseCommand):
    help = 'Synchronize player balances across PlayerSession and GameSession'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=str,
            help='Specific game ID to sync (default: all games)',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check for mismatches, do not fix them',
        )

    def handle(self, *args, **options):
        game_id = options.get('game_id')
        check_only = options.get('check_only')

        if game_id:
            # Sync specific game
            try:
                game = MultiplayerGame.objects.get(id=game_id)
                self.stdout.write(f"Processing game: {game.name}")
                self.sync_game_balances(game, check_only)
            except MultiplayerGame.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Game with ID {game_id} not found"))
                return
        else:
            # Sync all games
            games = MultiplayerGame.objects.all()
            self.stdout.write(f"Processing {games.count()} games...")

            for game in games:
                self.stdout.write(f"\n{game.name} ({game.status}):")
                self.sync_game_balances(game, check_only)

        self.stdout.write(self.style.SUCCESS('\nBalance synchronization complete!'))

    def sync_game_balances(self, game, check_only=False):
        """Sync balances for all players in a game."""
        players = PlayerSession.objects.filter(multiplayer_game=game)
        state_mgr = PlayerStateManager(game)

        mismatches = 0
        synced = 0

        for player in players:
            try:
                # Get game session
                game_session = state_mgr.get_player_game_session(player)

                # Create balance manager
                balance_mgr = BalanceManager(player, game_session)

                # Check for mismatch
                had_mismatch, current_balance = balance_mgr.check_and_fix_balance_mismatch()

                if had_mismatch:
                    mismatches += 1
                    if check_only:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ✗ {player.company_name}: MISMATCH DETECTED "
                                f"(would fix to {current_balance}€)"
                            )
                        )
                    else:
                        synced += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ {player.company_name}: Fixed mismatch, "
                                f"balance now {current_balance}€"
                            )
                        )
                else:
                    self.stdout.write(
                        f"  ✓ {player.company_name}: Balance OK ({current_balance}€)"
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {player.company_name}: Error - {str(e)}"
                    )
                )

        # Summary
        if check_only:
            if mismatches > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Found {mismatches} mismatches (use without --check-only to fix)"
                    )
                )
            else:
                self.stdout.write("  All balances are synchronized")
        else:
            if synced > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  Fixed {synced} mismatches")
                )
            else:
                self.stdout.write("  All balances are synchronized")
