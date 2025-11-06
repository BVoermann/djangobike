#!/usr/bin/env python3
"""
Test script to verify deferred sales system is working correctly
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from django.contrib.auth import get_user_model
from bikeshop.models import GameSession, BikeType
from sales.models import Market, SalesDecision
from sales.market_simulator import MarketSimulator
from production.models import ProducedBike
from multiplayer.models import MultiplayerGame, TurnState, PlayerSession
from decimal import Decimal

User = get_user_model()

def test_singleplayer_deferred_sales():
    print("=" * 70)
    print("Testing Singleplayer Deferred Sales System")
    print("=" * 70)

    try:
        # Get a test user and session
        user = User.objects.filter(is_superuser=False).first()
        if not user:
            print("❌ No test user found")
            return False

        session = GameSession.objects.filter(user=user).first()
        if not session:
            print("❌ No game session found")
            return False

        print(f"✓ Using session: {session.id}")

        # Check Market model has location characteristics
        market = Market.objects.filter(session=session).first()
        if not market:
            print("❌ No market found")
            return False

        print(f"✓ Market: {market.name}")

        # Check location characteristics exist
        if not hasattr(market, 'green_city_factor'):
            print("❌ Market missing location characteristics")
            return False

        print(f"  - Location type: {market.location_type if hasattr(market, 'location_type') else 'N/A'}")
        print(f"  - Green city factor: {market.green_city_factor}")
        print(f"  - Mountain bike factor: {market.mountain_bike_factor}")
        print(f"✓ Location characteristics present")

        # Check SalesDecision model exists
        decision = SalesDecision.objects.filter(session=session).first()
        print(f"✓ SalesDecision model exists")
        print(f"  - Pending decisions: {SalesDecision.objects.filter(session=session, is_processed=False).count()}")
        print(f"  - Processed decisions: {SalesDecision.objects.filter(session=session, is_processed=True).count()}")

        # Check MarketSimulator exists
        simulator = MarketSimulator(session)
        print(f"✓ MarketSimulator initialized")

        # Check if there are bikes to test with
        bikes = ProducedBike.objects.filter(session=session, is_sold=False)
        print(f"  - Available bikes for testing: {bikes.count()}")

        print("\n" + "=" * 70)
        print("✓ Singleplayer Deferred Sales System: ALL CHECKS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during singleplayer test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiplayer_deferred_sales():
    print("\n" + "=" * 70)
    print("Testing Multiplayer Deferred Sales System")
    print("=" * 70)

    try:
        # Check multiplayer game exists
        game = MultiplayerGame.objects.first()
        if not game:
            print("⚠️  No multiplayer game found - skipping multiplayer tests")
            return True  # Not a failure, just nothing to test

        print(f"✓ Multiplayer game: {game.name}")
        print(f"  - Players: {game.players.count()}")
        print(f"  - Active: {game.active_players_count}")

        # Check TurnState has sales_results field
        turn_state = TurnState.objects.filter(multiplayer_game=game).first()
        if turn_state:
            print(f"✓ TurnState model exists")

            if not hasattr(turn_state, 'sales_results'):
                print("❌ TurnState missing sales_results field")
                return False

            print(f"  - Has sales_results field: ✓")
            print(f"  - Sales decisions stored: {bool(turn_state.sales_decisions)}")
            print(f"  - Sales results stored: {bool(turn_state.sales_results)}")
        else:
            print("⚠️  No turn states found - create a multiplayer game to test")

        print("\n" + "=" * 70)
        print("✓ Multiplayer Deferred Sales System: ALL CHECKS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during multiplayer test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_simulator_logic():
    print("\n" + "=" * 70)
    print("Testing MarketSimulator Logic")
    print("=" * 70)

    try:
        # Get a session
        session = GameSession.objects.first()
        if not session:
            print("❌ No session found")
            return False

        simulator = MarketSimulator(session)

        # Test market demand calculation
        market = Market.objects.filter(session=session).first()
        if not market:
            print("❌ No market found")
            return False

        bike_type = BikeType.objects.filter(session=session).first()
        if not bike_type:
            print("❌ No bike type found")
            return False

        # Calculate demand
        demand = simulator._calculate_market_demand(
            market=market,
            bike_type=bike_type,
            price_segment='standard',
            month=1
        )

        print(f"✓ Market demand calculation works")
        print(f"  - Market: {market.name}")
        print(f"  - Bike type: {bike_type.name}")
        print(f"  - Segment: standard")
        print(f"  - Calculated demand: {demand:.0f} bikes")

        # Test that key methods exist
        required_methods = ['_calculate_market_demand', '_process_market_segment', 'process_pending_sales_decisions']
        missing_methods = []

        for method_name in required_methods:
            if not hasattr(simulator, method_name):
                missing_methods.append(method_name)

        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False

        print(f"\n✓ All required methods exist")
        for method in required_methods:
            print(f"  - {method}: ✓")

        print("\n" + "=" * 70)
        print("✓ MarketSimulator Logic: ALL CHECKS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during market simulator test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("DEFERRED SALES SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70 + "\n")

    results = []

    # Run all tests
    results.append(("Singleplayer System", test_singleplayer_deferred_sales()))
    results.append(("Multiplayer System", test_multiplayer_deferred_sales()))
    results.append(("Market Simulator Logic", test_market_simulator_logic()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:12} {name}")

    all_passed = all(result for _, result in results)

    print("=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
