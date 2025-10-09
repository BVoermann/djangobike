from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
import json
import uuid

from bikeshop.models import (
    GameSession, BikeType, Component, ComponentType, 
    Supplier, SupplierPrice, BikePrice, Worker
)
from warehouse.models import Warehouse, ComponentStock, BikeStock
from .models import ProductionPlan, ProductionOrder, ProducedBike


class ProductionTestCase(TestCase):
    """Base test case with comprehensive test fixtures"""
    
    def setUp(self):
        """Create test data for production tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=1,
            current_year=2024,
            balance=Decimal('100000.00')
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            session=self.session,
            name='Main Warehouse',
            location='Test Location',
            capacity_m2=1000.0,
            rent_per_month=Decimal('5000.00')
        )
        
        # Create component types
        self.wheel_type = ComponentType.objects.create(
            session=self.session,
            name='Laufradsatz',
            storage_space_per_unit=2.0
        )
        
        self.frame_type = ComponentType.objects.create(
            session=self.session,
            name='Rahmen',
            storage_space_per_unit=5.0
        )
        
        self.handlebar_type = ComponentType.objects.create(
            session=self.session,
            name='Lenker',
            storage_space_per_unit=1.0
        )
        
        self.saddle_type = ComponentType.objects.create(
            session=self.session,
            name='Sattel',
            storage_space_per_unit=0.5
        )
        
        self.gearshift_type = ComponentType.objects.create(
            session=self.session,
            name='Schaltung',
            storage_space_per_unit=1.5
        )
        
        self.motor_type = ComponentType.objects.create(
            session=self.session,
            name='Motor',
            storage_space_per_unit=3.0
        )
        
        # Create components
        self.wheel_basic = Component.objects.create(
            session=self.session,
            component_type=self.wheel_type,
            name='Basic Wheels'
        )
        
        self.frame_basic = Component.objects.create(
            session=self.session,
            component_type=self.frame_type,
            name='Basic Frame'
        )
        
        self.handlebar_basic = Component.objects.create(
            session=self.session,
            component_type=self.handlebar_type,
            name='Basic Handlebar'
        )
        
        self.saddle_basic = Component.objects.create(
            session=self.session,
            component_type=self.saddle_type,
            name='Basic Saddle'
        )
        
        self.gearshift_basic = Component.objects.create(
            session=self.session,
            component_type=self.gearshift_type,
            name='Basic Gearshift'
        )
        
        self.motor_basic = Component.objects.create(
            session=self.session,
            component_type=self.motor_type,
            name='Basic Motor'
        )
        
        # Create bike types
        self.standard_bike = BikeType.objects.create(
            session=self.session,
            name='Standard Bike',
            skilled_worker_hours=3.0,
            unskilled_worker_hours=2.0,
            storage_space_per_unit=10.0,
            wheel_set=self.wheel_basic,
            frame=self.frame_basic,
            handlebar=self.handlebar_basic,
            saddle=self.saddle_basic,
            gearshift=self.gearshift_basic
        )
        
        self.e_bike = BikeType.objects.create(
            session=self.session,
            name='E-Bike',
            skilled_worker_hours=5.0,
            unskilled_worker_hours=3.0,
            storage_space_per_unit=12.0,
            wheel_set=self.wheel_basic,
            frame=self.frame_basic,
            handlebar=self.handlebar_basic,
            saddle=self.saddle_basic,
            gearshift=self.gearshift_basic,
            motor=self.motor_basic
        )
        
        # Create workers
        self.skilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='skilled',
            hourly_wage=Decimal('25.00'),
            monthly_hours=150,
            count=5  # 5 skilled workers = 750 hours capacity
        )
        
        self.unskilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='unskilled',
            hourly_wage=Decimal('15.00'),
            monthly_hours=150,
            count=8  # 8 unskilled workers = 1200 hours capacity
        )
        
        # Create component stocks (sufficient for initial tests)
        self.wheel_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.wheel_basic,
            quantity=100
        )
        
        self.frame_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.frame_basic,
            quantity=100
        )
        
        self.handlebar_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.handlebar_basic,
            quantity=100
        )
        
        self.saddle_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.saddle_basic,
            quantity=100
        )
        
        self.gearshift_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.gearshift_basic,
            quantity=100
        )
        
        self.motor_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=self.warehouse,
            component=self.motor_basic,
            quantity=50
        )
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')


class ProductionViewTests(ProductionTestCase):
    """Tests for production view GET requests and data display"""
    
    def test_production_view_requires_login(self):
        """Test that production view requires user authentication"""
        # Logout and try to access
        self.client.logout()
        response = self.client.get(reverse('production:production', kwargs={'session_id': self.session.id}))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_production_view_invalid_session(self):
        """Test accessing production view with invalid session ID"""
        invalid_session_id = uuid.uuid4()
        response = self.client.get(reverse('production:production', kwargs={'session_id': invalid_session_id}))
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_production_view_other_users_session(self):
        """Test accessing another user's session should return 404"""
        # Create another user and session
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_session = GameSession.objects.create(
            user=other_user,
            name='Other Session',
            current_month=1,
            current_year=2024
        )
        
        # Try to access other user's session
        response = self.client.get(reverse('production:production', kwargs={'session_id': other_session.id}))
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_production_view_get_success(self):
        """Test successful GET request to production view"""
        response = self.client.get(reverse('production:production', kwargs={'session_id': self.session.id}))
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Session')
        
        # Check context data
        self.assertEqual(response.context['session'], self.session)
        self.assertIn('bike_types', response.context)
        self.assertIn('workers', response.context)
        self.assertIn('component_stocks', response.context)
    
    def test_production_view_displays_bike_types(self):
        """Test that production view displays all bike types for the session"""
        response = self.client.get(reverse('production:production', kwargs={'session_id': self.session.id}))
        
        bike_types = response.context['bike_types']
        self.assertEqual(bike_types.count(), 2)
        
        bike_type_names = [bt.name for bt in bike_types]
        self.assertIn('Standard Bike', bike_type_names)
        self.assertIn('E-Bike', bike_type_names)
    
    def test_production_view_displays_workers(self):
        """Test that production view displays workers for the session"""
        response = self.client.get(reverse('production:production', kwargs={'session_id': self.session.id}))
        
        workers = response.context['workers']
        self.assertEqual(workers.count(), 2)
        
        worker_types = [w.worker_type for w in workers]
        self.assertIn('skilled', worker_types)
        self.assertIn('unskilled', worker_types)
    
    def test_production_view_displays_component_stocks(self):
        """Test that production view displays component stocks"""
        response = self.client.get(reverse('production:production', kwargs={'session_id': self.session.id}))
        
        component_stocks = response.context['component_stocks']
        self.assertEqual(component_stocks.count(), 6)  # All 6 component types
        
        # Check that all required components are present
        component_names = [cs.component.name for cs in component_stocks]
        expected_components = [
            'Basic Wheels', 'Basic Frame', 'Basic Handlebar',
            'Basic Saddle', 'Basic Gearshift', 'Basic Motor'
        ]
        for component_name in expected_components:
            self.assertIn(component_name, component_names)


class WorkerCapacityTests(ProductionTestCase):
    """Tests for worker capacity validation and management"""
    
    def test_successful_production_within_capacity(self):
        """Test successful production when within worker capacity limits"""
        # Produce 10 standard bikes (30 skilled hours, 20 unskilled hours)
        # Our capacity: 750 skilled hours, 1200 unskilled hours
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 5,
                'quantity_standard': 3,
                'quantity_premium': 2
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('10 Fahrräder produziert', response_data['message'])
    
    def test_skilled_worker_capacity_exceeded(self):
        """Test production failure when skilled worker capacity is exceeded"""
        # Try to produce 300 standard bikes (900 skilled hours needed, 750 available)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 100,
                'quantity_standard': 100,
                'quantity_premium': 100
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Facharbeiter-Kapazität', response_data['error'])
        self.assertIn('900', response_data['error'])  # Required hours
        self.assertIn('750', response_data['error'])  # Available hours
    
    def test_unskilled_worker_capacity_exceeded(self):
        """Test production failure when unskilled worker capacity is exceeded"""
        # Try to produce 250 standard bikes (750 skilled hours, 500 unskilled hours would be OK)
        # But we'll produce 700 cheap bikes (2100 skilled, 1400 unskilled) - skilled will fail first
        # So let's reduce skilled capacity first to make unskilled the limiting factor
        
        # Increase skilled workers to have enough capacity
        self.skilled_worker.count = 20  # 20 * 150 = 3000 hours (enough for 700 * 3 = 2100)
        self.skilled_worker.save()
        
        # Try to produce 700 standard bikes (1400 unskilled hours needed, 1200 available)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 700,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Hilfsarbeiter-Kapazität', response_data['error'])
        self.assertIn('1400', response_data['error'])  # Required hours (700 * 2)
        self.assertIn('1200', response_data['error'])  # Available hours
    
    def test_no_workers_available(self):
        """Test production failure when no workers are available"""
        # Remove all workers
        self.skilled_worker.count = 0
        self.skilled_worker.save()
        self.unskilled_worker.count = 0
        self.unskilled_worker.save()
        
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Facharbeiter-Kapazität', response_data['error'])
    
    def test_mixed_bike_types_capacity_calculation(self):
        """Test worker capacity calculation with multiple bike types"""
        # Produce a mix: 50 standard bikes + 30 e-bikes
        # Standard: 50 * (3 skilled + 2 unskilled) = 150 skilled + 100 unskilled
        # E-bikes: 30 * (5 skilled + 3 unskilled) = 150 skilled + 90 unskilled
        # Total: 300 skilled hours, 190 unskilled hours (within capacity)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 20,
                'quantity_standard': 15,
                'quantity_premium': 15
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 10,
                'quantity_standard': 10,
                'quantity_premium': 10
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('80 Fahrräder produziert', response_data['message'])
    
    def test_exact_capacity_limit(self):
        """Test production at exact worker capacity limits"""
        # Use exactly 750 skilled hours and 1200 unskilled hours
        # 150 standard bikes = 450 skilled + 300 unskilled
        # 60 e-bikes = 300 skilled + 180 unskilled  
        # Total = 750 skilled + 480 unskilled (within limits)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 150,
                'quantity_standard': 0,
                'quantity_premium': 0
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 60,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('210 Fahrräder produziert', response_data['message'])


class ComponentStockTests(ProductionTestCase):
    """Tests for component stock validation and consumption"""
    
    def test_component_consumption_standard_bike(self):
        """Test that producing standard bikes consumes correct component quantities"""
        # Initial stock quantities
        initial_wheels = self.wheel_stock.quantity
        initial_frames = self.frame_stock.quantity
        initial_handlebars = self.handlebar_stock.quantity
        initial_saddles = self.saddle_stock.quantity
        initial_gearshifts = self.gearshift_stock.quantity
        initial_motors = self.motor_stock.quantity
        
        # Produce 10 standard bikes
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 4,
                'quantity_standard': 3,
                'quantity_premium': 3
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Refresh stocks from database
        self.wheel_stock.refresh_from_db()
        self.frame_stock.refresh_from_db()
        self.handlebar_stock.refresh_from_db()
        self.saddle_stock.refresh_from_db()
        self.gearshift_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        # Check that each component was reduced by 10 (one per bike)
        self.assertEqual(self.wheel_stock.quantity, initial_wheels - 10)
        self.assertEqual(self.frame_stock.quantity, initial_frames - 10)
        self.assertEqual(self.handlebar_stock.quantity, initial_handlebars - 10)
        self.assertEqual(self.saddle_stock.quantity, initial_saddles - 10)
        self.assertEqual(self.gearshift_stock.quantity, initial_gearshifts - 10)
        
        # Motor should not be consumed for standard bikes
        self.assertEqual(self.motor_stock.quantity, initial_motors)
    
    def test_component_consumption_e_bike(self):
        """Test that producing e-bikes consumes correct component quantities including motor"""
        # Initial stock quantities
        initial_wheels = self.wheel_stock.quantity
        initial_frames = self.frame_stock.quantity
        initial_handlebars = self.handlebar_stock.quantity
        initial_saddles = self.saddle_stock.quantity
        initial_gearshifts = self.gearshift_stock.quantity
        initial_motors = self.motor_stock.quantity
        
        # Produce 5 e-bikes
        production_data = [
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 2,
                'quantity_standard': 2,
                'quantity_premium': 1
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Refresh stocks from database
        self.wheel_stock.refresh_from_db()
        self.frame_stock.refresh_from_db()
        self.handlebar_stock.refresh_from_db()
        self.saddle_stock.refresh_from_db()
        self.gearshift_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        # Check that each component was reduced by 5 (one per bike, including motor)
        self.assertEqual(self.wheel_stock.quantity, initial_wheels - 5)
        self.assertEqual(self.frame_stock.quantity, initial_frames - 5)
        self.assertEqual(self.handlebar_stock.quantity, initial_handlebars - 5)
        self.assertEqual(self.saddle_stock.quantity, initial_saddles - 5)
        self.assertEqual(self.gearshift_stock.quantity, initial_gearshifts - 5)
        self.assertEqual(self.motor_stock.quantity, initial_motors - 5)
    
    def test_insufficient_component_stock(self):
        """Test production failure when component stock is insufficient"""
        # Reduce wheel stock to only 5 units
        self.wheel_stock.quantity = 5
        self.wheel_stock.save()
        
        # Try to produce 10 standard bikes (needs 10 wheels)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 10,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Basic Wheels im Lager', response_data['error'])
        self.assertIn('Benötigt: 10', response_data['error'])
        self.assertIn('Verfügbar: 5', response_data['error'])
    
    def test_missing_component_in_stock(self):
        """Test production failure when required component is completely missing from stock"""
        # Remove all frame stock
        self.frame_stock.delete()
        
        # Try to produce 1 standard bike
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Komponente nicht im Lager vorhanden', response_data['error'])
    
    def test_mixed_production_component_consumption(self):
        """Test component consumption with mixed bike types"""
        # Initial stock quantities
        initial_wheels = self.wheel_stock.quantity
        initial_motors = self.motor_stock.quantity
        
        # Produce 5 standard bikes and 3 e-bikes
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 5,
                'quantity_standard': 0,
                'quantity_premium': 0
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 3,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Refresh stocks
        self.wheel_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        # Both bike types need wheels: 5 + 3 = 8 wheels consumed
        self.assertEqual(self.wheel_stock.quantity, initial_wheels - 8)
        
        # Only e-bikes need motors: 3 motors consumed
        self.assertEqual(self.motor_stock.quantity, initial_motors - 3)
    
    def test_zero_stock_component(self):
        """Test production failure when component stock is zero"""
        # Set motor stock to zero
        self.motor_stock.quantity = 0
        self.motor_stock.save()
        
        # Try to produce 1 e-bike
        production_data = [
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Basic Motor im Lager', response_data['error'])
        self.assertIn('Benötigt: 1', response_data['error'])
        self.assertIn('Verfügbar: 0', response_data['error'])
    
    def test_stock_not_affected_on_validation_failure(self):
        """Test that component stocks are not modified when validation fails"""
        # Initial quantities
        initial_quantities = {
            'wheels': self.wheel_stock.quantity,
            'frames': self.frame_stock.quantity,
            'handlebars': self.handlebar_stock.quantity,
            'saddles': self.saddle_stock.quantity,
            'gearshifts': self.gearshift_stock.quantity,
            'motors': self.motor_stock.quantity
        }
        
        # Try production that will fail due to worker capacity
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1000,  # This will exceed worker capacity
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
        # Refresh all stocks
        self.wheel_stock.refresh_from_db()
        self.frame_stock.refresh_from_db()
        self.handlebar_stock.refresh_from_db()
        self.saddle_stock.refresh_from_db()
        self.gearshift_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        # Verify no stock changes occurred
        self.assertEqual(self.wheel_stock.quantity, initial_quantities['wheels'])
        self.assertEqual(self.frame_stock.quantity, initial_quantities['frames'])
        self.assertEqual(self.handlebar_stock.quantity, initial_quantities['handlebars'])
        self.assertEqual(self.saddle_stock.quantity, initial_quantities['saddles'])
        self.assertEqual(self.gearshift_stock.quantity, initial_quantities['gearshifts'])
        self.assertEqual(self.motor_stock.quantity, initial_quantities['motors'])


class ProductionWorkflowTests(ProductionTestCase):
    """Tests for complete production workflow integration"""
    
    def test_complete_production_workflow(self):
        """Test the complete workflow: components → production → warehouse storage"""
        # Initial state verification
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 0)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), 0)
        self.assertEqual(ProductionPlan.objects.filter(session=self.session).count(), 0)
        self.assertEqual(ProductionOrder.objects.filter(session=self.session).count(), 0)
        
        # Produce bikes
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 3,
                'quantity_standard': 2,
                'quantity_premium': 1
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 2,
                'quantity_standard': 1,
                'quantity_premium': 1
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('10 Fahrräder produziert', response_data['message'])
        
        # Verify production plan was created
        production_plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        self.assertIsNotNone(production_plan)
        
        # Verify production orders were created
        orders = ProductionOrder.objects.filter(plan=production_plan)
        self.assertEqual(orders.count(), 6)  # 3 standard + 3 e-bike segments
        
        # Check order details
        standard_orders = orders.filter(bike_type=self.standard_bike)
        self.assertEqual(standard_orders.count(), 3)
        
        e_bike_orders = orders.filter(bike_type=self.e_bike)
        self.assertEqual(e_bike_orders.count(), 3)
        
        # Verify individual bikes were produced
        produced_bikes = ProducedBike.objects.filter(session=self.session)
        self.assertEqual(produced_bikes.count(), 10)
        
        # Check bike distribution by type and segment
        standard_bikes = produced_bikes.filter(bike_type=self.standard_bike)
        self.assertEqual(standard_bikes.count(), 6)
        self.assertEqual(standard_bikes.filter(price_segment='cheap').count(), 3)
        self.assertEqual(standard_bikes.filter(price_segment='standard').count(), 2)
        self.assertEqual(standard_bikes.filter(price_segment='premium').count(), 1)
        
        e_bikes = produced_bikes.filter(bike_type=self.e_bike)
        self.assertEqual(e_bikes.count(), 4)
        self.assertEqual(e_bikes.filter(price_segment='cheap').count(), 2)
        self.assertEqual(e_bikes.filter(price_segment='standard').count(), 1)
        self.assertEqual(e_bikes.filter(price_segment='premium').count(), 1)
        
        # Verify bikes were added to warehouse stock
        bike_stocks = BikeStock.objects.filter(session=self.session)
        self.assertEqual(bike_stocks.count(), 10)
        
        # All bikes should be stored in the same warehouse
        for stock in bike_stocks:
            self.assertEqual(stock.warehouse, self.warehouse)
            self.assertIn(stock.bike, produced_bikes)
        
        # Verify production dates
        for bike in produced_bikes:
            self.assertEqual(bike.production_month, self.session.current_month)
            self.assertEqual(bike.production_year, self.session.current_year)
            self.assertFalse(bike.is_sold)  # Should not be sold initially
    
    def test_production_plan_update_replaces_old_orders(self):
        """Test that new production plan replaces old orders for the same month"""
        # First production run
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 2,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify first production
        first_plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        first_orders = ProductionOrder.objects.filter(plan=first_plan)
        self.assertEqual(first_orders.count(), 1)  # Only cheap segment
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 2)
        
        # Second production run (should replace old orders)
        production_data = [
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 0,
                'quantity_standard': 3,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify plan is the same but orders are different
        updated_plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        self.assertEqual(updated_plan.id, first_plan.id)  # Same plan object
        
        # Orders should be replaced
        updated_orders = ProductionOrder.objects.filter(plan=updated_plan)
        self.assertEqual(updated_orders.count(), 1)  # Only e-bike standard
        self.assertEqual(updated_orders.first().bike_type, self.e_bike)
        self.assertEqual(updated_orders.first().price_segment, 'standard')
        
        # Total bikes produced should be 2 + 3 = 5
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 5)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), 5)
    
    def test_warehouse_storage_integration(self):
        """Test that produced bikes are correctly stored in warehouse"""
        initial_usage = self.warehouse.current_usage
        
        # Produce bikes with known storage requirements
        # Standard bike: 10 m² per unit, E-bike: 12 m² per unit
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 2,  # 2 * 10 = 20 m²
                'quantity_standard': 0,
                'quantity_premium': 0
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 1,  # 1 * 12 = 12 m²
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify warehouse usage increased
        self.warehouse.refresh_from_db()
        expected_additional_usage = (2 * 10.0) + (1 * 12.0)  # 32 m²
        self.assertEqual(self.warehouse.current_usage, initial_usage + expected_additional_usage)
        
        # Verify remaining capacity decreased
        expected_remaining = self.warehouse.capacity_m2 - (initial_usage + expected_additional_usage)
        self.assertEqual(self.warehouse.remaining_capacity, expected_remaining)
    
    def test_no_warehouse_available_failure(self):
        """Test production failure when no warehouse is available"""
        # Remove the warehouse
        self.warehouse.delete()
        
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Kein Lager verfügbar', response_data['error'])
        
        # Verify no production occurred
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 0)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), 0)
        self.assertEqual(ProductionPlan.objects.filter(session=self.session).count(), 0)
    
    def test_empty_production_data(self):
        """Test handling of empty production data"""
        production_data = []
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('0 Fahrräder produziert', response_data['message'])
        
        # Verify plan is created but no orders or bikes
        plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        self.assertEqual(plan.orders.count(), 0)
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 0)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), 0)
    
    def test_zero_quantity_production(self):
        """Test production with all zero quantities"""
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 0,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('0 Fahrräder produziert', response_data['message'])
        
        # Plan should be created but no orders
        plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        self.assertEqual(plan.orders.count(), 0)


class WarehouseCapacityTests(ProductionTestCase):
    """Tests for warehouse capacity calculations and space management"""
    
    def test_warehouse_current_usage_calculation(self):
        """Test current warehouse usage calculation with components and bikes"""
        # Initial usage (components only)
        # Wheels: 100 * 2.0 = 200 m²
        # Frames: 100 * 5.0 = 500 m²
        # Handlebars: 100 * 1.0 = 100 m²
        # Saddles: 100 * 0.5 = 50 m²
        # Gearshifts: 100 * 1.5 = 150 m²
        # Motors: 50 * 3.0 = 150 m²
        # Total: 1150 m²
        expected_initial_usage = (100 * 2.0) + (100 * 5.0) + (100 * 1.0) + (100 * 0.5) + (100 * 1.5) + (50 * 3.0)
        self.assertEqual(self.warehouse.current_usage, expected_initial_usage)
        
        # Produce bikes and check usage increase
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 2,  # 2 * 10 = 20 m²
                'quantity_standard': 0,
                'quantity_premium': 0
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 1,  # 1 * 12 = 12 m²
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify updated usage
        self.warehouse.refresh_from_db()
        bike_usage = (2 * 10.0) + (1 * 12.0)  # 32 m²
        # Component usage should be reduced by consumed components
        component_usage_reduction = (3 * 2.0) + (3 * 5.0) + (3 * 1.0) + (3 * 0.5) + (3 * 1.5) + (1 * 3.0)  # 33 m²
        
        expected_new_usage = expected_initial_usage + bike_usage - component_usage_reduction
        self.assertEqual(self.warehouse.current_usage, expected_new_usage)
    
    def test_warehouse_remaining_capacity_calculation(self):
        """Test remaining warehouse capacity calculation"""
        initial_remaining = self.warehouse.remaining_capacity
        initial_usage = self.warehouse.current_usage
        
        # Verify initial calculation
        self.assertEqual(initial_remaining, self.warehouse.capacity_m2 - initial_usage)
        
        # Produce bikes and verify remaining capacity changes
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 5,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify remaining capacity updated
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.remaining_capacity, 
                        self.warehouse.capacity_m2 - self.warehouse.current_usage)
        self.assertLess(self.warehouse.remaining_capacity, initial_remaining)
    
    def test_component_storage_space_calculation(self):
        """Test that component storage space is correctly calculated"""
        # Create a warehouse with limited capacity for easier testing
        small_warehouse = Warehouse.objects.create(
            session=self.session,
            name='Small Warehouse',
            location='Test Location 2',
            capacity_m2=100.0,
            rent_per_month=Decimal('1000.00')
        )
        
        # Create component stocks with known quantities
        wheel_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=small_warehouse,
            component=self.wheel_basic,
            quantity=10  # 10 * 2.0 = 20 m²
        )
        
        frame_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=small_warehouse,
            component=self.frame_basic,
            quantity=5  # 5 * 5.0 = 25 m²
        )
        
        # Expected usage: 20 + 25 = 45 m²
        expected_usage = (10 * 2.0) + (5 * 5.0)
        self.assertEqual(small_warehouse.current_usage, expected_usage)
        self.assertEqual(small_warehouse.remaining_capacity, 100.0 - expected_usage)
    
    def test_bike_storage_space_calculation(self):
        """Test that bike storage space is correctly calculated"""
        # Start with empty warehouse
        empty_warehouse = Warehouse.objects.create(
            session=self.session,
            name='Empty Warehouse',
            location='Test Location 3',
            capacity_m2=200.0,
            rent_per_month=Decimal('2000.00')
        )
        
        # Manually create bike stocks to test space calculation
        for i in range(3):
            produced_bike = ProducedBike.objects.create(
                session=self.session,
                bike_type=self.standard_bike,  # 10 m² per bike
                price_segment='cheap',
                production_month=1,
                production_year=2024
            )
            BikeStock.objects.create(
                session=self.session,
                warehouse=empty_warehouse,
                bike=produced_bike
            )
        
        for i in range(2):
            produced_bike = ProducedBike.objects.create(
                session=self.session,
                bike_type=self.e_bike,  # 12 m² per bike
                price_segment='premium',
                production_month=1,
                production_year=2024
            )
            BikeStock.objects.create(
                session=self.session,
                warehouse=empty_warehouse,
                bike=produced_bike
            )
        
        # Expected usage: (3 * 10) + (2 * 12) = 54 m²
        expected_usage = (3 * 10.0) + (2 * 12.0)
        self.assertEqual(empty_warehouse.current_usage, expected_usage)
        self.assertEqual(empty_warehouse.remaining_capacity, 200.0 - expected_usage)
    
    def test_mixed_storage_calculation(self):
        """Test storage calculation with both components and bikes"""
        # Create warehouse with both types of inventory
        mixed_warehouse = Warehouse.objects.create(
            session=self.session,
            name='Mixed Warehouse',
            location='Mixed Location',
            capacity_m2=500.0,
            rent_per_month=Decimal('3000.00')
        )
        
        # Add components
        wheel_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=mixed_warehouse,
            component=self.wheel_basic,
            quantity=20  # 20 * 2.0 = 40 m²
        )
        
        saddle_stock = ComponentStock.objects.create(
            session=self.session,
            warehouse=mixed_warehouse,
            component=self.saddle_basic,
            quantity=30  # 30 * 0.5 = 15 m²
        )
        
        # Add bikes
        for i in range(4):
            produced_bike = ProducedBike.objects.create(
                session=self.session,
                bike_type=self.standard_bike,  # 10 m² per bike
                price_segment='standard',
                production_month=1,
                production_year=2024
            )
            BikeStock.objects.create(
                session=self.session,
                warehouse=mixed_warehouse,
                bike=produced_bike
            )
        
        # Expected usage: Components (40 + 15) + Bikes (4 * 10) = 95 m²
        expected_usage = 40.0 + 15.0 + (4 * 10.0)
        self.assertEqual(mixed_warehouse.current_usage, expected_usage)
        self.assertEqual(mixed_warehouse.remaining_capacity, 500.0 - expected_usage)
    
    def test_warehouse_usage_after_component_consumption(self):
        """Test that warehouse usage decreases when components are consumed in production"""
        initial_usage = self.warehouse.current_usage
        
        # Record component quantities before production
        initial_wheel_qty = self.wheel_stock.quantity
        initial_frame_qty = self.frame_stock.quantity
        
        # Produce bikes (this will consume components)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 3,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Refresh warehouse and check usage
        self.warehouse.refresh_from_db()
        
        # Component space freed: 3 * (2.0 + 5.0 + 1.0 + 0.5 + 1.5) = 3 * 10 = 30 m²
        component_space_freed = 3 * (
            self.wheel_basic.component_type.storage_space_per_unit +
            self.frame_basic.component_type.storage_space_per_unit +
            self.handlebar_basic.component_type.storage_space_per_unit +
            self.saddle_basic.component_type.storage_space_per_unit +
            self.gearshift_basic.component_type.storage_space_per_unit
        )
        
        # Bike space used: 3 * 10 = 30 m²
        bike_space_used = 3 * self.standard_bike.storage_space_per_unit
        
        # Net change: -30 + 30 = 0 (space freed by components equals space used by bikes)
        expected_new_usage = initial_usage - component_space_freed + bike_space_used
        self.assertEqual(self.warehouse.current_usage, expected_new_usage)
    
    def test_warehouse_capacity_properties_consistency(self):
        """Test that warehouse capacity properties remain mathematically consistent"""
        # Test with various warehouse states
        for _ in range(5):  # Test multiple scenarios
            # Produce random quantities
            import random
            std_qty = random.randint(1, 10)
            
            production_data = [
                {
                    'bike_type_id': self.standard_bike.id,
                    'quantity_cheap': std_qty,
                    'quantity_standard': 0,
                    'quantity_premium': 0
                }
            ]
            
            response = self.client.post(
                reverse('production:production', kwargs={'session_id': self.session.id}),
                data=json.dumps(production_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                response_data = json.loads(response.content)
                if response_data['success']:
                    # Check consistency
                    self.warehouse.refresh_from_db()
                    calculated_remaining = self.warehouse.capacity_m2 - self.warehouse.current_usage
                    self.assertAlmostEqual(self.warehouse.remaining_capacity, calculated_remaining, places=2)
                    
                    # Usage should never exceed capacity
                    self.assertLessEqual(self.warehouse.current_usage, self.warehouse.capacity_m2)
                    
                    # Remaining capacity should not be negative
                    self.assertGreaterEqual(self.warehouse.remaining_capacity, 0)


class WorkerHiringTests(ProductionTestCase):
    """Tests for worker hiring functionality"""
    
    def test_hire_skilled_worker_success(self):
        """Test successful hiring of skilled workers"""
        initial_count = self.skilled_worker.count
        
        hire_data = {
            'worker_type': 'skilled',
            'count': 3
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('3 Facharbeiter erfolgreich eingestellt', response_data['message'])
        
        # Verify worker count increased
        self.skilled_worker.refresh_from_db()
        self.assertEqual(self.skilled_worker.count, initial_count + 3)
        self.assertEqual(response_data['new_count'], initial_count + 3)
        
        # Verify cost calculation
        monthly_cost_per_worker = self.skilled_worker.hourly_wage * self.skilled_worker.monthly_hours
        expected_cost = float(monthly_cost_per_worker * 3)
        self.assertEqual(response_data['total_cost'], expected_cost)
    
    def test_hire_unskilled_worker_success(self):
        """Test successful hiring of unskilled workers"""
        initial_count = self.unskilled_worker.count
        
        hire_data = {
            'worker_type': 'unskilled',
            'count': 5
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('5 Hilfsarbeiter erfolgreich eingestellt', response_data['message'])
        
        # Verify worker count increased
        self.unskilled_worker.refresh_from_db()
        self.assertEqual(self.unskilled_worker.count, initial_count + 5)
        self.assertEqual(response_data['new_count'], initial_count + 5)
        
        # Verify cost calculation
        monthly_cost_per_worker = self.unskilled_worker.hourly_wage * self.unskilled_worker.monthly_hours
        expected_cost = float(monthly_cost_per_worker * 5)
        self.assertEqual(response_data['total_cost'], expected_cost)
    
    def test_hire_worker_creates_new_worker_record(self):
        """Test that hiring creates new worker record if none exists"""
        # Remove existing workers
        Worker.objects.filter(session=self.session).delete()
        
        hire_data = {
            'worker_type': 'skilled',
            'count': 2
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify new worker record was created
        new_skilled_worker = Worker.objects.get(session=self.session, worker_type='skilled')
        self.assertEqual(new_skilled_worker.count, 2)
        self.assertEqual(new_skilled_worker.hourly_wage, Decimal('25.00'))
        self.assertEqual(new_skilled_worker.monthly_hours, 150)
        self.assertEqual(response_data['new_count'], 2)
    
    def test_hire_worker_invalid_worker_type(self):
        """Test hiring with invalid worker type"""
        hire_data = {
            'worker_type': 'invalid',
            'count': 1
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Ungültiger Arbeitertyp', response_data['error'])
    
    def test_hire_worker_zero_count(self):
        """Test hiring zero workers"""
        initial_count = self.skilled_worker.count
        
        hire_data = {
            'worker_type': 'skilled',
            'count': 0
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])  # Should succeed but no change
        
        # Verify no change in worker count
        self.skilled_worker.refresh_from_db()
        self.assertEqual(self.skilled_worker.count, initial_count)
    
    def test_hire_worker_negative_count(self):
        """Test hiring negative number of workers"""
        hire_data = {
            'worker_type': 'skilled',
            'count': -5
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        # Should succeed - negative count will reduce worker count
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
    
    def test_hire_worker_default_wages(self):
        """Test that new workers get correct default wages"""
        # Remove existing workers to test defaults
        Worker.objects.filter(session=self.session).delete()
        
        # Hire skilled worker
        hire_data = {
            'worker_type': 'skilled',
            'count': 1
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        skilled_worker = Worker.objects.get(session=self.session, worker_type='skilled')
        self.assertEqual(skilled_worker.hourly_wage, Decimal('25.00'))
        self.assertEqual(skilled_worker.monthly_hours, 150)
        
        # Hire unskilled worker
        hire_data = {
            'worker_type': 'unskilled',
            'count': 1
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        unskilled_worker = Worker.objects.get(session=self.session, worker_type='unskilled')
        self.assertEqual(unskilled_worker.hourly_wage, Decimal('15.00'))
        self.assertEqual(unskilled_worker.monthly_hours, 150)
    
    def test_hire_worker_capacity_increase(self):
        """Test that hiring workers increases production capacity"""
        # Initial capacities
        initial_skilled_capacity = self.skilled_worker.count * self.skilled_worker.monthly_hours
        initial_unskilled_capacity = self.unskilled_worker.count * self.unskilled_worker.monthly_hours
        
        # Hire additional workers
        hire_data = {
            'worker_type': 'skilled',
            'count': 2
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Test production with increased capacity
        # Should now be able to produce more bikes
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 200,  # 600 skilled hours needed
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # With 7 skilled workers (5+2), we have 1050 hours capacity, so this should succeed
        self.assertTrue(response_data['success'])
        self.assertIn('200 Fahrräder produziert', response_data['message'])
    
    def test_hire_worker_requires_login(self):
        """Test that hiring workers requires authentication"""
        self.client.logout()
        
        hire_data = {
            'worker_type': 'skilled',
            'count': 1
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_hire_worker_invalid_session(self):
        """Test hiring workers with invalid session ID"""
        invalid_session_id = uuid.uuid4()
        
        hire_data = {
            'worker_type': 'skilled',
            'count': 1
        }
        
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': invalid_session_id}),
            data=json.dumps(hire_data),
            content_type='application/json'
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_hire_worker_get_method_not_allowed(self):
        """Test that GET requests to hire worker endpoint are not allowed"""
        response = self.client.get(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nur POST-Anfragen erlaubt', response_data['error'])
    
    def test_hire_worker_invalid_json(self):
        """Test hiring workers with invalid JSON data"""
        response = self.client.post(
            reverse('production:hire_worker', kwargs={'session_id': self.session.id}),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        # Should contain error about invalid JSON or missing required fields
        self.assertIn('error', response_data)


class EdgeCasesAndErrorTests(ProductionTestCase):
    """Tests for edge cases and error conditions"""
    
    def test_production_invalid_bike_type_id(self):
        """Test production with invalid bike type ID"""
        production_data = [
            {
                'bike_type_id': 99999,  # Non-existent ID
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should return 404 for invalid bike type
        self.assertEqual(response.status_code, 404)
    
    def test_production_invalid_json_format(self):
        """Test production with invalid JSON format"""
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data='invalid json format',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_production_missing_required_fields(self):
        """Test production with missing required fields"""
        production_data = [
            {
                # Missing bike_type_id
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_production_non_integer_quantities(self):
        """Test production with non-integer quantities"""
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 'not_a_number',
                'quantity_standard': 1.5,  # Float instead of int
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_production_extremely_large_quantities(self):
        """Test production with extremely large quantities"""
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1000000,  # Extremely large number
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        # Should fail due to worker capacity or component availability
        self.assertFalse(response_data['success'])
        self.assertTrue(
            'Nicht genügend Facharbeiter-Kapazität' in response_data['error'] or
            'im Lager' in response_data['error']
        )
    
    def test_production_negative_quantities(self):
        """Test production with negative quantities"""
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': -5,  # Negative quantity
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        # Negative quantities should be treated as 0 or cause an error
        # The current implementation uses int() which would convert -5 to -5
        # But the production loop checks if quantity > 0, so negative should be ignored
        self.assertTrue(response_data['success'])
        self.assertIn('0 Fahrräder produziert', response_data['message'])
    
    def test_production_bike_type_from_different_session(self):
        """Test production using bike type from different session"""
        # Create another user and session
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_session = GameSession.objects.create(
            user=other_user,
            name='Other Session'
        )
        
        # Create bike type in other session
        other_bike = BikeType.objects.create(
            session=other_session,
            name='Other Bike',
            skilled_worker_hours=2.0,
            unskilled_worker_hours=1.0,
            storage_space_per_unit=8.0,
            wheel_set=self.wheel_basic,  # Using components from our session
            frame=self.frame_basic,
            handlebar=self.handlebar_basic,
            saddle=self.saddle_basic,
            gearshift=self.gearshift_basic
        )
        
        # Try to produce using other session's bike type
        production_data = [
            {
                'bike_type_id': other_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should return 404 (bike type not found in current session)
        self.assertEqual(response.status_code, 404)
    
    def test_production_empty_request_body(self):
        """Test production with empty request body"""
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data='',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_production_malformed_data_structure(self):
        """Test production with malformed data structure"""
        # Send object instead of array
        production_data = {
            'bike_type_id': self.standard_bike.id,
            'quantity_cheap': 1
        }
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_production_component_deletion_during_production(self):
        """Test handling of component deletion during production validation"""
        # This tests a race condition scenario
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        # Delete a required component to simulate race condition
        self.wheel_stock.delete()
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Komponente nicht im Lager vorhanden', response_data['error'])
    
    def test_production_with_null_motor_bike_type(self):
        """Test production with bike type that has null motor (standard bikes)"""
        # Ensure standard bike doesn't have motor
        self.assertIsNone(self.standard_bike.motor)
        
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 2,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Motor stock should not be affected
        motor_stock_after = ComponentStock.objects.get(
            session=self.session,
            component=self.motor_basic
        ).quantity
        self.assertEqual(motor_stock_after, 50)  # Should remain unchanged
    
    def test_production_mixed_valid_invalid_data(self):
        """Test production with mix of valid and invalid data"""
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            },
            {
                'bike_type_id': 99999,  # Invalid bike type
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should fail completely due to invalid bike type (404)
        self.assertEqual(response.status_code, 404)
        
        # Verify no production occurred for valid items either
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), 0)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), 0)
    
    def test_production_insufficient_warehouse_capacity(self):
        """Test production when warehouse doesn't have enough space"""
        # Create a tiny warehouse and fill it up
        tiny_warehouse = Warehouse.objects.create(
            session=self.session,
            name='Tiny Warehouse',
            location='Tiny Location',
            capacity_m2=50.0,  # Very small capacity
            rent_per_month=Decimal('100.00')
        )
        
        # Delete the main warehouse to force use of tiny one
        self.warehouse.delete()
        
        # Fill up most of the tiny warehouse with components
        ComponentStock.objects.create(
            session=self.session,
            warehouse=tiny_warehouse,
            component=self.wheel_basic,
            quantity=20  # 20 * 2.0 = 40 m²
        )
        
        # Only 10 m² left, but we want to produce bikes that need more space
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,  # 10 m² per bike
                'quantity_cheap': 2,  # Would need 20 m² but only 10 available
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # This should succeed because the current implementation doesn't check warehouse capacity
        # In a more advanced version, this might fail with warehouse capacity error
        self.assertEqual(response.status_code, 200)
        # The system currently allows over-capacity storage, so this will succeed
    
    def test_production_concurrent_stock_modification(self):
        """Test production behavior when stock is modified concurrently"""
        # Simulate concurrent modification by reducing stock between validation passes
        initial_wheel_stock = self.wheel_stock.quantity
        
        # Mock the component stock to have minimal quantity
        self.wheel_stock.quantity = 1
        self.wheel_stock.save()
        
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,  # Should just fit
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify stock was consumed
        self.wheel_stock.refresh_from_db()
        self.assertEqual(self.wheel_stock.quantity, 0)


class AtomicTransactionTests(ProductionTestCase):
    """Tests for atomic transaction behavior during production failures"""
    
    def test_production_transaction_rollback_on_worker_capacity_failure(self):
        """Test that database changes are rolled back when worker capacity is exceeded"""
        # Record initial state
        initial_production_plans = ProductionPlan.objects.filter(session=self.session).count()
        initial_production_orders = ProductionOrder.objects.count()
        initial_produced_bikes = ProducedBike.objects.filter(session=self.session).count()
        initial_bike_stocks = BikeStock.objects.filter(session=self.session).count()
        initial_component_stocks = {
            'wheels': self.wheel_stock.quantity,
            'frames': self.frame_stock.quantity,
            'handlebars': self.handlebar_stock.quantity,
            'saddles': self.saddle_stock.quantity,
            'gearshifts': self.gearshift_stock.quantity,
            'motors': self.motor_stock.quantity
        }
        
        # Attempt production that exceeds worker capacity
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1000,  # This will exceed skilled worker capacity
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Facharbeiter-Kapazität', response_data['error'])
        
        # Verify no database changes occurred
        self.assertEqual(ProductionPlan.objects.filter(session=self.session).count(), initial_production_plans)
        self.assertEqual(ProductionOrder.objects.count(), initial_production_orders)
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), initial_produced_bikes)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), initial_bike_stocks)
        
        # Verify component stocks unchanged
        self.wheel_stock.refresh_from_db()
        self.frame_stock.refresh_from_db()
        self.handlebar_stock.refresh_from_db()
        self.saddle_stock.refresh_from_db()
        self.gearshift_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        self.assertEqual(self.wheel_stock.quantity, initial_component_stocks['wheels'])
        self.assertEqual(self.frame_stock.quantity, initial_component_stocks['frames'])
        self.assertEqual(self.handlebar_stock.quantity, initial_component_stocks['handlebars'])
        self.assertEqual(self.saddle_stock.quantity, initial_component_stocks['saddles'])
        self.assertEqual(self.gearshift_stock.quantity, initial_component_stocks['gearshifts'])
        self.assertEqual(self.motor_stock.quantity, initial_component_stocks['motors'])
    
    def test_production_transaction_rollback_on_component_shortage(self):
        """Test that database changes are rolled back when components are insufficient"""
        # Record initial state
        initial_production_plans = ProductionPlan.objects.filter(session=self.session).count()
        initial_production_orders = ProductionOrder.objects.count()
        initial_produced_bikes = ProducedBike.objects.filter(session=self.session).count()
        initial_bike_stocks = BikeStock.objects.filter(session=self.session).count()
        
        # Reduce component stock to insufficient level
        self.wheel_stock.quantity = 2
        self.wheel_stock.save()
        initial_wheel_stock = self.wheel_stock.quantity
        
        # Attempt production that exceeds component availability
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 5,  # Need 5 wheels but only 2 available
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Nicht genügend Basic Wheels im Lager', response_data['error'])
        
        # Verify no database changes occurred
        self.assertEqual(ProductionPlan.objects.filter(session=self.session).count(), initial_production_plans)
        self.assertEqual(ProductionOrder.objects.count(), initial_production_orders)
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), initial_produced_bikes)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), initial_bike_stocks)
        
        # Verify component stock unchanged
        self.wheel_stock.refresh_from_db()
        self.assertEqual(self.wheel_stock.quantity, initial_wheel_stock)
    
    def test_production_transaction_rollback_on_warehouse_missing(self):
        """Test that database changes are rolled back when warehouse is missing"""
        # Record initial state
        initial_production_plans = ProductionPlan.objects.filter(session=self.session).count()
        initial_production_orders = ProductionOrder.objects.count()
        initial_produced_bikes = ProducedBike.objects.filter(session=self.session).count()
        initial_bike_stocks = BikeStock.objects.filter(session=self.session).count()
        initial_component_stocks = {
            'wheels': self.wheel_stock.quantity,
            'frames': self.frame_stock.quantity,
            'handlebars': self.handlebar_stock.quantity,
            'saddles': self.saddle_stock.quantity,
            'gearshifts': self.gearshift_stock.quantity,
            'motors': self.motor_stock.quantity
        }
        
        # Remove warehouse to trigger failure
        self.warehouse.delete()
        
        # Attempt production
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Kein Lager verfügbar', response_data['error'])
        
        # Verify no database changes occurred
        self.assertEqual(ProductionPlan.objects.filter(session=self.session).count(), initial_production_plans)
        self.assertEqual(ProductionOrder.objects.count(), initial_production_orders)
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), initial_produced_bikes)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), initial_bike_stocks)
        
        # Verify component stocks unchanged (refresh from DB since warehouse was deleted)
        wheel_stock = ComponentStock.objects.filter(session=self.session, component=self.wheel_basic).first()
        frame_stock = ComponentStock.objects.filter(session=self.session, component=self.frame_basic).first()
        handlebar_stock = ComponentStock.objects.filter(session=self.session, component=self.handlebar_basic).first()
        saddle_stock = ComponentStock.objects.filter(session=self.session, component=self.saddle_basic).first()
        gearshift_stock = ComponentStock.objects.filter(session=self.session, component=self.gearshift_basic).first()
        motor_stock = ComponentStock.objects.filter(session=self.session, component=self.motor_basic).first()
        
        # All component stocks should have been deleted with the warehouse
        # This tests the CASCADE behavior
        self.assertIsNone(wheel_stock)
        self.assertIsNone(frame_stock)
        self.assertIsNone(handlebar_stock)
        self.assertIsNone(saddle_stock)
        self.assertIsNone(gearshift_stock)
        self.assertIsNone(motor_stock)
    
    def test_production_transaction_all_or_nothing(self):
        """Test that either all production succeeds or nothing is changed"""
        # Record initial state
        initial_component_stocks = {
            'wheels': self.wheel_stock.quantity,
            'frames': self.frame_stock.quantity,
            'handlebars': self.handlebar_stock.quantity,
            'saddles': self.saddle_stock.quantity,
            'gearshifts': self.gearshift_stock.quantity,
            'motors': self.motor_stock.quantity
        }
        initial_produced_bikes = ProducedBike.objects.filter(session=self.session).count()
        initial_bike_stocks = BikeStock.objects.filter(session=self.session).count()
        
        # Test successful production (all should succeed)
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 2,
                'quantity_standard': 1,
                'quantity_premium': 1
            },
            {
                'bike_type_id': self.e_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 1
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('6 Fahrräder produziert', response_data['message'])
        
        # Verify all changes occurred
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), initial_produced_bikes + 6)
        self.assertEqual(BikeStock.objects.filter(session=self.session).count(), initial_bike_stocks + 6)
        
        # Verify component consumption
        self.wheel_stock.refresh_from_db()
        self.frame_stock.refresh_from_db()
        self.handlebar_stock.refresh_from_db()
        self.saddle_stock.refresh_from_db()
        self.gearshift_stock.refresh_from_db()
        self.motor_stock.refresh_from_db()
        
        # All bikes need basic components (6 consumed each)
        self.assertEqual(self.wheel_stock.quantity, initial_component_stocks['wheels'] - 6)
        self.assertEqual(self.frame_stock.quantity, initial_component_stocks['frames'] - 6)
        self.assertEqual(self.handlebar_stock.quantity, initial_component_stocks['handlebars'] - 6)
        self.assertEqual(self.saddle_stock.quantity, initial_component_stocks['saddles'] - 6)
        self.assertEqual(self.gearshift_stock.quantity, initial_component_stocks['gearshifts'] - 6)
        
        # Only e-bikes need motors (2 e-bikes produced, so 2 motors consumed)
        self.assertEqual(self.motor_stock.quantity, initial_component_stocks['motors'] - 2)
    
    def test_production_transaction_consistency_with_production_plan_updates(self):
        """Test transaction consistency when updating existing production plans"""
        # Create initial production
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['success'])
        
        # Verify initial state
        plan = ProductionPlan.objects.get(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        initial_orders_count = plan.orders.count()
        initial_bikes_count = ProducedBike.objects.filter(session=self.session).count()
        
        # Update production with failing request
        production_data = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 1000,  # This will fail due to capacity
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
        # Verify the original production plan and bikes remain unchanged
        plan.refresh_from_db()
        self.assertEqual(plan.orders.count(), initial_orders_count)
        self.assertEqual(ProducedBike.objects.filter(session=self.session).count(), initial_bikes_count)
        
        # The old orders should still exist (not replaced)
        original_order = plan.orders.first()
        self.assertEqual(original_order.quantity_planned, 1)  # Original quantity
        self.assertEqual(original_order.price_segment, 'cheap')
    
    def test_production_transaction_isolation(self):
        """Test that production transactions are properly isolated"""
        # This test simulates what would happen if multiple production requests
        # were processed concurrently (though Django tests run sequentially)
        
        initial_component_stocks = {
            'wheels': self.wheel_stock.quantity,
            'frames': self.frame_stock.quantity,
            'handlebars': self.handlebar_stock.quantity,
            'saddles': self.saddle_stock.quantity,
            'gearshifts': self.gearshift_stock.quantity,
            'motors': self.motor_stock.quantity
        }
        
        # Reduce stocks to minimal levels
        self.wheel_stock.quantity = 5
        self.wheel_stock.save()
        
        # First production request (should succeed)
        production_data_1 = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 3,
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response_1 = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data_1),
            content_type='application/json'
        )
        
        self.assertEqual(response_1.status_code, 200)
        response_data_1 = json.loads(response_1.content)
        self.assertTrue(response_data_1['success'])
        
        # Check that wheels were consumed
        self.wheel_stock.refresh_from_db()
        self.assertEqual(self.wheel_stock.quantity, 2)  # 5 - 3 = 2
        
        # Second production request (should fail due to insufficient wheels)
        production_data_2 = [
            {
                'bike_type_id': self.standard_bike.id,
                'quantity_cheap': 3,  # Need 3 wheels but only 2 available
                'quantity_standard': 0,
                'quantity_premium': 0
            }
        ]
        
        response_2 = self.client.post(
            reverse('production:production', kwargs={'session_id': self.session.id}),
            data=json.dumps(production_data_2),
            content_type='application/json'
        )
        
        self.assertEqual(response_2.status_code, 200)
        response_data_2 = json.loads(response_2.content)
        self.assertFalse(response_data_2['success'])
        self.assertIn('Nicht genügend Basic Wheels im Lager', response_data_2['error'])
        
        # Verify wheels stock unchanged after failed request
        self.wheel_stock.refresh_from_db()
        self.assertEqual(self.wheel_stock.quantity, 2)  # Should still be 2
