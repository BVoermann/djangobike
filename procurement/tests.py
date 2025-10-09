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


class ProcurementTestCase(TestCase):
    """Base test case with common setup for procurement tests"""
    
    def setUp(self):
        """Set up test data for procurement tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=1,
            current_year=2024,
            balance=Decimal('80000.00')
        )
        
        # Create component types for all bike parts
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
        
        # Create components for each type
        self.wheel_set_basic = Component.objects.create(
            session=self.session,
            component_type=self.wheel_set_type,
            name='Basic Wheelset'
        )
        
        self.wheel_set_premium = Component.objects.create(
            session=self.session,
            component_type=self.wheel_set_type,
            name='Premium Wheelset'
        )
        
        self.frame_aluminum = Component.objects.create(
            session=self.session,
            component_type=self.frame_type,
            name='Aluminum Frame'
        )
        
        self.frame_carbon = Component.objects.create(
            session=self.session,
            component_type=self.frame_type,
            name='Carbon Frame'
        )
        
        self.handlebar_basic = Component.objects.create(
            session=self.session,
            component_type=self.handlebar_type,
            name='Basic Handlebar'
        )
        
        self.saddle_comfort = Component.objects.create(
            session=self.session,
            component_type=self.saddle_type,
            name='Comfort Saddle'
        )
        
        self.gearshift_7speed = Component.objects.create(
            session=self.session,
            component_type=self.gearshift_type,
            name='7-Speed Gearshift'
        )
        
        self.gearshift_21speed = Component.objects.create(
            session=self.session,
            component_type=self.gearshift_type,
            name='21-Speed Gearshift'
        )
        
        self.motor_250w = Component.objects.create(
            session=self.session,
            component_type=self.motor_type,
            name='250W E-Motor'
        )
        
        # Create suppliers with different quality levels
        self.supplier_basic = Supplier.objects.create(
            session=self.session,
            name='Basic Parts Co',
            payment_terms=30,
            delivery_time=14,
            complaint_probability=15.0,
            complaint_quantity=5.0,
            quality='basic'
        )
        
        self.supplier_premium = Supplier.objects.create(
            session=self.session,
            name='Premium Components Ltd',
            payment_terms=60,
            delivery_time=7,
            complaint_probability=2.0,
            complaint_quantity=1.0,
            quality='premium'
        )
        
        self.supplier_standard = Supplier.objects.create(
            session=self.session,
            name='Standard Bike Parts',
            payment_terms=45,
            delivery_time=10,
            complaint_probability=8.0,
            complaint_quantity=3.0,
            quality='standard'
        )
        
        # Create supplier prices for comprehensive testing
        self._create_supplier_prices()
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # URL for procurement view
        self.procurement_url = reverse('procurement:procurement', args=[self.session.id])
    
    def _create_supplier_prices(self):
        """Create realistic supplier prices for all components"""
        
        # Basic supplier prices (cheaper but lower quality)
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_basic, 
            component=self.wheel_set_basic, price=Decimal('45.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_basic, 
            component=self.frame_aluminum, price=Decimal('85.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_basic, 
            component=self.handlebar_basic, price=Decimal('15.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_basic, 
            component=self.saddle_comfort, price=Decimal('25.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_basic, 
            component=self.gearshift_7speed, price=Decimal('35.00')
        )
        
        # Premium supplier prices (more expensive but higher quality)
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.wheel_set_premium, price=Decimal('120.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.frame_carbon, price=Decimal('250.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.handlebar_basic, price=Decimal('35.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.saddle_comfort, price=Decimal('45.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.gearshift_21speed, price=Decimal('85.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_premium, 
            component=self.motor_250w, price=Decimal('180.00')
        )
        
        # Standard supplier prices (middle ground)
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.wheel_set_basic, price=Decimal('65.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.frame_aluminum, price=Decimal('125.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.handlebar_basic, price=Decimal('22.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.saddle_comfort, price=Decimal('32.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.gearshift_7speed, price=Decimal('48.00')
        )
        SupplierPrice.objects.create(
            session=self.session, supplier=self.supplier_standard, 
            component=self.motor_250w, price=Decimal('155.00')
        )


class ProcurementViewGETTestCase(ProcurementTestCase):
    """Test GET requests to the procurement view"""
    
    def test_procurement_view_loads_successfully(self):
        """Test that the procurement view loads without errors"""
        response = self.client.get(self.procurement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Basic Parts Co')
        self.assertContains(response, 'Premium Components Ltd')
        self.assertContains(response, 'Standard Bike Parts')
    
    def test_procurement_view_shows_suppliers_and_prices(self):
        """Test that suppliers and their component prices are displayed"""
        response = self.client.get(self.procurement_url)
        
        # Check that supplier data is in context
        self.assertIn('supplier_data', response.context)
        self.assertIn('supplier_data_json', response.context)
        
        supplier_data = response.context['supplier_data']
        
        # Verify basic supplier data
        basic_supplier_data = supplier_data[self.supplier_basic.id]
        self.assertEqual(basic_supplier_data['supplier'], self.supplier_basic)
        self.assertTrue(basic_supplier_data['prices'].count() > 0)
        
        # Verify premium supplier data
        premium_supplier_data = supplier_data[self.supplier_premium.id]
        self.assertEqual(premium_supplier_data['supplier'], self.supplier_premium)
        self.assertTrue(premium_supplier_data['prices'].count() > 0)
    
    def test_procurement_view_json_data_structure(self):
        """Test that JSON data for JavaScript is properly structured"""
        response = self.client.get(self.procurement_url)
        
        supplier_data_json = json.loads(response.context['supplier_data_json'])
        
        # Check structure for basic supplier
        basic_id = str(self.supplier_basic.id)
        self.assertIn(basic_id, supplier_data_json)
        
        basic_data = supplier_data_json[basic_id]
        self.assertIn('supplier', basic_data)
        self.assertIn('prices', basic_data)
        
        # Check supplier info
        supplier_info = basic_data['supplier']
        self.assertEqual(supplier_info['name'], 'Basic Parts Co')
        self.assertEqual(supplier_info['quality'], 'basic')
        self.assertEqual(supplier_info['delivery_time'], 14)
        
        # Check price structure
        prices = basic_data['prices']
        self.assertTrue(len(prices) > 0)
        
        price_item = prices[0]
        self.assertIn('component', price_item)
        self.assertIn('price', price_item)
        self.assertIn('id', price_item['component'])
        self.assertIn('name', price_item['component'])
    
    def test_procurement_view_requires_login(self):
        """Test that the procurement view requires user authentication"""
        # Logout the user
        self.client.logout()
        
        response = self.client.get(self.procurement_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)
    
    def test_procurement_view_wrong_session_404(self):
        """Test that accessing wrong session returns 404"""
        # Create another user's session
        other_user = User.objects.create_user(
            username='otheruser', password='otherpass'
        )
        other_session = GameSession.objects.create(
            user=other_user, name='Other Session'
        )
        
        wrong_url = reverse('procurement:procurement', args=[other_session.id])
        response = self.client.get(wrong_url)
        
        self.assertEqual(response.status_code, 404)


class ProcurementOrderCreationTestCase(ProcurementTestCase):
    """Test POST requests for creating procurement orders"""
    
    def test_successful_single_component_order(self):
        """Test ordering a single component successfully"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 10
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
        
        # Check that order was created
        order = ProcurementOrder.objects.get(
            session=self.session,
            supplier=self.supplier_basic
        )
        self.assertEqual(order.month, self.session.current_month)
        self.assertEqual(order.year, self.session.current_year)
        self.assertEqual(order.total_cost, Decimal('450.00'))  # 10 * 45.00
        
        # Check order item
        order_item = order.items.first()
        self.assertEqual(order_item.component, self.wheel_set_basic)
        self.assertEqual(order_item.quantity_ordered, 10)
        self.assertEqual(order_item.quantity_delivered, 10)
        self.assertEqual(order_item.unit_price, Decimal('45.00'))
    
    def test_successful_multiple_components_order(self):
        """Test ordering multiple components from same supplier"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 5
                },
                {
                    'component_id': self.frame_aluminum.id,
                    'quantity': 3
                },
                {
                    'component_id': self.handlebar_basic.id,
                    'quantity': 8
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
        
        # Check order
        order = ProcurementOrder.objects.get(
            session=self.session,
            supplier=self.supplier_basic
        )
        
        # Expected total: 5*45 + 3*85 + 8*15 = 225 + 255 + 120 = 600
        self.assertEqual(order.total_cost, Decimal('600.00'))
        
        # Check all order items were created
        self.assertEqual(order.items.count(), 3)
        
        # Check specific items
        wheel_item = order.items.get(component=self.wheel_set_basic)
        self.assertEqual(wheel_item.quantity_ordered, 5)
        
        frame_item = order.items.get(component=self.frame_aluminum)
        self.assertEqual(frame_item.quantity_ordered, 3)
        
        handlebar_item = order.items.get(component=self.handlebar_basic)
        self.assertEqual(handlebar_item.quantity_ordered, 8)
    
    def test_successful_multiple_suppliers_order(self):
        """Test ordering from multiple suppliers simultaneously"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 2
                }
            ],
            str(self.supplier_premium.id): [
                {
                    'component_id': self.motor_250w.id,
                    'quantity': 1
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
        
        # Check that two separate orders were created
        orders = ProcurementOrder.objects.filter(session=self.session)
        self.assertEqual(orders.count(), 2)
        
        # Check basic supplier order
        basic_order = orders.get(supplier=self.supplier_basic)
        self.assertEqual(basic_order.total_cost, Decimal('90.00'))  # 2 * 45.00
        
        # Check premium supplier order
        premium_order = orders.get(supplier=self.supplier_premium)
        self.assertEqual(premium_order.total_cost, Decimal('180.00'))  # 1 * 180.00


class ProcurementInventoryIntegrationTestCase(ProcurementTestCase):
    """Test integration with warehouse inventory system"""
    
    def test_order_updates_inventory_stock(self):
        """Test that successful orders update component stock in warehouse"""
        initial_balance = self.session.balance
        
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 5
                },
                {
                    'component_id': self.frame_aluminum.id,
                    'quantity': 3
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that warehouse was created
        warehouse = Warehouse.objects.get(session=self.session)
        self.assertEqual(warehouse.name, 'Hauptlager')
        self.assertEqual(warehouse.capacity_m2, 200.0)
        
        # Check component stocks
        wheel_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.wheel_set_basic
        )
        self.assertEqual(wheel_stock.quantity, 5)
        
        frame_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.frame_aluminum
        )
        self.assertEqual(frame_stock.quantity, 3)
    
    def test_multiple_orders_accumulate_inventory(self):
        """Test that multiple orders accumulate component quantities"""
        # First order
        order_data_1 = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 5
                }
            ]
        }
        
        self.client.post(
            self.procurement_url,
            data=json.dumps(order_data_1),
            content_type='application/json'
        )
        
        # Second order
        order_data_2 = {
            str(self.supplier_standard.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 3
                }
            ]
        }
        
        self.client.post(
            self.procurement_url,
            data=json.dumps(order_data_2),
            content_type='application/json'
        )
        
        # Check accumulated stock
        warehouse = Warehouse.objects.get(session=self.session)
        wheel_stock = ComponentStock.objects.get(
            session=self.session,
            warehouse=warehouse,
            component=self.wheel_set_basic
        )
        self.assertEqual(wheel_stock.quantity, 8)  # 5 + 3
    
    def test_order_reduces_session_balance(self):
        """Test that orders reduce the session balance correctly"""
        initial_balance = self.session.balance
        
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 10
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh session from database
        self.session.refresh_from_db()
        
        expected_cost = Decimal('450.00')  # 10 * 45.00
        expected_balance = initial_balance - expected_cost
        
        self.assertEqual(self.session.balance, expected_balance)
    
    def test_multiple_suppliers_total_cost_calculation(self):
        """Test that total cost is calculated correctly for multiple suppliers"""
        initial_balance = self.session.balance
        
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 2
                }
            ],
            str(self.supplier_premium.id): [
                {
                    'component_id': self.motor_250w.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh session from database
        self.session.refresh_from_db()
        
        expected_cost = Decimal('270.00')  # (2 * 45.00) + (1 * 180.00)
        expected_balance = initial_balance - expected_cost
        
        self.assertEqual(self.session.balance, expected_balance)


class ProcurementErrorHandlingTestCase(ProcurementTestCase):
    """Test error handling and edge cases"""
    
    def test_invalid_json_data(self):
        """Test handling of invalid JSON data"""
        response = self.client.post(
            self.procurement_url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_invalid_supplier_id(self):
        """Test handling of invalid supplier ID"""
        order_data = {
            '99999': [  # Non-existent supplier ID
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 1
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
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_invalid_component_id(self):
        """Test handling of invalid component ID"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': 99999,  # Non-existent component ID
                    'quantity': 1
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
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_component_not_available_from_supplier(self):
        """Test ordering component that supplier doesn't offer"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.motor_250w.id,  # Basic supplier doesn't offer motors
                    'quantity': 1
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
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_zero_quantity_order(self):
        """Test handling of zero quantity orders"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 0
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
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_negative_quantity_order(self):
        """Test handling of negative quantity orders"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': -5
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
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_empty_order_data(self):
        """Test handling of empty order data"""
        order_data = {}
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])  # Empty orders should succeed
        
        # No orders should be created
        self.assertEqual(ProcurementOrder.objects.filter(session=self.session).count(), 0)
    
    def test_supplier_with_empty_items(self):
        """Test supplier entry with empty items list"""
        order_data = {
            str(self.supplier_basic.id): []  # Empty items list
        }
        
        response = self.client.post(
            self.procurement_url,
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # No orders should be created for supplier with empty items
        self.assertEqual(ProcurementOrder.objects.filter(session=self.session).count(), 0)


class ComprehensiveBikeComponentTestCase(ProcurementTestCase):
    """Test procurement of complete bike component sets"""
    
    def test_order_complete_basic_bike_components(self):
        """Test ordering all components needed for a basic bike"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 10  # For 10 bikes
                },
                {
                    'component_id': self.frame_aluminum.id,
                    'quantity': 10
                },
                {
                    'component_id': self.handlebar_basic.id,
                    'quantity': 10
                },
                {
                    'component_id': self.saddle_comfort.id,
                    'quantity': 10
                },
                {
                    'component_id': self.gearshift_7speed.id,
                    'quantity': 10
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
        
        # Check that all components are in inventory
        warehouse = Warehouse.objects.get(session=self.session)
        
        wheel_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.wheel_set_basic
        )
        self.assertEqual(wheel_stock.quantity, 10)
        
        frame_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.frame_aluminum
        )
        self.assertEqual(frame_stock.quantity, 10)
        
        handlebar_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.handlebar_basic
        )
        self.assertEqual(handlebar_stock.quantity, 10)
        
        saddle_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.saddle_comfort
        )
        self.assertEqual(saddle_stock.quantity, 10)
        
        gearshift_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.gearshift_7speed
        )
        self.assertEqual(gearshift_stock.quantity, 10)
        
        # Check total cost calculation
        expected_cost = Decimal('2050.00')  # (45+85+15+25+35) * 10 = 205 * 10
        order = ProcurementOrder.objects.get(session=self.session)
        self.assertEqual(order.total_cost, expected_cost)
    
    def test_order_premium_e_bike_components(self):
        """Test ordering all components for premium e-bikes including motors"""
        order_data = {
            str(self.supplier_premium.id): [
                {
                    'component_id': self.wheel_set_premium.id,
                    'quantity': 5
                },
                {
                    'component_id': self.frame_carbon.id,
                    'quantity': 5
                },
                {
                    'component_id': self.handlebar_basic.id,
                    'quantity': 5
                },
                {
                    'component_id': self.saddle_comfort.id,
                    'quantity': 5
                },
                {
                    'component_id': self.gearshift_21speed.id,
                    'quantity': 5
                },
                {
                    'component_id': self.motor_250w.id,
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
        
        # Check motor inventory specifically
        warehouse = Warehouse.objects.get(session=self.session)
        motor_stock = ComponentStock.objects.get(
            session=self.session, warehouse=warehouse, component=self.motor_250w
        )
        self.assertEqual(motor_stock.quantity, 5)
        
        # Check total cost for premium components
        # 120 + 250 + 35 + 45 + 85 + 180 = 715 per bike * 5 = 3575
        expected_cost = Decimal('3575.00')
        order = ProcurementOrder.objects.get(session=self.session)
        self.assertEqual(order.total_cost, expected_cost)
    
    def test_mixed_supplier_complete_bike_order(self):
        """Test ordering bike components from multiple suppliers for cost optimization"""
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.frame_aluminum.id,  # Cheaper frame from basic supplier
                    'quantity': 20
                },
                {
                    'component_id': self.handlebar_basic.id,  # Cheaper handlebar
                    'quantity': 20
                }
            ],
            str(self.supplier_premium.id): [
                {
                    'component_id': self.wheel_set_premium.id,  # Premium wheels
                    'quantity': 20
                },
                {
                    'component_id': self.motor_250w.id,  # Motors only from premium supplier
                    'quantity': 10  # Only half the bikes are e-bikes
                }
            ],
            str(self.supplier_standard.id): [
                {
                    'component_id': self.saddle_comfort.id,  # Standard quality saddles
                    'quantity': 20
                },
                {
                    'component_id': self.gearshift_7speed.id,  # Standard gearshifts
                    'quantity': 20
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
        
        # Check that three orders were created
        orders = ProcurementOrder.objects.filter(session=self.session)
        self.assertEqual(orders.count(), 3)
        
        # Check warehouse inventory has all components
        warehouse = Warehouse.objects.get(session=self.session)
        
        # Check each component stock
        components_to_check = [
            (self.frame_aluminum, 20),
            (self.handlebar_basic, 20),
            (self.wheel_set_premium, 20),
            (self.motor_250w, 10),
            (self.saddle_comfort, 20),
            (self.gearshift_7speed, 20)
        ]
        
        for component, expected_quantity in components_to_check:
            stock = ComponentStock.objects.get(
                session=self.session, warehouse=warehouse, component=component
            )
            self.assertEqual(stock.quantity, expected_quantity)
    
    def test_large_quantity_order_balance_impact(self):
        """Test that large orders properly impact the session balance"""
        initial_balance = self.session.balance
        
        # Order enough components for 100 basic bikes
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 100
                },
                {
                    'component_id': self.frame_aluminum.id,
                    'quantity': 100
                },
                {
                    'component_id': self.handlebar_basic.id,
                    'quantity': 100
                },
                {
                    'component_id': self.saddle_comfort.id,
                    'quantity': 100
                },
                {
                    'component_id': self.gearshift_7speed.id,
                    'quantity': 100
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
        
        # Calculate expected total cost
        # (45 + 85 + 15 + 25 + 35) * 100 = 205 * 100 = 20,500
        expected_cost = Decimal('20500.00')
        expected_remaining_balance = initial_balance - expected_cost
        
        # Check session balance was reduced correctly
        self.session.refresh_from_db()
        self.assertEqual(self.session.balance, expected_remaining_balance)
        
        # Ensure we still have positive balance for this test
        self.assertGreater(self.session.balance, 0)
    
    def test_transaction_atomicity_on_error(self):
        """Test that failed orders don't partially update database"""
        initial_balance = self.session.balance
        
        # Create an order with one valid and one invalid component
        order_data = {
            str(self.supplier_basic.id): [
                {
                    'component_id': self.wheel_set_basic.id,
                    'quantity': 5
                },
                {
                    'component_id': 99999,  # Invalid component ID
                    'quantity': 3
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
        self.assertFalse(response_data['success'])
        
        # Check that no orders were created
        self.assertEqual(ProcurementOrder.objects.filter(session=self.session).count(), 0)
        
        # Check that no inventory was added
        self.assertEqual(ComponentStock.objects.filter(session=self.session).count(), 0)
        
        # Check that warehouse was not created
        self.assertEqual(Warehouse.objects.filter(session=self.session).count(), 0)
        
        # Check that balance wasn't changed
        self.session.refresh_from_db()
        self.assertEqual(self.session.balance, initial_balance)


class BikeComponentFilteringTestCase(ProcurementTestCase):
    """Test bike type component filtering functionality"""
    
    def setUp(self):
        super().setUp()
        
        # Create bike types with component requirements for testing filtering
        self.city_bike = BikeType.objects.create(
            session=self.session,
            name='Stadtrad',
            skilled_worker_hours=2.5,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.2,
            required_frame_names=['Aluminum Frame'],
            required_wheel_set_names=['Basic Wheelset'],
            required_handlebar_names=['Basic Handlebar'],
            required_saddle_names=['Comfort Saddle'],
            required_gearshift_names=['7-Speed Gearshift'],
            required_motor_names=[]  # No motor for regular city bike
        )
        
        self.e_bike = BikeType.objects.create(
            session=self.session,
            name='E-Bike',
            skilled_worker_hours=3.5,
            unskilled_worker_hours=1.5,
            storage_space_per_unit=1.5,
            required_frame_names=['Carbon Frame', 'Aluminum Frame'],
            required_wheel_set_names=['Premium Wheelset', 'Basic Wheelset'],
            required_handlebar_names=['Basic Handlebar'],
            required_saddle_names=['Comfort Saddle'],
            required_gearshift_names=['21-Speed Gearshift', '7-Speed Gearshift'],
            required_motor_names=['250W E-Motor']  # Requires motor
        )
        
        self.mountain_bike = BikeType.objects.create(
            session=self.session,
            name='Mountainbike',
            skilled_worker_hours=4.0,
            unskilled_worker_hours=2.0,
            storage_space_per_unit=1.3,
            required_frame_names=['Carbon Frame'],  # Only carbon for mountain
            required_wheel_set_names=['Premium Wheelset'],  # Only premium wheels
            required_handlebar_names=['Basic Handlebar'],
            required_saddle_names=['Comfort Saddle'],
            required_gearshift_names=['21-Speed Gearshift'],  # Only advanced gearshift
            required_motor_names=[]  # No motor for regular mountain bike
        )
    
    def test_bike_component_mapping_generation(self):
        """Test that bike component mapping is correctly generated in view"""
        response = self.client.get(self.procurement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('bike_component_mapping', response.context)
        
        bike_mapping_json = response.context['bike_component_mapping']
        bike_mapping = json.loads(bike_mapping_json)
        
        # Check that city bike mapping includes correct components
        city_bike_components = bike_mapping[str(self.city_bike.id)]
        
        # Should include aluminum frame, basic wheelset, basic handlebar, comfort saddle, 7-speed gearshift
        # Should NOT include motor or carbon frame or premium components
        expected_components = [
            self.frame_aluminum.id,  # 3
            self.wheel_set_basic.id,  # 1
            self.handlebar_basic.id,  # 5
            self.saddle_comfort.id,   # 6
            self.gearshift_7speed.id  # 7
        ]
        
        for component_id in expected_components:
            self.assertIn(component_id, city_bike_components)
        
        # Should NOT include motor for city bike
        self.assertNotIn(self.motor_250w.id, city_bike_components)
        
        # Should NOT include premium wheelset for city bike
        self.assertNotIn(self.wheel_set_premium.id, city_bike_components)
        
        # Should NOT include carbon frame for city bike
        self.assertNotIn(self.frame_carbon.id, city_bike_components)
    
    def test_e_bike_component_mapping_includes_motor(self):
        """Test that E-bike mapping includes motors and allows flexible components"""
        response = self.client.get(self.procurement_url)
        
        bike_mapping = json.loads(response.context['bike_component_mapping'])
        e_bike_components = bike_mapping[str(self.e_bike.id)]
        
        # E-bike should include motor
        self.assertIn(self.motor_250w.id, e_bike_components)
        
        # E-bike should allow both frame types
        self.assertIn(self.frame_aluminum.id, e_bike_components)
        self.assertIn(self.frame_carbon.id, e_bike_components)
        
        # E-bike should allow both wheelset types
        self.assertIn(self.wheel_set_basic.id, e_bike_components)
        self.assertIn(self.wheel_set_premium.id, e_bike_components)
        
        # E-bike should allow both gearshift types
        self.assertIn(self.gearshift_7speed.id, e_bike_components)
        self.assertIn(self.gearshift_21speed.id, e_bike_components)
    
    def test_mountain_bike_component_mapping_premium_only(self):
        """Test that mountain bike mapping only includes premium components"""
        response = self.client.get(self.procurement_url)
        
        bike_mapping = json.loads(response.context['bike_component_mapping'])
        mountain_bike_components = bike_mapping[str(self.mountain_bike.id)]
        
        # Mountain bike should only include carbon frame
        self.assertIn(self.frame_carbon.id, mountain_bike_components)
        self.assertNotIn(self.frame_aluminum.id, mountain_bike_components)
        
        # Mountain bike should only include premium wheelset
        self.assertIn(self.wheel_set_premium.id, mountain_bike_components)
        self.assertNotIn(self.wheel_set_basic.id, mountain_bike_components)
        
        # Mountain bike should only include advanced gearshift
        self.assertIn(self.gearshift_21speed.id, mountain_bike_components)
        self.assertNotIn(self.gearshift_7speed.id, mountain_bike_components)
        
        # Mountain bike should NOT include motor
        self.assertNotIn(self.motor_250w.id, mountain_bike_components)
    
    def test_empty_component_requirements_fallback(self):
        """Test fallback behavior when bike type has no component requirements"""
        # Create bike type without component requirements
        empty_bike = BikeType.objects.create(
            session=self.session,
            name='Empty Bike',
            skilled_worker_hours=2.0,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.0,
            # No component requirements set - should use legacy fields
            wheel_set=self.wheel_set_basic,
            frame=self.frame_aluminum,
            handlebar=self.handlebar_basic,
            saddle=self.saddle_comfort,
            gearshift=self.gearshift_7speed,
            motor=None
        )
        
        response = self.client.get(self.procurement_url)
        
        bike_mapping = json.loads(response.context['bike_component_mapping'])
        empty_bike_components = bike_mapping[str(empty_bike.id)]
        
        # Should fallback to legacy fields
        expected_legacy_components = [
            self.wheel_set_basic.id,
            self.frame_aluminum.id,
            self.handlebar_basic.id,
            self.saddle_comfort.id,
            self.gearshift_7speed.id
        ]
        
        for component_id in expected_legacy_components:
            self.assertIn(component_id, empty_bike_components)
        
        # Should not include motor since legacy motor field is None
        self.assertNotIn(self.motor_250w.id, empty_bike_components)
    
    def test_completely_empty_bike_type_fallback(self):
        """Test ultimate fallback when bike type has no requirements or legacy fields"""
        # Create bike type with no requirements and no legacy fields
        ultimate_fallback_bike = BikeType.objects.create(
            session=self.session,
            name='Ultimate Fallback Bike',
            skilled_worker_hours=2.0,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=1.0
            # No component requirements AND no legacy fields
        )
        
        response = self.client.get(self.procurement_url)
        
        bike_mapping = json.loads(response.context['bike_component_mapping'])
        fallback_bike_components = bike_mapping[str(ultimate_fallback_bike.id)]
        
        # Should include all components as ultimate fallback
        all_component_ids = [
            self.wheel_set_basic.id,
            self.wheel_set_premium.id,
            self.frame_aluminum.id,
            self.frame_carbon.id,
            self.handlebar_basic.id,
            self.saddle_comfort.id,
            self.gearshift_7speed.id,
            self.gearshift_21speed.id,
            self.motor_250w.id
        ]
        
        for component_id in all_component_ids:
            self.assertIn(component_id, fallback_bike_components)
    
    def test_bike_types_included_in_context(self):
        """Test that bike types are included in template context for filtering UI"""
        response = self.client.get(self.procurement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('bike_types', response.context)
        
        bike_types = response.context['bike_types']
        bike_type_names = [bt.name for bt in bike_types]
        
        self.assertIn('Stadtrad', bike_type_names)
        self.assertIn('E-Bike', bike_type_names)
        self.assertIn('Mountainbike', bike_type_names)
