"""
Player State Manager for Multiplayer Games

This module manages individual player game states in multiplayer games.
Each player gets their own GameSession with all necessary game objects.
"""

from decimal import Decimal
from django.db import transaction
import logging

from bikeshop.models import (
    GameSession, Supplier, Component, ComponentType, SupplierPrice,
    BikeType, BikePrice, Worker, TransportCost
)
from warehouse.models import Warehouse, ComponentStock, WarehouseType
from sales.models import Market, MarketDemand, MarketPriceSensitivity
from .models import PlayerSession, MultiplayerGame

logger = logging.getLogger(__name__)


class PlayerStateManager:
    """Manages player-specific game state for multiplayer games."""

    def __init__(self, multiplayer_game):
        self.multiplayer_game = multiplayer_game

    @transaction.atomic
    def initialize_player_game_state(self, player_session):
        """
        Initialize complete game state for a player.
        Creates a GameSession and all necessary game objects.
        """
        logger.info(f"Initializing game state for player: {player_session.company_name}")

        # Create or get GameSession for this player
        game_session, created = GameSession.objects.get_or_create(
            user=player_session.user,
            name=f"{player_session.company_name} - {self.multiplayer_game.name}",
            defaults={
                'current_month': self.multiplayer_game.current_month,
                'current_year': self.multiplayer_game.current_year,
                'balance': self.multiplayer_game.starting_balance,
                'is_active': True
            }
        )

        if not created:
            # Update existing session to sync with multiplayer game
            game_session.current_month = self.multiplayer_game.current_month
            game_session.current_year = self.multiplayer_game.current_year
            game_session.balance = player_session.balance
            game_session.save()
            logger.info(f"Updated existing GameSession for {player_session.company_name}")
            return game_session

        # Initialize game parameters based on multiplayer game difficulty
        self._initialize_suppliers(game_session)
        self._initialize_components(game_session)
        self._initialize_bike_types(game_session)
        self._initialize_workers(game_session)
        self._initialize_warehouses(game_session)
        self._initialize_markets(game_session)
        self._initialize_starting_inventory(game_session)

        logger.info(f"Game state initialized for {player_session.company_name}")
        return game_session

    def _initialize_suppliers(self, session):
        """Create suppliers with varying quality and terms."""
        suppliers_data = [
            {
                'name': 'BikeComponents GmbH',
                'payment_terms': 30,
                'delivery_time': 14,
                'complaint_probability': 2.5,
                'complaint_quantity': 1.2,
                'quality': 'standard'
            },
            {
                'name': 'Premium Parts AG',
                'payment_terms': 45,
                'delivery_time': 21,
                'complaint_probability': 1.0,
                'complaint_quantity': 0.8,
                'quality': 'premium'
            },
            {
                'name': 'Budget Bike Supply',
                'payment_terms': 14,
                'delivery_time': 7,
                'complaint_probability': 5.0,
                'complaint_quantity': 2.5,
                'quality': 'basic'
            },
            {
                'name': 'EuroCycle Distribution',
                'payment_terms': 30,
                'delivery_time': 10,
                'complaint_probability': 2.0,
                'complaint_quantity': 1.0,
                'quality': 'standard'
            }
        ]

        for supplier_data in suppliers_data:
            Supplier.objects.create(session=session, **supplier_data)

    def _initialize_components(self, session):
        """Create component types and components."""
        # Component types
        component_types_data = [
            {'name': 'Laufradsatz', 'storage_space_per_unit': 1.5},
            {'name': 'Rahmen', 'storage_space_per_unit': 2.0},
            {'name': 'Lenker', 'storage_space_per_unit': 0.5},
            {'name': 'Sattel', 'storage_space_per_unit': 0.3},
            {'name': 'Schaltung', 'storage_space_per_unit': 0.4},
            {'name': 'Motor', 'storage_space_per_unit': 3.0}
        ]

        component_types = {}
        for ct_data in component_types_data:
            ct = ComponentType.objects.create(session=session, **ct_data)
            component_types[ct.name] = ct

        # Components with prices from Excel data
        components_data = [
            # Wheel sets (Laufradsatz)
            {'type': 'Laufradsatz', 'name': 'Standard', 'prices': {'basic': 80, 'standard': 100, 'premium': 130}},
            {'type': 'Laufradsatz', 'name': 'Alpin', 'prices': {'basic': 96, 'standard': 120, 'premium': 156}},
            {'type': 'Laufradsatz', 'name': 'Speed', 'prices': {'basic': 144, 'standard': 180, 'premium': 234}},
            {'type': 'Laufradsatz', 'name': 'Ampere', 'prices': {'basic': 120, 'standard': 150, 'premium': 195}},
            {'type': 'Laufradsatz', 'name': 'E-Mountain Pro', 'prices': {'basic': 224, 'standard': 280, 'premium': 364}},

            # Frames (Rahmen)
            {'type': 'Rahmen', 'name': 'Herrenrahmen Basic', 'prices': {'basic': 64, 'standard': 80, 'premium': 104}},
            {'type': 'Rahmen', 'name': 'Damenrahmen Basic', 'prices': {'basic': 64, 'standard': 80, 'premium': 104}},
            {'type': 'Rahmen', 'name': 'Mountain Basic', 'prices': {'basic': 96, 'standard': 120, 'premium': 156}},
            {'type': 'Rahmen', 'name': 'Renn Basic', 'prices': {'basic': 80, 'standard': 100, 'premium': 130}},
            {'type': 'Rahmen', 'name': 'E-Mountain Carbon', 'prices': {'basic': 280, 'standard': 350, 'premium': 455}},

            # Handlebars (Lenker)
            {'type': 'Lenker', 'name': 'Comfort', 'prices': {'basic': 20, 'standard': 25, 'premium': 33}},
            {'type': 'Lenker', 'name': 'Sport', 'prices': {'basic': 28, 'standard': 35, 'premium': 46}},
            {'type': 'Lenker', 'name': 'E-Mountain Pro', 'prices': {'basic': 52, 'standard': 65, 'premium': 85}},

            # Saddles (Sattel)
            {'type': 'Sattel', 'name': 'Comfort', 'prices': {'basic': 24, 'standard': 30, 'premium': 39}},
            {'type': 'Sattel', 'name': 'Sport', 'prices': {'basic': 36, 'standard': 45, 'premium': 59}},
            {'type': 'Sattel', 'name': 'E-Mountain Pro', 'prices': {'basic': 68, 'standard': 85, 'premium': 111}},

            # Gearshifts (Schaltung)
            {'type': 'Schaltung', 'name': 'Albatross', 'prices': {'basic': 48, 'standard': 60, 'premium': 78}},
            {'type': 'Schaltung', 'name': 'Gepard', 'prices': {'basic': 68, 'standard': 85, 'premium': 111}},
            {'type': 'Schaltung', 'name': 'E-Mountain Electronic', 'prices': {'basic': 144, 'standard': 180, 'premium': 234}},

            # Motors
            {'type': 'Motor', 'name': 'Standard', 'prices': {'basic': 240, 'standard': 300, 'premium': 390}},
            {'type': 'Motor', 'name': 'Mountain', 'prices': {'basic': 360, 'standard': 450, 'premium': 585}},
            {'type': 'Motor', 'name': 'High-Performance E-Motor', 'prices': {'basic': 520, 'standard': 650, 'premium': 845}}
        ]

        suppliers = Supplier.objects.filter(session=session)
        supplier_map = {s.quality: s for s in suppliers}

        for comp_data in components_data:
            component = Component.objects.create(
                session=session,
                component_type=component_types[comp_data['type']],
                name=comp_data['name']
            )

            # Create supplier prices for each quality tier
            for quality, supplier in supplier_map.items():
                price = comp_data['prices'].get(quality, comp_data['prices']['standard'])
                SupplierPrice.objects.create(
                    session=session,
                    supplier=supplier,
                    component=component,
                    price=Decimal(str(price))
                )

    def _initialize_bike_types(self, session):
        """Create bike types with pricing."""
        bike_types_data = [
            {
                'name': 'Damenrad',
                'skilled_worker_hours': 3.5,
                'unskilled_worker_hours': 2.0,
                'storage_space_per_unit': 3.5,
                'prices': {'cheap': 299, 'standard': 449, 'premium': 699},
                'components': {
                    'wheel_set': ['Standard'],
                    'frame': ['Damenrahmen Basic'],
                    'handlebar': ['Comfort'],
                    'saddle': ['Comfort'],
                    'gearshift': ['Albatross'],
                    'motor': []
                }
            },
            {
                'name': 'Herrenrad',
                'skilled_worker_hours': 3.5,
                'unskilled_worker_hours': 2.0,
                'storage_space_per_unit': 3.5,
                'prices': {'cheap': 299, 'standard': 449, 'premium': 699},
                'components': {
                    'wheel_set': ['Standard'],
                    'frame': ['Herrenrahmen Basic'],
                    'handlebar': ['Comfort'],
                    'saddle': ['Comfort'],
                    'gearshift': ['Albatross'],
                    'motor': []
                }
            },
            {
                'name': 'Mountainbike',
                'skilled_worker_hours': 4.0,
                'unskilled_worker_hours': 2.5,
                'storage_space_per_unit': 4.0,
                'prices': {'cheap': 449, 'standard': 699, 'premium': 999},
                'components': {
                    'wheel_set': ['Alpin'],
                    'frame': ['Mountain Basic'],
                    'handlebar': ['Sport'],
                    'saddle': ['Sport'],
                    'gearshift': ['Gepard'],
                    'motor': []
                }
            },
            {
                'name': 'Rennrad',
                'skilled_worker_hours': 4.5,
                'unskilled_worker_hours': 1.5,
                'storage_space_per_unit': 3.5,
                'prices': {'cheap': 549, 'standard': 799, 'premium': 1199},
                'components': {
                    'wheel_set': ['Speed'],
                    'frame': ['Renn Basic'],
                    'handlebar': ['Sport'],
                    'saddle': ['Sport'],
                    'gearshift': ['Gepard'],
                    'motor': []
                }
            },
            {
                'name': 'E-Bike',
                'skilled_worker_hours': 5.0,
                'unskilled_worker_hours': 3.0,
                'storage_space_per_unit': 4.5,
                'prices': {'cheap': 1299, 'standard': 1799, 'premium': 2499},
                'components': {
                    'wheel_set': ['Ampere'],
                    'frame': ['Damenrahmen Basic'],
                    'handlebar': ['Comfort'],
                    'saddle': ['Comfort'],
                    'gearshift': ['Albatross'],
                    'motor': ['Standard']
                }
            },
            {
                'name': 'E-Mountainbike',
                'skilled_worker_hours': 5.5,
                'unskilled_worker_hours': 3.5,
                'storage_space_per_unit': 4.5,
                'prices': {'cheap': 1699, 'standard': 2299, 'premium': 3199},
                'components': {
                    'wheel_set': ['Alpin'],
                    'frame': ['Mountain Basic'],
                    'handlebar': ['Sport'],
                    'saddle': ['Sport'],
                    'gearshift': ['Gepard'],
                    'motor': ['Mountain']
                }
            },
            {
                'name': 'E-Mountain-Bike',
                'skilled_worker_hours': 8.5,
                'unskilled_worker_hours': 4.0,
                'storage_space_per_unit': 5.0,
                'prices': {'cheap': 2999, 'standard': 3999, 'premium': 5499},
                'components': {
                    'wheel_set': ['E-Mountain Pro'],
                    'frame': ['E-Mountain Carbon'],
                    'handlebar': ['E-Mountain Pro'],
                    'saddle': ['E-Mountain Pro'],
                    'gearshift': ['E-Mountain Electronic'],
                    'motor': ['High-Performance E-Motor']
                }
            }
        ]

        for bike_data in bike_types_data:
            bike_type = BikeType.objects.create(
                session=session,
                name=bike_data['name'],
                skilled_worker_hours=bike_data['skilled_worker_hours'],
                unskilled_worker_hours=bike_data['unskilled_worker_hours'],
                storage_space_per_unit=bike_data['storage_space_per_unit'],
                required_wheel_set_names=bike_data['components']['wheel_set'],
                required_frame_names=bike_data['components']['frame'],
                required_handlebar_names=bike_data['components']['handlebar'],
                required_saddle_names=bike_data['components']['saddle'],
                required_gearshift_names=bike_data['components']['gearshift'],
                required_motor_names=bike_data['components']['motor']
            )

            # Create prices
            for segment, price in bike_data['prices'].items():
                BikePrice.objects.create(
                    session=session,
                    bike_type=bike_type,
                    price_segment=segment,
                    price=Decimal(str(price))
                )

    def _initialize_workers(self, session):
        """Create initial worker types."""
        workers_data = [
            {'worker_type': 'skilled', 'hourly_wage': Decimal('25.00'), 'monthly_hours': 160, 'count': 2},
            {'worker_type': 'unskilled', 'hourly_wage': Decimal('15.00'), 'monthly_hours': 160, 'count': 3}
        ]

        for worker_data in workers_data:
            Worker.objects.create(session=session, **worker_data)

    def _initialize_warehouses(self, session):
        """Create initial warehouse."""
        # Ensure warehouse types exist
        if WarehouseType.objects.count() == 0:
            self._create_default_warehouse_types()

        # Create initial warehouse for player
        Warehouse.objects.create(
            session=session,
            name='Main Warehouse',
            location='Central',
            capacity_m2=200.0,
            rent_per_month=Decimal('2000.00')
        )

    def _create_default_warehouse_types(self):
        """Create default warehouse types if they don't exist."""
        warehouse_types = [
            {'name': 'Klein', 'capacity_m2': 100.0, 'purchase_price': Decimal('0'), 'monthly_rent': Decimal('1500.00'), 'order': 1},
            {'name': 'Mittel', 'capacity_m2': 200.0, 'purchase_price': Decimal('0'), 'monthly_rent': Decimal('2000.00'), 'order': 2},
            {'name': 'Groß', 'capacity_m2': 500.0, 'purchase_price': Decimal('0'), 'monthly_rent': Decimal('4000.00'), 'order': 3},
            {'name': 'Sehr Groß', 'capacity_m2': 1000.0, 'purchase_price': Decimal('0'), 'monthly_rent': Decimal('7000.00'), 'order': 4}
        ]

        for wt_data in warehouse_types:
            WarehouseType.objects.get_or_create(name=wt_data['name'], defaults=wt_data)

    def _initialize_markets(self, session):
        """Create markets with demand patterns."""
        markets_data = [
            {
                'name': 'Domestic Market',
                'location': 'Germany',
                'transport_cost_home': Decimal('50.00'),
                'transport_cost_foreign': Decimal('100.00'),
                'monthly_volume_capacity': 200
            },
            {
                'name': 'EU Market',
                'location': 'Europe',
                'transport_cost_home': Decimal('150.00'),
                'transport_cost_foreign': Decimal('200.00'),
                'monthly_volume_capacity': 300
            }
        ]

        bike_types = BikeType.objects.filter(session=session)

        for market_data in markets_data:
            market = Market.objects.create(session=session, **market_data)

            # Create market demand for each bike type
            for bike_type in bike_types:
                demand_pct = 33.33  # Equal distribution
                MarketDemand.objects.create(
                    session=session,
                    market=market,
                    bike_type=bike_type,
                    demand_percentage=demand_pct
                )

            # Create price sensitivity
            price_segments = [
                ('cheap', 40.0),
                ('standard', 40.0),
                ('premium', 20.0)
            ]

            for segment, percentage in price_segments:
                MarketPriceSensitivity.objects.create(
                    session=session,
                    market=market,
                    price_segment=segment,
                    percentage=percentage
                )

    def _initialize_starting_inventory(self, session):
        """Give player some starting inventory."""
        # Get warehouse
        warehouse = Warehouse.objects.filter(session=session).first()
        if not warehouse:
            return

        # Add some basic components to start - use component type + name to be specific
        starting_components = [
            ('Rahmen', 'Damenrahmen Basic', 10),
            ('Rahmen', 'Herrenrahmen Basic', 10),
            ('Laufradsatz', 'Standard', 20),
            ('Lenker', 'Comfort', 20),
            ('Sattel', 'Comfort', 20),
            ('Schaltung', 'Albatross', 20)
        ]

        for type_name, comp_name, quantity in starting_components:
            try:
                component_type = ComponentType.objects.get(session=session, name=type_name)
                component = Component.objects.get(
                    session=session,
                    component_type=component_type,
                    name=comp_name
                )
                # Use get_or_create to avoid duplicates
                ComponentStock.objects.get_or_create(
                    session=session,
                    warehouse=warehouse,
                    component=component,
                    defaults={'quantity': quantity}
                )
            except (Component.DoesNotExist, ComponentType.DoesNotExist) as e:
                logger.warning(f"Component {type_name}/{comp_name} not found for starting inventory: {e}")

    def get_player_game_session(self, player_session):
        """Get the GameSession for a player."""
        try:
            return GameSession.objects.get(
                user=player_session.user,
                name__contains=self.multiplayer_game.name
            )
        except GameSession.DoesNotExist:
            return self.initialize_player_game_state(player_session)
        except GameSession.MultipleObjectsReturned:
            # Return the most recent one
            return GameSession.objects.filter(
                user=player_session.user,
                name__contains=self.multiplayer_game.name
            ).order_by('-created_at').first()
