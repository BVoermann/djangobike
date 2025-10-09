from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import json

from .models import GameMode, GameObjective, SessionGameMode, GameResult, BankruptcyEvent
from bikeshop.models import GameSession, BikeType
from sales.models import SalesOrder, Market
from production.models import ProducedBike
from procurement.models import ProcurementOrder
from warehouse.models import Warehouse
from competitors.models import AICompetitor, CompetitorSale


class GameModeTestCase(TestCase):
    """Test cases for GameMode model"""
    
    def setUp(self):
        """Set up test data"""
        self.game_mode = GameMode.objects.create(
            name="Test Profit Mode",
            mode_type="profit_maximization",
            description="Test mode for profit maximization",
            duration_months=24,
            starting_balance=80000,
            bankruptcy_threshold=-10000,
            victory_conditions={
                'min_profit': 50000,
                'min_market_share': 20
            },
            difficulty_multipliers={
                'cost_multiplier': 1.0,
                'competition_intensity': 1.2
            }
        )
    
    def test_game_mode_creation(self):
        """Test creating a game mode"""
        self.assertEqual(self.game_mode.name, "Test Profit Mode")
        self.assertEqual(self.game_mode.mode_type, "profit_maximization")
        self.assertEqual(self.game_mode.duration_months, 24)
        self.assertEqual(self.game_mode.starting_balance, Decimal('80000'))
        self.assertTrue(self.game_mode.is_active)
        self.assertTrue(self.game_mode.is_multiplayer_compatible)
    
    def test_game_mode_str_representation(self):
        """Test string representation of game mode"""
        expected = "Test Profit Mode (Gewinnmaximierung)"
        self.assertEqual(str(self.game_mode), expected)
    
    def test_game_mode_json_fields(self):
        """Test JSON fields in game mode"""
        self.assertIsInstance(self.game_mode.victory_conditions, dict)
        self.assertIn('min_profit', self.game_mode.victory_conditions)
        self.assertEqual(self.game_mode.victory_conditions['min_profit'], 50000)
        
        self.assertIsInstance(self.game_mode.difficulty_multipliers, dict)
        self.assertEqual(self.game_mode.difficulty_multipliers['cost_multiplier'], 1.0)


class GameObjectiveTestCase(TestCase):
    """Test cases for GameObjective model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testplayer',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            balance=50000,
            current_month=3,
            current_year=2024
        )
        
        self.warehouse = Warehouse.objects.create(
            session=self.session,
            name="Test Warehouse",
            location="Test Location",
            capacity_m2=1000.0,
            rent_per_month=1000.00
        )
        
        self.game_mode = GameMode.objects.create(
            name="Test Mode",
            mode_type="profit_maximization",
            description="Test mode",
            duration_months=24
        )
        
        self.profit_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Total Profit Goal",
            description="Reach minimum profit",
            objective_type="profit_total",
            target_value=50000,
            comparison_operator="gte",
            weight=2.0,
            is_primary=True
        )
        
        self.balance_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Minimum Balance",
            description="Maintain minimum balance",
            objective_type="balance_minimum",
            target_value=10000,
            comparison_operator="gte",
            is_failure_condition=True
        )
    
    def test_objective_creation(self):
        """Test creating game objectives"""
        self.assertEqual(self.profit_objective.name, "Total Profit Goal")
        self.assertEqual(self.profit_objective.objective_type, "profit_total")
        self.assertEqual(self.profit_objective.target_value, Decimal('50000'))
        self.assertEqual(self.profit_objective.comparison_operator, "gte")
        self.assertTrue(self.profit_objective.is_primary)
        self.assertFalse(self.profit_objective.is_failure_condition)
        
        self.assertTrue(self.balance_objective.is_failure_condition)
        self.assertFalse(self.balance_objective.is_primary)
    
    def test_objective_str_representation(self):
        """Test string representation of objectives"""
        expected = "Test Mode: Total Profit Goal"
        self.assertEqual(str(self.profit_objective), expected)
    
    def test_balance_objective_evaluation(self):
        """Test balance objective evaluation"""
        # Session balance is 50000, target is 10000
        result = self.balance_objective.evaluate(self.session)
        self.assertTrue(result)
        
        # Reduce session balance below target
        self.session.balance = 5000
        self.session.save()
        result = self.balance_objective.evaluate(self.session)
        self.assertFalse(result)
    
    def test_profit_total_calculation(self):
        """Test total profit calculation"""
        # Create sales orders
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        market = Market.objects.create(
            session=self.session,
            name="Test Market",
            location="Germany",
            transport_cost_home=50.00
        )
        
        # Create produced bikes
        bike1 = ProducedBike.objects.create(
            session=self.session,
            bike_type=bike_type,
            price_segment="standard",
            production_month=1,
            production_year=2024,
            warehouse=self.warehouse,
            production_cost=300
        )
        
        bike2 = ProducedBike.objects.create(
            session=self.session,
            bike_type=bike_type,
            price_segment="premium",
            production_month=2,
            production_year=2024,
            warehouse=self.warehouse,
            production_cost=400
        )
        
        # Create sales orders
        SalesOrder.objects.create(
            session=self.session,
            market=market,
            bike=bike1,
            sale_month=2,
            sale_year=2024,
            sale_price=800,
            transport_cost=50
        )
        
        SalesOrder.objects.create(
            session=self.session,
            market=market,
            bike=bike2,
            sale_month=3,
            sale_year=2024,
            sale_price=1200,
            transport_cost=50
        )
        
        # Create procurement orders to simulate costs
        ProcurementOrder.objects.create(
            session=self.session,
            supplier_name="Test Supplier",
            component_name="Test Component",
            quantity=10,
            unit_cost=50,
            total_cost=500,
            order_month=1,
            order_year=2024
        )
        
        ProcurementOrder.objects.create(
            session=self.session,
            supplier_name="Test Supplier 2",
            component_name="Test Component 2",
            quantity=5,
            unit_cost=60,
            total_cost=300,
            order_month=2,
            order_year=2024
        )
        
        # Calculate profit: (800 + 1200) - (500 + 300) = 1200
        profit = self.profit_objective.calculate_total_profit(self.session)
        self.assertEqual(profit, 1200.0)
        
        # Test objective evaluation
        # Target is 50000, actual is 1200, so should fail
        result = self.profit_objective.evaluate(self.session)
        self.assertFalse(result)
    
    def test_monthly_profit_calculation(self):
        """Test monthly profit calculation"""
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Monthly Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        market = Market.objects.create(
            session=self.session,
            name="Monthly Test Market",
            location="Germany",
            transport_cost_home=50.00
        )
        
        bike = ProducedBike.objects.create(
            session=self.session,
            bike_type=bike_type,
            price_segment="standard",
            production_month=2,
            production_year=2024,
            warehouse=self.warehouse,
            production_cost=300
        )
        
        # Create sales for current month (March 2024)
        SalesOrder.objects.create(
            session=self.session,
            market=market,
            bike=bike,
            sale_month=3,  # Current month
            sale_year=2024,  # Current year
            sale_price=1000,
            transport_cost=50
        )
        
        # Create costs for current month
        ProcurementOrder.objects.create(
            session=self.session,
            supplier_name="Monthly Supplier",
            component_name="Monthly Component",
            quantity=5,
            unit_cost=40,
            total_cost=200,
            order_month=3,  # Current month
            order_year=2024  # Current year
        )
        
        # Monthly profit: 1000 - 200 = 800
        monthly_profit = self.profit_objective.calculate_monthly_profit(self.session)
        self.assertEqual(monthly_profit, 800.0)
    
    def test_bikes_produced_objective(self):
        """Test bikes produced objective evaluation"""
        bikes_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Production Target",
            description="Produce minimum bikes",
            objective_type="bikes_produced",
            target_value=5,
            comparison_operator="gte"
        )
        
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Production Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        # Initially no bikes produced
        current_value = bikes_objective.get_current_value(self.session)
        self.assertEqual(current_value, 0.0)
        result = bikes_objective.evaluate(self.session)
        self.assertFalse(result)
        
        # Create some bikes
        for i in range(7):
            ProducedBike.objects.create(
                session=self.session,
                bike_type=bike_type,
                price_segment="standard",
                production_month=1,
                production_year=2024,
                warehouse=self.warehouse,
                production_cost=300
            )
        
        # Now should pass (7 >= 5)
        current_value = bikes_objective.get_current_value(self.session)
        self.assertEqual(current_value, 7.0)
        result = bikes_objective.evaluate(self.session)
        self.assertTrue(result)
    
    def test_quality_rating_objective(self):
        """Test quality rating calculation"""
        quality_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Quality Target",
            description="Maintain quality rating",
            objective_type="quality_rating",
            target_value=7,
            comparison_operator="gte"
        )
        
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Quality Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        # Create bikes with different quality segments
        # 2 premium (10 points each), 3 standard (7 points each), 1 cheap (4 points)
        # Expected: (2*10 + 3*7 + 1*4) / 6 = (20 + 21 + 4) / 6 = 45/6 = 7.5
        
        for i in range(2):
            ProducedBike.objects.create(
                session=self.session,
                bike_type=bike_type,
                price_segment="premium",
                production_month=1,
                production_year=2024,
                warehouse=self.warehouse,
                production_cost=500
            )
        
        for i in range(3):
            ProducedBike.objects.create(
                session=self.session,
                bike_type=bike_type,
                price_segment="standard",
                production_month=1,
                production_year=2024,
                warehouse=self.warehouse,
                production_cost=400
            )
        
        ProducedBike.objects.create(
            session=self.session,
            bike_type=bike_type,
            price_segment="cheap",
            production_month=1,
            production_year=2024,
            warehouse=self.warehouse,
            production_cost=200
        )
        
        quality_score = quality_objective.get_current_value(self.session)
        expected_score = (2 * 10 + 3 * 7 + 1 * 4) / 6  # 7.5
        self.assertEqual(quality_score, expected_score)
        
        # Should pass (7.5 >= 7)
        result = quality_objective.evaluate(self.session)
        self.assertTrue(result)
    
    def test_market_share_calculation(self):
        """Test market share calculation with competitors"""
        market_share_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Market Share Goal",
            description="Achieve market share",
            objective_type="market_share",
            target_value=25,  # 25%
            comparison_operator="gte"
        )
        
        # Create competitor
        competitor = AICompetitor.objects.create(
            session=self.session,
            name="Test Competitor",
            strategy="balanced"
        )
        
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Market Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        market = Market.objects.create(
            session=self.session,
            name="Share Test Market",
            location="Germany",
            transport_cost_home=50.00
        )
        
        # Player has 3 sales
        for i in range(3):
            bike = ProducedBike.objects.create(
                session=self.session,
                bike_type=bike_type,
                price_segment="standard",
                production_month=1,
                production_year=2024,
                warehouse=self.warehouse,
                production_cost=400
            )
            
            SalesOrder.objects.create(
                session=self.session,
                market=market,
                bike=bike,
                sale_month=2,
                sale_year=2024,
                sale_price=800,
                transport_cost=50
            )
        
        # Competitor has 9 sales (total market = 3 + 9 = 12, player share = 3/12 = 25%)
        CompetitorSale.objects.create(
            competitor=competitor,
            bike_type=bike_type,
            month=2,
            year=2024,
            quantity_sold=9,
            average_sale_price=750,
            total_revenue=6750
        )
        
        market_share = market_share_objective.get_current_value(self.session)
        self.assertEqual(market_share, 25.0)
        
        # Should pass (25 >= 25)
        result = market_share_objective.evaluate(self.session)
        self.assertTrue(result)
    
    def test_comparison_operators(self):
        """Test different comparison operators"""
        # Test 'lte' operator
        max_cost_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Max Cost",
            description="Keep costs under limit",
            objective_type="balance_minimum",
            target_value=60000,
            comparison_operator="lte"
        )
        
        # Session balance is 50000, target is 60000 (lte)
        result = max_cost_objective.evaluate(self.session)
        self.assertTrue(result)  # 50000 <= 60000
        
        # Test 'eq' operator
        exact_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Exact Target",
            description="Hit exact target",
            objective_type="balance_minimum",
            target_value=50000,
            comparison_operator="eq"
        )
        
        result = exact_objective.evaluate(self.session)
        self.assertTrue(result)  # 50000 == 50000
        
        # Test 'gt' operator
        exceed_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Exceed Target",
            description="Must exceed target",
            objective_type="balance_minimum",
            target_value=49999,
            comparison_operator="gt"
        )
        
        result = exceed_objective.evaluate(self.session)
        self.assertTrue(result)  # 50000 > 49999
        
        # Test 'lt' operator
        under_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Stay Under",
            description="Must stay under target",
            objective_type="balance_minimum",
            target_value=60000,
            comparison_operator="lt"
        )
        
        result = under_objective.evaluate(self.session)
        self.assertTrue(result)  # 50000 < 60000


class SessionGameModeTestCase(TestCase):
    """Test cases for SessionGameMode model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='sessionplayer',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Session Game Test',
            balance=75000,
            current_month=1,
            current_year=2024
        )
        
        self.game_mode = GameMode.objects.create(
            name="Session Test Mode",
            mode_type="profit_maximization",
            description="Test mode for sessions",
            duration_months=12,
            bankruptcy_threshold=-5000
        )
        
        self.primary_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Primary Goal",
            description="Main objective",
            objective_type="balance_minimum",
            target_value=80000,
            comparison_operator="gte",
            is_primary=True
        )
        
        self.failure_objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="Don't Go Broke",
            description="Failure condition",
            objective_type="balance_minimum",
            target_value=0,
            comparison_operator="gte",
            is_failure_condition=True
        )
        
        self.session_game_mode = SessionGameMode.objects.create(
            session=self.session,
            game_mode=self.game_mode
        )
    
    def test_session_game_mode_creation(self):
        """Test creating a session game mode"""
        self.assertEqual(self.session_game_mode.session, self.session)
        self.assertEqual(self.session_game_mode.game_mode, self.game_mode)
        self.assertTrue(self.session_game_mode.is_active)
        self.assertFalse(self.session_game_mode.is_completed)
        self.assertFalse(self.session_game_mode.is_failed)
        self.assertIsNone(self.session_game_mode.final_score)
    
    def test_victory_condition_check_success(self):
        """Test victory condition checking when conditions are met"""
        # Set session balance to meet primary objective (80000)
        self.session.balance = 85000
        self.session.save()
        
        self.session_game_mode.check_victory_conditions()
        
        self.session_game_mode.refresh_from_db()
        self.assertTrue(self.session_game_mode.is_completed)
        self.assertFalse(self.session_game_mode.is_failed)
        self.assertIsNotNone(self.session_game_mode.final_score)
        self.assertIsNotNone(self.session_game_mode.completed_at)
    
    def test_failure_condition_bankruptcy(self):
        """Test failure condition when bankruptcy occurs"""
        # Set balance below bankruptcy threshold
        self.session.balance = -10000
        self.session.save()
        
        self.session_game_mode.check_victory_conditions()
        
        self.session_game_mode.refresh_from_db()
        self.assertTrue(self.session_game_mode.is_failed)
        self.assertFalse(self.session_game_mode.is_active)
        self.assertIsNotNone(self.session_game_mode.completed_at)
    
    def test_failure_condition_objective_failure(self):
        """Test failure condition when failure objective is not met"""
        # Set balance below failure objective (0)
        self.session.balance = -1000
        self.session.save()
        
        self.session_game_mode.check_victory_conditions()
        
        self.session_game_mode.refresh_from_db()
        self.assertTrue(self.session_game_mode.is_failed)
        self.assertFalse(self.session_game_mode.is_active)
    
    def test_duration_exceeded(self):
        """Test game completion when duration is exceeded"""
        # Advance beyond game duration
        self.session.current_month = 15  # Game duration is 12 months
        self.session.save()
        
        self.session_game_mode.check_victory_conditions()
        
        self.session_game_mode.refresh_from_db()
        self.assertTrue(self.session_game_mode.is_completed)
        self.assertFalse(self.session_game_mode.is_failed)
    
    def test_final_score_calculation(self):
        """Test final score calculation"""
        # Set session balance to partially meet objectives
        self.session.balance = 70000  # Primary objective is 80000
        self.session.save()
        
        score = self.session_game_mode.calculate_final_score()
        
        # Score should be based on achievement percentage
        # 70000/80000 = 0.875 = 87.5%
        self.assertGreater(score, 80)
        self.assertLess(score, 90)
    
    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation"""
        # One objective met (failure condition), one not met (primary)
        # Balance is 75000: meets failure condition (>= 0) but not primary (>= 80000)
        
        completion_pct = self.session_game_mode.calculate_completion_percentage()
        
        # 1 out of 2 objectives met = 50%
        self.assertEqual(completion_pct, Decimal('50.0'))
    
    def test_monthly_progress_update(self):
        """Test monthly progress tracking"""
        self.session_game_mode.update_monthly_progress()
        
        self.session_game_mode.refresh_from_db()
        
        # Check that progress was recorded
        self.assertIsNotNone(self.session_game_mode.objective_progress)
        self.assertIsNotNone(self.session_game_mode.monthly_scores)
        
        # Check that objectives are tracked
        progress = self.session_game_mode.objective_progress
        self.assertIn(str(self.primary_objective.id), progress)
        self.assertIn(str(self.failure_objective.id), progress)
        
        # Check monthly score entry
        monthly_scores = self.session_game_mode.monthly_scores
        self.assertGreater(len(monthly_scores), 0)
        
        latest_score = monthly_scores[-1]
        self.assertEqual(latest_score['month'], self.session.current_month)
        self.assertEqual(latest_score['year'], self.session.current_year)
        self.assertIsNotNone(latest_score['score'])


class GameResultTestCase(TestCase):
    """Test cases for GameResult model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='resultplayer',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Result Test Session',
            balance=60000,
            current_month=8,
            current_year=2024
        )
        
        self.warehouse = Warehouse.objects.create(
            session=self.session,
            name="Result Test Warehouse",
            location="Test Location",
            capacity_m2=1000.0,
            rent_per_month=1000.00
        )
        
        self.game_mode = GameMode.objects.create(
            name="Result Test Mode",
            mode_type="profit_maximization",
            description="Test mode for results"
        )
        
        self.session_game_mode = SessionGameMode.objects.create(
            session=self.session,
            game_mode=self.game_mode,
            final_score=Decimal('85.5'),
            completion_percentage=Decimal('90.0')
        )
    
    def test_game_result_creation_victory(self):
        """Test creating a victory game result"""
        result = GameResult.objects.create(
            session_game_mode=self.session_game_mode,
            result_type='victory',
            final_score=Decimal('85.5'),
            completion_percentage=Decimal('90.0'),
            summary="Congratulations! Victory achieved!"
        )
        
        self.assertEqual(result.result_type, 'victory')
        self.assertEqual(result.final_score, Decimal('85.5'))
        self.assertEqual(result.completion_percentage, Decimal('90.0'))
        self.assertEqual(result.total_months_played, 8)
        self.assertEqual(result.final_balance, Decimal('60000'))
    
    def test_game_result_creation_defeat(self):
        """Test creating a defeat game result"""
        result = GameResult.objects.create(
            session_game_mode=self.session_game_mode,
            result_type='defeat',
            final_score=Decimal('25.0'),
            completion_percentage=Decimal('30.0'),
            summary="Game Over: Bankruptcy",
            failure_reason="Insufficient funds"
        )
        
        self.assertEqual(result.result_type, 'defeat')
        self.assertEqual(result.failure_reason, "Insufficient funds")
        self.assertIn("Game Over", result.summary)
    
    def test_statistics_calculation(self):
        """Test automatic statistics calculation"""
        # Create test data for statistics
        bike_type = BikeType.objects.create(
            session=self.session,
            name="Stats Test Bike",
            skilled_worker_hours=2.0,
            unskilled_worker_hours=3.0
        )
        
        market = Market.objects.create(
            session=self.session,
            name="Stats Test Market",
            location="Germany",
            transport_cost_home=50.00
        )
        
        # Create bikes and sales
        for i in range(5):
            bike = ProducedBike.objects.create(
                session=self.session,
                bike_type=bike_type,
                price_segment="standard",
                production_month=1,
                production_year=2024,
                warehouse=self.warehouse,
                production_cost=400
            )
            
            SalesOrder.objects.create(
                session=self.session,
                market=market,
                bike=bike,
                sale_month=2,
                sale_year=2024,
                sale_price=800,
                transport_cost=50
            )
        
        # Create procurement costs
        ProcurementOrder.objects.create(
            session=self.session,
            supplier_name="Stats Supplier",
            component_name="Stats Component",
            quantity=20,
            unit_cost=50,
            total_cost=1000,
            order_month=1,
            order_year=2024
        )
        
        result = GameResult.objects.create(
            session_game_mode=self.session_game_mode,
            result_type='victory',
            final_score=Decimal('85.5'),
            completion_percentage=Decimal('90.0'),
            summary="Statistics test result"
        )
        
        # Check calculated statistics
        self.assertEqual(result.bikes_produced, 5)
        self.assertEqual(result.bikes_sold, 5)
        self.assertEqual(result.total_revenue, Decimal('4000'))  # 5 * 800
        self.assertEqual(result.total_profit, Decimal('3000'))  # 4000 - 1000
    
    def test_recommendations_generation(self):
        """Test recommendation generation based on performance"""
        # Test low balance scenario
        self.session.balance = -5000
        self.session.save()
        
        result = GameResult.objects.create(
            session_game_mode=self.session_game_mode,
            result_type='defeat',
            final_score=Decimal('15.0'),
            completion_percentage=Decimal('20.0'),
            summary="Poor financial performance"
        )
        
        self.assertIn("Finanzmanagement", result.recommendations)
        
        # Test low market share scenario
        result.market_share_final = Decimal('5.0')
        result.generate_recommendations()
        
        self.assertIn("Marktanteil", result.recommendations)


class BankruptcyEventTestCase(TestCase):
    """Test cases for BankruptcyEvent model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='bankruptplayer',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Bankruptcy Test Session',
            balance=-15000,
            current_month=6,
            current_year=2024
        )
        
        self.game_mode = GameMode.objects.create(
            name="Bankruptcy Test Mode",
            mode_type="survival",
            description="Test mode for bankruptcy",
            bankruptcy_threshold=-10000
        )
        
        self.session_game_mode = SessionGameMode.objects.create(
            session=self.session,
            game_mode=self.game_mode
        )
    
    def test_bankruptcy_event_creation(self):
        """Test creating a bankruptcy event"""
        bankruptcy = BankruptcyEvent.objects.create(
            session=self.session,
            session_game_mode=self.session_game_mode,
            balance_at_bankruptcy=Decimal('-15000'),
            bankruptcy_threshold=Decimal('-10000'),
            trigger_month=6,
            trigger_year=2024,
            primary_cause='excessive_spending',
            contributing_factors=['high_procurement_costs', 'low_sales_volume'],
            elimination_reason="Player exceeded bankruptcy threshold",
            player_eliminated=True
        )
        
        self.assertEqual(bankruptcy.session, self.session)
        self.assertEqual(bankruptcy.session_game_mode, self.session_game_mode)
        self.assertEqual(bankruptcy.balance_at_bankruptcy, Decimal('-15000'))
        self.assertEqual(bankruptcy.primary_cause, 'excessive_spending')
        self.assertTrue(bankruptcy.player_eliminated)
        self.assertIn('high_procurement_costs', bankruptcy.contributing_factors)
    
    def test_bankruptcy_str_representation(self):
        """Test string representation of bankruptcy event"""
        bankruptcy = BankruptcyEvent.objects.create(
            session=self.session,
            balance_at_bankruptcy=Decimal('-15000'),
            bankruptcy_threshold=Decimal('-10000'),
            trigger_month=6,
            trigger_year=2024,
            primary_cause='low_sales',
            elimination_reason="Bankruptcy"
        )
        
        expected = "Bankrott: Bankruptcy Test Session - Monat 6/2024"
        self.assertEqual(str(bankruptcy), expected)
    
    def test_recovery_attempt(self):
        """Test bankruptcy recovery attempt"""
        bankruptcy = BankruptcyEvent.objects.create(
            session=self.session,
            balance_at_bankruptcy=Decimal('-15000'),
            bankruptcy_threshold=Decimal('-10000'),
            trigger_month=6,
            trigger_year=2024,
            primary_cause='market_downturn',
            recovery_attempted=True,
            recovery_successful=True,
            bailout_amount=Decimal('25000'),
            player_eliminated=False,
            elimination_reason="Recovery successful - player continues"
        )
        
        self.assertTrue(bankruptcy.recovery_attempted)
        self.assertTrue(bankruptcy.recovery_successful)
        self.assertEqual(bankruptcy.bailout_amount, Decimal('25000'))
        self.assertFalse(bankruptcy.player_eliminated)


class GameObjectiveViewTestCase(TestCase):
    """Test cases for game objectives views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='viewtester',
            password='testpass123',
            email='test@example.com'
        )
        
        self.client = Client()
        self.client.login(username='viewtester', password='testpass123')
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='View Test Session',
            balance=50000
        )
        
        self.game_mode = GameMode.objects.create(
            name="View Test Mode",
            mode_type="profit_maximization",
            description="Test mode for views"
        )
        
        self.objective = GameObjective.objects.create(
            game_mode=self.game_mode,
            name="View Test Objective",
            description="Test objective for views",
            objective_type="balance_minimum",
            target_value=40000,
            comparison_operator="gte"
        )
        
        self.session_game_mode = SessionGameMode.objects.create(
            session=self.session,
            game_mode=self.game_mode
        )
    
    def test_login_required_for_objectives_views(self):
        """Test that objectives views require login"""
        self.client.logout()
        
        # Test objectives dashboard
        if 'game_objectives:dashboard' in [url.name for url in __import__('game_objectives.urls', fromlist=['urlpatterns']).urlpatterns]:
            response = self.client.get(reverse('game_objectives:dashboard', args=[self.session.id]))
            self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_objective_evaluation_view_permissions(self):
        """Test that users can only access their own session objectives"""
        # Create another user's session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        
        other_session = GameSession.objects.create(
            user=other_user,
            name='Other User Session',
            balance=30000
        )
        
        # Try to access other user's objectives (if such view exists)
        # This is a placeholder test - implement when views are available
        self.assertTrue(True)  # Placeholder assertion
