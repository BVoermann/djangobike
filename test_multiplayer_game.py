#!/usr/bin/env python
"""
Test script to play through a multiplayer game with 2 players and analyze issues.
"""
import os
import sys
import django
from decimal import Decimal
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from multiplayer.models import MultiplayerGame, PlayerSession, TurnState, GameEvent
from bikeshop.models import GameSession
from multiplayer.player_state_manager import PlayerStateManager
from multiplayer.simulation_engine import MultiplayerTurnManager, MultiplayerSimulationEngine
from django.db import transaction

User = get_user_model()

class MultiplayerGameTester:
    def __init__(self):
        self.issues = []
        self.game = None
        self.player1 = None
        self.player2 = None
        self.player1_session = None
        self.player2_session = None

    def log_issue(self, severity, category, message, details=None):
        """Log an issue found during testing"""
        issue = {
            'severity': severity,  # 'critical', 'warning', 'info'
            'category': category,  # 'balance', 'mechanics', 'UX', 'data', 'performance'
            'message': message,
            'details': details or {}
        }
        self.issues.append(issue)
        print(f"[{severity.upper()}] {category}: {message}")
        if details:
            print(f"  Details: {details}")

    def setup_test_users(self):
        """Create or get test users"""
        print("\n=== Setting up test users ===")

        user1, created = User.objects.get_or_create(
            username='test_player1',
            defaults={
                'email': 'player1@test.com',
                'first_name': 'Player',
                'last_name': 'One'
            }
        )
        if created:
            user1.set_password('testpass123')
            user1.save()
            print("Created test_player1")
        else:
            print("Using existing test_player1")

        user2, created = User.objects.get_or_create(
            username='test_player2',
            defaults={
                'email': 'player2@test.com',
                'first_name': 'Player',
                'last_name': 'Two'
            }
        )
        if created:
            user2.set_password('testpass123')
            user2.save()
            print("Created test_player2")
        else:
            print("Using existing test_player2")

        return user1, user2

    def create_game(self, user1):
        """Create a new multiplayer game"""
        print("\n=== Creating multiplayer game ===")

        game = MultiplayerGame.objects.create(
            name="Test Game - 2 Players",
            description="Test game for analysis",
            max_players=2,
            human_players_count=2,
            ai_players_count=0,
            difficulty='medium',
            turn_deadline_hours=0,  # Instant mode
            turn_duration_minutes=0,  # No waiting
            max_months=12,  # 1 year
            starting_balance=Decimal('80000.00'),
            bankruptcy_threshold=Decimal('-50000.00'),
            created_by=user1,
            status='setup',
            parameters_uploaded=False  # We'll check if parameters are needed
        )

        print(f"Created game: {game.name} (ID: {game.id})")
        print(f"  Status: {game.status}")
        print(f"  Starting balance: {game.starting_balance}")
        print(f"  Turn deadline: {game.turn_deadline_hours}h")

        # Check if parameters_uploaded is blocking
        if not game.parameters_uploaded:
            self.log_issue('warning', 'UX',
                          'Game requires parameters to be uploaded before players can join',
                          {'current_status': 'parameters_uploaded=False'})

        return game

    def join_players(self, game, user1, user2):
        """Have both players join the game"""
        print("\n=== Players joining game ===")

        # Create first player
        player1 = PlayerSession.objects.create(
            multiplayer_game=game,
            user=user1,
            company_name="Alpha Bikes",
            player_type='human',
            balance=game.starting_balance
        )
        print(f"Player 1 joined: {player1.company_name}")

        # Check if player initialization needs game state
        try:
            state_manager = PlayerStateManager(game)
            # This might fail if parameters aren't uploaded
            game_session1 = state_manager.initialize_player_game_state(player1)
            print(f"  Game state initialized: {game_session1}")
        except Exception as e:
            self.log_issue('critical', 'mechanics',
                          'Failed to initialize player game state',
                          {'error': str(e), 'player': player1.company_name})
            print(f"  WARNING: Could not initialize game state: {e}")
            game_session1 = None

        # Create second player
        player2 = PlayerSession.objects.create(
            multiplayer_game=game,
            user=user2,
            company_name="Beta Cycles",
            player_type='human',
            balance=game.starting_balance
        )
        print(f"Player 2 joined: {player2.company_name}")

        try:
            state_manager = PlayerStateManager(game)
            game_session2 = state_manager.initialize_player_game_state(player2)
            print(f"  Game state initialized: {game_session2}")
        except Exception as e:
            self.log_issue('critical', 'mechanics',
                          'Failed to initialize player game state',
                          {'error': str(e), 'player': player2.company_name})
            print(f"  WARNING: Could not initialize game state: {e}")
            game_session2 = None

        return player1, player2

    def start_game(self, game):
        """Start the game"""
        print("\n=== Starting game ===")

        game.status = 'active'
        game.started_at = timezone.now()
        game.save()

        print(f"Game started: {game.status}")
        print(f"  Current month: {game.current_month}/{game.current_year}")

        # Create game start event
        GameEvent.objects.create(
            multiplayer_game=game,
            event_type='game_started',
            message=f"Game started with {game.players.count()} players",
            data={
                'total_players': game.players.count(),
                'human_players': game.players.filter(player_type='human').count()
            }
        )

    def play_turn(self, turn_number):
        """Play through one turn"""
        print(f"\n=== Playing Turn {turn_number} ===")
        print(f"Month: {self.game.current_month}/{self.game.current_year}")

        # Get player game sessions
        state_manager = PlayerStateManager(self.game)

        try:
            game_session1 = state_manager.get_player_game_session(self.player1_session)
            game_session2 = state_manager.get_player_game_session(self.player2_session)
        except Exception as e:
            self.log_issue('critical', 'mechanics',
                          'Cannot access player game sessions',
                          {'error': str(e)})
            return False

        # Check balances
        print(f"  {self.player1_session.company_name}: Balance = {game_session1.balance}")
        print(f"  {self.player2_session.company_name}: Balance = {game_session2.balance}")

        # Submit decisions for both players
        turn_state1, _ = TurnState.objects.get_or_create(
            multiplayer_game=self.game,
            player_session=self.player1_session,
            month=self.game.current_month,
            year=self.game.current_year,
            defaults={'decisions_submitted': False}
        )

        turn_state2, _ = TurnState.objects.get_or_create(
            multiplayer_game=self.game,
            player_session=self.player2_session,
            month=self.game.current_month,
            year=self.game.current_year,
            defaults={'decisions_submitted': False}
        )

        # Mark decisions as submitted
        turn_state1.decisions_submitted = True
        turn_state1.submitted_at = timezone.now()
        turn_state1.save()

        turn_state2.decisions_submitted = True
        turn_state2.submitted_at = timezone.now()
        turn_state2.save()

        print("  Both players submitted decisions")

        # Process turn
        try:
            turn_manager = MultiplayerTurnManager(self.game)
            result = turn_manager.process_turn_if_ready()

            if result.get('processed'):
                print(f"  Turn processed successfully!")
                print(f"  New month: {self.game.current_month}/{self.game.current_year}")
                return True
            else:
                self.log_issue('warning', 'mechanics',
                              'Turn not processed despite all players submitting',
                              {'result': result})
                return False
        except Exception as e:
            self.log_issue('critical', 'mechanics',
                          'Turn processing failed',
                          {'error': str(e), 'turn': turn_number})
            print(f"  ERROR processing turn: {e}")
            import traceback
            traceback.print_exc()
            return False

    def check_game_state(self):
        """Check current game state for issues"""
        print("\n=== Checking game state ===")

        # Refresh objects
        self.game.refresh_from_db()
        self.player1_session.refresh_from_db()
        self.player2_session.refresh_from_db()

        # Check player balances
        print(f"Player 1 ({self.player1_session.company_name}):")
        print(f"  Balance: {self.player1_session.balance}")
        print(f"  Revenue: {self.player1_session.total_revenue}")
        print(f"  Profit: {self.player1_session.total_profit}")
        print(f"  Bikes produced: {self.player1_session.bikes_produced}")
        print(f"  Bikes sold: {self.player1_session.bikes_sold}")
        print(f"  Market share: {self.player1_session.market_share}%")
        print(f"  Bankrupt: {self.player1_session.is_bankrupt}")

        print(f"\nPlayer 2 ({self.player2_session.company_name}):")
        print(f"  Balance: {self.player2_session.balance}")
        print(f"  Revenue: {self.player2_session.total_revenue}")
        print(f"  Profit: {self.player2_session.total_profit}")
        print(f"  Bikes produced: {self.player2_session.bikes_produced}")
        print(f"  Bikes sold: {self.player2_session.bikes_sold}")
        print(f"  Market share: {self.player2_session.market_share}%")
        print(f"  Bankrupt: {self.player2_session.is_bankrupt}")

        # Check for issues
        if self.player1_session.balance == self.game.starting_balance:
            self.log_issue('info', 'mechanics',
                          'Player 1 balance unchanged from start',
                          {'balance': self.player1_session.balance})

        if self.player2_session.balance == self.game.starting_balance:
            self.log_issue('info', 'mechanics',
                          'Player 2 balance unchanged from start',
                          {'balance': self.player2_session.balance})

        if self.player1_session.total_revenue == 0 and self.player2_session.total_revenue == 0:
            self.log_issue('warning', 'mechanics',
                          'No revenue generated for any player',
                          {})

        # Check turn states
        turn_states = TurnState.objects.filter(multiplayer_game=self.game).order_by('-year', '-month')
        print(f"\nTotal turn states: {turn_states.count()}")

        for ts in turn_states[:5]:  # Show last 5
            print(f"  {ts.year}/{ts.month:02d} - {ts.player_session.company_name}: Submitted={ts.decisions_submitted}")

    def analyze_simulation_engine(self):
        """Analyze the simulation engine and market mechanics"""
        print("\n=== Analyzing simulation engine ===")

        try:
            sim_engine = MultiplayerSimulationEngine(self.game)
            print("Simulation engine initialized successfully")

            # Check if there are markets configured
            state_manager = PlayerStateManager(self.game)
            game_session1 = state_manager.get_player_game_session(self.player1_session)

            from sales.models import Market
            markets = Market.objects.filter(session=game_session1)
            print(f"Markets available: {markets.count()}")

            if markets.count() == 0:
                self.log_issue('critical', 'data',
                              'No markets configured in game',
                              {'session': game_session1.id})

            # Check bike types
            from bikeshop.models import BikeType
            bike_types = BikeType.objects.filter(session=game_session1)
            print(f"Bike types available: {bike_types.count()}")

            if bike_types.count() == 0:
                self.log_issue('critical', 'data',
                              'No bike types configured in game',
                              {'session': game_session1.id})

            # Check suppliers
            from bikeshop.models import Supplier
            suppliers = Supplier.objects.filter(session=game_session1)
            print(f"Suppliers available: {suppliers.count()}")

            if suppliers.count() == 0:
                self.log_issue('critical', 'data',
                              'No suppliers configured in game',
                              {'session': game_session1.id})

        except Exception as e:
            self.log_issue('critical', 'mechanics',
                          'Simulation engine initialization failed',
                          {'error': str(e)})
            import traceback
            traceback.print_exc()

    def generate_report(self):
        """Generate final analysis report"""
        print("\n" + "="*60)
        print("MULTIPLAYER GAME ANALYSIS REPORT")
        print("="*60)

        # Categorize issues
        critical = [i for i in self.issues if i['severity'] == 'critical']
        warnings = [i for i in self.issues if i['severity'] == 'warning']
        info = [i for i in self.issues if i['severity'] == 'info']

        print(f"\nIssues Found: {len(self.issues)} total")
        print(f"  Critical: {len(critical)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Info: {len(info)}")

        if critical:
            print("\n### CRITICAL ISSUES ###")
            for i, issue in enumerate(critical, 1):
                print(f"\n{i}. [{issue['category'].upper()}] {issue['message']}")
                if issue['details']:
                    print(f"   Details: {json.dumps(issue['details'], indent=4)}")

        if warnings:
            print("\n### WARNINGS ###")
            for i, issue in enumerate(warnings, 1):
                print(f"\n{i}. [{issue['category'].upper()}] {issue['message']}")
                if issue['details']:
                    print(f"   Details: {json.dumps(issue['details'], indent=4)}")

        if info:
            print("\n### INFORMATIONAL ###")
            for i, issue in enumerate(info, 1):
                print(f"\n{i}. [{issue['category'].upper()}] {issue['message']}")

        print("\n" + "="*60)
        print("END OF REPORT")
        print("="*60)

    def run_test(self):
        """Run the complete test"""
        try:
            # Setup
            user1, user2 = self.setup_test_users()
            self.game = self.create_game(user1)
            self.player1_session, self.player2_session = self.join_players(self.game, user1, user2)

            # Check if we can proceed
            if not self.player1_session or not self.player2_session:
                print("\n❌ Cannot proceed - player session creation failed")
                self.generate_report()
                return

            # Start game
            self.start_game(self.game)

            # Analyze initial state
            self.analyze_simulation_engine()

            # Try to play a few turns
            for turn in range(1, 4):
                success = self.play_turn(turn)
                if not success:
                    print(f"\n⚠️ Turn {turn} failed - stopping gameplay")
                    break

                self.check_game_state()

            # Final report
            self.generate_report()

        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self.generate_report()


if __name__ == '__main__':
    print("Starting multiplayer game test...")
    tester = MultiplayerGameTester()
    tester.run_test()
