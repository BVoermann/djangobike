"""
Management command to fix BikeComponents GmbH having no components in existing games.

This adds SupplierPrice entries for BikeComponents GmbH based on its quality level.

Usage:
    python manage.py fix_supplier_components [--game-id GAME_ID] [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from multiplayer.models import MultiplayerGame, PlayerSession
from multiplayer.player_state_manager import PlayerStateManager
from bikeshop.models import Supplier, SupplierPrice, Component


class Command(BaseCommand):
    help = 'Fix BikeComponents GmbH having no components in existing games'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=str,
            help='Specific game ID to fix (default: all games)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        game_id = options.get('game_id')
        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        if game_id:
            # Fix specific game
            try:
                game = MultiplayerGame.objects.get(id=game_id)
                self.stdout.write(f"\nProcessing game: {game.name}")
                self.fix_game_suppliers(game, dry_run)
            except MultiplayerGame.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Game with ID {game_id} not found"))
                return
        else:
            # Fix all games
            games = MultiplayerGame.objects.all()
            self.stdout.write(f"Processing {games.count()} games...\n")

            for game in games:
                self.stdout.write(f"\n{game.name} ({game.status}):")
                self.fix_game_suppliers(game, dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS('\nSupplier fix complete!'))

    def fix_game_suppliers(self, game, dry_run=False):
        """Fix suppliers for all players in a game."""
        players = PlayerSession.objects.filter(multiplayer_game=game)
        state_mgr = PlayerStateManager(game)

        suppliers_fixed = 0

        for player in players:
            try:
                # Get game session
                game_session = state_mgr.get_player_game_session(player)

                # Check BikeComponents GmbH
                bike_components = Supplier.objects.filter(
                    session=game_session,
                    name="BikeComponents GmbH"
                ).first()

                if not bike_components:
                    continue

                # Check if it already has components
                existing_prices = SupplierPrice.objects.filter(
                    session=game_session,
                    supplier=bike_components
                ).count()

                if existing_prices > 0:
                    self.stdout.write(
                        f"  {player.company_name}: BikeComponents GmbH already has {existing_prices} components"
                    )
                    continue

                # BikeComponents GmbH has no components - fix it!
                all_components = Component.objects.filter(session=game_session)
                components_to_add = all_components.count()

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  {player.company_name}: Would add {components_to_add} components "
                            f"to BikeComponents GmbH ({bike_components.get_quality_display()} quality)"
                        )
                    )
                else:
                    # Add SupplierPrice entries for all components
                    added = 0
                    for component in all_components:
                        # Check if this component has price data we can use
                        # Get a sample price from another supplier with same quality
                        sample_price = SupplierPrice.objects.filter(
                            session=game_session,
                            component=component
                        ).first()

                        if sample_price:
                            # Create SupplierPrice for BikeComponents GmbH
                            # Use the base_price from a supplier with matching quality
                            matching_price = SupplierPrice.objects.filter(
                                session=game_session,
                                component=component,
                                supplier__quality=bike_components.quality
                            ).first()

                            if matching_price:
                                SupplierPrice.objects.create(
                                    session=game_session,
                                    supplier=bike_components,
                                    component=component,
                                    base_price=matching_price.base_price
                                )
                                added += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {player.company_name}: Added {added} components to BikeComponents GmbH"
                        )
                    )
                    suppliers_fixed += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {player.company_name}: Error - {str(e)}"
                    )
                )

        # Summary
        if suppliers_fixed > 0:
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Fixed BikeComponents GmbH for {suppliers_fixed} player(s)"
                    )
                )
