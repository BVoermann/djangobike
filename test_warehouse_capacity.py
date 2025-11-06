#!/usr/bin/env python3
"""
Test script to verify warehouse capacity limits are properly enforced
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from django.contrib.auth import get_user_model
from bikeshop.models import GameSession, Component, ComponentType, BikeType, Supplier, SupplierPrice
from warehouse.models import Warehouse, ComponentStock, BikeStock
from production.models import ProducedBike
from decimal import Decimal

User = get_user_model()

def test_warehouse_capacity():
    print("=" * 60)
    print("Testing Warehouse Capacity Enforcement")
    print("=" * 60)

    # Get a test user and session
    try:
        user = User.objects.filter(is_superuser=False).first()
        if not user:
            print("❌ No test user found. Creating one...")
            user = User.objects.create_user(username='testuser', password='testpass123')

        session = GameSession.objects.filter(user=user).first()
        if not session:
            print("❌ No game session found for user. Please create a session first.")
            return False

        print(f"✓ Using session: {session.id} (User: {user.username})")

        # Get warehouses for this session
        warehouses = Warehouse.objects.filter(session=session)
        if not warehouses.exists():
            print("❌ No warehouses found. Creating a small test warehouse...")
            warehouse = Warehouse.objects.create(
                session=session,
                name='Test Warehouse',
                location='Test Location',
                capacity_m2=10.0,  # Very small capacity for testing
                rent_per_month=Decimal('100.00')
            )
        else:
            warehouse = warehouses.first()

        print(f"✓ Using warehouse: {warehouse.name} (Capacity: {warehouse.capacity_m2}m²)")
        print(f"  Current usage: {warehouse.current_usage:.1f}m² ({warehouse.usage_percentage:.1f}%)")
        print(f"  Remaining: {warehouse.remaining_capacity:.1f}m²")

        # Test 1: Check if we can calculate capacity correctly
        print("\n" + "=" * 60)
        print("Test 1: Verify capacity calculation")
        print("=" * 60)

        # Get component stocks
        component_stocks = ComponentStock.objects.filter(session=session, warehouse=warehouse)
        if component_stocks.exists():
            print(f"✓ Found {component_stocks.count()} component stocks in warehouse:")
            total_component_space = 0
            for stock in component_stocks:
                space = stock.quantity * stock.component.component_type.storage_space_per_unit
                total_component_space += space
                print(f"  - {stock.component.name}: {stock.quantity} units × {stock.component.component_type.storage_space_per_unit:.2f}m² = {space:.2f}m²")
            print(f"  Total component space: {total_component_space:.1f}m²")
        else:
            print("  No component stocks found")

        # Get bike stocks
        bike_stocks = BikeStock.objects.filter(session=session, warehouse=warehouse)
        if bike_stocks.exists():
            print(f"✓ Found {bike_stocks.count()} bikes in warehouse:")
            total_bike_space = 0
            for stock in bike_stocks:
                space = stock.bike.bike_type.storage_space_per_unit
                total_bike_space += space
                print(f"  - {stock.bike.bike_type.name}: {space:.2f}m²")
            print(f"  Total bike space: {total_bike_space:.1f}m²")
        else:
            print("  No bike stocks found")

        calculated_usage = warehouse.current_usage
        print(f"\n✓ Calculated usage: {calculated_usage:.1f}m²")
        print(f"✓ Usage percentage: {warehouse.usage_percentage:.1f}%")

        if warehouse.usage_percentage > 100:
            print("❌ FAIL: Warehouse is over 100% capacity!")
            return False
        else:
            print("✓ PASS: Warehouse is within capacity limits")

        # Test 2: Verify capacity methods work correctly
        print("\n" + "=" * 60)
        print("Test 2: Test warehouse capacity check methods")
        print("=" * 60)

        # Get a component to test with
        components = Component.objects.filter(session=session)
        if components.exists():
            test_component = components.first()
            test_quantity = 10

            required_space = warehouse.get_required_space_for_components(test_component, test_quantity)
            can_store = warehouse.can_store_components(test_component, test_quantity)

            print(f"Test component: {test_component.name}")
            print(f"Test quantity: {test_quantity}")
            print(f"Required space: {required_space:.1f}m²")
            print(f"Remaining capacity: {warehouse.remaining_capacity:.1f}m²")
            print(f"Can store: {can_store}")

            if can_store and required_space > warehouse.remaining_capacity:
                print("❌ FAIL: can_store_components returned True but there's not enough space!")
                return False
            elif not can_store and required_space <= warehouse.remaining_capacity:
                print("❌ FAIL: can_store_components returned False but there is enough space!")
                return False
            else:
                print("✓ PASS: Capacity check methods work correctly")

        # Test 3: Check bike capacity methods
        bike_types = BikeType.objects.filter(session=session)
        if bike_types.exists():
            test_bike = bike_types.first()
            test_quantity = 5

            required_space = warehouse.get_required_space_for_bikes(test_bike, test_quantity)
            can_store = warehouse.can_store_bikes(test_bike, test_quantity)

            print(f"\nTest bike type: {test_bike.name}")
            print(f"Test quantity: {test_quantity}")
            print(f"Required space: {required_space:.1f}m²")
            print(f"Can store: {can_store}")

            if can_store and required_space > warehouse.remaining_capacity:
                print("❌ FAIL: can_store_bikes returned True but there's not enough space!")
                return False
            elif not can_store and required_space <= warehouse.remaining_capacity:
                print("❌ FAIL: can_store_bikes returned False but there is enough space!")
                return False
            else:
                print("✓ PASS: Bike capacity check methods work correctly")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_warehouse_capacity()
    sys.exit(0 if success else 1)
