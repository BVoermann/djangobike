from django.core.management.base import BaseCommand
from django.db import transaction
from bikeshop.models import GameSession
from competitors.models import AICompetitor
from competitors.ai_engine import initialize_competitors_for_session


class Command(BaseCommand):
    help = 'Add AI competitors to existing game sessions that don\'t have any'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        # Find sessions without competitors
        sessions_without_competitors = []
        for session in GameSession.objects.all():
            if not AICompetitor.objects.filter(session=session).exists():
                sessions_without_competitors.append(session)
        
        if not sessions_without_competitors:
            self.stdout.write(
                self.style.SUCCESS("All sessions already have competitors!")
            )
            return
        
        self.stdout.write(f"Found {len(sessions_without_competitors)} sessions without competitors")
        
        if dry_run:
            for session in sessions_without_competitors:
                self.stdout.write(f"Would add competitors to: {session.name} (ID: {session.id})")
            return
        
        # Add competitors to sessions
        competitors_data = [
            {
                'name': 'BudgetCycles GmbH',
                'strategy': 'cheap_only',
                'financial_resources': 45000.00,
                'market_presence': 18.0,
                'aggressiveness': 0.8,
                'efficiency': 0.6
            },
            {
                'name': 'CycleTech Solutions',
                'strategy': 'balanced',
                'financial_resources': 65000.00,
                'market_presence': 22.0,
                'aggressiveness': 0.5,
                'efficiency': 0.8
            },
            {
                'name': 'PremiumWheels AG',
                'strategy': 'premium_focus',
                'financial_resources': 55000.00,
                'market_presence': 12.0,
                'aggressiveness': 0.3,
                'efficiency': 0.9
            },
            {
                'name': 'E-Motion Bikes',
                'strategy': 'e_bike_specialist',
                'financial_resources': 60000.00,
                'market_presence': 16.0,
                'aggressiveness': 0.6,
                'efficiency': 0.7
            }
        ]
        
        for session in sessions_without_competitors:
            with transaction.atomic():
                self.stdout.write(f"Adding competitors to session: {session.name}")
                
                # Create competitors
                for competitor_data in competitors_data:
                    AICompetitor.objects.create(
                        session=session,
                        name=competitor_data['name'],
                        strategy=competitor_data['strategy'],
                        financial_resources=competitor_data['financial_resources'],
                        market_presence=competitor_data['market_presence'],
                        aggressiveness=competitor_data['aggressiveness'],
                        efficiency=competitor_data['efficiency']
                    )
                
                # Initialize competitors
                try:
                    initialize_competitors_for_session(session)
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Successfully added 4 competitors to {session.name}")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ Competitors created but initialization failed for {session.name}: {e}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"Completed! Added competitors to {len(sessions_without_competitors)} sessions.")
        )