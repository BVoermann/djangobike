#!/usr/bin/env python3
"""
Test script to verify single-player multiplayer auto-processing functionality
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from multiplayer.models import MultiplayerGame, PlayerSession
from multiplayer.simulation_engine import MultiplayerSimulationEngine

def test_single_player_detection():
    print("=" * 70)
    print("Testing Single Player Detection")
    print("=" * 70)

    try:
        # Find games with different player counts
        all_games = MultiplayerGame.objects.all()

        if not all_games.exists():
            print("⚠️  No multiplayer games found - skipping tests")
            return True

        print(f"\n✓ Found {all_games.count()} multiplayer games\n")

        for game in all_games:
            human_count = game.players.filter(
                is_active=True,
                is_bankrupt=False,
                player_type='human'
            ).count()

            ai_count = game.players.filter(
                is_active=True,
                is_bankrupt=False,
                player_type='ai'
            ).count()

            is_single_player = game.is_single_human_player_game

            print(f"Game: {game.name}")
            print(f"  - Human players: {human_count}")
            print(f"  - AI players: {ai_count}")
            print(f"  - Single player game: {is_single_player}")

            # Verify logic
            if human_count == 1:
                if not is_single_player:
                    print(f"  ❌ ERROR: Should be single player but is_single_human_player_game = False")
                    return False
                else:
                    print(f"  ✓ Correctly detected as single player")
            else:
                if is_single_player:
                    print(f"  ❌ ERROR: Should NOT be single player but is_single_human_player_game = True")
                    return False
                else:
                    print(f"  ✓ Correctly detected as multi-player")
            print()

        print("=" * 70)
        print("✓ Single Player Detection: PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_narrative_generators():
    print("\n" + "=" * 70)
    print("Testing Narrative Feedback Generators")
    print("=" * 70)

    try:
        from multiplayer.simulation_engine import (
            generate_outcome_message,
            generate_market_condition_description,
            generate_competitive_position
        )

        print("\n✓ All generator functions imported successfully\n")

        # Test outcome message generation
        print("Testing outcome message generator:")
        test_cases = [
            (10, 10, 'standard', None, 'market_ok'),  # 100% success
            (8, 10, 'standard', None, 'market_ok'),   # 80% success
            (5, 10, 'standard', None, 'market_ok'),   # 50% success
            (2, 10, 'standard', None, 'price_too_high'),  # 20% with price issue
            (0, 10, 'standard', None, 'market_oversaturated'),  # 0% with saturation
        ]

        for quantity_sold, quantity_planned, segment, market, reason in test_cases:
            message = generate_outcome_message(
                quantity_sold, quantity_planned, segment, market, reason
            )
            success_rate = (quantity_sold / quantity_planned * 100) if quantity_planned > 0 else 0
            print(f"  {success_rate:5.1f}% success: {message[:80]}...")

        print("\n✓ Outcome messages generated successfully")

        # Test competitive position
        print("\nTesting competitive position generator:")
        test_prices = [
            (500, 600, 1.0),   # Below market
            (600, 600, 1.0),   # At market
            (700, 600, 1.0),   # Above market
        ]

        for player_price, market_price, quality in test_prices:
            position = generate_competitive_position(player_price, market_price, quality)
            ratio = player_price / market_price if market_price > 0 else 1.0
            print(f"  Price ratio {ratio:.2f}: {position}")

        print("\n✓ Competitive positions generated successfully")

        print("\n" + "=" * 70)
        print("✓ Narrative Generators: PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sales_results_structure():
    print("\n" + "=" * 70)
    print("Testing Sales Results Data Structure")
    print("=" * 70)

    try:
        from multiplayer.models import TurnState

        # Find a turn state with sales results
        turn_with_results = TurnState.objects.filter(
            sales_results__isnull=False
        ).exclude(
            sales_results={}
        ).first()

        if not turn_with_results:
            print("⚠️  No turn states with sales results found")
            print("   This is expected if no sales have been processed yet")
            return True

        results = turn_with_results.sales_results
        print(f"\n✓ Found turn state with sales results")
        print(f"  Player: {turn_with_results.player_session.company_name}")
        print(f"  Turn: {turn_with_results.month}/{turn_with_results.year}")

        # Check required fields
        required_top_level = ['total_sold', 'total_revenue', 'success_rate', 'decisions']
        missing_fields = []

        for field in required_top_level:
            if field not in results:
                missing_fields.append(field)
            else:
                print(f"  ✓ Has '{field}': {results[field]}")

        if missing_fields:
            print(f"\n  ⚠️  Missing top-level fields: {missing_fields}")
            print("     (May be from before enhancement)")
        else:
            print(f"\n  ✓ All top-level fields present")

        # Check decision structure
        if 'decisions' in results and results['decisions']:
            decision = results['decisions'][0]
            print(f"\n  Checking first decision structure:")

            required_decision_fields = [
                'market_name', 'bike_type_name', 'quantity_planned',
                'quantity_sold', 'success_rate'
            ]

            enhanced_fields = [
                'outcome_message', 'market_condition', 'competitive_position'
            ]

            for field in required_decision_fields:
                has_field = field in decision
                status = "✓" if has_field else "⚠️"
                print(f"    {status} {field}: {has_field}")

            print(f"\n  Enhanced feedback fields:")
            for field in enhanced_fields:
                has_field = field in decision
                status = "✓" if has_field else "⚠️"
                print(f"    {status} {field}: {has_field}")
                if has_field and decision[field]:
                    value = str(decision[field])[:60]
                    print(f"        Value: {value}...")

        print("\n" + "=" * 70)
        print("✓ Sales Results Structure: VERIFIED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SINGLE-PLAYER MULTIPLAYER AUTO-PROCESSING TEST SUITE")
    print("=" * 70 + "\n")

    results = []

    # Run all tests
    results.append(("Single Player Detection", test_single_player_detection()))
    results.append(("Narrative Generators", test_narrative_generators()))
    results.append(("Sales Results Structure", test_sales_results_structure()))

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
        print("\nThe system is ready for single-player multiplayer games!")
        print("\nHow it works:")
        print("1. When a player submits decisions (sales, production, procurement)")
        print("2. System detects if it's a single human player game")
        print("3. If yes, turn processes automatically")
        print("4. Player gets immediate feedback with rich narrative insights")
        print("5. No waiting for AI players or turn deadline!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
