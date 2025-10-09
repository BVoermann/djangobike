"""
Django management command to initialize and test the multiplayer AI system.
This command sets up AI players, runs tests, and demonstrates the AI capabilities.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from decimal import Decimal
import random

from multiplayer.models import MultiplayerGame, PlayerSession, GameEvent
from multiplayer.ai_manager import MultiplayerAIManager
from multiplayer.ai_integration import MultiplayerIntegrationManager, DifficultyScalingEngine
from bikeshop.models import GameSession, BikeType
from sales.models import Market


class Command(BaseCommand):
    help = 'Initialize and test the multiplayer AI competitor system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-game',
            action='store_true',
            help='Create a test multiplayer game with AI players',
        )
        parser.add_argument(
            '--test-ai-decisions',
            action='store_true',
            help='Test AI decision-making algorithms',
        )
        parser.add_argument(
            '--test-difficulty-scaling',
            action='store_true',
            help='Test difficulty scaling system',
        )
        parser.add_argument(
            '--demo-personalities',
            action='store_true',
            help='Demonstrate different AI personalities',
        )
        parser.add_argument(
            '--game-id',
            type=str,
            help='Specify multiplayer game ID for testing',
        )
        parser.add_argument(
            '--ai-count',
            type=int,
            default=4,
            help='Number of AI players to create (default: 4)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Initializing Multiplayer AI Competitor System')
        )
        
        try:
            if options['create_test_game']:
                self.create_test_game(options['ai_count'])
            
            if options['test_ai_decisions']:
                game_id = options.get('game_id')
                self.test_ai_decisions(game_id)
            
            if options['test_difficulty_scaling']:
                game_id = options.get('game_id')
                self.test_difficulty_scaling(game_id)
            
            if options['demo_personalities']:
                self.demo_ai_personalities()
            
            # If no specific options, run full demo
            if not any([
                options['create_test_game'],
                options['test_ai_decisions'],
                options['test_difficulty_scaling'],
                options['demo_personalities']
            ]):
                self.run_full_demo(options['ai_count'])
                
        except Exception as e:
            raise CommandError(f'Error during AI system initialization: {str(e)}')
    
    def create_test_game(self, ai_count):
        """Create a test multiplayer game with AI players"""
        
        self.stdout.write('Creating test multiplayer game...')
        
        with transaction.atomic():
            # Create or get a test user
            test_user, created = User.objects.get_or_create(
                username='test_host',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            # Create multiplayer game
            game = MultiplayerGame.objects.create(
                name='AI Test Game',
                description='Test game for AI competitor system',
                max_players=ai_count + 1,
                human_players_count=1,
                ai_players_count=ai_count,
                difficulty='medium',
                created_by=test_user,
                status='setup'
            )
            
            # Create human player session
            human_player = PlayerSession.objects.create(
                multiplayer_game=game,
                user=test_user,
                company_name='Human Test Company',
                player_type='human',
                balance=game.starting_balance
            )
            
            # Create AI players with different strategies
            ai_strategies = ['aggressive', 'conservative', 'innovative', 'balanced']
            
            for i in range(ai_count):
                strategy = ai_strategies[i % len(ai_strategies)]
                
                ai_player = PlayerSession.objects.create(
                    multiplayer_game=game,
                    company_name=f'AI {strategy.title()} Corp',
                    player_type='ai',
                    ai_strategy=strategy,
                    balance=game.starting_balance,
                    ai_difficulty=random.uniform(0.8, 1.2),
                    ai_aggressiveness=self._get_strategy_aggressiveness(strategy),
                    ai_risk_tolerance=self._get_strategy_risk_tolerance(strategy)
                )
                
                self.stdout.write(
                    f'  Created AI player: {ai_player.company_name} '
                    f'(Strategy: {strategy}, Difficulty: {ai_player.ai_difficulty:.2f})'
                )
            
            game.status = 'waiting'
            game.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created test game "{game.name}" with ID: {game.id}'
                )
            )
            self.stdout.write(f'  Human players: {human_players_count}')
            self.stdout.write(f'  AI players: {ai_count}')
            
            return game
    
    def test_ai_decisions(self, game_id=None):
        """Test AI decision-making algorithms"""
        
        self.stdout.write('Testing AI decision-making algorithms...')
        
        if game_id:
            try:
                game = MultiplayerGame.objects.get(id=game_id)
            except MultiplayerGame.DoesNotExist:
                raise CommandError(f'Game with ID {game_id} not found')
        else:
            game = MultiplayerGame.objects.filter(status__in=['setup', 'waiting']).first()
            if not game:
                self.stdout.write('No test game found, creating one...')
                game = self.create_test_game(4)
        
        # Initialize AI manager
        ai_manager = MultiplayerAIManager(game)
        integration_manager = MultiplayerIntegrationManager(game)
        
        # Test AI decisions for each AI player
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=game,
            player_type='ai',
            is_active=True
        )
        
        for ai_player in ai_players:
            self.stdout.write(f'\nTesting decisions for {ai_player.company_name}:')
            
            # Get AI personality
            personality = ai_manager._get_ai_personality(ai_player)
            
            # Generate test market data
            test_market_data = self._generate_test_market_data()
            test_competition_data = self._generate_test_competition_data()
            test_financial_data = integration_manager._get_financial_state(ai_player)
            test_inventory_data = integration_manager._get_inventory_state(ai_player)
            
            # Test production decisions
            production_decisions = personality.get_production_strategy(test_market_data)
            self.stdout.write(f'  Production: {production_decisions["target_volume"]} bikes')
            
            # Test pricing decisions
            pricing_decisions = personality.get_pricing_strategy(test_competition_data)
            self.stdout.write(f'  Pricing: {pricing_decisions["pricing_method"]}')
            
            # Test procurement decisions
            procurement_decisions = personality.get_procurement_strategy(test_inventory_data)
            self.stdout.write(f'  Procurement: {procurement_decisions["ordering_strategy"]}')
            
            # Test market strategy
            market_decisions = personality.get_market_strategy(test_market_data)
            self.stdout.write(f'  Market: {market_decisions["market_entry"]}')
            
            # Test financial strategy
            financial_decisions = personality.get_financial_strategy(test_financial_data)
            self.stdout.write(f'  Finance: {financial_decisions["debt_tolerance"]}')
        
        self.stdout.write(self.style.SUCCESS('AI decision testing completed'))
    
    def test_difficulty_scaling(self, game_id=None):
        """Test difficulty scaling system"""
        
        self.stdout.write('Testing difficulty scaling system...')
        
        if game_id:
            try:
                game = MultiplayerGame.objects.get(id=game_id)
            except MultiplayerGame.DoesNotExist:
                raise CommandError(f'Game with ID {game_id} not found')
        else:
            game = MultiplayerGame.objects.filter(status__in=['setup', 'waiting']).first()
            if not game:
                self.stdout.write('No test game found, creating one...')
                game = self.create_test_game(4)
        
        # Test each difficulty level
        difficulty_levels = ['easy', 'medium', 'hard', 'expert']
        
        for difficulty in difficulty_levels:
            self.stdout.write(f'\nTesting {difficulty.upper()} difficulty:')
            
            # Create temporary game with this difficulty
            game.difficulty = difficulty
            game.save()
            
            scaling_engine = DifficultyScalingEngine(game)
            
            # Get an AI player for testing
            ai_player = PlayerSession.objects.filter(
                multiplayer_game=game,
                player_type='ai'
            ).first()
            
            if ai_player:
                # Generate base decisions
                base_decisions = {
                    'production': {
                        'target_volume': 100,
                        'bike_priorities': {'Mountain Bike': 0.8, 'City Bike': 0.6},
                        'quality_vs_speed': 'balanced'
                    },
                    'pricing': {
                        'pricing_method': 'market_adaptive',
                        'margin_target': 0.25
                    }
                }
                
                # Apply difficulty scaling
                scaled_decisions = scaling_engine.get_scaled_decisions(ai_player, base_decisions)
                
                # Show scaling effects
                original_volume = base_decisions['production']['target_volume']
                scaled_volume = scaled_decisions['production']['target_volume']
                
                self.stdout.write(f'  Production volume: {original_volume} → {scaled_volume}')
                
                original_margin = base_decisions['pricing']['margin_target']
                scaled_margin = scaled_decisions['pricing']['margin_target']
                
                self.stdout.write(f'  Margin target: {original_margin:.2f} → {scaled_margin:.2f}')
                
                # Get difficulty description
                description = scaling_engine.get_difficulty_description(ai_player)
                self.stdout.write(f'  Description: {description}')
        
        self.stdout.write(self.style.SUCCESS('Difficulty scaling testing completed'))
    
    def demo_ai_personalities(self):
        """Demonstrate different AI personalities"""
        
        self.stdout.write('Demonstrating AI Personalities...')
        
        # Create a test game for demonstration
        game = self.create_test_game(4)
        
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=game,
            player_type='ai'
        )
        
        ai_manager = MultiplayerAIManager(game)
        test_market_data = self._generate_test_market_data()
        
        for ai_player in ai_players:
            personality = ai_manager._get_ai_personality(ai_player)
            
            self.stdout.write(f'\n{ai_player.company_name} ({ai_player.ai_strategy.upper()}):')
            self.stdout.write(f'  Aggressiveness: {ai_player.ai_aggressiveness:.2f}')
            self.stdout.write(f'  Risk Tolerance: {ai_player.ai_risk_tolerance:.2f}')
            self.stdout.write(f'  Difficulty: {ai_player.ai_difficulty:.2f}')
            
            # Show personality traits in decisions
            production = personality.get_production_strategy(test_market_data)
            pricing = personality.get_pricing_strategy({})
            
            self.stdout.write(f'  Production approach: {production.get("quality_vs_speed", "unknown")}')
            self.stdout.write(f'  Pricing method: {pricing.get("pricing_method", "unknown")}')
            self.stdout.write(f'  Segment focus: {", ".join(production.get("segment_focus", []))}')
        
        self.stdout.write(self.style.SUCCESS('AI personality demonstration completed'))
    
    def run_full_demo(self, ai_count):
        """Run full demonstration of AI system"""
        
        self.stdout.write(self.style.SUCCESS('Running Full AI System Demo'))
        self.stdout.write('=' * 50)
        
        # Create test game
        game = self.create_test_game(ai_count)
        
        # Test AI decisions
        self.test_ai_decisions(str(game.id))
        
        # Test difficulty scaling
        self.test_difficulty_scaling(str(game.id))
        
        # Demo personalities
        self.stdout.write('\n' + '=' * 50)
        self.demo_ai_personalities()
        
        # Simulate a turn
        self.stdout.write('\n' + '=' * 50)
        self.simulate_ai_turn(game)
        
        self.stdout.write('\n' + self.style.SUCCESS('Full demo completed successfully!'))
        self.stdout.write(f'Test game ID: {game.id}')
    
    def simulate_ai_turn(self, game):
        """Simulate an AI turn to demonstrate the system in action"""
        
        self.stdout.write('Simulating AI Turn Processing...')
        
        ai_manager = MultiplayerAIManager(game)
        
        # Set game to active status
        game.status = 'active'
        game.save()
        
        try:
            # Process AI turn
            ai_manager.process_ai_turn(game.current_month, game.current_year)
            
            # Show results
            ai_players = PlayerSession.objects.filter(
                multiplayer_game=game,
                player_type='ai'
            )
            
            self.stdout.write('AI Turn Results:')
            for ai_player in ai_players:
                self.stdout.write(f'  {ai_player.company_name}:')
                self.stdout.write(f'    Balance: ${ai_player.balance:,.2f}')
                self.stdout.write(f'    Bikes Produced: {ai_player.bikes_produced}')
                self.stdout.write(f'    Bikes Sold: {ai_player.bikes_sold}')
                self.stdout.write(f'    Total Revenue: ${ai_player.total_revenue:,.2f}')
            
            # Show game events
            recent_events = GameEvent.objects.filter(
                multiplayer_game=game,
                event_type='ai_action'
            ).order_by('-timestamp')[:5]
            
            if recent_events.exists():
                self.stdout.write('\nRecent AI Actions:')
                for event in recent_events:
                    self.stdout.write(f'  {event.message}')
        
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Turn simulation error: {str(e)}')
            )
    
    def _get_strategy_aggressiveness(self, strategy):
        """Get aggressiveness level for strategy"""
        aggressiveness_map = {
            'aggressive': 0.9,
            'conservative': 0.3,
            'innovative': 0.7,
            'balanced': 0.5,
            'cheap_only': 0.8,
            'premium_focus': 0.4,
            'e_bike_specialist': 0.6
        }
        return aggressiveness_map.get(strategy, 0.5)
    
    def _get_strategy_risk_tolerance(self, strategy):
        """Get risk tolerance for strategy"""
        risk_map = {
            'aggressive': 0.9,
            'conservative': 0.2,
            'innovative': 0.8,
            'balanced': 0.5,
            'cheap_only': 0.6,
            'premium_focus': 0.3,
            'e_bike_specialist': 0.7
        }
        return risk_map.get(strategy, 0.5)
    
    def _generate_test_market_data(self):
        """Generate test market data for AI decision testing"""
        return {
            'markets': {
                'Local Market': {
                    'demand_trend': 1.1,
                    'competition_intensity': 0.6,
                    'growth_rate': 1.05,
                    'profit_potential': 0.7,
                    'volatility': 0.3
                },
                'Regional Market': {
                    'demand_trend': 1.2,
                    'competition_intensity': 0.8,
                    'growth_rate': 1.15,
                    'profit_potential': 0.8,
                    'volatility': 0.5
                }
            },
            'bike_demand': {
                'Mountain Bike': {
                    'demand_score': 0.8,
                    'profit_margin': 0.3,
                    'competition_intensity': 0.6,
                    'growth_rate': 1.1,
                    'volatility': 0.4
                },
                'City Bike': {
                    'demand_score': 0.7,
                    'profit_margin': 0.25,
                    'competition_intensity': 0.7,
                    'growth_rate': 1.05,
                    'volatility': 0.3
                },
                'E-Bike': {
                    'demand_score': 0.9,
                    'profit_margin': 0.4,
                    'competition_intensity': 0.5,
                    'growth_rate': 1.3,
                    'volatility': 0.6
                }
            },
            'last_updated': '2024-01-01T00:00:00Z'
        }
    
    def _generate_test_competition_data(self):
        """Generate test competition data"""
        return {
            'competitor_count': 4,
            'market_leaders': [
                {'rank': 1, 'company': 'Market Leader Inc', 'revenue': 150000, 'market_share': 25.0},
                {'rank': 2, 'company': 'Strong Competitor', 'revenue': 120000, 'market_share': 20.0}
            ],
            'competitive_threats': [
                {'company': 'Aggressive Rival', 'threat_level': 'high', 'advantage': 'revenue_leader'}
            ],
            'pricing_pressure': 0.7,
            'market_concentration': 0.6
        }