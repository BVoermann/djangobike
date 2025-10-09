from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json

from bikeshop.models import (
    GameSession, BikeType, Component, ComponentType, 
    Supplier, SupplierPrice, Worker
)
from warehouse.models import Warehouse, ComponentStock, BikeStock
from production.models import ProductionPlan, ProductionOrder, ProducedBike


class ProductionQualityMatchingTestCase(TestCase):
    """
    Comprehensive tests for the Produktion tab quality-based component matching system.
    Tests the specific requirements:
    1. Cheap bikes can be built with any available parts in needed categories
    2. Standard bikes can be built with standard or premium parts (fallback)
    3. Premium bikes can only be produced with premium parts
    4. Correct components are used as specified in "Benötigte Komponenten"
    5. Used components are properly removed from Lager inventory
    """
    
    def setUp(self):
        """Set up comprehensive test data for production quality matching"""
        # Create test user
        self.user = User.objects.create_user(
            username='productiontest',
            password='testpass123',
            email='production@example.com'
        )
        
        # Create game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Production Quality Test',
            current_month=1,
            current_year=2024,
            balance=Decimal('100000.00')
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            session=self.session,
            name='Test Warehouse',
            location='Test Location',
            capacity_m2=1000.0,
            rent_per_month=Decimal('2000.00')
        )
        
        # Create workers with sufficient capacity
        self.skilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='skilled',
            hourly_wage=Decimal('29.00'),
            monthly_hours=160,
            count=10  # High capacity for testing
        )
        
        self.unskilled_worker = Worker.objects.create(
            session=self.session,
            worker_type='unskilled',
            hourly_wage=Decimal('19.00'),
            monthly_hours=160,
            count=10  # High capacity for testing
        )
        
        # Create component types matching real system
        self.component_types = self._create_component_types()
        
        # Create suppliers with different quality levels
        self.suppliers = self._create_suppliers()
        
        # Create components that match Damenrad requirements exactly
        self.components = self._create_components()
        
        # Create supplier prices for all quality levels
        self._create_supplier_prices()
        
        # Create test bike type (Damenrad) with specific component requirements
        self.bike_type = self._create_damenrad_bike_type()
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='productiontest', password='testpass123')
        
        # Production URL
        self.production_url = reverse('production:production', args=[self.session.id])
    
    def _create_component_types(self):
        """Create component types matching the real system"""
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
            name='Basic Components Ltd',
            payment_terms=30,
            delivery_time=14,
            complaint_probability=15.0,
            complaint_quantity=8.0,
            quality='basic'
        )
        
        suppliers['standard'] = Supplier.objects.create(
            session=self.session,
            name='Standard Parts GmbH',
            payment_terms=45,
            delivery_time=10,
            complaint_probability=8.0,
            complaint_quantity=5.0,
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
        
        return suppliers
    
    def _create_components(self):
        """Create components that match Damenrad requirements exactly"""
        components = {}
        
        # Create components matching Damenrad requirements for each quality level
        # Damenrad requirements: {'Laufradsatz': ['Standard'], 'Rahmen': ['Damenrahmen Basic'], 
        #                        'Lenker': ['Comfort'], 'Sattel': ['Comfort'], 'Schaltung': ['Albatross']}
        
        # Basic quality components
        components['laufradsatz_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['laufradsatz'],
            name='Standard'
        )
        components['rahmen_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['rahmen'],
            name='Damenrahmen Basic'
        )
        components['lenker_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['lenker'],
            name='Comfort'
        )
        components['sattel_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['sattel'],
            name='Comfort'
        )
        components['schaltung_basic'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['schaltung'],
            name='Albatross'
        )
        
        # Standard quality components (same names, different supplier)
        components['laufradsatz_standard'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['laufradsatz'],
            name='Standard'
        )
        components['rahmen_standard'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['rahmen'],
            name='Damenrahmen Basic'
        )
        components['lenker_standard'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['lenker'],
            name='Comfort'
        )
        components['sattel_standard'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['sattel'],
            name='Comfort'
        )
        components['schaltung_standard'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['schaltung'],
            name='Albatross'
        )
        
        # Premium quality components (same names, different supplier)
        components['laufradsatz_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['laufradsatz'],
            name='Standard'
        )
        components['rahmen_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['rahmen'],
            name='Damenrahmen Basic'
        )
        components['lenker_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['lenker'],
            name='Comfort'
        )
        components['sattel_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['sattel'],
            name='Comfort'
        )
        components['schaltung_premium'] = Component.objects.create(
            session=self.session,
            component_type=self.component_types['schaltung'],
            name='Albatross'
        )
        
        return components
    
    def _create_supplier_prices(self):
        """Create supplier prices for all quality levels"""
        # Basic components from basic supplier
        basic_components = [
            'laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic'
        ]
        for comp_key in basic_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['basic'],
                component=self.components[comp_key],
                price=Decimal('50.00')
            )
        
        # Standard components from standard supplier
        standard_components = [
            'laufradsatz_standard', 'rahmen_standard', 'lenker_standard', 'sattel_standard', 'schaltung_standard'
        ]
        for comp_key in standard_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['standard'],
                component=self.components[comp_key],
                price=Decimal('100.00')
            )
        
        # Premium components from premium supplier
        premium_components = [
            'laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium'
        ]
        for comp_key in premium_components:
            SupplierPrice.objects.create(
                session=self.session,
                supplier=self.suppliers['premium'],
                component=self.components[comp_key],
                price=Decimal('200.00')
            )
    
    def _create_damenrad_bike_type(self):
        """Create Damenrad bike type with proper component requirements"""
        return BikeType.objects.create(
            session=self.session,
            name='Damenrad',
            skilled_worker_hours=4.5,
            unskilled_worker_hours=2.5,
            storage_space_per_unit=1.2,
            # Component requirements matching real system
            required_wheel_set_names=['Standard'],
            required_frame_names=['Damenrahmen Basic'],
            required_handlebar_names=['Comfort'],
            required_saddle_names=['Comfort'],
            required_gearshift_names=['Albatross'],
            required_motor_names=[]  # No motor for regular bikes
        )
    
    def _add_components_to_warehouse(self, component_quantities):
        """Add components to warehouse with specified quantities"""
        for component_key, quantity in component_quantities.items():
            ComponentStock.objects.create(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key],
                quantity=quantity
            )
    
    def _get_component_stock_quantity(self, component_key):
        """Get current stock quantity for a component"""
        try:
            stock = ComponentStock.objects.get(
                session=self.session,
                warehouse=self.warehouse,
                component=self.components[component_key]
            )
            return stock.quantity
        except ComponentStock.DoesNotExist:
            return 0
    
    def _produce_bike(self, segment, quantity=1, confirm_upgrades=False):
        """Helper method to produce bikes with optional upgrade confirmation"""
        production_data = [{
            'bike_type_id': self.bike_type.id,
            'quantity_cheap': quantity if segment == 'cheap' else 0,
            'quantity_standard': quantity if segment == 'standard' else 0,
            'quantity_premium': quantity if segment == 'premium' else 0
        }]
        
        url = self.production_url
        if confirm_upgrades:
            url += '?confirm_upgrades=true'
        
        response = self.client.post(
            url,
            data=json.dumps(production_data),
            content_type='application/json'
        )
        
        return response
    
    def test_cheap_bike_production_with_basic_components(self):
        """Test that cheap bikes can be built with basic components"""
        # Add basic components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_basic': 2,
            'rahmen_basic': 2,
            'lenker_basic': 2,
            'sattel_basic': 2,
            'schaltung_basic': 2
        })
        
        # Produce 1 cheap Damenrad
        response = self._produce_bike('cheap', 1)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='cheap'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that bike is in warehouse
        bike_stock = BikeStock.objects.filter(
            session=self.session,
            warehouse=self.warehouse,
            bike__price_segment='cheap'
        )
        self.assertEqual(bike_stock.count(), 1)
        
        # Check that basic components were consumed (1 each used, 1 each remaining)
        basic_components = ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic']
        for component_key in basic_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 1, f"Expected 1 {component_key} remaining, got {remaining_stock}")
    
    def test_cheap_bike_production_with_standard_components(self):
        """Test that cheap bikes can be built with standard components"""
        # Add only standard components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_standard': 1,
            'rahmen_standard': 1,
            'lenker_standard': 1,
            'sattel_standard': 1,
            'schaltung_standard': 1
        })
        
        # Produce 1 cheap Damenrad (should require confirmation due to quality upgrade)
        response = self._produce_bike('cheap', 1)
        
        # Should return upgrade confirmation request
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertTrue(response_data.get('upgrades_needed', False))
        
        # Confirm the upgrade and produce
        response = self._produce_bike('cheap', 1, confirm_upgrades=True)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production with confirmation failed: {response_data}")
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='cheap'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that standard components were consumed
        standard_components = ['laufradsatz_standard', 'rahmen_standard', 'lenker_standard', 'sattel_standard', 'schaltung_standard']
        for component_key in standard_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining, got {remaining_stock}")
    
    def test_cheap_bike_production_with_premium_components(self):
        """Test that cheap bikes can be built with premium components (with confirmation)"""
        # Add only premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Produce 1 cheap Damenrad (should require confirmation)
        response = self._produce_bike('cheap', 1)
        
        # Should return upgrade confirmation request
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertTrue(response_data.get('upgrades_needed', False))
        
        # Check upgrade details
        upgrades = response_data.get('upgrades', [])
        self.assertEqual(len(upgrades), 5)  # All 5 components require upgrade
        
        # All upgrades should be from Premium to Günstig (cheap)
        for upgrade in upgrades:
            self.assertEqual(upgrade['component_quality'], 'Premium')
            self.assertEqual(upgrade['target_segment'], 'Günstig')
        
        # Confirm the upgrade and produce
        response = self._produce_bike('cheap', 1, confirm_upgrades=True)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production with confirmation failed: {response_data}")
        
        # Check that premium components were consumed
        premium_components = ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']
        for component_key in premium_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining, got {remaining_stock}")
    
    def test_standard_bike_production_with_standard_components(self):
        """Test that standard bikes can be built with standard components (exact match)"""
        # Add standard components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_standard': 1,
            'rahmen_standard': 1,
            'lenker_standard': 1,
            'sattel_standard': 1,
            'schaltung_standard': 1
        })
        
        # Produce 1 standard Damenrad
        response = self._produce_bike('standard', 1)
        
        # Should be successful without confirmation
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='standard'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that standard components were consumed
        standard_components = ['laufradsatz_standard', 'rahmen_standard', 'lenker_standard', 'sattel_standard', 'schaltung_standard']
        for component_key in standard_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining, got {remaining_stock}")
    
    def test_standard_bike_production_fallback_to_premium_components(self):
        """Test that standard bikes can be built with premium components when no standard parts available"""
        # Add only premium components to warehouse (no standard components)
        self._add_components_to_warehouse({
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Produce 1 standard Damenrad (should require confirmation for quality upgrade)
        response = self._produce_bike('standard', 1)
        
        # Should return upgrade confirmation request
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertTrue(response_data.get('upgrades_needed', False))
        
        # Confirm the upgrade and produce
        response = self._produce_bike('standard', 1, confirm_upgrades=True)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production with confirmation failed: {response_data}")
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='standard'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that premium components were consumed (fallback worked)
        premium_components = ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']
        for component_key in premium_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining, got {remaining_stock}")
    
    def test_standard_bike_prefers_exact_match_over_premium(self):
        """Test that standard bikes prefer standard components over premium when both available"""
        # Add both standard and premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_standard': 1,
            'rahmen_standard': 1,
            'lenker_standard': 1,
            'sattel_standard': 1,
            'schaltung_standard': 1,
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Produce 1 standard Damenrad
        response = self._produce_bike('standard', 1)
        
        # Should be successful without confirmation (exact match preferred)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that standard components were consumed (preferred over premium)
        standard_components = ['laufradsatz_standard', 'rahmen_standard', 'lenker_standard', 'sattel_standard', 'schaltung_standard']
        for component_key in standard_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining (consumed), got {remaining_stock}")
        
        # Check that premium components were NOT consumed (exact match was preferred)
        premium_components = ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']
        for component_key in premium_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 1, f"Expected 1 {component_key} remaining (untouched), got {remaining_stock}")
    
    def test_premium_bike_production_with_premium_components_only(self):
        """Test that premium bikes can only be produced with premium components"""
        # Add premium components to warehouse
        self._add_components_to_warehouse({
            'laufradsatz_premium': 1,
            'rahmen_premium': 1,
            'lenker_premium': 1,
            'sattel_premium': 1,
            'schaltung_premium': 1
        })
        
        # Produce 1 premium Damenrad
        response = self._produce_bike('premium', 1)
        
        # Should be successful without confirmation (exact match)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that bike was produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='premium'
        )
        self.assertEqual(produced_bikes.count(), 1)
        
        # Check that premium components were consumed
        premium_components = ['laufradsatz_premium', 'rahmen_premium', 'lenker_premium', 'sattel_premium', 'schaltung_premium']
        for component_key in premium_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining, got {remaining_stock}")
    
    def test_premium_bike_production_fails_with_basic_or_standard_components(self):
        """Test that premium bikes cannot be produced with basic or standard components"""
        # Test with basic components only
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,
            'rahmen_basic': 1,
            'lenker_basic': 1,
            'sattel_basic': 1,
            'schaltung_basic': 1
        })
        
        # Try to produce 1 premium Damenrad
        response = self._produce_bike('premium', 1)
        
        # Should fail (no downgrades allowed)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Check that no bikes were produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='premium'
        )
        self.assertEqual(produced_bikes.count(), 0)
        
        # Test with standard components only
        # Clear warehouse first
        ComponentStock.objects.filter(session=self.session).delete()
        
        self._add_components_to_warehouse({
            'laufradsatz_standard': 1,
            'rahmen_standard': 1,
            'lenker_standard': 1,
            'sattel_standard': 1,
            'schaltung_standard': 1
        })
        
        # Try to produce 1 premium Damenrad
        response = self._produce_bike('premium', 1)
        
        # Should fail (no downgrades allowed)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_component_requirements_match_benoetigte_komponenten(self):
        """Test that the components used match exactly what's specified in 'Benötigte Komponenten'"""
        # Get the actual component requirements from the bike type
        damenrad_requirements = self.bike_type.get_required_components()
        
        # Expected requirements based on our setup
        expected_requirements = {
            'Laufradsatz': ['Standard'],
            'Rahmen': ['Damenrahmen Basic'],
            'Lenker': ['Comfort'],
            'Sattel': ['Comfort'],
            'Schaltung': ['Albatross']
        }
        
        # Verify that our bike type has the correct requirements
        self.assertEqual(damenrad_requirements, expected_requirements,
                        "Bike type requirements don't match expected 'Benötigte Komponenten'")
        
        # Add components with exact names from requirements
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,  # 'Standard' laufradsatz
            'rahmen_basic': 1,       # 'Damenrahmen Basic' rahmen
            'lenker_basic': 1,       # 'Comfort' lenker
            'sattel_basic': 1,       # 'Comfort' sattel
            'schaltung_basic': 1     # 'Albatross' schaltung
        })
        
        # Produce 1 bike
        response = self._produce_bike('cheap', 1)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Verify that the exact components specified in requirements were consumed
        used_components = {
            'Standard': self._get_component_stock_quantity('laufradsatz_basic'),
            'Damenrahmen Basic': self._get_component_stock_quantity('rahmen_basic'),
            'Comfort (Lenker)': self._get_component_stock_quantity('lenker_basic'),
            'Comfort (Sattel)': self._get_component_stock_quantity('sattel_basic'),
            'Albatross': self._get_component_stock_quantity('schaltung_basic')
        }
        
        # All should be consumed (0 remaining)
        for component_name, remaining_stock in used_components.items():
            self.assertEqual(remaining_stock, 0, 
                           f"Component {component_name} from requirements not properly consumed")
    
    def test_mixed_component_qualities_production(self):
        """Test production with mixed component qualities to ensure correct selection priority"""
        # Add components with mixed qualities - some basic, some standard, some premium
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,      # Basic quality
            'rahmen_standard': 1,        # Standard quality
            'lenker_premium': 1,         # Premium quality
            'sattel_basic': 1,          # Basic quality
            'schaltung_standard': 1     # Standard quality
        })
        
        # Produce 1 cheap bike (should use available components but require confirmation for upgrades)
        response = self._produce_bike('cheap', 1)
        
        # Should return upgrade confirmation (standard and premium components being used for cheap bike)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        if not response_data.get('success', False) and response_data.get('upgrades_needed', False):
            # Confirm upgrades and produce
            response = self._produce_bike('cheap', 1, confirm_upgrades=True)
            response_data = json.loads(response.content)
        
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that all available components were consumed (mixed qualities)
        consumed_components = {
            'laufradsatz_basic': self._get_component_stock_quantity('laufradsatz_basic'),
            'rahmen_standard': self._get_component_stock_quantity('rahmen_standard'),
            'lenker_premium': self._get_component_stock_quantity('lenker_premium'),
            'sattel_basic': self._get_component_stock_quantity('sattel_basic'),
            'schaltung_standard': self._get_component_stock_quantity('schaltung_standard')
        }
        
        for component_key, remaining_stock in consumed_components.items():
            self.assertEqual(remaining_stock, 0, 
                           f"Component {component_key} not properly consumed from mixed inventory")
    
    def test_multiple_bikes_production_with_component_depletion(self):
        """Test producing multiple bikes and verify correct component depletion"""
        # Add enough components for 3 bikes
        self._add_components_to_warehouse({
            'laufradsatz_basic': 3,
            'rahmen_basic': 3,
            'lenker_basic': 3,
            'sattel_basic': 3,
            'schaltung_basic': 3
        })
        
        # Produce 2 cheap bikes
        response = self._produce_bike('cheap', 2)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Production failed: {response_data}")
        
        # Check that 2 bikes were produced
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            bike_type=self.bike_type,
            price_segment='cheap'
        )
        self.assertEqual(produced_bikes.count(), 2)
        
        # Check that 2 bikes are in warehouse
        bike_stock = BikeStock.objects.filter(
            session=self.session,
            warehouse=self.warehouse,
            bike__price_segment='cheap'
        )
        self.assertEqual(bike_stock.count(), 2)
        
        # Check that components were properly depleted (3 - 2 = 1 remaining each)
        basic_components = ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic', 'schaltung_basic']
        for component_key in basic_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 1, f"Expected 1 {component_key} remaining after producing 2 bikes, got {remaining_stock}")
        
        # Produce 1 more bike (should use the remaining components)
        response = self._produce_bike('cheap', 1)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'], f"Third bike production failed: {response_data}")
        
        # Check that all components are now depleted (0 remaining)
        for component_key in basic_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 0, f"Expected 0 {component_key} remaining after producing 3 bikes, got {remaining_stock}")
        
        # Try to produce another bike (should fail due to lack of components)
        response = self._produce_bike('cheap', 1)
        
        # Should fail
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_partial_component_availability_error(self):
        """Test that production fails when only some required components are available"""
        # Add only some components (missing schaltung)
        self._add_components_to_warehouse({
            'laufradsatz_basic': 1,
            'rahmen_basic': 1,
            'lenker_basic': 1,
            'sattel_basic': 1,
            # Missing 'schaltung_basic'
        })
        
        # Try to produce 1 cheap bike
        response = self._produce_bike('cheap', 1)
        
        # Should fail
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        
        # Error should mention missing components
        error_message = response_data['error'].lower()
        self.assertTrue('fehlend' in error_message or 'missing' in error_message or 'schaltung' in error_message)
        
        # Check that no bikes were produced
        produced_bikes = ProducedBike.objects.filter(session=self.session)
        self.assertEqual(produced_bikes.count(), 0)
        
        # Check that no components were consumed (transaction rollback)
        available_components = ['laufradsatz_basic', 'rahmen_basic', 'lenker_basic', 'sattel_basic']
        for component_key in available_components:
            remaining_stock = self._get_component_stock_quantity(component_key)
            self.assertEqual(remaining_stock, 1, f"Component {component_key} was consumed despite failed production")
    
    def test_warehouse_inventory_consistency(self):
        """Test that warehouse inventory remains consistent after production operations"""
        # Add components to warehouse
        initial_quantities = {
            'laufradsatz_basic': 5,
            'rahmen_basic': 5,
            'lenker_basic': 5,
            'sattel_basic': 5,
            'schaltung_basic': 5
        }
        self._add_components_to_warehouse(initial_quantities)
        
        # Produce 2 bikes
        response = self._produce_bike('cheap', 2)
        self.assertTrue(json.loads(response.content)['success'])
        
        # Check individual component stocks
        for component_key, initial_qty in initial_quantities.items():
            remaining_stock = self._get_component_stock_quantity(component_key)
            expected_remaining = initial_qty - 2  # 2 bikes produced
            self.assertEqual(remaining_stock, expected_remaining, 
                           f"Component {component_key} inventory inconsistent: expected {expected_remaining}, got {remaining_stock}")
        
        # Check total component stock count
        total_component_stocks = ComponentStock.objects.filter(session=self.session).count()
        self.assertEqual(total_component_stocks, 5, "Unexpected number of component stock entries")
        
        # Check bike inventory
        bike_stocks = BikeStock.objects.filter(session=self.session).count()
        self.assertEqual(bike_stocks, 2, "Unexpected number of bikes in warehouse inventory")
        
        # Check produced bike records
        produced_bikes = ProducedBike.objects.filter(session=self.session).count()
        self.assertEqual(produced_bikes, 2, "Unexpected number of produced bike records")