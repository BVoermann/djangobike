#!/usr/bin/env python
"""
Comprehensive gameplay test with actual procurement, production, and sales.
"""
import os
import sys
import django
from decimal import Decimal
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from multiplayer.models import MultiplayerGame, PlayerSession, TurnState
from bikeshop.models import GameSession, BikeType, Supplier, SupplierPrice, Component
from production.models import ProducedBike
from sales.models import Market
from warehouse.models import Warehouse, ComponentStock, BikeStock
from procurement.models import ProcurementOrder
from django.db import transaction

User = get_user_model()

def test_full_gameplay():
    """Run full gameplay test"""
    print("\n" + "="*60)
    print("COMPREHENSIVE MULTIPLAYER GAMEPLAY TEST")
    print("="*60)

    issues = []

    # Get the test game
    game = MultiplayerGame.objects.filter(name__icontains="Test Game").first()

    if not game:
        print("ERROR: No test game found")
        return

    print(f"\nGame: {game.name}")
    print(f"Current month: {game.current_month}/{game.current_year}")

    players = PlayerSession.objects.filter(multiplayer_game=game)
    player1 = players[0]
    player2 = players[1]

    print(f"\nPlayers:")
    print(f"  1. {player1.company_name} - Balance: {player1.balance}")
    print(f"  2. {player2.company_name} - Balance: {player2.balance}")

    # Get game sessions
    from multiplayer.player_state_manager import PlayerStateManager
    state_mgr = PlayerStateManager(game)

    gs1 = state_mgr.get_player_game_session(player1)
    gs2 = state_mgr.get_player_game_session(player2)

    print(f"\nGame Sessions:")
    print(f"  1. {gs1.name} - ID: {gs1.id}")
    print(f"  2. {gs2.name} - ID: {gs2.id}")

    # ===  ANALYZE AVAILABLE RESOURCES ===
    print(f"\n=== ANALYZING AVAILABLE RESOURCES ===")

    # Check markets
    markets1 = Market.objects.filter(session=gs1)
    print(f"Player 1 markets: {markets1.count()}")
    for m in markets1:
        print(f"  - {m.name}: {m.location}")

    # Check bike types
    bike_types1 = BikeType.objects.filter(session=gs1)
    print(f"\nPlayer 1 bike types: {bike_types1.count()}")
    for bt in bike_types1[:3]:  # Show first 3
        print(f"  - {bt.name}: Skilled={bt.skilled_worker_hours}h, Unskilled={bt.unskilled_worker_hours}h")

    # Check suppliers
    suppliers1 = Supplier.objects.filter(session=gs1)
    print(f"\nPlayer 1 suppliers: {suppliers1.count()}")
    for s in suppliers1:
        prices = SupplierPrice.objects.filter(session=gs1, supplier=s)
        print(f"  - {s.name}: {prices.count()} components, Quality={s.quality}")

    # Check warehouses
    warehouses1 = Warehouse.objects.filter(session=gs1)
    print(f"\nPlayer 1 warehouses: {warehouses1.count()}")
    for w in warehouses1:
        print(f"  - {w.name}: {w.capacity_m2}m², Rent={w.rent_per_month}€/month")

    # Check component stocks
    stocks1 = ComponentStock.objects.filter(session=gs1)
    print(f"\nPlayer 1 component stocks: {stocks1.count()}")
    if stocks1.exists():
        for s in stocks1[:5]:
            print(f"  - {s.component.name}: {s.quantity} units")

    # Check produced bikes
    bikes1 = ProducedBike.objects.filter(session=gs1)
    print(f"\nPlayer 1 produced bikes: {bikes1.count()}")

    # === ISSUE ANALYSIS ===
    print(f"\n=== ISSUE ANALYSIS ===")

    # 1. Check if players have any components to start with
    if stocks1.count() == 0:
        issues.append({
            'severity': 'warning',
            'category': 'balance',
            'message': 'Players start with no components in warehouse',
            'details': 'Players must procure all components before producing anything'
        })

    # 2. Check initial warehouse capacity
    if warehouses1.count() == 0:
        issues.append({
            'severity': 'critical',
            'category': 'mechanics',
            'message': 'No warehouses initialized for players',
            'details': 'Players cannot store components or bikes without warehouses'
        })
    else:
        total_capacity = sum(w.capacity_m2 for w in warehouses1)
        if total_capacity < 100:
            issues.append({
                'severity': 'warning',
                'category': 'balance',
                'message': 'Very low initial warehouse capacity',
                'details': f'Only {total_capacity}m² available'
            })

    # 3. Check starting balance vs costs
    if suppliers1.exists():
        sample_prices = SupplierPrice.objects.filter(session=gs1, supplier=suppliers1.first())[:5]
        if sample_prices.exists():
            avg_component_cost = sum(float(sp.price) for sp in sample_prices) / len(sample_prices)
            print(f"\nAverage component cost: {avg_component_cost:.2f}€")

            # Estimate cost to build one bike
            if bike_types1.exists():
                sample_bike = bike_types1.first()
                # Typically needs 5-7 components
                estimated_component_cost = avg_component_cost * 6
                print(f"Estimated cost to build one {sample_bike.name}: {estimated_component_cost:.2f}€")

                bikes_buildable = float(gs1.balance) / estimated_component_cost if estimated_component_cost > 0 else 0
                print(f"Bikes buildable with starting capital: ~{int(bikes_buildable)}")

                if bikes_buildable < 10:
                    issues.append({
                        'severity': 'warning',
                        'category': 'balance',
                        'message': 'Low starting capital relative to production costs',
                        'details': f'Can only build ~{int(bikes_buildable)} bikes with starting capital'
                    })

    # 4. Check market demand
    if markets1.exists():
        from sales.models import MarketDemand
        sample_market = markets1.first()
        demands = MarketDemand.objects.filter(market=sample_market)
        if demands.exists():
            total_demand = sum(d.quantity for d in demands)
            print(f"\nTotal monthly demand in {sample_market.name}: {total_demand} bikes")

            if total_demand < 10:
                issues.append({
                    'severity': 'warning',
                    'category': 'balance',
                    'message': 'Low market demand may make sales difficult',
                    'details': f'Only {total_demand} bikes demanded per month in sample market'
                })
        else:
            issues.append({
                'severity': 'critical',
                'category': 'data',
                'message': 'No market demand data configured',
                'details': f'Market {sample_market.name} has no demand entries'
            })

    # 5. Check for workers
    from bikeshop.models import Worker
    workers1 = Worker.objects.filter(session=gs1)
    print(f"\nWorkers: {workers1.count()}")
    if workers1.count() == 0:
        issues.append({
            'severity': 'critical',
            'category': 'mechanics',
            'message': 'No workers initialized',
            'details': 'Cannot produce bikes without workers'
        })
    else:
        for w in workers1:
            monthly_hours = w.hours_per_week * 4
            print(f"  - {w.get_worker_type_display()}: {monthly_hours}h/month @ {w.hourly_wage}€/h")

    # 6. Check GameParameters
    from multiplayer.models import GameParameters
    try:
        params = GameParameters.objects.get(multiplayer_game=game)
        print(f"\nGame Parameters: Found (ID: {params.id})")
    except GameParameters.DoesNotExist:
        print(f"\nGame Parameters: NOT FOUND")
        issues.append({
            'severity': 'warning',
            'category': 'mechanics',
            'message': 'GameParameters object not created',
            'details': 'This causes repeated "No GameParameters found" warnings'
        })

    # 7. Check if both players share the same data or have separate data
    markets2 = Market.objects.filter(session=gs2)
    suppliers2 = Supplier.objects.filter(session=gs2)

    print(f"\nData Isolation Check:")
    print(f"  Player 1 markets: {markets1.count()}")
    print(f"  Player 2 markets: {markets2.count()}")
    print(f"  Player 1 suppliers: {suppliers1.count()}")
    print(f"  Player 2 suppliers: {suppliers2.count()}")

    if markets1.count() != markets2.count():
        issues.append({
            'severity': 'warning',
            'category': 'mechanics',
            'message': 'Players have different market counts',
            'details': f'P1: {markets1.count()}, P2: {markets2.count()}'
        })

    # 8. Check procurement orders
    orders1 = ProcurementOrder.objects.filter(session=gs1)
    print(f"\nProcurement orders (Player 1): {orders1.count()}")

    # 9. Test balance tracking
    print(f"\nBalance Tracking:")
    print(f"  Player 1 session balance: {gs1.balance}")
    print(f"  Player 1 PlayerSession balance: {player1.balance}")

    if gs1.balance != player1.balance:
        issues.append({
            'severity': 'critical',
            'category': 'data',
            'message': 'Balance mismatch between GameSession and PlayerSession',
            'details': f'GameSession: {gs1.balance}, PlayerSession: {player1.balance}'
        })

    # === GENERATE REPORT ===
    print(f"\n" + "="*60)
    print("ANALYSIS REPORT")
    print("="*60)

    critical = [i for i in issues if i['severity'] == 'critical']
    warnings = [i for i in issues if i['severity'] == 'warning']
    info = [i for i in issues if i['severity'] == 'info']

    print(f"\nIssues Found: {len(issues)} total")
    print(f"  Critical: {len(critical)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info: {len(info)}")

    if critical:
        print("\n### CRITICAL ISSUES ###")
        for i, issue in enumerate(critical, 1):
            print(f"\n{i}. [{issue['category'].upper()}] {issue['message']}")
            print(f"   {issue['details']}")

    if warnings:
        print("\n### WARNINGS ###")
        for i, issue in enumerate(warnings, 1):
            print(f"\n{i}. [{issue['category'].upper()}] {issue['message']}")
            print(f"   {issue['details']}")

    print(f"\n" + "="*60)
    print("END OF REPORT")
    print("="*60)

    return issues

if __name__ == '__main__':
    test_full_gameplay()
