from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import json
import uuid

from .models import MultiplayerGame, PlayerSession, TurnState, GameEvent
from bikeshop.models import GameSession


class MultiplayerGameTestCase(TestCase):
    """Test cases for multiplayer game functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='player1',
            password='testpass123',
            email='player1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='player2', 
            password='testpass123',
            email='player2@example.com'
        )
        
        self.client = Client()
    
    def test_create_multiplayer_game(self):
        """Test creating a new multiplayer game"""
        self.client.login(username='player1', password='testpass123')
        
        response = self.client.post(reverse('multiplayer:create_game'), {
            'name': 'Test Game',
            'description': 'A test multiplayer game',
            'max_players': 4,
            'human_players': 2,
            'difficulty': 'medium',
            'turn_deadline': 24,
            'max_months': 60,
            'starting_balance': 80000,
            'bankruptcy_threshold': -50000
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check game was created
        game = MultiplayerGame.objects.get(name='Test Game')
        self.assertEqual(game.created_by, self.user1)
        self.assertEqual(game.max_players, 4)
        self.assertEqual(game.human_players_count, 2)
        self.assertEqual(game.ai_players_count, 2)
        self.assertEqual(game.status, 'setup')
        
        # Check creator was added as first player
        player = PlayerSession.objects.get(multiplayer_game=game, user=self.user1)
        self.assertEqual(player.player_type, 'human')
        self.assertEqual(player.balance, Decimal('80000.00'))
    
    def test_join_multiplayer_game(self):
        """Test joining an existing multiplayer game"""
        # Create game with user1
        game = MultiplayerGame.objects.create(
            name='Test Game',
            created_by=self.user1,
            max_players=4,
            human_players_count=2,
            ai_players_count=2,
            starting_balance=80000
        )
        
        # Add creator as player
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user1,
            company_name="Player1 Corp",
            player_type='human',
            balance=80000
        )
        
        # User2 joins the game
        self.client.login(username='player2', password='testpass123')
        response = self.client.post(
            reverse('multiplayer:join_game', args=[game.id]),
            {'company_name': 'Player2 Industries'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check player2 was added
        player2 = PlayerSession.objects.get(multiplayer_game=game, user=self.user2)
        self.assertEqual(player2.company_name, 'Player2 Industries')
        self.assertEqual(player2.player_type, 'human')
        self.assertEqual(player2.balance, Decimal('80000.00'))
        
        # Check game event was created
        event = GameEvent.objects.filter(
            multiplayer_game=game,
            event_type='player_joined'
        ).first()
        self.assertIsNotNone(event)
        self.assertIn('Player2 Industries', event.message)
    
    def test_start_multiplayer_game(self):
        """Test starting a multiplayer game with AI players"""
        # Create game with 2 human players
        game = MultiplayerGame.objects.create(
            name='Test Game',
            created_by=self.user1,
            max_players=4,
            human_players_count=2,
            ai_players_count=2,
            starting_balance=80000
        )
        
        # Add human players
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user1,
            company_name="Player1 Corp",
            player_type='human',
            balance=80000
        )
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user2,
            company_name="Player2 Corp",
            player_type='human',
            balance=80000
        )
        
        # Start the game
        self.client.login(username='player1', password='testpass123')
        response = self.client.post(reverse('multiplayer:start_game', args=[game.id]))
        
        self.assertEqual(response.status_code, 302)
        
        # Refresh from database
        game.refresh_from_db()
        
        # Check game status changed
        self.assertEqual(game.status, 'active')
        self.assertIsNotNone(game.started_at)
        
        # Check AI players were added
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=game,
            player_type='ai'
        )
        self.assertEqual(ai_players.count(), 2)
        
        # Check AI players have strategies
        for ai_player in ai_players:
            self.assertIsNotNone(ai_player.ai_strategy)
            self.assertEqual(ai_player.balance, Decimal('80000.00'))
    
    def test_game_full_prevention(self):
        """Test that players cannot join a full game"""
        game = MultiplayerGame.objects.create(
            name='Full Game',
            created_by=self.user1,
            max_players=2,
            human_players_count=2,
            ai_players_count=0,
            starting_balance=80000
        )
        
        # Fill the game
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user1,
            company_name="Player1 Corp",
            player_type='human',
            balance=80000
        )
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user2,
            company_name="Player2 Corp", 
            player_type='human',
            balance=80000
        )
        
        # Create third user and try to join
        user3 = User.objects.create_user(
            username='player3',
            password='testpass123'
        )
        
        self.client.login(username='player3', password='testpass123')
        response = self.client.post(
            reverse('multiplayer:join_game', args=[game.id]),
            {'company_name': 'Player3 Corp'}
        )
        
        # Should redirect back to game detail with error
        self.assertEqual(response.status_code, 302)
        
        # Player3 should not be added
        self.assertFalse(
            PlayerSession.objects.filter(
                multiplayer_game=game,
                user=user3
            ).exists()
        )
    
    def test_multiplayer_lobby_view(self):
        """Test the multiplayer lobby view"""
        # Create some games
        available_game = MultiplayerGame.objects.create(
            name='Available Game',
            created_by=self.user2,
            status='waiting',
            max_players=4
        )
        
        user_game = MultiplayerGame.objects.create(
            name='User Game',
            created_by=self.user1,
            max_players=4
        )
        PlayerSession.objects.create(
            multiplayer_game=user_game,
            user=self.user1,
            company_name="My Corp",
            player_type='human'
        )
        
        self.client.login(username='player1', password='testpass123')
        response = self.client.get(reverse('multiplayer:lobby'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available Game')
        self.assertContains(response, 'User Game')
        self.assertIn('available_games', response.context)
        self.assertIn('user_games', response.context)
    
    def test_game_detail_view(self):
        """Test the game detail view"""
        game = MultiplayerGame.objects.create(
            name='Detail Test Game',
            created_by=self.user1,
            description='Test description',
            max_players=4,
            status='active'
        )
        
        player = PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user1,
            company_name="Test Corp",
            player_type='human',
            balance=75000
        )
        
        self.client.login(username='player1', password='testpass123')
        response = self.client.get(reverse('multiplayer:game_detail', args=[game.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Test Game')
        self.assertContains(response, 'Test description')
        self.assertContains(response, 'Test Corp')
        self.assertIn('game', response.context)
        self.assertIn('is_player', response.context)
        self.assertTrue(response.context['is_player'])
    
    def test_leaderboard_view(self):
        """Test the leaderboard view"""
        game = MultiplayerGame.objects.create(
            name='Leaderboard Game',
            created_by=self.user1,
            max_players=4
        )
        
        # Create players with different balances
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user1,
            company_name="First Corp",
            player_type='human',
            balance=90000  # Highest balance
        )
        
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=self.user2,
            company_name="Second Corp",
            player_type='human',
            balance=70000  # Lower balance
        )
        
        self.client.login(username='player1', password='testpass123')
        response = self.client.get(reverse('multiplayer:leaderboard', args=[game.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Corp')
        self.assertContains(response, 'Second Corp')
        self.assertIn('players', response.context)


class PlayerSessionTestCase(TestCase):
    """Test cases for player sessions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testplayer',
            password='testpass123'
        )
        
        self.game = MultiplayerGame.objects.create(
            name='Test Game',
            created_by=self.user,
            max_players=4
        )
    
    def test_player_session_creation(self):
        """Test creating a player session"""
        player = PlayerSession.objects.create(
            multiplayer_game=self.game,
            user=self.user,
            company_name="Test Company",
            player_type='human',
            balance=80000
        )
        
        self.assertEqual(player.multiplayer_game, self.game)
        self.assertEqual(player.user, self.user)
        self.assertEqual(player.company_name, "Test Company")
        self.assertEqual(player.player_type, 'human')
        self.assertEqual(player.balance, Decimal('80000'))
        self.assertFalse(player.is_bankrupt)
        self.assertTrue(player.is_active)
    
    def test_ai_player_creation(self):
        """Test creating an AI player"""
        ai_player = PlayerSession.objects.create(
            multiplayer_game=self.game,
            company_name="AI Corp",
            player_type='ai',
            ai_strategy='balanced',
            ai_difficulty=1.0,
            balance=80000
        )
        
        self.assertIsNone(ai_player.user)
        self.assertEqual(ai_player.player_type, 'ai')
        self.assertEqual(ai_player.ai_strategy, 'balanced')
        self.assertEqual(ai_player.ai_difficulty, 1.0)
    
    def test_bankruptcy_status(self):
        """Test bankruptcy status tracking"""
        player = PlayerSession.objects.create(
            multiplayer_game=self.game,
            user=self.user,
            company_name="Broke Company",
            player_type='human',
            balance=-60000  # Below bankruptcy threshold
        )
        
        # Bankruptcy status would be set by game logic
        player.is_bankrupt = True
        player.save()
        
        self.assertTrue(player.is_bankrupt)
        # Bankrupt players might be marked inactive by game logic
        player.is_active = False
        player.save()
        self.assertFalse(player.is_active)


class GameEventTestCase(TestCase):
    """Test cases for game events"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testplayer',
            password='testpass123'
        )
        
        self.game = MultiplayerGame.objects.create(
            name='Event Test Game',
            created_by=self.user,
            max_players=4
        )
    
    def test_game_event_creation(self):
        """Test creating game events"""
        event = GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='player_joined',
            message='Test player joined the game',
            data={'player_name': 'Test Player'}
        )
        
        self.assertEqual(event.multiplayer_game, self.game)
        self.assertEqual(event.event_type, 'player_joined')
        self.assertIn('Test player', event.message)
        self.assertEqual(event.data['player_name'], 'Test Player')
        self.assertIsNotNone(event.timestamp)
    
    def test_event_ordering(self):
        """Test that events are ordered by timestamp"""
        # Create events in reverse chronological order
        event1 = GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='game_started',
            message='Game started'
        )
        
        event2 = GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='player_joined',
            message='Player joined'
        )
        
        # Get events ordered by timestamp (newest first)
        events = GameEvent.objects.filter(
            multiplayer_game=self.game
        ).order_by('-timestamp')
        
        # Event2 (newer) should come first
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)


class MultiplayerViewPermissionsTestCase(TestCase):
    """Test access controls for multiplayer views"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='creator',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='player',
            password='testpass123'
        )
        
        self.game = MultiplayerGame.objects.create(
            name='Permission Test',
            created_by=self.user1,
            max_players=4
        )
        
        self.client = Client()
    
    def test_login_required(self):
        """Test that multiplayer views require login"""
        # Test lobby view
        response = self.client.get(reverse('multiplayer:lobby'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test game creation
        response = self.client.get(reverse('multiplayer:create_game'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test game detail
        response = self.client.get(reverse('multiplayer:game_detail', args=[self.game.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_start_game_permissions(self):
        """Test that only game creator can start the game"""
        # Add some players
        PlayerSession.objects.create(
            multiplayer_game=self.game,
            user=self.user1,
            company_name="Creator Corp",
            player_type='human'
        )
        PlayerSession.objects.create(
            multiplayer_game=self.game,
            user=self.user2, 
            company_name="Player Corp",
            player_type='human'
        )
        
        # Non-creator tries to start game
        self.client.login(username='player', password='testpass123')
        response = self.client.post(reverse('multiplayer:start_game', args=[self.game.id]))
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Game should still be in setup
        self.game.refresh_from_db()
        self.assertEqual(self.game.status, 'setup')
        
        # Creator should be able to start
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(reverse('multiplayer:start_game', args=[self.game.id]))
        
        self.assertEqual(response.status_code, 302)
        self.game.refresh_from_db()
        self.assertEqual(self.game.status, 'active')
    
    def test_join_own_game_prevention(self):
        """Test that users cannot join their own games multiple times"""
        # Creator already added as player when game was created in a real scenario
        PlayerSession.objects.create(
            multiplayer_game=self.game,
            user=self.user1,
            company_name="Creator Corp",
            player_type='human'
        )
        
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('multiplayer:join_game', args=[self.game.id]),
            {'company_name': 'Another Corp'}
        )
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        
        # Should still have only one session for this user
        sessions = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            user=self.user1
        )
        self.assertEqual(sessions.count(), 1)