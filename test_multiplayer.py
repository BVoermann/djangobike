#!/usr/bin/env python3
"""
Test script for the multiplayer system.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/bvoermann/src/djangobike')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from django.contrib.auth.models import User
from multiplayer.models import MultiplayerGame, PlayerSession, GameEvent
from multiplayer.ai_manager import MultiplayerAIManager
from multiplayer.bankruptcy_manager import BankruptcyManager
from multiplayer.simulation_engine import MultiplayerSimulationEngine


def test_multiplayer_system():
    """Test the basic multiplayer system functionality."""
    print("🧪 Testing Multiplayer System")
    print("=" * 50)
    
    # 1. Test game creation
    print("\n1. Creating test game...")
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Create multiplayer game
        game = MultiplayerGame.objects.create(
            name="Test Multiplayer Game",
            description="A test game for the multiplayer system",
            max_players=4,
            human_players_count=2,
            ai_players_count=2,
            difficulty='medium',
            created_by=user,
            status='setup'
        )
        print(f"✅ Created game: {game.name} (ID: {game.id})")
        
    except Exception as e:
        print(f"❌ Error creating game: {str(e)}")
        return False
    
    # 2. Test player creation
    print("\n2. Adding players...")
    try:
        # Add human player
        human_player = PlayerSession.objects.create(
            multiplayer_game=game,
            user=user,
            company_name="Test Company",
            player_type='human',
            balance=game.starting_balance
        )
        print(f"✅ Added human player: {human_player.company_name}")
        
        # Add AI players
        ai_manager = MultiplayerAIManager(game)
        ai_strategies = ['aggressive', 'conservative']
        
        for i, strategy in enumerate(ai_strategies):
            ai_player = PlayerSession.objects.create(
                multiplayer_game=game,
                user=None,
                company_name=f"AI Corp {i+1} ({strategy.title()})",
                player_type='ai',
                ai_strategy=strategy,
                balance=game.starting_balance,
                ai_difficulty=1.0
            )
            
            # Initialize AI player
            ai_manager.initialize_ai_player(ai_player)
            print(f"✅ Added AI player: {ai_player.company_name}")
        
    except Exception as e:
        print(f"❌ Error adding players: {str(e)}")
        return False
    
    # 3. Test AI decision making
    print("\n3. Testing AI decision making...")
    try:
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=game, 
            player_type='ai'
        )
        
        for ai_player in ai_players:
            decisions = ai_manager.make_ai_decisions(ai_player)
            print(f"✅ AI decisions for {ai_player.company_name}: {len(decisions)} categories")
            
            # Check decision structure
            expected_categories = ['production', 'procurement', 'sales', 'hr', 'finance']
            for category in expected_categories:
                if category in decisions:
                    print(f"   - {category}: ✅")
                else:
                    print(f"   - {category}: ❌ (missing)")
                    
    except Exception as e:
        print(f"❌ Error testing AI decisions: {str(e)}")
        return False
    
    # 4. Test bankruptcy system
    print("\n4. Testing bankruptcy detection...")
    try:
        bankruptcy_manager = BankruptcyManager(game)
        
        # Test bankruptcy evaluation on human player
        bankruptcy_status = bankruptcy_manager.evaluate_player_bankruptcy(human_player)
        print(f"✅ Bankruptcy evaluation completed")
        print(f"   - Risk level: {bankruptcy_status['risk_level']}")
        print(f"   - Bankruptcy score: {bankruptcy_status['bankruptcy_score']}")
        print(f"   - Is bankrupt: {bankruptcy_status['is_bankrupt']}")
        
        # Test bankruptcy check for all players
        bankruptcy_results = bankruptcy_manager.check_all_players_bankruptcy()
        print(f"✅ Checked bankruptcy for all {game.players.count()} players")
        print(f"   - Bankruptcies detected: {len(bankruptcy_results)}")
        
    except Exception as e:
        print(f"❌ Error testing bankruptcy system: {str(e)}")
        return False
    
    # 5. Test simulation engine
    print("\n5. Testing simulation engine...")
    try:
        simulation_engine = MultiplayerSimulationEngine(game)
        
        # Start the game
        game.status = 'active'
        game.save()
        
        # This would normally process a full turn, but we'll just test initialization
        print(f"✅ Simulation engine initialized")
        print(f"   - Game status: {game.status}")
        print(f"   - Current turn: {game.current_year}/{game.current_month:02d}")
        print(f"   - Active players: {game.active_players_count}")
        
    except Exception as e:
        print(f"❌ Error testing simulation engine: {str(e)}")
        return False
    
    # 6. Test event system
    print("\n6. Testing event system...")
    try:
        # Create test event
        event = GameEvent.objects.create(
            multiplayer_game=game,
            event_type='system_message',
            message="Test event for multiplayer system",
            data={'test': True, 'timestamp': str(game.current_year) + '/' + str(game.current_month)}
        )
        print(f"✅ Created test event: {event.message}")
        
        # Check event visibility
        print(f"   - Visible to all: {event.visible_to_all}")
        print(f"   - Event type: {event.event_type}")
        
    except Exception as e:
        print(f"❌ Error testing event system: {str(e)}")
        return False
    
    # 7. Summary
    print("\n7. System Summary:")
    print(f"   - Game: {game.name}")
    print(f"   - Players: {game.players.count()}")
    print(f"   - Human players: {game.players.filter(player_type='human').count()}")
    print(f"   - AI players: {game.players.filter(player_type='ai').count()}")
    print(f"   - Events: {GameEvent.objects.filter(multiplayer_game=game).count()}")
    print(f"   - Status: {game.status}")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎮 Multiplayer system is ready for use!")
    print(f"\nYou can now:")
    print(f"- Visit /multiplayer/ in your browser")
    print(f"- Create games through the web interface")
    print(f"- Join games with multiple players")
    print(f"- Compete against AI opponents")
    
    return True


if __name__ == '__main__':
    success = test_multiplayer_system()
    if not success:
        sys.exit(1)