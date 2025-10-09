from django.core.management.base import BaseCommand
from game_objectives.models import GameMode, GameObjective
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample game modes with different objectives'

    def handle(self, *args, **options):
        self.stdout.write('Creating game modes and objectives...')
        
        # Create different game modes
        self.create_profit_maximization_mode()
        self.create_market_dominance_mode()
        self.create_survival_mode()
        self.create_growth_focused_mode()
        self.create_balanced_scorecard_mode()
        self.create_time_challenge_mode()
        self.create_efficiency_master_mode()
        
        self.stdout.write(self.style.SUCCESS('Successfully created all game modes'))

    def create_profit_maximization_mode(self):
        """Create profit maximization game mode"""
        self.stdout.write('Creating Profit Maximization mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Gewinnmaximierung',
            defaults={
                'mode_type': 'profit_maximization',
                'description': 'Ziel: Maximieren Sie Ihren Gewinn innerhalb von 24 Monaten. Fokus auf Profitabilität und finanzielle Effizienz.',
                'duration_months': 24,
                'starting_balance': Decimal('80000.00'),
                'bankruptcy_threshold': Decimal('-15000.00'),
                'victory_conditions': {
                    'min_score': 85.0,
                    'primary_objectives_required': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.0,
                    'competition_intensity': 1.0,
                    'market_volatility': 1.0
                }
            }
        )
        
        if created:
            # Primary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Mindestgewinn erreichen',
                description='Erreichen Sie einen Gesamtgewinn von mindestens 50.000€',
                objective_type='profit_total',
                target_value=Decimal('50000.00'),
                comparison_operator='gte',
                weight=Decimal('3.0'),
                is_primary=True,
                order=1
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Durchschnittlicher Monatsgewinn',
                description='Erreichen Sie einen durchschnittlichen Monatsgewinn von 3.000€',
                objective_type='profit_monthly',
                target_value=Decimal('3000.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=2
            )
            
            # Secondary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Mindest-Liquidität',
                description='Halten Sie jederzeit einen Mindestkontostand von 10.000€',
                objective_type='balance_minimum',
                target_value=Decimal('10000.00'),
                comparison_operator='gte',
                weight=Decimal('1.5'),
                is_failure_condition=True,
                evaluation_frequency='continuous',
                order=3
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Effizienz-Score',
                description='Erreichen Sie einen Gewinn pro produziertem Fahrrad von mindestens 300€',
                objective_type='efficiency_score',
                target_value=Decimal('300.00'),
                comparison_operator='gte',
                weight=Decimal('1.0'),
                order=4
            )

    def create_market_dominance_mode(self):
        """Create market dominance game mode"""
        self.stdout.write('Creating Market Dominance mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Marktdominanz',
            defaults={
                'mode_type': 'market_dominance',
                'description': 'Ziel: Erobern Sie den Markt! Erreichen Sie mindestens 25% Marktanteil und verkaufen Sie mehr als die Konkurrenz.',
                'duration_months': 30,
                'starting_balance': Decimal('100000.00'),
                'bankruptcy_threshold': Decimal('-20000.00'),
                'victory_conditions': {
                    'min_score': 80.0,
                    'primary_objectives_required': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.1,
                    'competition_intensity': 1.3,
                    'market_volatility': 1.2
                }
            }
        )
        
        if created:
            # Primary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Marktanteil erobern',
                description='Erreichen Sie einen Marktanteil von mindestens 25%',
                objective_type='market_share',
                target_value=Decimal('25.00'),
                comparison_operator='gte',
                weight=Decimal('3.0'),
                is_primary=True,
                order=1
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Verkaufsvolumen',
                description='Verkaufen Sie mindestens 200 Fahrräder',
                objective_type='bikes_sold',
                target_value=Decimal('200.00'),
                comparison_operator='gte',
                weight=Decimal('2.5'),
                is_primary=True,
                order=2
            )
            
            # Secondary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Produktionsvolumen',
                description='Produzieren Sie mindestens 250 Fahrräder',
                objective_type='bikes_produced',
                target_value=Decimal('250.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                order=3
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Umsatzziel',
                description='Erreichen Sie einen Gesamtumsatz von 300.000€',
                objective_type='revenue_total',
                target_value=Decimal('300000.00'),
                comparison_operator='gte',
                weight=Decimal('1.5'),
                order=4
            )

    def create_survival_mode(self):
        """Create survival game mode"""
        self.stdout.write('Creating Survival mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Überlebenskampf',
            defaults={
                'mode_type': 'survival',
                'description': 'Harte Zeiten! Überleben Sie 18 Monate mit begrenzten Ressourcen und vermeiden Sie den Bankrott.',
                'duration_months': 18,
                'starting_balance': Decimal('40000.00'),
                'bankruptcy_threshold': Decimal('-5000.00'),
                'victory_conditions': {
                    'min_completion_percentage': 75.0,
                    'survival_required': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.3,
                    'competition_intensity': 1.5,
                    'market_volatility': 1.4
                }
            }
        )
        
        if created:
            # Primary objective - survival
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Überleben',
                description='Vermeiden Sie den Bankrott für 18 Monate',
                objective_type='balance_minimum',
                target_value=Decimal('-5000.00'),
                comparison_operator='gte',
                weight=Decimal('4.0'),
                is_primary=True,
                is_failure_condition=True,
                evaluation_frequency='continuous',
                order=1
            )
            
            # Secondary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Mindestverkäufe',
                description='Verkaufen Sie mindestens 50 Fahrräder',
                objective_type='bikes_sold',
                target_value=Decimal('50.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                order=2
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Kosteneffizienz',
                description='Halten Sie die Kosten pro Einheit unter 800€',
                objective_type='cost_per_unit',
                target_value=Decimal('800.00'),
                comparison_operator='lte',
                weight=Decimal('1.5'),
                order=3
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Mindestgewinn',
                description='Erreichen Sie einen Gesamtgewinn von mindestens 5.000€',
                objective_type='profit_total',
                target_value=Decimal('5000.00'),
                comparison_operator='gte',
                weight=Decimal('1.0'),
                order=4
            )

    def create_growth_focused_mode(self):
        """Create growth-focused game mode"""
        self.stdout.write('Creating Growth-Focused mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Wachstumsstrategie',
            defaults={
                'mode_type': 'growth_focused',
                'description': 'Fokus auf nachhaltiges Wachstum. Bauen Sie Ihr Unternehmen systematisch auf und expandieren Sie.',
                'duration_months': 36,
                'starting_balance': Decimal('60000.00'),
                'bankruptcy_threshold': Decimal('-10000.00'),
                'victory_conditions': {
                    'min_score': 75.0,
                    'growth_required': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.0,
                    'competition_intensity': 1.1,
                    'market_volatility': 1.0
                }
            }
        )
        
        if created:
            # Primary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Produktionskapazität',
                description='Produzieren Sie mindestens 300 Fahrräder',
                objective_type='bikes_produced',
                target_value=Decimal('300.00'),
                comparison_operator='gte',
                weight=Decimal('2.5'),
                is_primary=True,
                order=1
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Umsatzwachstum',
                description='Erreichen Sie einen Gesamtumsatz von 400.000€',
                objective_type='revenue_total',
                target_value=Decimal('400000.00'),
                comparison_operator='gte',
                weight=Decimal('2.5'),
                is_primary=True,
                order=2
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Marktposition',
                description='Erreichen Sie einen Marktanteil von mindestens 15%',
                objective_type='market_share',
                target_value=Decimal('15.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=3
            )
            
            # Secondary objectives
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Lagerumschlag',
                description='Erreichen Sie einen Lagerumschlag von mindestens 4.0',
                objective_type='inventory_turnover',
                target_value=Decimal('4.00'),
                comparison_operator='gte',
                weight=Decimal('1.5'),
                order=4
            )

    def create_balanced_scorecard_mode(self):
        """Create balanced scorecard game mode"""
        self.stdout.write('Creating Balanced Scorecard mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Balanced Scorecard',
            defaults={
                'mode_type': 'balanced_scorecard',
                'description': 'Ausgewogene Unternehmensfhrung. Erreichen Sie Ziele in allen Bereichen: Finanzen, Markt, Qualität und Effizienz.',
                'duration_months': 24,
                'starting_balance': Decimal('80000.00'),
                'bankruptcy_threshold': Decimal('-12000.00'),
                'victory_conditions': {
                    'min_score': 80.0,
                    'balanced_performance': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.05,
                    'competition_intensity': 1.2,
                    'market_volatility': 1.1
                }
            }
        )
        
        if created:
            # Financial perspective
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Finanzielle Performance',
                description='Erreichen Sie einen Gesamtgewinn von 30.000€',
                objective_type='profit_total',
                target_value=Decimal('30000.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=1
            )
            
            # Market perspective
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Marktperformance',
                description='Erreichen Sie einen Marktanteil von 12%',
                objective_type='market_share',
                target_value=Decimal('12.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=2
            )
            
            # Quality perspective
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Qualitätsstandard',
                description='Erreichen Sie eine durchschnittliche Qualitätsbewertung von 85',
                objective_type='quality_rating',
                target_value=Decimal('85.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=3
            )
            
            # Efficiency perspective
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Effizienzstandard',
                description='Erreichen Sie einen Gewinn pro Fahrrad von 250€',
                objective_type='efficiency_score',
                target_value=Decimal('250.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=4
            )

    def create_time_challenge_mode(self):
        """Create time challenge game mode"""
        self.stdout.write('Creating Time Challenge mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Schneller Erfolg',
            defaults={
                'mode_type': 'time_challenge',
                'description': 'Gegen die Zeit! Erreichen Sie schnell ehrgeizige Ziele in nur 12 Monaten.',
                'duration_months': 12,
                'starting_balance': Decimal('80000.00'),
                'bankruptcy_threshold': Decimal('-15000.00'),
                'victory_conditions': {
                    'min_score': 90.0,
                    'time_pressure': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 0.95,
                    'competition_intensity': 1.0,
                    'market_volatility': 1.2
                }
            }
        )
        
        if created:
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Schneller Gewinn',
                description='Erreichen Sie 25.000€ Gewinn in 12 Monaten',
                objective_type='profit_total',
                target_value=Decimal('25000.00'),
                comparison_operator='gte',
                weight=Decimal('3.0'),
                is_primary=True,
                order=1
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Verkaufsrekord',
                description='Verkaufen Sie 100 Fahrräder in 12 Monaten',
                objective_type='bikes_sold',
                target_value=Decimal('100.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                is_primary=True,
                order=2
            )

    def create_efficiency_master_mode(self):
        """Create efficiency master game mode"""
        self.stdout.write('Creating Efficiency Master mode...')
        
        game_mode, created = GameMode.objects.get_or_create(
            name='Effizienz-Meister',
            defaults={
                'mode_type': 'efficiency_master',
                'description': 'Maximale Effizienz! Erreichen Sie hohe Leistung mit minimalen Ressourcen.',
                'duration_months': 20,
                'starting_balance': Decimal('50000.00'),
                'bankruptcy_threshold': Decimal('-8000.00'),
                'victory_conditions': {
                    'min_score': 85.0,
                    'efficiency_focus': True
                },
                'difficulty_multipliers': {
                    'cost_multiplier': 1.2,
                    'competition_intensity': 1.1,
                    'market_volatility': 1.0
                }
            }
        )
        
        if created:
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Gewinn-Effizienz',
                description='Erreichen Sie mindestens 400€ Gewinn pro Fahrrad',
                objective_type='efficiency_score',
                target_value=Decimal('400.00'),
                comparison_operator='gte',
                weight=Decimal('3.0'),
                is_primary=True,
                order=1
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Kostenoptimierung',
                description='Halten Sie Kosten pro Einheit unter 600€',
                objective_type='cost_per_unit',
                target_value=Decimal('600.00'),
                comparison_operator='lte',
                weight=Decimal('2.5'),
                is_primary=True,
                order=2
            )
            
            GameObjective.objects.create(
                game_mode=game_mode,
                name='Lageroptimierung',
                description='Erreichen Sie einen Lagerumschlag von mindestens 6.0',
                objective_type='inventory_turnover',
                target_value=Decimal('6.00'),
                comparison_operator='gte',
                weight=Decimal('2.0'),
                order=3
            )