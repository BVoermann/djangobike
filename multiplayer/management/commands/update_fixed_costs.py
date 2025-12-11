"""
Management command to update fixed costs in existing multiplayer games.

This command reduces warehouse rents and worker wages to the new balanced values.

Usage:
    python manage.py update_fixed_costs [--game-id GAME_ID] [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from multiplayer.models import MultiplayerGame, PlayerSession
from multiplayer.player_state_manager import PlayerStateManager
from bikeshop.models import Worker
from warehouse.models import Warehouse


class Command(BaseCommand):
    help = 'Update fixed costs (warehouse rent, worker wages) in existing games'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=str,
            help='Specific game ID to update (default: all games)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        game_id = options.get('game_id')
        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        if game_id:
            # Update specific game
            try:
                game = MultiplayerGame.objects.get(id=game_id)
                self.stdout.write(f"\nProcessing game: {game.name}")
                self.update_game_costs(game, dry_run)
            except MultiplayerGame.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Game with ID {game_id} not found"))
                return
        else:
            # Update all games
            games = MultiplayerGame.objects.all()
            self.stdout.write(f"Processing {games.count()} games...\n")

            for game in games:
                self.stdout.write(f"\n{game.name} ({game.status}):")
                self.update_game_costs(game, dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS('\nFixed cost update complete!'))

    def update_game_costs(self, game, dry_run=False):
        """Update costs for all players in a game."""
        players = PlayerSession.objects.filter(multiplayer_game=game)
        state_mgr = PlayerStateManager(game)

        warehouses_updated = 0
        workers_updated = 0

        for player in players:
            try:
                # Get game session
                game_session = state_mgr.get_player_game_session(player)

                # Update warehouses
                warehouses = Warehouse.objects.filter(session=game_session)
                for warehouse in warehouses:
                    old_rent = warehouse.rent_per_month

                    # Calculate new rent (40% reduction)
                    # Map old rents to new rents
                    new_rent_map = {
                        Decimal('1500.00'): Decimal('900.00'),   # Klein
                        Decimal('2000.00'): Decimal('1200.00'),  # Mittel (Main Warehouse)
                        Decimal('4000.00'): Decimal('2400.00'),  # Groß
                        Decimal('7000.00'): Decimal('4200.00'),  # Sehr Groß
                    }

                    # Find matching new rent or calculate 40% reduction
                    new_rent = new_rent_map.get(old_rent, old_rent * Decimal('0.6'))

                    if old_rent != new_rent:
                        if dry_run:
                            self.stdout.write(
                                f"  Would update {warehouse.name}: {old_rent}€ → {new_rent}€"
                            )
                        else:
                            warehouse.rent_per_month = new_rent
                            warehouse.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Updated {warehouse.name}: {old_rent}€ → {new_rent}€"
                                )
                            )
                        warehouses_updated += 1

                # Update workers
                workers = Worker.objects.filter(session=game_session)
                for worker in workers:
                    old_wage = worker.hourly_wage

                    # Calculate new wage based on worker type
                    if worker.worker_type == 'skilled':
                        # 28% reduction: 25€ → 18€
                        if old_wage == Decimal('25.00'):
                            new_wage = Decimal('18.00')
                        else:
                            new_wage = old_wage * Decimal('0.72')
                    elif worker.worker_type == 'unskilled':
                        # 20% reduction: 15€ → 12€
                        if old_wage == Decimal('15.00'):
                            new_wage = Decimal('12.00')
                        else:
                            new_wage = old_wage * Decimal('0.80')
                    else:
                        new_wage = old_wage

                    if old_wage != new_wage:
                        old_monthly = old_wage * worker.monthly_hours
                        new_monthly = new_wage * worker.monthly_hours

                        if dry_run:
                            self.stdout.write(
                                f"  Would update {worker.get_worker_type_display()}: "
                                f"{old_wage}€/h ({old_monthly}€/mo) → "
                                f"{new_wage}€/h ({new_monthly}€/mo)"
                            )
                        else:
                            worker.hourly_wage = new_wage
                            worker.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Updated {worker.get_worker_type_display()}: "
                                    f"{old_wage}€/h → {new_wage}€/h "
                                    f"({old_monthly}€/mo → {new_monthly}€/mo)"
                                )
                            )
                        workers_updated += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {player.company_name}: Error - {str(e)}"
                    )
                )

        # Summary for this game
        if warehouses_updated > 0 or workers_updated > 0:
            if dry_run:
                self.stdout.write(
                    f"  Would update: {warehouses_updated} warehouses, {workers_updated} workers"
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Updated: {warehouses_updated} warehouses, {workers_updated} workers"
                    )
                )
        else:
            self.stdout.write("  No updates needed - costs already at new values")
