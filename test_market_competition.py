#!/usr/bin/env python3
"""
Test script for the enhanced market competition system
"""

import os
import sys
import django
from django.db import transaction
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from bikeshop.models import GameSession, BikeType
from sales.models import Market, MarketDemand, MarketPriceSensitivity
from competitors.models import AICompetitor, CompetitorProduction, MarketCompetition
from production.models import ProducedBike
from simulation.market_volume_engine import MarketVolumeEngine
from simulation.competitive_sales_engine import CompetitiveSalesEngine
from warehouse.models import Warehouse

def create_test_session():
    """Create a test session with basic data"""
    print("Creating test session...")
    
    # Create a user for the session (required field)
    from django.contrib.auth.models import User
    test_user, created = User.objects.get_or_create(
        username="test_user",
        defaults={"email": "test@example.com"}
    )
    
    session = GameSession.objects.create(
        user=test_user,
        name="Market Competition Test",
        current_month=1,
        current_year=2024,
        balance=Decimal('50000.00')
    )
    
    # Create a test warehouse
    warehouse = Warehouse.objects.create(
        session=session,
        name="Test Warehouse",
        location="Test Location",
        capacity_m2=1000.0,
        rent_per_month=Decimal('1000.00')
    )
    
    # Create bike types
    city_bike = BikeType.objects.create(
        session=session,
        name="City Bike Standard",
        skilled_worker_hours=2.0,
        unskilled_worker_hours=3.0,
        storage_space_per_unit=2.0
    )
    
    e_bike = BikeType.objects.create(
        session=session,
        name="E-Bike Premium",
        skilled_worker_hours=4.0,
        unskilled_worker_hours=2.0,
        storage_space_per_unit=2.5
    )
    
    # Create markets
    market_berlin = Market.objects.create(
        session=session,
        name="Berlin",
        location="Germany",
        transport_cost_home=Decimal('50.00'),
        transport_cost_foreign=Decimal('150.00'),
        monthly_volume_capacity=300,
        price_elasticity_factor=1.0
    )
    
    market_munich = Market.objects.create(
        session=session,
        name="Munich",
        location="Germany", 
        transport_cost_home=Decimal('80.00'),
        transport_cost_foreign=Decimal('180.00'),
        monthly_volume_capacity=250,
        price_elasticity_factor=1.2
    )
    
    # Create market demand
    MarketDemand.objects.create(
        session=session,
        market=market_berlin,
        bike_type=city_bike,
        demand_percentage=0.4
    )
    
    MarketDemand.objects.create(
        session=session,
        market=market_berlin,
        bike_type=e_bike,
        demand_percentage=0.3
    )
    
    # Create price sensitivity
    for market in [market_berlin, market_munich]:
        MarketPriceSensitivity.objects.create(
            session=session,
            market=market,
            price_segment='cheap',
            percentage=50.0
        )
        MarketPriceSensitivity.objects.create(
            session=session,
            market=market,
            price_segment='standard',
            percentage=30.0
        )
        MarketPriceSensitivity.objects.create(
            session=session,
            market=market,
            price_segment='premium',
            percentage=20.0
        )
    
    # Create AI competitors
    competitor1 = AICompetitor.objects.create(
        session=session,
        name="BudgetBikes Corp",
        strategy='cheap_only',
        financial_resources=Decimal('40000.00'),
        market_presence=15.0,
        aggressiveness=0.8,
        efficiency=0.7
    )
    
    competitor2 = AICompetitor.objects.create(
        session=session,
        name="PremiumCycles Ltd",
        strategy='premium_focus',
        financial_resources=Decimal('60000.00'),
        market_presence=12.0,
        aggressiveness=0.4,
        efficiency=0.9
    )
    
    print(f"Created test session: {session.id}")
    print(f"Created {BikeType.objects.filter(session=session).count()} bike types")
    print(f"Created {Market.objects.filter(session=session).count()} markets")
    print(f"Created {AICompetitor.objects.filter(session=session).count()} competitors")
    
    return session

def test_market_volume_engine(session):
    """Test the market volume engine"""
    print("\nTesting MarketVolumeEngine...")
    
    engine = MarketVolumeEngine(session)
    engine.calculate_market_volume_for_period(1, 2024)
    
    # Check if market competitions were created
    competitions = MarketCompetition.objects.filter(session=session)
    print(f"Created {competitions.count()} market competition records")
    
    for comp in competitions[:5]:  # Show first 5
        print(f"  {comp.market.name} - {comp.bike_type.name} ({comp.price_segment}): "
              f"Demand={comp.estimated_demand}, MaxVolume={comp.maximum_market_volume}, "
              f"Elasticity={comp.demand_curve_elasticity:.2f}")
    
    return competitions

def test_competitor_production(session):
    """Test competitor production and inventory"""
    print("\nTesting competitor production...")
    
    # Create some competitor productions
    competitors = AICompetitor.objects.filter(session=session)
    bike_types = BikeType.objects.filter(session=session)
    
    for competitor in competitors:
        for bike_type in bike_types:
            for segment in ['cheap', 'standard']:
                CompetitorProduction.objects.create(
                    competitor=competitor,
                    bike_type=bike_type,
                    price_segment=segment,
                    month=1,
                    year=2024,
                    quantity_planned=10,
                    quantity_produced=8,
                    quantity_in_inventory=8,
                    production_cost_per_unit=Decimal('300.00'),
                    months_in_inventory=0
                )
    
    productions = CompetitorProduction.objects.filter(competitor__session=session)
    print(f"Created {productions.count()} competitor production records")
    
    for prod in productions[:3]:  # Show first 3
        print(f"  {prod.competitor.name} - {prod.bike_type.name} ({prod.price_segment}): "
              f"Produced={prod.quantity_produced}, Inventory={prod.quantity_in_inventory}")

def test_player_bikes(session):
    """Create some player bikes for testing"""
    print("\nCreating player bikes...")
    
    bike_types = BikeType.objects.filter(session=session)
    warehouse = Warehouse.objects.filter(session=session).first()
    
    for bike_type in bike_types:
        for segment in ['standard', 'premium']:
            for i in range(3):  # 3 bikes of each type/segment
                ProducedBike.objects.create(
                    session=session,
                    bike_type=bike_type,
                    price_segment=segment,
                    production_month=1,
                    production_year=2024,
                    warehouse=warehouse,
                    production_cost=Decimal('400.00'),
                    months_in_inventory=0,
                    storage_cost_accumulated=Decimal('0.00')
                )
    
    player_bikes = ProducedBike.objects.filter(session=session, is_sold=False)
    print(f"Created {player_bikes.count()} player bikes")

def test_player_sales_orders(session):
    """Create some player sales orders"""
    print("\nCreating player sales orders...")
    
    from sales.models import SalesOrder
    
    # Get some bikes and markets to create sales orders
    bikes = ProducedBike.objects.filter(session=session, is_sold=False)[:6]  # Use 6 bikes
    markets = Market.objects.filter(session=session)
    
    orders_created = 0
    for bike in bikes:
        for market in markets[:1]:  # Use only first market to keep it simple
            # Create sales order
            SalesOrder.objects.create(
                session=session,
                market=market,
                bike=bike,
                sale_month=1,
                sale_year=2024,
                sale_price=Decimal('800.00'),
                transport_cost=market.transport_cost_home,
                is_completed=False
            )
            orders_created += 1
    
    print(f"Created {orders_created} player sales orders")

def test_competitive_sales(session):
    """Test the competitive sales engine"""
    print("\nTesting competitive sales engine...")
    
    engine = CompetitiveSalesEngine(session)
    
    # Process competitive sales
    engine.process_competitive_sales(1, 2024)
    
    # Check results
    competitions = MarketCompetition.objects.filter(session=session, month=1, year=2024)
    print(f"Market competitions processed: {competitions.count()}")
    
    for comp in competitions[:3]:  # Show first 3
        print(f"  {comp.market.name} - {comp.bike_type.name} ({comp.price_segment}): "
              f"Supply={comp.total_supply}, Sold={comp.actual_sales_volume}, "
              f"Saturation={comp.saturation_level:.2f}, Price Pressure={comp.price_pressure:.2f}")

def test_inventory_aging(session):
    """Test inventory aging mechanism"""
    print("\nTesting inventory aging...")
    
    # Fast-forward time and test aging
    session.current_month = 4
    session.current_year = 2024
    session.save()
    
    # Update all bike ages
    bikes = ProducedBike.objects.filter(session=session, is_sold=False)
    for bike in bikes:
        bike.update_inventory_age(session.current_month, session.current_year)
    
    # Show aging results
    aged_bikes = ProducedBike.objects.filter(session=session, months_in_inventory__gt=0)
    print(f"Bikes with aging: {aged_bikes.count()}")
    
    for bike in aged_bikes[:3]:  # Show first 3
        print(f"  {bike.bike_type.name} ({bike.price_segment}): "
              f"Age={bike.months_in_inventory} months, "
              f"Storage Cost={bike.storage_cost_accumulated}, "
              f"Age Penalty={bike.get_age_penalty_factor():.2f}")

def run_full_test():
    """Run complete test suite"""
    try:
        print("=== Market Competition System Test ===")
        
        # Clean up any existing test data
        GameSession.objects.filter(name="Market Competition Test").delete()
        
        with transaction.atomic():
            # Create test environment
            session = create_test_session()
            
            # Test individual components
            competitions = test_market_volume_engine(session)
            test_competitor_production(session)
            test_player_bikes(session)
            test_player_sales_orders(session)
            test_competitive_sales(session)
            test_inventory_aging(session)
            
            print("\n=== Test Summary ===")
            print(f"Session ID: {session.id}")
            print(f"Markets: {Market.objects.filter(session=session).count()}")
            print(f"Bike Types: {BikeType.objects.filter(session=session).count()}")
            print(f"Competitors: {AICompetitor.objects.filter(session=session).count()}")
            print(f"Market Competitions: {MarketCompetition.objects.filter(session=session).count()}")
            print(f"Player Bikes: {ProducedBike.objects.filter(session=session).count()}")
            print(f"Competitor Productions: {CompetitorProduction.objects.filter(competitor__session=session).count()}")
            
            print(f"\nFinal Session Balance: {session.balance}")
            
            print("\n✅ All tests completed successfully!")
            print("The enhanced market competition system is ready to use.")
            
        return session
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    session = run_full_test()