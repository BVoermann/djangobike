from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
import json

from bikeshop.models import (
    GameSession, Supplier, Component, ComponentType, 
    SupplierPrice, BikeType
)
from procurement.models import ProcurementOrder, ProcurementOrderItem
from warehouse.models import Warehouse, ComponentStock


class ProcurementDropdownFilteringTestCase(TestCase):
    """Test dropdown menus and filtering functionality in the Einkauf (Procurement) tab"""
    
    def setUp(self):
        """Set up test data for dropdown filtering tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Dropdown Test Session',
            current_month=1,
            current_year=2024,
            balance=Decimal('80000.00')
        )
        
        # Create comprehensive component types
        self.wheel_set_type = ComponentType.objects.create(
            session=self.session,
            name='Laufradsatz',
            storage_space_per_unit=2.5
        )
        
        self.frame_type = ComponentType.objects.create(
            session=self.session,
            name='Rahmen',
            storage_space_per_unit=3.0
        )
        
        self.handlebar_type = ComponentType.objects.create(
            session=self.session,
            name='Lenker',
            storage_space_per_unit=0.5
        )
        
        self.saddle_type = ComponentType.objects.create(
            session=self.session,
            name='Sattel',
            storage_space_per_unit=0.3
        )
        
        self.gearshift_type = ComponentType.objects.create(
            session=self.session,
            name='Schaltung',
            storage_space_per_unit=0.8
        )
        
        self.motor_type = ComponentType.objects.create(
            session=self.session,
            name='Motor',
            storage_space_per_unit=1.5
        )
        
        # Create diverse components for testing filtering
        self.components = self._create_test_components()
        
        # Create suppliers with different qualities
        self.suppliers = self._create_test_suppliers()
        
        # Create supplier prices for all component-supplier combinations
        self._create_supplier_prices()
        
        # Create bike types with specific component requirements for filtering tests
        self.bike_types = self._create_test_bike_types()
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # URL for procurement view
        self.procurement_url = reverse('procurement:procurement', args=[self.session.id])
    
    def _create_test_components(self):
        """Create a comprehensive set of components for testing"""
        components = {}
        
        # Wheel sets
        components['basic_wheels'] = Component.objects.create(
            session=self.session, component_type=self.wheel_set_type, name='Basic Wheels'
        )
        components['sport_wheels'] = Component.objects.create(
            session=self.session, component_type=self.wheel_set_type, name='Sport Wheels'
        )
        components['premium_wheels'] = Component.objects.create(
            session=self.session, component_type=self.wheel_set_type, name='Premium Wheels'
        )
        components['e_bike_wheels'] = Component.objects.create(
            session=self.session, component_type=self.wheel_set_type, name='E-Bike Wheels'
        )
        
        # Frames
        components['aluminum_frame'] = Component.objects.create(
            session=self.session, component_type=self.frame_type, name='Aluminum Frame'
        )
        components['carbon_frame'] = Component.objects.create(
            session=self.session, component_type=self.frame_type, name='Carbon Frame'
        )
        components['steel_frame'] = Component.objects.create(
            session=self.session, component_type=self.frame_type, name='Steel Frame'
        )
        components['e_bike_frame'] = Component.objects.create(
            session=self.session, component_type=self.frame_type, name='E-Bike Frame'
        )
        
        # Handlebars
        components['comfort_handlebar'] = Component.objects.create(
            session=self.session, component_type=self.handlebar_type, name='Comfort Handlebar'
        )
        components['sport_handlebar'] = Component.objects.create(
            session=self.session, component_type=self.handlebar_type, name='Sport Handlebar'
        )
        components['racing_handlebar'] = Component.objects.create(
            session=self.session, component_type=self.handlebar_type, name='Racing Handlebar'
        )
        
        # Saddles
        components['comfort_saddle'] = Component.objects.create(
            session=self.session, component_type=self.saddle_type, name='Comfort Saddle'
        )
        components['sport_saddle'] = Component.objects.create(
            session=self.session, component_type=self.saddle_type, name='Sport Saddle'
        )
        components['racing_saddle'] = Component.objects.create(
            session=self.session, component_type=self.saddle_type, name='Racing Saddle'
        )
        
        # Gearshifts
        components['basic_gearshift'] = Component.objects.create(
            session=self.session, component_type=self.gearshift_type, name='Basic Gearshift'
        )
        components['advanced_gearshift'] = Component.objects.create(
            session=self.session, component_type=self.gearshift_type, name='Advanced Gearshift'
        )
        components['electronic_gearshift'] = Component.objects.create(
            session=self.session, component_type=self.gearshift_type, name='Electronic Gearshift'
        )
        
        # Motors (for E-bikes)
        components['standard_motor'] = Component.objects.create(
            session=self.session, component_type=self.motor_type, name='Standard Motor'
        )
        components['high_power_motor'] = Component.objects.create(
            session=self.session, component_type=self.motor_type, name='High Power Motor'
        )
        components['mountain_motor'] = Component.objects.create(
            session=self.session, component_type=self.motor_type, name='Mountain Motor'
        )
        
        return components
    
    def _create_test_suppliers(self):
        """Create suppliers with different quality levels"""
        suppliers = {}
        
        suppliers['budget'] = Supplier.objects.create(
            session=self.session,
            name='Budget Components Ltd',
            payment_terms=30,
            delivery_time=14,
            complaint_probability=12.0,
            complaint_quantity=5.0,
            quality='basic'
        )
        
        suppliers['standard'] = Supplier.objects.create(
            session=self.session,
            name='Standard Bike Parts',
            payment_terms=45,
            delivery_time=10,
            complaint_probability=7.0,
            complaint_quantity=3.0,
            quality='standard'
        )
        
        suppliers['premium'] = Supplier.objects.create(
            session=self.session,
            name='Premium Components Inc',
            payment_terms=60,
            delivery_time=7,
            complaint_probability=2.0,
            complaint_quantity=1.0,
            quality='premium'
        )
        
        suppliers['specialized'] = Supplier.objects.create(
            session=self.session,
            name='E-Bike Specialists',
            payment_terms=30,
            delivery_time=5,
            complaint_probability=3.0,
            complaint_quantity=2.0,
            quality='premium'
        )
        
        return suppliers
    
    def _create_supplier_prices(self):
        """Create supplier prices for testing"""
        # Budget supplier - basic components only
        basic_components = [
            'basic_wheels', 'aluminum_frame', 'comfort_handlebar', 
            'comfort_saddle', 'basic_gearshift'
        ]
        
        for comp_key in basic_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['budget'],
                component=self.components[comp_key],
                price=Decimal('50.00')
            )
        
        # Standard supplier - standard and some sport components
        standard_components = [
            'basic_wheels', 'sport_wheels', 'aluminum_frame', 'steel_frame',
            'comfort_handlebar', 'sport_handlebar', 'comfort_saddle', 'sport_saddle',
            'basic_gearshift', 'advanced_gearshift'
        ]
        
        for comp_key in standard_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['standard'],
                component=self.components[comp_key],
                price=Decimal('85.00')
            )
        
        # Premium supplier - high-end components
        premium_components = [
            'sport_wheels', 'premium_wheels', 'carbon_frame', 'steel_frame',
            'sport_handlebar', 'racing_handlebar', 'sport_saddle', 'racing_saddle',
            'advanced_gearshift', 'electronic_gearshift'
        ]
        
        for comp_key in premium_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['premium'],
                component=self.components[comp_key],
                price=Decimal('150.00')
            )
        
        # Specialized E-bike supplier - E-bike specific components
        e_bike_components = [
            'e_bike_wheels', 'e_bike_frame', 'sport_handlebar', 'comfort_saddle',
            'electronic_gearshift', 'standard_motor', 'high_power_motor', 'mountain_motor'
        ]
        
        for comp_key in e_bike_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['specialized'],
                component=self.components[comp_key],
                price=Decimal('200.00')
            )
    
    def _create_test_bike_types(self):
        """Create bike types with specific component requirements for filtering tests"""
        bike_types = {}
        
        # City bike - basic components
        bike_types['city'] = BikeType.objects.create(
            session=self.session,
            name='City Bike',
            skilled_worker_hours=2.5,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.2,
            required_wheel_set_names=['Basic Wheels'],
            required_frame_names=['Aluminum Frame', 'Steel Frame'],
            required_handlebar_names=['Comfort Handlebar'],
            required_saddle_names=['Comfort Saddle'],
            required_gearshift_names=['Basic Gearshift'],
            required_motor_names=[]
        )
        
        # Sport bike - sport components
        bike_types['sport'] = BikeType.objects.create(
            session=self.session,
            name='Sport Bike',
            skilled_worker_hours=3.5,
            unskilled_worker_hours=1.5,
            storage_space_per_unit=1.3,
            required_wheel_set_names=['Sport Wheels', 'Premium Wheels'],
            required_frame_names=['Carbon Frame'],
            required_handlebar_names=['Sport Handlebar', 'Racing Handlebar'],
            required_saddle_names=['Sport Saddle', 'Racing Saddle'],
            required_gearshift_names=['Advanced Gearshift'],
            required_motor_names=[]
        )
        
        # E-bike - includes motors
        bike_types['e_bike'] = BikeType.objects.create(
            session=self.session,
            name='E-Bike',
            skilled_worker_hours=4.0,
            unskilled_worker_hours=2.0,
            storage_space_per_unit=1.5,
            required_wheel_set_names=['E-Bike Wheels', 'Sport Wheels'],
            required_frame_names=['E-Bike Frame', 'Aluminum Frame'],
            required_handlebar_names=['Comfort Handlebar', 'Sport Handlebar'],
            required_saddle_names=['Comfort Saddle'],
            required_gearshift_names=['Electronic Gearshift', 'Advanced Gearshift'],
            required_motor_names=['Standard Motor', 'High Power Motor']
        )
        
        # Racing bike - premium racing components
        bike_types['racing'] = BikeType.objects.create(
            session=self.session,
            name='Racing Bike',
            skilled_worker_hours=5.0,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.1,
            required_wheel_set_names=['Premium Wheels'],
            required_frame_names=['Carbon Frame'],
            required_handlebar_names=['Racing Handlebar'],
            required_saddle_names=['Racing Saddle'],
            required_gearshift_names=['Electronic Gearshift'],
            required_motor_names=[]
        )
        
        return bike_types
    
    def test_supplier_dropdown_functionality(self):
        """Test that supplier dropdown shows all suppliers with correct data"""
        response = self.client.get(self.procurement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('supplier_data', response.context)
        
        supplier_data = response.context['supplier_data']
        
        # Check that all 4 suppliers are present
        self.assertEqual(len(supplier_data), 4)
        
        # Check specific supplier data
        budget_supplier_data = supplier_data[self.suppliers['budget'].id]
        self.assertEqual(budget_supplier_data['supplier'].name, 'Budget Components Ltd')
        self.assertEqual(budget_supplier_data['supplier'].quality, 'basic')
        self.assertEqual(budget_supplier_data['supplier'].delivery_time, 14)
        
        # Check that supplier has prices
        self.assertTrue(budget_supplier_data['prices'].count() > 0)
    
    def test_bike_type_dropdown_functionality(self):
        """Test that bike type dropdown shows all bike types for filtering"""
        response = self.client.get(self.procurement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('bike_types', response.context)
        
        bike_types = response.context['bike_types']
        bike_type_names = [bt.name for bt in bike_types]
        
        # Check that all bike types are present
        self.assertIn('City Bike', bike_type_names)
        self.assertIn('Sport Bike', bike_type_names)
        self.assertIn('E-Bike', bike_type_names)
        self.assertIn('Racing Bike', bike_type_names)
    
    def test_component_filtering_by_bike_type(self):
        """Test that component filtering by bike type works correctly"""
        response = self.client.get(self.procurement_url)
        
        # Get bike component mapping from context
        bike_mapping_json = response.context['bike_component_mapping']
        bike_mapping = json.loads(bike_mapping_json)
        
        # Test City Bike filtering
        city_bike_components = bike_mapping[str(self.bike_types['city'].id)]
        
        # Should include basic components
        self.assertIn(self.components['basic_wheels'].id, city_bike_components)
        self.assertIn(self.components['aluminum_frame'].id, city_bike_components)
        self.assertIn(self.components['comfort_handlebar'].id, city_bike_components)
        self.assertIn(self.components['comfort_saddle'].id, city_bike_components)
        self.assertIn(self.components['basic_gearshift'].id, city_bike_components)
        
        # Should NOT include motors or premium components
        self.assertNotIn(self.components['standard_motor'].id, city_bike_components)
        self.assertNotIn(self.components['premium_wheels'].id, city_bike_components)
        self.assertNotIn(self.components['carbon_frame'].id, city_bike_components)
        
        # Test E-Bike filtering
        e_bike_components = bike_mapping[str(self.bike_types['e_bike'].id)]
        
        # Should include motors and e-bike specific components
        self.assertIn(self.components['standard_motor'].id, e_bike_components)
        self.assertIn(self.components['high_power_motor'].id, e_bike_components)
        self.assertIn(self.components['e_bike_wheels'].id, e_bike_components)
        self.assertIn(self.components['e_bike_frame'].id, e_bike_components)
        self.assertIn(self.components['electronic_gearshift'].id, e_bike_components)
        
        # Should NOT include mountain motor (not in requirements)
        self.assertNotIn(self.components['mountain_motor'].id, e_bike_components)
        
        # Test Racing Bike filtering
        racing_bike_components = bike_mapping[str(self.bike_types['racing'].id)]
        
        # Should only include premium racing components
        self.assertIn(self.components['premium_wheels'].id, racing_bike_components)
        self.assertIn(self.components['carbon_frame'].id, racing_bike_components)
        self.assertIn(self.components['racing_handlebar'].id, racing_bike_components)
        self.assertIn(self.components['racing_saddle'].id, racing_bike_components)
        self.assertIn(self.components['electronic_gearshift'].id, racing_bike_components)
        
        # Should NOT include basic components or motors
        self.assertNotIn(self.components['basic_wheels'].id, racing_bike_components)
        self.assertNotIn(self.components['comfort_handlebar'].id, racing_bike_components)
        self.assertNotIn(self.components['standard_motor'].id, racing_bike_components)
    
    def test_purchase_creates_warehouse_inventory(self):
        """Test that purchases are correctly stored in warehouse (Lager)"""
        initial_balance = self.session.balance
        
        # Create order for multiple components
        order_data = {
            str(self.suppliers['budget'].id): [
                {
                    'component_id': self.components['basic_wheels'].id,
                    'quantity': 10
                },
                {
                    'component_id': self.components['aluminum_frame'].id,
                    'quantity': 8
                }
            ],
            str(self.suppliers['specialized'].id): [
                {
                    'component_id': self.components['standard_motor'].id,
                    'quantity': 5
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that warehouse was created
        warehouse = Warehouse.objects.get(session=self.session)
        self.assertEqual(warehouse.name, 'Hauptlager')
        
        # Check component stocks in warehouse
        basic_wheels_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.components['basic_wheels']
        )
        self.assertEqual(basic_wheels_stock.quantity, 10)
        
        aluminum_frame_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.components['aluminum_frame']
        )
        self.assertEqual(aluminum_frame_stock.quantity, 8)
        
        standard_motor_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.components['standard_motor']
        )
        self.assertEqual(standard_motor_stock.quantity, 5)
        
        # Check that session balance was reduced correctly
        self.session.refresh_from_db()
        expected_cost = Decimal('1400.00')  # (10*50 + 8*50) + (5*200) = 900 + 1000 = 1900
        # Actually: Budget: 10*50 + 8*50 = 900, Specialized: 5*200 = 1000, Total = 1900
        # Wait, let me recalculate: (10 + 8) * 50 + 5 * 200 = 18*50 + 1000 = 900 + 1000 = 1900
        expected_total_cost = Decimal('1900.00')
        expected_balance = initial_balance - expected_total_cost
        self.assertEqual(self.session.balance, expected_balance)
    
    def test_multiple_purchases_accumulate_inventory(self):
        """Test that multiple purchases accumulate correctly in warehouse"""
        # First purchase
        order_data_1 = {
            str(self.suppliers['budget'].id): [
                {
                    'component_id': self.components['basic_wheels'].id,
                    'quantity': 5
                }
            ]
        }
        
        response_1 = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data_1),
            content_type='application/json'
        )
        self.assertEqual(response_1.status_code, 200)
        
        # Second purchase
        order_data_2 = {
            str(self.suppliers['standard'].id): [
                {
                    'component_id': self.components['basic_wheels'].id,
                    'quantity': 7
                }
            ]
        }
        
        response_2 = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data_2),
            content_type='application/json'
        )
        self.assertEqual(response_2.status_code, 200)
        
        # Check accumulated inventory
        warehouse = Warehouse.objects.get(session=self.session)
        basic_wheels_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.components['basic_wheels']
        )
        self.assertEqual(basic_wheels_stock.quantity, 12)  # 5 + 7
    
    def test_filtered_purchase_for_specific_bike_type(self):
        """Test complete workflow: filter by bike type, then purchase those components"""
        # Test purchasing all components for E-bike production
        e_bike_order_data = {
            str(self.suppliers['specialized'].id): [
                {
                    'component_id': self.components['e_bike_wheels'].id,
                    'quantity': 20
                },
                {
                    'component_id': self.components['e_bike_frame'].id,
                    'quantity': 20
                },
                {
                    'component_id': self.components['sport_handlebar'].id,
                    'quantity': 20
                },
                {
                    'component_id': self.components['comfort_saddle'].id,
                    'quantity': 20
                },
                {
                    'component_id': self.components['electronic_gearshift'].id,
                    'quantity': 20
                },
                {
                    'component_id': self.components['standard_motor'].id,
                    'quantity': 20
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(e_bike_order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that all E-bike components are in warehouse
        warehouse = Warehouse.objects.get(session=self.session)
        
        # Define expected components and quantities
        e_bike_components_expected = [
            (self.components['e_bike_wheels'], 20),
            (self.components['e_bike_frame'], 20),
            (self.components['sport_handlebar'], 20),
            (self.components['comfort_saddle'], 20),
            (self.components['electronic_gearshift'], 20),
            (self.components['standard_motor'], 20)
        ]
        
        for component, expected_quantity in e_bike_components_expected:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=warehouse,
                component=component
            )
            self.assertEqual(stock.quantity, expected_quantity)
        
        # Check total cost (6 components * 20 units * 200 price = 24,000)
        expected_total_cost = Decimal('24000.00')
        procurement_order = ProcurementOrder.objects.get(
            session=self.session,
            supplier=self.suppliers['specialized']
        )
        self.assertEqual(procurement_order.total_cost, expected_total_cost)
    
    def test_warehouse_capacity_and_storage_calculation(self):
        """Test that warehouse storage space is properly calculated"""
        # Purchase components with different storage requirements
        order_data = {
            str(self.suppliers['budget'].id): [
                {
                    'component_id': self.components['basic_wheels'].id,  # 2.5 m² each
                    'quantity': 4  # 4 * 2.5 = 10 m²
                },
                {
                    'component_id': self.components['aluminum_frame'].id,  # 3.0 m² each
                    'quantity': 3  # 3 * 3.0 = 9 m²
                }
            ],
            str(self.suppliers['specialized'].id): [
                {
                    'component_id': self.components['standard_motor'].id,  # 1.5 m² each
                    'quantity': 6  # 6 * 1.5 = 9 m²
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Get warehouse and check it was created with correct capacity
        warehouse = Warehouse.objects.get(session=self.session)
        self.assertGreaterEqual(warehouse.capacity_m2, 28)  # Should be sufficient for our test
        
        # Check that all components are stored
        component_stocks = ComponentStock.objects.filter(
            session=self.session,
            warehouse=warehouse
        )
        
        total_storage_used = 0
        for stock in component_stocks:
            storage_per_unit = stock.component.component_type.storage_space_per_unit
            total_storage_used += stock.quantity * storage_per_unit
        
        # Expected: 4*2.5 + 3*3.0 + 6*1.5 = 10 + 9 + 9 = 28 m²
        expected_storage_used = 28.0
        self.assertEqual(total_storage_used, expected_storage_used)
    
    def test_procurement_order_creation_and_details(self):
        """Test that procurement orders are created with correct details"""
        order_data = {
            str(self.suppliers['premium'].id): [
                {
                    'component_id': self.components['carbon_frame'].id,
                    'quantity': 5
                },
                {
                    'component_id': self.components['racing_handlebar'].id,
                    'quantity': 5
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check procurement order was created
        procurement_order = ProcurementOrder.objects.get(
            session=self.session,
            supplier=self.suppliers['premium']
        )
        
        # Check order details
        self.assertEqual(procurement_order.month, self.session.current_month)
        self.assertEqual(procurement_order.year, self.session.current_year)
        self.assertEqual(procurement_order.total_cost, Decimal('1500.00'))  # (5 + 5) * 150
        self.assertFalse(procurement_order.is_delivered)  # Default should be False
        
        # Check order items
        order_items = procurement_order.items.all()
        self.assertEqual(order_items.count(), 2)
        
        carbon_frame_item = order_items.get(component=self.components['carbon_frame'])
        self.assertEqual(carbon_frame_item.quantity_ordered, 5)
        self.assertEqual(carbon_frame_item.quantity_delivered, 5)  # Simplified delivery
        self.assertEqual(carbon_frame_item.unit_price, Decimal('150.00'))
        
        racing_handlebar_item = order_items.get(component=self.components['racing_handlebar'])
        self.assertEqual(racing_handlebar_item.quantity_ordered, 5)
        self.assertEqual(racing_handlebar_item.quantity_delivered, 5)
        self.assertEqual(racing_handlebar_item.unit_price, Decimal('150.00'))
    
    def test_dropdown_filtering_error_handling(self):
        """Test error handling for dropdown filtering edge cases"""
        # Test with invalid bike type filtering
        response = self.client.get(self.procurement_url)
        bike_mapping_json = response.context['bike_component_mapping']
        bike_mapping = json.loads(bike_mapping_json)
        
        # Check that non-existent bike type IDs are handled gracefully
        # (Should not crash the view)
        self.assertIsInstance(bike_mapping, dict)
        
        # Test with empty component requirements
        empty_bike = BikeType.objects.create(
            session=self.session,
            name='Empty Requirements Bike',
            skilled_worker_hours=2.0,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.0
            # No component requirements - should use fallback
        )
        
        # Re-fetch the page to get updated mapping
        response = self.client.get(self.procurement_url)
        bike_mapping_json = response.context['bike_component_mapping']
        bike_mapping = json.loads(bike_mapping_json)
        
        # Empty bike should still have some components (fallback behavior)
        empty_bike_components = bike_mapping.get(str(empty_bike.id), [])
        self.assertGreater(len(empty_bike_components), 0)
    
    def test_complete_bike_production_workflow(self):
        """Test complete workflow: filter for bike type, purchase all components, verify inventory"""
        # Simulate purchasing all components needed for Sport Bike production
        
        # First, get the sport bike component mapping
        response = self.client.get(self.procurement_url)
        bike_mapping = json.loads(response.context['bike_component_mapping'])
        sport_bike_components = bike_mapping[str(self.bike_types['sport'].id)]
        
        # Purchase components for 10 sport bikes
        sport_bike_order = {}
        
        # Group components by supplier for ordering
        for supplier_id, supplier in self.suppliers.items():
            supplier_prices = SupplierPrice.objects.filter(
                session=self.session,
                supplier=supplier,
                component__id__in=sport_bike_components
            )
            
            if supplier_prices.exists():
                sport_bike_order[str(supplier.id)] = [
                    {
                        'component_id': sp.component.id,
                        'quantity': 10
                    }
                    for sp in supplier_prices
                ]
        
        # Place the order
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(sport_bike_order),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify that all sport bike components are now in inventory
        warehouse = Warehouse.objects.get(session=self.session)
        sport_bike_component_objects = Component.objects.filter(
            session=self.session,
            id__in=sport_bike_components
        )
        
        for component in sport_bike_component_objects:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=warehouse,
                component=component
            )
            # Components might be ordered from multiple suppliers, so quantity could be higher
            self.assertGreaterEqual(stock.quantity, 10)
        
        # Verify that we can now theoretically produce 10 sport bikes
        # (All required components are available in quantities of 10)
        sport_bike_requirements = self.bike_types['sport'].get_required_components()
        
        for component_type_name, required_names in sport_bike_requirements.items():
            for required_name in required_names:
                matching_components = Component.objects.filter(
                    session=self.session,
                    component_type__name=component_type_name,
                    name=required_name
                )
                
                # At least one matching component should be in stock
                found_in_stock = False
                for component in matching_components:
                    try:
                        stock = ComponentStock.objects.get(
                            session=self.session,
                            warehouse=warehouse,
                            component=component
                        )
                        if stock.quantity >= 10:
                            found_in_stock = True
                            break
                    except ComponentStock.DoesNotExist:
                        continue
                
                if not found_in_stock:
                    self.fail(f"Required component type '{component_type_name}' with name in {required_names} not found in sufficient quantity")