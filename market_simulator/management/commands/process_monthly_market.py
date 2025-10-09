from django.core.management.base import BaseCommand
from django.utils import timezone
from multiplayer.models import MultiplayerGame
from market_simulator.models import MarketConfiguration
from market_simulator.economic_cycle_engine import EconomicCycleEngine
from market_simulator.market_factors_engine import MarketFactorsEngine
from market_simulator.customer_demographics_engine import CustomerDemographicsEngine
from market_simulator.market_clearing_engine import MarketClearingEngine
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process monthly market clearing for all active multiplayer sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='Process specific multiplayer session ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the process without saving results'
        )

    def handle(self, *args, **options):
        try:
            if options['session_id']:
                sessions = MultiplayerGame.objects.filter(
                    id=options['session_id'],
                    status='active'
                )
                if not sessions.exists():
                    self.stdout.write(
                        self.style.ERROR(f'No active game found with ID {options["session_id"]}')
                    )
                    return
            else:
                sessions = MultiplayerGame.objects.filter(status='active')

            if not sessions.exists():
                self.stdout.write(self.style.WARNING('No active multiplayer sessions found'))
                return

            total_processed = 0
            for session in sessions:
                self.stdout.write(f'Processing session: {session.name} (ID: {session.id})')
                
                try:
                    market_config = MarketConfiguration.objects.get(multiplayer_game=session)
                except MarketConfiguration.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'No market configuration found for session {session.id}. Creating default...')
                    )
                    market_config = MarketConfiguration.objects.create(
                        multiplayer_game=session,
                        market_structure='monopolistic_competition',
                        total_market_size=5000000,
                        price_competition_intensity=1.0,
                        quality_competition_intensity=1.0
                    )

                current_month = session.current_month or 1
                
                if not options['dry_run']:
                    economic_engine = EconomicCycleEngine(session)
                    market_factors_engine = MarketFactorsEngine(session)
                    demographics_engine = CustomerDemographicsEngine(session)
                    clearing_engine = MarketClearingEngine(session)

                    current_year = session.current_year or 2024
                    
                    self.stdout.write(f'  Advancing economic cycle for month {current_month}/{current_year}...')
                    economic_condition = economic_engine.advance_economic_cycle(current_month, current_year)

                    self.stdout.write(f'  Updating market factors for month {current_month}/{current_year}...')
                    market_factors = market_factors_engine.advance_market_factors(current_month, current_year, economic_condition)

                    self.stdout.write(f'  Evolving customer demographics for month {current_month}/{current_year}...')
                    demographics = demographics_engine.advance_customer_demographics(current_month, current_year, economic_condition, market_factors)

                    self.stdout.write(f'  Processing market clearing for month {current_month}/{current_year}...')
                    results = clearing_engine.process_monthly_market_clearing(current_month, current_year)

                    self.stdout.write(
                        self.style.SUCCESS(f'  Successfully processed {len(results)} market results')
                    )
                    
                    session.current_month = current_month + 1
                    session.save()
                else:
                    self.stdout.write(f'  [DRY RUN] Would process month {current_month}')

                total_processed += 1

            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f'[DRY RUN] Would process {total_processed} sessions')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed {total_processed} sessions')
                )

        except Exception as e:
            logger.exception(f'Error processing monthly market: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error processing monthly market: {e}')
            )
            raise