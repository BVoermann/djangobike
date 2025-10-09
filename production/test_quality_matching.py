from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json

from bikeshop.models import (
    GameSession, BikeType, Component, ComponentType, 
    Supplier, SupplierPrice, Worker
)
from warehouse.models import Warehouse, ComponentStock
from production.models import ProductionPlan, ProductionOrder, ProducedBike
from warehouse.models import BikeStock


class QualityBasedProductionTestCase(TestCase):
    """Test the new flexible quality-based component matching system"""
    
    def setUp(self):
        """Set up test data for quality matching tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='qualitytest',
            password='testpass123',
            email='quality@example.com'
        )
        
        # Create game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Quality Test Session',
            current_month=1,
            current_year=2024,
            balance=Decimal('80000.00')
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            session=self.session,
            name='Test Warehouse',
            location='Test Location',
            capacity_m2=1000.0,
            rent_per_month=Decimal('2000.00')
        )
        
        # Create workers
        self.skilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='skilled',
            hourly_wage=Decimal('29.00'),
            monthly_hours=160,
            count=5
        )
        
        self.unskilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='unskilled',
            hourly_wage=Decimal('19.00'),
            monthly_hours=160,
            count=3
        )
        
        # Create component types
        self.component_types = self._create_component_types()
        
        # Create suppliers with different quality levels
        self.suppliers = self._create_suppliers()
        
        # Create components
        self.components = self._create_components()
        
        # Create supplier prices
        self._create_supplier_prices()
        
        # Create bike types
        self.bike_types = self._create_bike_types()
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='qualitytest', password='testpass123')
        
        # Production URL
        self.production_url = reverse('production:production', args=[self.session.id])
    
    def _create_component_types(self):
        """Create component types for testing"""
        types = {}
        
        types['laufradsatz'] = ComponentType.objects.create(
            session=self.session, name='Laufradsatz', storage_space_per_unit=2.5
        )
        types['rahmen'] = ComponentType.objects.create(
            session=self.session, name='Rahmen', storage_space_per_unit=3.0
        )
        types['lenker'] = ComponentType.objects.create(
            session=self.session, name='Lenker', storage_space_per_unit=0.5
        )
        types['sattel'] = ComponentType.objects.create(
            session=self.session, name='Sattel', storage_space_per_unit=0.3
        )
        types['schaltung'] = ComponentType.objects.create(
            session=self.session, name='Schaltung', storage_space_per_unit=0.8
        )
        
        return types
    
    def _create_suppliers(self):
        """Create suppliers with different quality levels"""
        suppliers = {}
        
        suppliers['basic'] = Supplier.objects.create(
            session=self.session,
            name='Basic Supplier',
            payment_terms=30,
            delivery_time=14,
            complaint_probability=15.0,
            complaint_quantity=8.0,
            quality='basic'
        )
        
        suppliers['standard'] = Supplier.objects.create(
            session=self.session,
            name='Standard Supplier',
            payment_terms=45,
            delivery_time=10,
            complaint_probability=8.0,
            complaint_quantity=5.0,
            quality='standard'
        )
        
        suppliers['premium'] = Supplier.objects.create(
            session=self.session,
            name='Premium Supplier',
            payment_terms=60,
            delivery_time=7,
            complaint_probability=2.0,
            complaint_quantity=1.0,
            quality='premium'
        )
        
        return suppliers
    
    def _create_components(self):
        """Create components for Damenrad testing"""
        components = {}
        
        # Laufradsatz components that match Damenrad requirements
        components['laufradsatz_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['laufradsatz'],
            name='Standard'  # Match Damenrad requirements
        )
        components['laufradsatz_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['laufradsatz'],
            name='Standard'  # Same name but premium quality from supplier
        )
        
        # Rahmen components that match Damenrad requirements
        components['rahmen_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['rahmen'],
            name='Damenrahmen Basic'  # Match Damenrad requirements
        )
        components['rahmen_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['rahmen'],
            name='Damenrahmen Basic'  # Same name but premium quality from supplier
        )
        
        # Lenker components that match Damenrad requirements
        components['lenker_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['lenker'],
            name='Comfort'  # Match Damenrad requirements
        )
        components['lenker_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['lenker'],
            name='Comfort'  # Same name but premium quality from supplier
        )
        
        # Sattel components that match Damenrad requirements
        components['sattel_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['sattel'],
            name='Comfort'  # Match Damenrad requirements
        )
        components['sattel_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['sattel'],
            name='Comfort'  # Same name but premium quality from supplier
        )
        
        # Schaltung components that match Damenrad requirements
        components['schaltung_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['schaltung'],
            name='Albatross'  # Match Damenrad requirements
        )
        components['schaltung_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['schaltung'],
            name='Albatross'  # Same name but premium quality from supplier
        )
        
        return components
    
    def _create_supplier_prices(self):
        """Create supplier prices for components"""
        # Basic components from basic supplier
        basic_components = ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic']
        for comp_key in basic_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['basic'],
                component=self.components[comp_key],
                price=Decimal('50.00')
            )
        
        # Premium components from premium supplier
        premium_components = ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']
        for comp_key in premium_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['premium'],
                component=self.components[comp_key],
                price=Decimal('150.00')
            )
        
        # Standard components from standard supplier for standard bikes
        standard_components = ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic']
        for comp_key in standard_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['standard'],
                component=self.components[comp_key],
                price=Decimal('80.00')
            )
    
    def _create_bike_types(self):
        """Create bike types for testing"""
        bike_types = {}
        
        bike_types['damenrad'] = BikeType.objects.create(
            session=self.session,
            name='Damenrad',
            skilled_worker_hours=4.5,
            unskilled_worker_hours=2.5,
            storage_space_per_unit=1.2,
            required_wheel_set_names=['Standard'],
            required_frame_names=['Damenrahmen Basic'],
            required_handlebar_names=['Comfort'],
            required_saddle_names=['Comfort'],
            required_gearshift_names=['Albatross'],
            required_motor_names=[]
        )
        
        return bike_types
    
    def _add_components_to_warehouse(self, component_quantities):
        """Add components to warehouse with specified quantities"""
        for component_key, quantity in component_quantities.items():
            ComponentStock.objects.create(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key],
                quantity=quantity
            )
    
    def test_premium_damenrad_production_with_premium_components(self):
        """Test producing premium Damenrad with all premium components available"""
        # Add premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_premium': 2,
            'rahmen_premium': 2,
            'lenker_premium': 2,
            'sattel_premium': 2,
            'schaltung_premium': 2
        })
        
        # Try to produce 1 premium Damenrad
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 0,
            'quantity_standard': 0,
            'quantity_premium': 1
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Check that production was successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Debug: Print response if not successful
        if not response_data.get('success', False):
            print(f"Premium Damenrad production failed: {response_data}")
        
        self.assertTrue(response_data['success'])
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_types['damenrad'],
            price_segment='premium'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that bike is in warehouse
        bike_stock = BikeStock.objects.filter(
            session=self.session,
            warehouse=self.warehouse,
            bike__bike_type=self.bike_types['damenrad'],
            bike__price_segment='premium'
        )
        self.assertEqual(bike_stock.count(), 1)
        
        # Check that components were consumed
        for component_key in ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key]
            )
            self.assertEqual(stock.quantity, 1)  # 2 - 1 = 1 remaining
    
    def test_standard_damenrad_production_with_basic_components(self):
        """Test producing standard Damenrad with basic components available"""
        # Add basic components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,
            'rahmen_basic': 1,
            'lenker_basic': 1,
            'sattel_basic': 1,
            'schaltung_basic': 1
        })
        
        # Try to produce 1 standard Damenrad
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 0,
            'quantity_standard': 1,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Check that production was successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Debug: Print response if not successful
        if not response_data.get('success', False):
            print(f"Standard Damenrad production failed: {response_data}")
        
        self.assertTrue(response_data['success'])
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_types['damenrad'],
            price_segment='standard'
        )
        self.assertEqual(produced_bikes.count(), 1)
    
    def test_quality_upgrade_detection_premium_to_cheap(self):
        """Test that system detects when premium components would be used for cheap bike"""
        # Add only premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Try to produce 1 cheap Damenrad (should require confirmation)
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 1,
            'quantity_standard': 0,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should return upgrade confirmation request
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('upgrades_needed', response_data)
        self.assertTrue(response_data['upgrades_needed'])
        self.assertIn('upgrades', response_data)
        
        # Check upgrade details
        upgrade_details = response_data['upgrades']
        self.assertGreater(len(upgrade_details), 0)
        
        # Should list all components that would be upgraded
        component_names = [detail['component_name'] for detail in upgrade_details]
        self.assertIn('Standard', component_names)  # laufradsatz_premium (same name, different quality)
    
    def test_confirmed_quality_upgrade_production(self):
        """Test production with confirmed quality upgrade"""
        # Add only premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Try to produce 1 cheap Damenrad with confirmed upgrade
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 1,
            'quantity_standard': 0,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url + '?confirm_upgrades=true',
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should be successful with confirmation
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_types['damenrad'],
            price_segment='cheap'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that premium components were consumed
        for component_key in ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key]
            )
            self.assertEqual(stock.quantity, 0)  # All consumed
    
    def test_mixed_quality_components_production(self):
        """Test production with mixed quality components available"""
        # Add mixed components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,      # Basic for laufradsatz
            'rahmen_premium': 1,         # Premium for rahmen
            'lenker_basic': 1,           # Basic for lenker
            'sattel_premium': 1,         # Premium for sattel  
            'schaltung_basic': 1         # Basic for schaltung
        })
        
        # Try to produce 1 standard Damenrad (should use mixed components with upgrade confirmation)
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 0,
            'quantity_standard': 1,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should require confirmation for premium components being used for standard bike
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        if not response_data['success'] and response_data.get('upgrades_needed'):
            # Confirm the upgrade
            response = self.client.post(
                self.production_url + '?confirm_upgrades=true',
                data=json.dumps(production_data),
                content_type='application/json'
            )
            
            response_data = json.loads(response.content)
            self.assertTrue(response_data['success'])
        else:
            # Should be successful if no upgrades needed
            self.assertTrue(response_data['success'])
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_types['damenrad'],
            price_segment='standard'
        )
        self.assertEqual(produced_bikes.count(), 1)
    
    def test_insufficient_components_error(self):
        """Test error when components are completely missing"""
        # Don't add any components to warehouse
        
        # Try to produce 1 Damenrad of any quality
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 1,
            'quantity_standard': 0,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Error should mention missing components
        error_message = response_data['error'].lower()
        self.assertTrue(
            'nicht verfügbar' in error_message or 
            'components' in error_message or
            'komponente' in error_message
        )
    
    def test_partial_components_available_error(self):
        """Test error when only some components are available"""
        # Add only some components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,
            'rahmen_basic': 1,
            # Missing lenker, sattel, schaltung
        })
        
        # Try to produce 1 cheap Damenrad
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 1,
            'quantity_standard': 0,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should return error for missing components
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Check that no bikes were produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_types['damenrad']
        )
        self.assertEqual(produced_bikes.count(), 0)
    
    def test_exact_quality_match_preferred_over_upgrade(self):
        """Test that exact quality matches are preferred over upgrades"""
        # Add both basic and premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,
            'laufradsatz_premium': 1,
            'rahmen_basic': 1, 
            'rahmen_premium': 1,
            'lenker_basic': 1,
            'lenker_premium': 1,
            'sattel_basic': 1,
            'sattel_premium': 1,
            'schaltung_basic': 1,
            'schaltung_premium': 1
        })
        
        # Produce 1 cheap Damenrad (should use basic components without confirmation)
        production_data = [{
            'bike_type_id': self.bike_types['damenrad'].id,
            'quantity_cheap': 1,
            'quantity_standard': 0,
            'quantity_premium': 0
        }]
        
        response = self.client.post(
            self.production_url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        # Should be successful without confirmation needed
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that basic components were consumed (preferred over premium)
        for component_key in ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic']:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key]
            )
            self.assertEqual(stock.quantity, 0)  # Basic components consumed
        
        # Check that premium components were not consumed
        for component_key in ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key]
            )
            self.assertEqual(stock.quantity, 1)  # Premium components untouched