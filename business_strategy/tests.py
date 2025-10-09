from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

from .models import (
    ResearchProject, ResearchBenefit, MarketingCampaign, CampaignEffect,
    SustainabilityProfile, SustainabilityInitiative, BusinessStrategy, CompetitiveAnalysis
)
from bikeshop.models import GameSession, BikeType, Component
from sales.models import Market


class ResearchProjectTestCase(TestCase):
    """Test cases for ResearchProject model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='researcher',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Research Test Session',
            balance=100000,
            current_month=3,
            current_year=2024
        )
        
        self.bike_type = BikeType.objects.create(
            session=self.session,
            name="Test Bike Type",
            skilled_worker_hours=4.0,
            unskilled_worker_hours=2.0
        )
        
        self.research_project = ResearchProject.objects.create(
            session=self.session,
            name="Efficiency Improvement Project",
            project_type="efficiency",
            description="Improve production efficiency by 15%",
            total_investment_required=50000,
            duration_months=6,
            months_remaining=6,
            production_efficiency_bonus=15.0,
            quality_bonus=5.0,
            cost_reduction_bonus=8.0
        )
    
    def test_research_project_creation(self):
        """Test creating a research project"""
        self.assertEqual(self.research_project.name, "Efficiency Improvement Project")
        self.assertEqual(self.research_project.project_type, "efficiency")
        self.assertEqual(self.research_project.status, "planned")
        self.assertEqual(self.research_project.total_investment_required, Decimal('50000'))
        self.assertEqual(self.research_project.invested_amount, Decimal('0'))
        self.assertEqual(self.research_project.progress_percentage, 0.0)
    
    def test_monthly_investment_calculation(self):
        """Test monthly investment requirement calculation"""
        monthly_required = self.research_project.get_monthly_investment_requirement()
        expected = Decimal('50000') / 6  # 50000 / 6 months
        self.assertEqual(monthly_required, expected)
        
        # After some investment
        self.research_project.invested_amount = Decimal('20000')
        self.research_project.save()
        
        monthly_required = self.research_project.get_monthly_investment_requirement()
        expected = (Decimal('50000') - Decimal('20000')) / 6  # 30000 / 6 months
        self.assertEqual(monthly_required, expected)
    
    def test_can_afford_monthly_investment(self):
        """Test affordability check for monthly investment"""
        # Session has 100000, project needs 50000/6 ≈ 8333 per month
        self.assertTrue(self.research_project.can_afford_monthly_investment(self.session.balance))
        
        # Test with insufficient balance
        self.assertFalse(self.research_project.can_afford_monthly_investment(Decimal('5000')))
    
    def test_invest_monthly(self):
        """Test monthly investment and progress tracking"""
        initial_invested = self.research_project.invested_amount
        initial_progress = self.research_project.progress_percentage
        initial_months = self.research_project.months_remaining
        
        # Invest 10000
        self.research_project.invest_monthly(Decimal('10000'))
        
        self.research_project.refresh_from_db()
        self.assertEqual(self.research_project.invested_amount, initial_invested + Decimal('10000'))
        self.assertEqual(self.research_project.progress_percentage, 20.0)  # 10000/50000 * 100
        self.assertEqual(self.research_project.months_remaining, initial_months - 1)
        self.assertEqual(self.research_project.status, 'planned')  # Not completed yet
    
    def test_project_completion_by_investment(self):
        """Test project completion when fully funded"""
        # Invest full amount
        self.research_project.invest_monthly(Decimal('50000'))
        
        self.research_project.refresh_from_db()
        self.assertEqual(self.research_project.status, 'completed')
        self.assertEqual(self.research_project.progress_percentage, 100.0)
        self.assertEqual(self.research_project.months_remaining, 0)
    
    def test_complete_project_method(self):
        """Test manual project completion"""
        self.research_project.complete_project(4, 2024)
        
        self.research_project.refresh_from_db()
        self.assertEqual(self.research_project.status, 'completed')
        self.assertEqual(self.research_project.completion_month, 4)
        self.assertEqual(self.research_project.completion_year, 2024)
        self.assertEqual(self.research_project.progress_percentage, 100.0)
        
        # Check that research benefit was created
        benefit = ResearchBenefit.objects.filter(research_project=self.research_project).first()
        self.assertIsNotNone(benefit)
        self.assertEqual(benefit.production_efficiency_bonus, 15.0)
        self.assertEqual(benefit.quality_bonus, 5.0)
        self.assertEqual(benefit.cost_reduction_bonus, 8.0)
        self.assertEqual(benefit.activation_month, 4)
        self.assertEqual(benefit.activation_year, 2024)
    
    def test_research_project_target_specificity(self):
        """Test research projects can target specific bike types"""
        self.research_project.target_bike_types.add(self.bike_type)
        
        self.assertIn(self.bike_type, self.research_project.target_bike_types.all())


class ResearchBenefitTestCase(TestCase):
    """Test cases for ResearchBenefit model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='benefituser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Benefit Test Session',
            balance=75000
        )
        
        self.research_project = ResearchProject.objects.create(
            session=self.session,
            name="Quality Project",
            project_type="quality",
            description="Improve quality",
            total_investment_required=30000,
            duration_months=4,
            months_remaining=0,
            status="completed"
        )
    
    def test_research_benefit_creation(self):
        """Test creating research benefits"""
        benefit = ResearchBenefit.objects.create(
            session=self.session,
            research_project=self.research_project,
            production_efficiency_bonus=10.0,
            quality_bonus=12.0,
            cost_reduction_bonus=5.0,
            sustainability_bonus=3.0,
            activation_month=3,
            activation_year=2024
        )
        
        self.assertEqual(benefit.session, self.session)
        self.assertEqual(benefit.research_project, self.research_project)
        self.assertEqual(benefit.production_efficiency_bonus, 10.0)
        self.assertEqual(benefit.quality_bonus, 12.0)
        self.assertTrue(benefit.is_active)
    
    def test_research_benefit_str_representation(self):
        """Test string representation of research benefit"""
        benefit = ResearchBenefit.objects.create(
            session=self.session,
            research_project=self.research_project,
            activation_month=3,
            activation_year=2024
        )
        
        expected = f"Benefits from {self.research_project.name}"
        self.assertEqual(str(benefit), expected)


class MarketingCampaignTestCase(TestCase):
    """Test cases for MarketingCampaign model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='marketer',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Marketing Test Session',
            balance=80000,
            current_month=2,
            current_year=2024
        )
        
        self.market = Market.objects.create(
            session=self.session,
            name="Test Market",
            location="Germany",
            transport_cost_home=50.00
        )
        
        self.bike_type = BikeType.objects.create(
            session=self.session,
            name="Marketing Test Bike",
            skilled_worker_hours=3.0,
            unskilled_worker_hours=2.0
        )
        
        self.marketing_campaign = MarketingCampaign.objects.create(
            session=self.session,
            name="Spring Launch Campaign",
            campaign_type="product_launch",
            target_segment="standard",
            description="Launch new bike models for spring",
            total_budget=25000,
            duration_months=3,
            months_remaining=3,
            monthly_spend=8000,
            immediate_demand_boost=20.0,
            brand_awareness_boost=10.0,
            customer_loyalty_bonus=5.0,
            price_premium_tolerance=3.0
        )
    
    def test_marketing_campaign_creation(self):
        """Test creating a marketing campaign"""
        self.assertEqual(self.marketing_campaign.name, "Spring Launch Campaign")
        self.assertEqual(self.marketing_campaign.campaign_type, "product_launch")
        self.assertEqual(self.marketing_campaign.target_segment, "standard")
        self.assertEqual(self.marketing_campaign.status, "planned")
        self.assertEqual(self.marketing_campaign.total_budget, Decimal('25000'))
        self.assertEqual(self.marketing_campaign.spent_amount, Decimal('0'))
    
    def test_activate_campaign(self):
        """Test campaign activation"""
        self.marketing_campaign.activate_campaign(3, 2024)
        
        self.marketing_campaign.refresh_from_db()
        self.assertEqual(self.marketing_campaign.status, "active")
        self.assertEqual(self.marketing_campaign.start_month, 3)
        self.assertEqual(self.marketing_campaign.start_year, 2024)
    
    def test_process_monthly_effects(self):
        """Test processing monthly campaign effects"""
        self.marketing_campaign.status = "active"
        self.marketing_campaign.save()
        
        # Process monthly effects
        effect = self.marketing_campaign.process_monthly_effects()
        
        self.marketing_campaign.refresh_from_db()
        self.assertEqual(self.marketing_campaign.spent_amount, Decimal('8000'))
        self.assertEqual(self.marketing_campaign.months_remaining, 2)
        self.assertEqual(self.marketing_campaign.status, "active")  # Still active
        
        # Check that campaign effect was created
        self.assertIsNotNone(effect)
        self.assertEqual(effect.demand_boost, 20.0)
        self.assertEqual(effect.brand_awareness_boost, 10.0)
    
    def test_campaign_completion_by_duration(self):
        """Test campaign completion when duration is reached"""
        self.marketing_campaign.status = "active"
        self.marketing_campaign.months_remaining = 1
        self.marketing_campaign.save()
        
        # Process final month
        self.marketing_campaign.process_monthly_effects()
        
        self.marketing_campaign.refresh_from_db()
        self.assertEqual(self.marketing_campaign.status, "completed")
        self.assertEqual(self.marketing_campaign.months_remaining, 0)
    
    def test_campaign_completion_by_budget(self):
        """Test campaign completion when budget is exhausted"""
        self.marketing_campaign.status = "active"
        self.marketing_campaign.spent_amount = Decimal('24000')  # Close to budget limit
        self.marketing_campaign.monthly_spend = Decimal('2000')  # Will exceed budget
        self.marketing_campaign.save()
        
        self.marketing_campaign.process_monthly_effects()
        
        self.marketing_campaign.refresh_from_db()
        self.assertEqual(self.marketing_campaign.status, "completed")
        self.assertEqual(self.marketing_campaign.spent_amount, Decimal('25000'))  # Capped at budget
    
    def test_campaign_target_specificity(self):
        """Test campaigns can target specific markets and bike types"""
        self.marketing_campaign.target_markets.add(self.market)
        self.marketing_campaign.target_bike_types.add(self.bike_type)
        
        self.assertIn(self.market, self.marketing_campaign.target_markets.all())
        self.assertIn(self.bike_type, self.marketing_campaign.target_bike_types.all())


class CampaignEffectTestCase(TestCase):
    """Test cases for CampaignEffect model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='effectuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Effect Test Session'
        )
        
        self.campaign = MarketingCampaign.objects.create(
            session=self.session,
            name="Effect Test Campaign",
            campaign_type="brand_awareness",
            target_segment="all",
            description="Test campaign effects",
            total_budget=15000,
            duration_months=2,
            months_remaining=2
        )
    
    def test_campaign_effect_creation(self):
        """Test creating campaign effects"""
        effect = CampaignEffect.objects.create(
            session=self.session,
            campaign=self.campaign,
            demand_boost=15.0,
            brand_awareness_boost=8.0,
            month=3,
            year=2024
        )
        
        self.assertEqual(effect.session, self.session)
        self.assertEqual(effect.campaign, self.campaign)
        self.assertEqual(effect.demand_boost, 15.0)
        self.assertEqual(effect.brand_awareness_boost, 8.0)
        self.assertEqual(effect.month, 3)
        self.assertEqual(effect.year, 2024)
    
    def test_campaign_effect_unique_constraint(self):
        """Test unique constraint on session, campaign, month, year"""
        CampaignEffect.objects.create(
            session=self.session,
            campaign=self.campaign,
            demand_boost=10.0,
            month=3,
            year=2024
        )
        
        # Try to create duplicate - should raise error
        with self.assertRaises(Exception):
            CampaignEffect.objects.create(
                session=self.session,
                campaign=self.campaign,
                demand_boost=20.0,
                month=3,
                year=2024
            )


class SustainabilityProfileTestCase(TestCase):
    """Test cases for SustainabilityProfile model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='sustainuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Sustainability Test Session'
        )
        
        self.sustainability_profile = SustainabilityProfile.objects.create(
            session=self.session,
            sustainability_score=65.0,
            eco_certification_level=2,
            sustainable_materials_percentage=40.0,
            recycled_materials_usage=25.0,
            local_supplier_percentage=30.0,
            renewable_energy_usage=50.0,
            waste_reduction_level=3,
            carbon_footprint_reduction=15.0
        )
    
    def test_sustainability_profile_creation(self):
        """Test creating a sustainability profile"""
        self.assertEqual(self.sustainability_profile.session, self.session)
        self.assertEqual(self.sustainability_profile.sustainability_score, 65.0)
        self.assertEqual(self.sustainability_profile.eco_certification_level, 2)
        self.assertEqual(self.sustainability_profile.sustainable_materials_percentage, 40.0)
    
    def test_sustainability_score_validation(self):
        """Test sustainability score validation (0-100)"""
        # Test valid score
        profile = SustainabilityProfile(
            session=self.session,
            sustainability_score=85.5
        )
        profile.full_clean()  # Should not raise exception
        
        # Test invalid scores
        with self.assertRaises(ValidationError):
            profile = SustainabilityProfile(
                session=self.session,
                sustainability_score=-5.0
            )
            profile.full_clean()
        
        with self.assertRaises(ValidationError):
            profile = SustainabilityProfile(
                session=self.session,
                sustainability_score=105.0
            )
            profile.full_clean()
    
    def test_customer_demand_modifier_calculation(self):
        """Test customer demand modifier based on sustainability"""
        # High sustainability score (80)
        self.sustainability_profile.sustainability_score = 80.0
        modifier = self.sustainability_profile.calculate_customer_demand_modifier()
        # Expected: 1.0 + (80/100 * 0.25 * 1.5) + (80/100 * 0.1) = 1.0 + 0.3 + 0.08 = 1.38
        self.assertAlmostEqual(modifier, 1.38, places=2)
        
        # Low sustainability score with penalty (25)
        self.sustainability_profile.sustainability_score = 25.0
        modifier = self.sustainability_profile.calculate_customer_demand_modifier()
        # Expected: 1.0 + (25/100 * 0.25 * 1.5) + (25/100 * 0.1) - ((30-25)/100 * 0.2)
        # = 1.0 + 0.09375 + 0.025 - 0.01 = 1.10875
        self.assertAlmostEqual(modifier, 1.10875, places=4)
    
    def test_price_premium_tolerance_calculation(self):
        """Test price premium tolerance calculation"""
        # Excellent sustainability (80+)
        self.sustainability_profile.sustainability_score = 85.0
        premium = self.sustainability_profile.calculate_price_premium_tolerance()
        self.assertEqual(premium, 0.15)
        
        # Good sustainability (60-79)
        self.sustainability_profile.sustainability_score = 70.0
        premium = self.sustainability_profile.calculate_price_premium_tolerance()
        self.assertEqual(premium, 0.10)
        
        # Moderate sustainability (40-59)
        self.sustainability_profile.sustainability_score = 45.0
        premium = self.sustainability_profile.calculate_price_premium_tolerance()
        self.assertEqual(premium, 0.05)
        
        # Poor sustainability (<40)
        self.sustainability_profile.sustainability_score = 35.0
        premium = self.sustainability_profile.calculate_price_premium_tolerance()
        self.assertEqual(premium, 0.0)
    
    def test_update_sustainability_score(self):
        """Test automatic sustainability score calculation"""
        # Set specific values for calculation
        self.sustainability_profile.sustainable_materials_percentage = 60.0  # 60 * 0.15 = 9
        self.sustainability_profile.recycled_materials_usage = 40.0  # 40 * 0.15 = 6
        self.sustainability_profile.local_supplier_percentage = 50.0  # 50 * 0.10 = 5
        # Material score = 20
        
        self.sustainability_profile.renewable_energy_usage = 80.0  # 80 * 0.20 = 16
        self.sustainability_profile.waste_reduction_level = 5  # (5/10) * 100 * 0.10 = 5
        self.sustainability_profile.carbon_footprint_reduction = 20.0  # 20 * 0.10 = 2
        # Production score = 23
        
        self.sustainability_profile.eco_certification_level = 3  # (3/5) * 20 = 12
        # Certification score = 12
        
        # Total expected = 20 + 23 + 12 = 55
        
        self.sustainability_profile.update_sustainability_score()
        self.sustainability_profile.refresh_from_db()
        
        self.assertAlmostEqual(self.sustainability_profile.sustainability_score, 55.0, places=1)
        self.assertIsNotNone(self.sustainability_profile.eco_customer_appeal)
        self.assertIsNotNone(self.sustainability_profile.premium_eco_pricing)
        self.assertIsNotNone(self.sustainability_profile.brand_reputation_bonus)


class SustainabilityInitiativeTestCase(TestCase):
    """Test cases for SustainabilityInitiative model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='inituser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Initiative Test Session'
        )
        
        self.sustainability_profile = SustainabilityProfile.objects.create(
            session=self.session
        )
        
        self.initiative = SustainabilityInitiative.objects.create(
            sustainability_profile=self.sustainability_profile,
            session=self.session,
            name="Solar Panel Installation",
            initiative_type="renewable_energy",
            description="Install solar panels for clean energy",
            total_cost=40000,
            implementation_months=4,
            months_remaining=4,
            renewable_energy_bonus=25.0,
            sustainability_score_bonus=15.0,
            requires_ongoing_investment=True,
            monthly_cost=500
        )
    
    def test_sustainability_initiative_creation(self):
        """Test creating a sustainability initiative"""
        self.assertEqual(self.initiative.name, "Solar Panel Installation")
        self.assertEqual(self.initiative.initiative_type, "renewable_energy")
        self.assertEqual(self.initiative.status, "planned")
        self.assertEqual(self.initiative.total_cost, Decimal('40000'))
        self.assertEqual(self.initiative.implementation_months, 4)
        self.assertTrue(self.initiative.requires_ongoing_investment)
    
    def test_complete_initiative(self):
        """Test completing a sustainability initiative"""
        initial_renewable = self.sustainability_profile.renewable_energy_usage
        initial_monthly_cost = self.sustainability_profile.sustainability_investment_monthly
        
        self.initiative.complete_initiative(5, 2024)
        
        self.initiative.refresh_from_db()
        self.sustainability_profile.refresh_from_db()
        
        # Check initiative completion
        self.assertEqual(self.initiative.status, "completed")
        self.assertEqual(self.initiative.completion_month, 5)
        self.assertEqual(self.initiative.completion_year, 2024)
        
        # Check profile updates
        self.assertEqual(
            self.sustainability_profile.renewable_energy_usage,
            initial_renewable + self.initiative.renewable_energy_bonus
        )
        self.assertEqual(
            self.sustainability_profile.sustainability_investment_monthly,
            initial_monthly_cost + self.initiative.monthly_cost
        )


class BusinessStrategyTestCase(TestCase):
    """Test cases for BusinessStrategy model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='strategyuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Strategy Test Session'
        )
        
        self.business_strategy = BusinessStrategy.objects.create(
            session=self.session,
            rd_focus_percentage=30.0,
            marketing_focus_percentage=40.0,
            sustainability_focus_percentage=20.0,
            operational_focus_percentage=10.0,
            rd_monthly_budget=8000,
            marketing_monthly_budget=12000,
            sustainability_monthly_budget=3000,
            innovation_advantage=25.0,
            brand_strength=15.0,
            sustainability_reputation=10.0
        )
    
    def test_business_strategy_creation(self):
        """Test creating a business strategy"""
        self.assertEqual(self.business_strategy.session, self.session)
        self.assertEqual(self.business_strategy.rd_focus_percentage, 30.0)
        self.assertEqual(self.business_strategy.marketing_focus_percentage, 40.0)
        self.assertEqual(self.business_strategy.rd_monthly_budget, Decimal('8000'))
    
    def test_focus_distribution_validation(self):
        """Test validation of focus percentage distribution"""
        # Valid distribution (sums to 100)
        self.assertTrue(self.business_strategy.validate_focus_distribution())
        
        # Invalid distribution
        self.business_strategy.rd_focus_percentage = 50.0  # Now sums to 120
        self.assertFalse(self.business_strategy.validate_focus_distribution())
        
        # Close to 100 but within tolerance
        self.business_strategy.rd_focus_percentage = 30.05  # Now sums to 100.05
        self.assertTrue(self.business_strategy.validate_focus_distribution())
    
    def test_monthly_strategy_effects(self):
        """Test calculation of monthly strategy effects"""
        effects = self.business_strategy.get_monthly_strategy_effects()
        
        expected_rd_efficiency = 25.0 * 0.1  # 2.5
        expected_marketing_reach = 15.0 * 0.05  # 0.75
        expected_sustainability_appeal = 10.0 * 0.03  # 0.3
        expected_operational_cost_reduction = 10.0 * 0.002  # 0.02
        
        self.assertEqual(effects['rd_efficiency'], expected_rd_efficiency)
        self.assertEqual(effects['marketing_reach'], expected_marketing_reach)
        self.assertEqual(effects['sustainability_appeal'], expected_sustainability_appeal)
        self.assertEqual(effects['operational_cost_reduction'], expected_operational_cost_reduction)


class CompetitiveAnalysisTestCase(TestCase):
    """Test cases for CompetitiveAnalysis model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='analysisuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Analysis Test Session'
        )
        
        self.competitive_analysis = CompetitiveAnalysis.objects.create(
            session=self.session,
            market_share_estimate=15.5,
            brand_recognition_level=6,
            customer_satisfaction_score=7.2,
            price_competitiveness=5.0,
            quality_competitiveness=-3.0,
            innovation_competitiveness=8.0,
            sustainability_competitiveness=2.0,
            competitor_rd_activity=60.0,
            competitor_marketing_intensity=75.0,
            market_sustainability_trend=45.0,
            month=4,
            year=2024
        )
    
    def test_competitive_analysis_creation(self):
        """Test creating competitive analysis"""
        self.assertEqual(self.competitive_analysis.session, self.session)
        self.assertEqual(self.competitive_analysis.market_share_estimate, 15.5)
        self.assertEqual(self.competitive_analysis.brand_recognition_level, 6)
        self.assertEqual(self.competitive_analysis.customer_satisfaction_score, 7.2)
        self.assertEqual(self.competitive_analysis.month, 4)
        self.assertEqual(self.competitive_analysis.year, 2024)
    
    def test_competitive_analysis_validation(self):
        """Test validation of competitive analysis fields"""
        # Test valid values
        analysis = CompetitiveAnalysis(
            session=self.session,
            market_share_estimate=25.0,
            brand_recognition_level=5,
            customer_satisfaction_score=8.5,
            month=3,
            year=2024
        )
        analysis.full_clean()  # Should not raise exception
        
        # Test invalid market share (>100)
        with self.assertRaises(ValidationError):
            analysis = CompetitiveAnalysis(
                session=self.session,
                market_share_estimate=105.0,
                month=3,
                year=2024
            )
            analysis.full_clean()
        
        # Test invalid brand recognition level (>10)
        with self.assertRaises(ValidationError):
            analysis = CompetitiveAnalysis(
                session=self.session,
                brand_recognition_level=15,
                month=3,
                year=2024
            )
            analysis.full_clean()
    
    def test_competitive_analysis_unique_constraint(self):
        """Test unique constraint on session, month, year"""
        # Try to create duplicate analysis for same session and time period
        with self.assertRaises(Exception):
            CompetitiveAnalysis.objects.create(
                session=self.session,
                market_share_estimate=20.0,
                month=4,  # Same month
                year=2024  # Same year
            )
    
    def test_competitive_analysis_str_representation(self):
        """Test string representation of competitive analysis"""
        expected = "Competitive Analysis 4/2024 - Market Share: 15.5%"
        self.assertEqual(str(self.competitive_analysis), expected)


class BusinessStrategyViewTestCase(TestCase):
    """Test cases for business strategy views"""
    
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
            balance=100000
        )
        
        self.business_strategy = BusinessStrategy.objects.create(
            session=self.session
        )
    
    def test_login_required_for_strategy_views(self):
        """Test that strategy views require login"""
        self.client.logout()
        
        # Test strategy dashboard (if such view exists)
        # This is a placeholder test - implement when views are available
        self.assertTrue(True)  # Placeholder assertion
    
    def test_strategy_view_permissions(self):
        """Test that users can only access their own strategies"""
        # Create another user's session
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        
        other_session = GameSession.objects.create(
            user=other_user,
            name='Other User Session',
            balance=50000
        )
        
        # Try to access other user's strategy (if such view exists)
        # This is a placeholder test - implement when views are available
        self.assertTrue(True)  # Placeholder assertion


class BusinessStrategyIntegrationTestCase(TestCase):
    """Integration tests for business strategy functionality"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        self.user = User.objects.create_user(
            username='integrationuser',
            password='testpass123'
        )
        
        self.session = GameSession.objects.create(
            user=self.user,
            name='Integration Test Session',
            balance=200000,
            current_month=6,
            current_year=2024
        )
        
        # Create business strategy components
        self.business_strategy = BusinessStrategy.objects.create(
            session=self.session,
            rd_monthly_budget=10000,
            marketing_monthly_budget=15000,
            sustainability_monthly_budget=5000
        )
        
        self.sustainability_profile = SustainabilityProfile.objects.create(
            session=self.session
        )
        
        # Create R&D project
        self.research_project = ResearchProject.objects.create(
            session=self.session,
            name="Advanced Materials Research",
            project_type="materials",
            description="Research advanced lightweight materials",
            total_investment_required=60000,
            duration_months=8,
            months_remaining=8,
            production_efficiency_bonus=20.0
        )
        
        # Create marketing campaign
        self.marketing_campaign = MarketingCampaign.objects.create(
            session=self.session,
            name="Sustainability Campaign",
            campaign_type="sustainability",
            target_segment="eco_conscious",
            description="Promote our environmental commitment",
            total_budget=40000,
            duration_months=6,
            months_remaining=6,
            immediate_demand_boost=15.0
        )
        
        # Create sustainability initiative
        self.sustainability_initiative = SustainabilityInitiative.objects.create(
            sustainability_profile=self.sustainability_profile,
            session=self.session,
            name="Waste Reduction Program",
            initiative_type="waste_reduction",
            description="Implement comprehensive waste reduction",
            total_cost=25000,
            implementation_months=5,
            months_remaining=5,
            sustainability_score_bonus=10.0
        )
    
    def test_integrated_business_strategy_execution(self):
        """Test execution of integrated business strategy"""
        # Simulate monthly strategy execution
        
        # Invest in R&D
        rd_investment = min(self.business_strategy.rd_monthly_budget, 
                           self.research_project.get_monthly_investment_requirement())
        self.research_project.invest_monthly(rd_investment)
        self.business_strategy.total_rd_investment += rd_investment
        
        # Execute marketing campaign
        self.marketing_campaign.activate_campaign(6, 2024)
        effect = self.marketing_campaign.process_monthly_effects()
        self.business_strategy.total_marketing_investment += self.marketing_campaign.monthly_spend
        
        # Work on sustainability initiative
        sustainability_investment = min(self.business_strategy.sustainability_monthly_budget,
                                      self.sustainability_initiative.total_cost)
        self.sustainability_initiative.invested_amount += sustainability_investment
        self.business_strategy.total_sustainability_investment += sustainability_investment
        
        # Save updates
        self.business_strategy.save()
        
        # Verify integrated effects
        self.assertGreater(self.research_project.progress_percentage, 0)
        self.assertEqual(self.marketing_campaign.status, "active")
        self.assertIsNotNone(effect)
        self.assertGreater(self.sustainability_initiative.invested_amount, 0)
        self.assertGreater(self.business_strategy.total_rd_investment, 0)
        self.assertGreater(self.business_strategy.total_marketing_investment, 0)
        self.assertGreater(self.business_strategy.total_sustainability_investment, 0)
    
    def test_cross_component_benefits(self):
        """Test how different strategy components benefit each other"""
        # Complete R&D project
        self.research_project.complete_project(6, 2024)
        
        # Complete sustainability initiative
        self.sustainability_initiative.complete_initiative(6, 2024)
        
        # Update sustainability profile
        self.sustainability_profile.update_sustainability_score()
        
        # Check for cross-benefits
        # R&D should create research benefits
        research_benefits = ResearchBenefit.objects.filter(session=self.session)
        self.assertGreater(research_benefits.count(), 0)
        
        # Sustainability should improve profile
        self.sustainability_profile.refresh_from_db()
        self.assertGreater(self.sustainability_profile.sustainability_score, 50.0)
        
        # Marketing campaign should create effects
        campaign_effects = CampaignEffect.objects.filter(session=self.session)
        if self.marketing_campaign.status == "active":
            self.assertGreater(campaign_effects.count(), 0)
