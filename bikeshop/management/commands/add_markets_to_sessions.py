#!/usr/bin/env python3
"""
Django management command to add markets to existing game sessions that don't have any markets yet.
This script finds all GameSession objects that don't have associated Market objects and creates
default markets based on the market data from the maerkte.xlsx template.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from bikeshop.models import GameSession, BikeType
from sales.models import Market, MarketDemand, MarketPriceSensitivity


class Command(BaseCommand):
    help = 'Adds markets to existing game sessions that don\'t have any markets yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Market data from create_default_xlsx_files.py
        market_locations = [
            {
                'name': 'Hamburg',
                'distance': 0,
                'transport_cost_per_km': 0.50
            },
            {
                'name': 'Berlin',
                'distance': 300,
                'transport_cost_per_km': 0.50
            },
            {
                'name': 'München',
                'distance': 600,
                'transport_cost_per_km': 0.50
            },
            {
                'name': 'Köln',
                'distance': 400,
                'transport_cost_per_km': 0.50
            },
            {
                'name': 'Frankfurt',
                'distance': 500,
                'transport_cost_per_km': 0.50
            }
        ]

        # Base demand per market and bike type (from create_default_xlsx_files.py)
        base_demand = {
            'Damenrad': 50,
            'Herrenrad': 45,
            'Mountainbike': 30,
            'Rennrad': 20,
            'E-Bike': 35,
            'E-Mountainbike': 25,
            'E-Mountain-Bike': 15
        }

        # Market size multipliers (from create_default_xlsx_files.py)
        market_multipliers = {
            'Hamburg': 1.0,
            'Berlin': 1.5,
            'München': 1.2,
            'Köln': 0.8,
            'Frankfurt': 0.9
        }

        # Price sensitivity (from create_default_xlsx_files.py)
        price_sensitivity = {
            'Damenrad': 0.8,
            'Herrenrad': 0.8,
            'Mountainbike': 0.6,
            'Rennrad': 0.6,
            'E-Bike': 0.4,
            'E-Mountainbike': 0.4,
            'E-Mountain-Bike': 0.3
        }

        # Find sessions without markets
        sessions_without_markets = []
        for session in GameSession.objects.all():
            market_count = Market.objects.filter(session=session).count()
            if market_count == 0:
                sessions_without_markets.append(session)

        if not sessions_without_markets:
            self.stdout.write(
                self.style.SUCCESS('All game sessions already have markets. Nothing to do.')
            )
            return

        self.stdout.write(
            f'Found {len(sessions_without_markets)} game sessions without markets:'
        )
        
        for session in sessions_without_markets:
            self.stdout.write(f'  - {session.name} (ID: {session.id})')

        if dry_run:
            self.stdout.write('\nWould create the following markets for each session:')
            for location in market_locations:
                transport_cost = location['distance'] * location['transport_cost_per_km']
                self.stdout.write(
                    f'  - {location["name"]}: distance {location["distance"]}km, '
                    f'home transport cost {transport_cost}€, '
                    f'foreign transport cost {transport_cost * 1.5}€'
                )
            return

        # Process each session
        created_markets_count = 0
        created_demands_count = 0
        created_sensitivities_count = 0

        for session in sessions_without_markets:
            self.stdout.write(f'\nProcessing session: {session.name}')
            
            try:
                with transaction.atomic():
                    # Create markets for this session
                    session_markets = {}
                    for location in market_locations:
                        distance = location['distance']
                        cost_per_km = location['transport_cost_per_km']
                        transport_cost = distance * cost_per_km
                        
                        market = Market.objects.create(
                            session=session,
                            name=location['name'],
                            location=location['name'],
                            transport_cost_home=transport_cost,
                            transport_cost_foreign=transport_cost * 1.5  # 50% higher for foreign markets
                        )
                        session_markets[location['name']] = market
                        created_markets_count += 1
                        
                        self.stdout.write(f'  Created market: {location["name"]}')

                    # Get bike types for this session
                    bike_types = BikeType.objects.filter(session=session)
                    
                    if not bike_types.exists():
                        self.stdout.write(
                            self.style.WARNING(f'  No bike types found for session {session.name}. Skipping demand/sensitivity creation.')
                        )
                        continue

                    # Create market demand for each market and bike type
                    for market_name, market in session_markets.items():
                        for bike_type in bike_types:
                            bike_name = bike_type.name
                            if bike_name in base_demand:
                                demand = int(base_demand[bike_name] * market_multipliers.get(market_name, 1.0))
                                
                                MarketDemand.objects.create(
                                    session=session,
                                    market=market,
                                    bike_type=bike_type,
                                    demand_percentage=demand
                                )
                                created_demands_count += 1

                    # Create price sensitivity for each market and bike type
                    for market_name, market in session_markets.items():
                        for bike_type in bike_types:
                            bike_name = bike_type.name
                            if bike_name in price_sensitivity:
                                sensitivity = price_sensitivity[bike_name]
                                
                                # Create sensitivity for each price segment
                                for segment in ['cheap', 'standard', 'premium']:
                                    MarketPriceSensitivity.objects.create(
                                        session=session,
                                        market=market,
                                        price_segment=segment,
                                        percentage=sensitivity
                                    )
                                    created_sensitivities_count += 1

                    self.stdout.write(f'  Created {len(session_markets)} markets, market demands, and price sensitivities')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing session {session.name}: {str(e)}')
                )
                raise CommandError(f'Failed to process session {session.name}: {str(e)}')

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully completed! Created:\n'
                f'  - {created_markets_count} markets\n'
                f'  - {created_demands_count} market demands\n'
                f'  - {created_sensitivities_count} price sensitivities\n'
                f'  - Processed {len(sessions_without_markets)} game sessions'
            )
        )