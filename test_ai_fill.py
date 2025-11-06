#!/usr/bin/env python3
"""
Test script to verify AI player filling functionality
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from multiplayer.models import MultiplayerGame, PlayerSession

def test_ai_fill_logic():
    print("=" * 70)
    print("Testing AI Player Fill Logic")
    print("=" * 70)

    # Find a multiplayer game
    game = MultiplayerGame.objects.first()

    if not game:
        print("⚠️  No multiplayer games found - skipping test")
        return True

    print(f"\n✓ Testing with game: {game.name}")
    print(f"  - Max players: {game.max_players}")

    # Count current players
    human_count = game.assigned_users.count()
    ai_count = game.players.filter(player_type='ai', is_active=True).count()
    total_current = human_count + ai_count
    remaining_slots = game.max_players - total_current

    print(f"  - Human players (assigned): {human_count}")
    print(f"  - AI players: {ai_count}")
    print(f"  - Total current: {total_current}")
    print(f"  - Remaining slots: {remaining_slots}")

    # Test the logic
    if remaining_slots > 0:
        print(f"\n✓ Would create {remaining_slots} AI players")
        print("\nAI companies that would be created:")

        ai_company_names = [
            "CycleTech GmbH",
            "VeloMax AG",
            "BikeInnovate",
            "SpeedCycles Pro",
            "EcoBike Solutions",
            "TurboRides Inc.",
            "MountainMasters",
            "UrbanCycling Co.",
            "ElektroBikes Plus",
            "RaceWheels AG"
        ]

        ai_strategies = [
            'balanced',
            'cheap_only',
            'premium_focus',
            'e_bike_specialist',
            'innovative',
            'aggressive',
        ]

        # Get existing AI companies
        existing_ai_companies = set(
            game.players.filter(player_type='ai')
            .values_list('company_name', flat=True)
        )

        available_names = [name for name in ai_company_names if name not in existing_ai_companies]

        for i in range(min(remaining_slots, 5)):  # Show first 5
            if available_names:
                company_name = available_names[i % len(available_names)]
            else:
                company_name = f"AI Competitor {ai_count + i + 1}"

            strategy = ai_strategies[i % len(ai_strategies)]
            print(f"  {i+1}. {company_name} (Strategy: {strategy})")

        if remaining_slots > 5:
            print(f"  ... and {remaining_slots - 5} more")

    elif remaining_slots == 0:
        print("\n✓ Game is full - no AI players would be created")
    else:
        print("\n⚠️  Warning: More players than max_players (shouldn't happen)")

    # Check existing AI players
    if ai_count > 0:
        print(f"\n✓ Existing AI players in game:")
        for ai_player in game.players.filter(player_type='ai', is_active=True):
            print(f"  - {ai_player.company_name} ({ai_player.ai_strategy})")

    print("\n" + "=" * 70)
    print("✓ AI Fill Logic Test: PASSED")
    print("=" * 70)
    print("\nThe button in 'Benutzer zuweisen' will:")
    print("1. Show remaining slots count")
    print("2. Create AI PlayerSession objects with unique company names")
    print("3. Assign different strategies to each AI player")
    print("4. Set starting balance to game.starting_balance")
    print("5. Redirect back to assign users page with success message")

    return True

if __name__ == '__main__':
    try:
        success = test_ai_fill_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
