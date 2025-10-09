from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    EventCategory, RandomEvent, EventOccurrence, EventChoice,
    RegulationTimeline, RegulationCompliance, MarketOpportunity
)
from bikeshop.models import GameSession
from .event_engine import RandomEventsEngine


class EventCategoryTestCase(TestCase):
    """Test cases for event categories"""
    
    def setUp(self):
        self.innovation_category = EventCategory.objects.create(
            name='Product Innovation',
            category_type='innovation',
            description='Product innovation opportunities',
            base_probability=10.0
        )
    
    def test_event_category_creation(self):
        """Test creating event categories"""
        self.assertEqual(self.innovation_category.name, 'Product Innovation')
        self.assertEqual(self.innovation_category.category_type, 'innovation')
        self.assertEqual(self.innovation_category.base_probability, 10.0)
        self.assertTrue(self.innovation_category.is_active)
    
    def test_category_str_representation(self):
        """Test string representation of categories"""
        expected = "Product Innovation (Product Innovation)"
        self.assertEqual(str(self.innovation_category), expected)


class RandomEventTestCase(TestCase):
    """Test cases for random events"""
    
    def setUp(self):
        self.category = EventCategory.objects.create(
            name='Market Events',
            category_type='market',
            description='Market change events',
            base_probability=5.0
        )
        
        self.event = RandomEvent.objects.create(
            category=self.category,
            title='New Market Opportunity',
            description='A new market segment opens up',
            detailed_description='Detailed description of the opportunity',
            severity='moderate',
            duration_type='temporary',
            probability_weight=2.0,
            min_game_month=3,
            max_game_month=24,
            financial_effects={'balance_change': 5000},
            production_effects={'efficiency_modifier': 0.1},
            market_effects={'demand_modifier': 0.15}
        )
    
    def test_random_event_creation(self):
        """Test creating random events"""
        self.assertEqual(self.event.title, 'New Market Opportunity')
        self.assertEqual(self.event.category, self.category)
        self.assertEqual(self.event.severity, 'moderate')
        self.assertEqual(self.event.duration_type, 'temporary')
        self.assertEqual(self.event.probability_weight, 2.0)
        self.assertEqual(self.event.min_game_month, 3)
        self.assertEqual(self.event.max_game_month, 24)
    
    def test_event_effects_json_fields(self):
        """Test JSON field storage of effects"""
        self.assertEqual(self.event.financial_effects['balance_change'], 5000)
        self.assertEqual(self.event.production_effects['efficiency_modifier'], 0.1)
        self.assertEqual(self.event.market_effects['demand_modifier'], 0.15)
    
    def test_event_choices(self):
        """Test creating event choices"""
        choice1 = EventChoice.objects.create(
            event=self.event,
            choice_text='Accept the opportunity',
            description='Take advantage of the new market',
            order=1,
            required_balance=Decimal('10000.00'),
            effects={'balance_change': 15000, 'reputation_boost': 5}
        )
        
        choice2 = EventChoice.objects.create(
            event=self.event,
            choice_text='Decline the opportunity',
            description='Keep current strategy',
            order=2,
            effects={'stability_bonus': 2}
        )
        
        choices = EventChoice.objects.filter(event=self.event).order_by('order')
        self.assertEqual(choices.count(), 2)
        self.assertEqual(choices[0].choice_text, 'Accept the opportunity')
        self.assertEqual(choices[1].choice_text, 'Decline the opportunity')
        self.assertEqual(choices[0].required_balance, Decimal('10000.00'))


class EventOccurrenceTestCase(TestCase):
    """Test cases for event occurrences"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=6,
            current_year=2024,
            balance=Decimal('75000.00')
        )
        
        self.category = EventCategory.objects.create(
            name='Crisis Events',
            category_type='crisis',
            description='Crisis situations',
            base_probability=3.0
        )
        
        self.event = RandomEvent.objects.create(
            category=self.category,
            title='Supply Chain Disruption',
            description='Major supplier has issues',
            severity='major',
            duration_type='medium_term',
            financial_effects={'cost_increase': 0.2}
        )
    
    def test_event_occurrence_creation(self):
        """Test creating event occurrences"""
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            duration_months=3,
            status='active',
            context_data={'trigger_reason': 'random_roll'}
        )
        
        self.assertEqual(occurrence.session, self.session)
        self.assertEqual(occurrence.event, self.event)
        self.assertEqual(occurrence.triggered_month, 6)
        self.assertEqual(occurrence.triggered_year, 2024)
        self.assertEqual(occurrence.duration_months, 3)
        self.assertEqual(occurrence.status, 'active')
        self.assertFalse(occurrence.is_acknowledged)
    
    def test_player_response_tracking(self):
        """Test tracking player responses to events"""
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active'
        )
        
        # Simulate player response
        response_data = {
            'choice_id': 'choice-1',
            'chosen_at_month': 6,
            'chosen_at_year': 2024,
            'response_text': 'Implement emergency protocols'
        }
        
        occurrence.player_response = response_data
        occurrence.is_acknowledged = True
        occurrence.save()
        
        self.assertTrue(occurrence.is_acknowledged)
        self.assertEqual(occurrence.player_response['choice_id'], 'choice-1')
        self.assertEqual(occurrence.player_response['response_text'], 'Implement emergency protocols')


class RegulationTestCase(TestCase):
    """Test cases for regulatory compliance"""
    
    def setUp(self):
        self.regulation = RegulationTimeline.objects.create(
            title='Environmental Standards',
            description='New environmental compliance requirements',
            implementation_year=2024,
            implementation_month=8,
            status='announced',
            compliance_cost=Decimal('25000.00'),
            penalty_per_month=Decimal('5000.00'),
            affects_production=True,
            affects_sales=False
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=7,
            current_year=2024,
            balance=Decimal('100000.00')
        )
    
    def test_regulation_creation(self):
        """Test creating regulations"""
        self.assertEqual(self.regulation.title, 'Environmental Standards')
        self.assertEqual(self.regulation.status, 'announced')
        self.assertEqual(self.regulation.implementation_year, 2024)
        self.assertEqual(self.regulation.implementation_month, 8)
        self.assertEqual(self.regulation.compliance_cost, Decimal('25000.00'))
        self.assertTrue(self.regulation.affects_production)
        self.assertFalse(self.regulation.affects_sales)
    
    def test_regulation_compliance_tracking(self):
        """Test tracking compliance with regulations"""
        compliance = RegulationCompliance.objects.create(
            session=self.session,
            regulation=self.regulation,
            is_compliant=False,
            compliance_date=None,
            total_penalties_paid=Decimal('0.00'),
            compliance_actions={'planned_investment': 30000}
        )
        
        self.assertEqual(compliance.session, self.session)
        self.assertEqual(compliance.regulation, self.regulation)
        self.assertFalse(compliance.is_compliant)
        self.assertIsNone(compliance.compliance_date)
        self.assertEqual(compliance.total_penalties_paid, Decimal('0.00'))
        
        # Simulate becoming compliant
        compliance.is_compliant = True
        compliance.compliance_date = timezone.now().date()
        compliance.save()
        
        self.assertTrue(compliance.is_compliant)
        self.assertIsNotNone(compliance.compliance_date)
    
    def test_penalty_accumulation(self):
        """Test penalty calculation for non-compliance"""
        compliance = RegulationCompliance.objects.create(
            session=self.session,
            regulation=self.regulation,
            is_compliant=False,
            total_penalties_paid=Decimal('15000.00')
        )
        
        # Simulate monthly penalty
        monthly_penalty = self.regulation.penalty_per_month
        compliance.total_penalties_paid += monthly_penalty
        compliance.save()
        
        expected_total = Decimal('20000.00')  # 15000 + 5000
        self.assertEqual(compliance.total_penalties_paid, expected_total)


class MarketOpportunityTestCase(TestCase):
    """Test cases for market opportunities"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=5,
            current_year=2024,
            balance=Decimal('80000.00')
        )
    
    def test_market_opportunity_creation(self):
        """Test creating market opportunities"""
        opportunity = MarketOpportunity.objects.create(
            session=self.session,
            title='Corporate Partnership',
            description='Partnership with major corporation',
            start_month=5,
            start_year=2024,
            end_month=8,
            end_year=2024,
            required_investment=Decimal('20000.00'),
            expected_return=Decimal('50000.00'),
            success_probability=0.8,
            risk_level='medium'
        )
        
        self.assertEqual(opportunity.session, self.session)
        self.assertEqual(opportunity.title, 'Corporate Partnership')
        self.assertEqual(opportunity.start_month, 5)
        self.assertEqual(opportunity.required_investment, Decimal('20000.00'))
        self.assertEqual(opportunity.success_probability, 0.8)
        self.assertFalse(opportunity.is_accepted)
    
    def test_opportunity_availability_window(self):
        """Test opportunity availability checking"""
        opportunity = MarketOpportunity.objects.create(
            session=self.session,
            title='Time-Limited Deal',
            description='Limited time offer',
            start_month=3,
            start_year=2024,
            end_month=7,
            end_year=2024,
            required_investment=Decimal('10000.00')
        )
        
        # Test availability during valid period
        self.assertTrue(opportunity.is_available(5, 2024))  # Within window
        self.assertTrue(opportunity.is_available(7, 2024))  # End month
        
        # Test unavailability outside period
        self.assertFalse(opportunity.is_available(2, 2024))  # Before start
        self.assertFalse(opportunity.is_available(8, 2024))  # After end
        self.assertFalse(opportunity.is_available(5, 2023))  # Wrong year
    
    def test_opportunity_acceptance(self):
        """Test accepting opportunities"""
        opportunity = MarketOpportunity.objects.create(
            session=self.session,
            title='Quick Win',
            description='Low-risk opportunity',
            start_month=5,
            start_year=2024,
            end_month=6,
            end_year=2024,
            required_investment=Decimal('5000.00')
        )
        
        # Accept the opportunity
        opportunity.is_accepted = True
        opportunity.acceptance_date = timezone.now()
        opportunity.save()
        
        self.assertTrue(opportunity.is_accepted)
        self.assertIsNotNone(opportunity.acceptance_date)


class RandomEventsEngineTestCase(TestCase):
    """Test cases for the random events engine"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Engine Test Session',
            current_month=10,
            current_year=2024,
            balance=Decimal('60000.00')
        )
        
        # Create test category and event
        self.category = EventCategory.objects.create(
            name='Test Category',
            category_type='market',
            description='Test events',
            base_probability=50.0  # High probability for testing
        )
        
        self.event = RandomEvent.objects.create(
            category=self.category,
            title='Test Event',
            description='A test event',
            severity='minor',
            probability_weight=3.0,
            min_game_month=1,
            max_game_month=12,
            production_effects={'efficiency_modifier': 0.05},
            market_effects={'demand_modifier': 0.1}
        )
        
        self.engine = RandomEventsEngine(self.session)
    
    def test_events_engine_initialization(self):
        """Test events engine initialization"""
        self.assertEqual(self.engine.session, self.session)
        self.assertEqual(self.engine.current_month, 10)
        self.assertEqual(self.engine.current_year, 2024)
    
    def test_eligible_events_filtering(self):
        """Test filtering events by game month"""
        # Create event that's too early
        early_event = RandomEvent.objects.create(
            category=self.category,
            title='Early Event',
            description='Too early',
            min_game_month=15,  # After current month
            max_game_month=20
        )
        
        # Create event that's too late
        late_event = RandomEvent.objects.create(
            category=self.category,
            title='Late Event',
            description='Too late',
            min_game_month=1,
            max_game_month=5  # Before current month
        )
        
        eligible_events = self.engine.get_eligible_events()
        
        # Only the original event should be eligible
        eligible_titles = [event.title for event in eligible_events]
        self.assertIn('Test Event', eligible_titles)
        self.assertNotIn('Early Event', eligible_titles)
        self.assertNotIn('Late Event', eligible_titles)
    
    def test_production_modifiers_calculation(self):
        """Test calculating production modifiers from active events"""
        # Create an active event occurrence
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=9,
            triggered_year=2024,
            duration_months=3,
            status='active',
            is_acknowledged=True
        )
        
        production_modifiers = self.engine.get_production_modifiers()
        
        # Should include the efficiency modifier from our test event
        self.assertIn('efficiency_modifier', production_modifiers)
        self.assertEqual(production_modifiers['efficiency_modifier'], 0.05)
    
    def test_market_modifiers_calculation(self):
        """Test calculating market modifiers from active events"""
        # Create an active event occurrence
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=9,
            triggered_year=2024,
            duration_months=2,
            status='active',
            is_acknowledged=True
        )
        
        market_modifiers = self.engine.get_market_modifiers()
        
        # Should include the demand modifier from our test event
        self.assertIn('demand_modifier', market_modifiers)
        self.assertEqual(market_modifiers['demand_modifier'], 0.1)
    
    def test_multiple_events_modifiers_combination(self):
        """Test combining modifiers from multiple active events"""
        # Create second event with different modifiers
        second_event = RandomEvent.objects.create(
            category=self.category,
            title='Second Event',
            description='Another event',
            production_effects={'cost_modifier': -0.1, 'efficiency_modifier': -0.02},
            market_effects={'price_modifier': 0.05}
        )
        
        # Create occurrences for both events
        EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=8,
            triggered_year=2024,
            duration_months=4,
            status='active',
            is_acknowledged=True
        )
        
        EventOccurrence.objects.create(
            session=self.session,
            event=second_event,
            triggered_month=9,
            triggered_year=2024,
            duration_months=2,
            status='active',
            is_acknowledged=True
        )
        
        production_modifiers = self.engine.get_production_modifiers()
        market_modifiers = self.engine.get_market_modifiers()
        
        # Should combine efficiency modifiers: 0.05 + (-0.02) = 0.03
        self.assertEqual(production_modifiers.get('efficiency_modifier'), 0.03)
        self.assertEqual(production_modifiers.get('cost_modifier'), -0.1)
        
        # Market modifiers should include both
        self.assertEqual(market_modifiers.get('demand_modifier'), 0.1)
        self.assertEqual(market_modifiers.get('price_modifier'), 0.05)


class RandomEventsViewTestCase(TestCase):
    """Test cases for random events views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='View Test Session',
            current_month=6,
            current_year=2024,
            balance=Decimal('85000.00')
        )
        
        self.category = EventCategory.objects.create(
            name='Test Category',
            category_type='innovation',
            description='Innovation events'
        )
        
        self.event = RandomEvent.objects.create(
            category=self.category,
            title='Innovation Breakthrough',
            description='New technology available',
            detailed_description='Detailed explanation of the breakthrough'
        )
        
        self.client = Client()
    
    def test_events_dashboard_view(self):
        """Test the events dashboard view"""
        # Create some test data
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active',
            is_acknowledged=False
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('random_events:dashboard', args=[self.session.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Innovation Breakthrough')
        self.assertIn('unacknowledged_events', response.context)
        self.assertIn('active_events', response.context)
    
    def test_event_detail_view(self):
        """Test the event detail view"""
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('random_events:event_detail', 
                   args=[self.session.id, occurrence.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Innovation Breakthrough')
        self.assertContains(response, 'New technology available')
        self.assertIn('event_occurrence', response.context)
    
    def test_acknowledge_event(self):
        """Test acknowledging events"""
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active',
            is_acknowledged=False
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('random_events:event_detail', 
                   args=[self.session.id, occurrence.id]),
            {'acknowledge': 'true'}
        )
        
        # Should redirect after acknowledgment
        self.assertEqual(response.status_code, 302)
        
        # Event should now be acknowledged
        occurrence.refresh_from_db()
        self.assertTrue(occurrence.is_acknowledged)
    
    def test_event_choice_selection(self):
        """Test selecting event choices"""
        # Create event with choices
        choice = EventChoice.objects.create(
            event=self.event,
            choice_text='Accept the innovation',
            description='Implement the new technology',
            order=1,
            required_balance=Decimal('20000.00'),
            effects={'balance_change': -20000, 'efficiency_boost': 0.15}
        )
        
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('random_events:event_detail', 
                   args=[self.session.id, occurrence.id]),
            {'choice_id': choice.id}
        )
        
        # Should redirect after choice
        self.assertEqual(response.status_code, 302)
        
        # Event should be acknowledged and have response data
        occurrence.refresh_from_db()
        self.assertTrue(occurrence.is_acknowledged)
        self.assertIsNotNone(occurrence.player_response)
        self.assertEqual(
            occurrence.player_response['choice_id'], 
            str(choice.id)
        )
    
    def test_insufficient_funds_choice_rejection(self):
        """Test rejecting choices due to insufficient funds"""
        # Create expensive choice
        expensive_choice = EventChoice.objects.create(
            event=self.event,
            choice_text='Expensive option',
            description='Costs more than player has',
            order=1,
            required_balance=Decimal('100000.00'),  # More than session balance
            effects={'big_benefit': 1}
        )
        
        occurrence = EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=6,
            triggered_year=2024,
            status='active'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('random_events:event_detail', 
                   args=[self.session.id, occurrence.id]),
            {'choice_id': expensive_choice.id}
        )
        
        # Should redirect back to event detail
        self.assertEqual(response.status_code, 302)
        
        # Event should not be acknowledged due to insufficient funds
        occurrence.refresh_from_db()
        self.assertFalse(occurrence.is_acknowledged)
        self.assertIsNone(occurrence.player_response)
    
    def test_events_history_view(self):
        """Test the events history view"""
        # Create some historical events
        EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=4,
            triggered_year=2024,
            status='completed',
            is_acknowledged=True
        )
        
        EventOccurrence.objects.create(
            session=self.session,
            event=self.event,
            triggered_month=5,
            triggered_year=2024,
            status='active',
            is_acknowledged=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('random_events:event_history', args=[self.session.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Innovation Breakthrough')
        self.assertIn('events', response.context)
    
    def test_view_requires_session_ownership(self):
        """Test that views require session ownership"""
        # Create another user's session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_session = GameSession.objects.create(
            user=other_user,
            name='Other Session',
            balance=Decimal('50000.00')
        )
        
        # Try to access other user's events
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('random_events:dashboard', args=[other_session.id])
        )
        
        # Should return 404 (not found) due to ownership check
        self.assertEqual(response.status_code, 404)
    
    def test_login_required_for_views(self):
        """Test that views require authentication"""
        response = self.client.get(
            reverse('random_events:dashboard', args=[self.session.id])
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))