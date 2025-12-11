"""
Management command to increase warehouse sizes for existing games.

This command updates warehouses that are still at the old default size (200 m²)
to the new default size (500 m²) for better gameplay experience.
"""

from django.core.management.base import BaseCommand
from warehouse.models import Warehouse
from decimal import Decimal


class Command(BaseCommand):
    help = 'Increase warehouse sizes from 200m² to 500m² for existing games'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--game-id',
            type=str,
            help='Only update warehouses for a specific game session ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        game_id = options.get('game_id')

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Warehouse Size Increase Utility'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # Build query
        warehouses_query = Warehouse.objects.filter(capacity_m2=200.0)

        if game_id:
            warehouses_query = warehouses_query.filter(session_id=game_id)
            self.stdout.write(f'Filtering for game session: {game_id}')

        warehouses = list(warehouses_query)

        if not warehouses:
            self.stdout.write(self.style.SUCCESS('✓ No warehouses found with 200m² capacity'))
            self.stdout.write(self.style.SUCCESS('  All warehouses are already at optimal size!'))
            return

        self.stdout.write(f'Found {len(warehouses)} warehouse(s) at 200m² that can be increased')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        # Process each warehouse
        updated_count = 0
        for warehouse in warehouses:
            old_capacity = warehouse.capacity_m2
            old_rent = warehouse.rent_per_month

            new_capacity = 500.0
            # Adjust rent proportionally: 200m² @ 1200€ → 500m² @ 2400€
            # But keep existing rent if it's custom
            if abs(float(old_rent) - 1200.0) < 0.01 or abs(float(old_rent) - 2500.0) < 0.01:
                new_rent = Decimal('2400.00')
            else:
                # Custom rent - scale proportionally
                new_rent = old_rent * Decimal(str(new_capacity / old_capacity))

            self.stdout.write(f'Warehouse: {warehouse.name} ({warehouse.session.name})')
            self.stdout.write(f'  Current: {old_capacity}m² @ {old_rent}€/month')
            self.stdout.write(f'  New:     {new_capacity}m² @ {new_rent}€/month')
            self.stdout.write(f'  Usage:   {warehouse.current_usage:.1f}m² ({warehouse.usage_percentage:.1f}%)')

            if not dry_run:
                warehouse.capacity_m2 = new_capacity
                warehouse.rent_per_month = new_rent
                warehouse.save()
                self.stdout.write(self.style.SUCCESS('  ✓ Updated!'))
                updated_count += 1
            else:
                self.stdout.write(self.style.WARNING('  → Would be updated'))

            self.stdout.write('')

        # Summary
        self.stdout.write(self.style.WARNING('=' * 70))
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would update {len(warehouses)} warehouse(s)'))
            self.stdout.write('')
            self.stdout.write('Run without --dry-run to apply changes:')
            if game_id:
                self.stdout.write(f'  python manage.py increase_warehouse_sizes --game-id {game_id}')
            else:
                self.stdout.write('  python manage.py increase_warehouse_sizes')
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully updated {updated_count} warehouse(s)'))
            self.stdout.write('')
            self.stdout.write('Changes applied:')
            self.stdout.write('  • Capacity increased from 200m² to 500m²')
            self.stdout.write('  • Rent adjusted to 2400€/month (or scaled proportionally)')
            self.stdout.write('  • All existing inventory preserved')

        self.stdout.write(self.style.WARNING('=' * 70))
