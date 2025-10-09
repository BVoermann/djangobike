"""
Business Strategy Engine - Processes R&D, Marketing, and Sustainability systems
"""
from django.db import transaction
from decimal import Decimal
import random
from .models import (
    ResearchProject, ResearchBenefit, MarketingCampaign, CampaignEffect,
    SustainabilityProfile, SustainabilityInitiative, BusinessStrategy,
    CompetitiveAnalysis
)
from finance.models import Transaction


class BusinessStrategyEngine:
    """Engine to process all business strategy systems"""
    
    def __init__(self, session):
        self.session = session
    
    def process_monthly_business_strategy(self):
        """Process all business strategy activities for the month"""
        with transaction.atomic():
            # Initialize business strategy if not exists
            self._ensure_business_strategy_exists()
            
            # Process R&D investments and projects
            self._process_rd_monthly()
            
            # Process marketing campaigns
            self._process_marketing_monthly()
            
            # Process sustainability initiatives
            self._process_sustainability_monthly()
            
            # Update competitive positioning
            self._update_competitive_analysis()
            
            # Update overall business strategy metrics
            self._update_business_strategy_metrics()
    
    def _ensure_business_strategy_exists(self):
        """Ensure BusinessStrategy and SustainabilityProfile exist for session"""
        business_strategy, created = BusinessStrategy.objects.get_or_create(
            session=self.session,
            defaults={
                'rd_monthly_budget': Decimal('5000'),
                'marketing_monthly_budget': Decimal('5000'),
                'sustainability_monthly_budget': Decimal('2000'),
            }
        )
        
        sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
            session=self.session,
            defaults={
                'sustainability_score': 50.0,
                'eco_certification_level': 0,
            }
        )
        
        return business_strategy, sustainability_profile
    
    def _process_rd_monthly(self):
        """Process R&D projects monthly"""
        business_strategy = BusinessStrategy.objects.get(session=self.session)
        monthly_rd_budget = business_strategy.rd_monthly_budget
        
        # Get active R&D projects
        active_projects = ResearchProject.objects.filter(
            session=self.session,
            status='active'
        )
        
        total_rd_spending = Decimal('0')
        
        for project in active_projects:
            if monthly_rd_budget <= 0:
                break
            
            # Calculate monthly investment for this project
            required_investment = project.get_monthly_investment_requirement()
            available_investment = min(required_investment, monthly_rd_budget)
            
            if available_investment > 0:
                # Invest in project
                project.invest_monthly(available_investment)
                total_rd_spending += available_investment
                monthly_rd_budget -= available_investment
                
                # Check if project is completed
                if project.status == 'completed':
                    project.complete_project(
                        self.session.current_month,
                        self.session.current_year
                    )
                    self._create_project_completion_transaction(project, available_investment)
                else:
                    self._create_rd_investment_transaction(project, available_investment)
        
        # Update total R&D investment
        business_strategy.total_rd_investment += total_rd_spending
        business_strategy.save()
        
        # Deduct from session balance
        if total_rd_spending > 0:
            self.session.balance -= total_rd_spending
            self.session.save()
    
    def _process_marketing_monthly(self):
        """Process marketing campaigns monthly"""
        business_strategy = BusinessStrategy.objects.get(session=self.session)
        monthly_marketing_budget = business_strategy.marketing_monthly_budget
        
        # Get active marketing campaigns
        active_campaigns = MarketingCampaign.objects.filter(
            session=self.session,
            status='active'
        )
        
        total_marketing_spending = Decimal('0')
        
        for campaign in active_campaigns:
            if monthly_marketing_budget <= 0:
                break
            
            # Process campaign monthly effects
            campaign_effect = campaign.process_monthly_effects()
            
            # Calculate spending for this campaign
            monthly_spend = min(campaign.monthly_spend, monthly_marketing_budget)
            
            if monthly_spend > 0:
                total_marketing_spending += monthly_spend
                monthly_marketing_budget -= monthly_spend
                
                # Create transaction for marketing spend
                self._create_marketing_transaction(campaign, monthly_spend)
        
        # Update total marketing investment
        business_strategy.total_marketing_investment += total_marketing_spending
        business_strategy.save()
        
        # Deduct from session balance
        if total_marketing_spending > 0:
            self.session.balance -= total_marketing_spending
            self.session.save()
    
    def _process_sustainability_monthly(self):
        """Process sustainability initiatives monthly"""
        business_strategy = BusinessStrategy.objects.get(session=self.session)
        sustainability_profile = SustainabilityProfile.objects.get(session=self.session)
        monthly_sustainability_budget = business_strategy.sustainability_monthly_budget
        
        # Get active sustainability initiatives
        active_initiatives = SustainabilityInitiative.objects.filter(
            session=self.session,
            status='active'
        )
        
        total_sustainability_spending = Decimal('0')
        
        for initiative in active_initiatives:
            if monthly_sustainability_budget <= 0:
                break
            
            # Calculate monthly investment for this initiative
            remaining_cost = initiative.total_cost - initiative.invested_amount
            monthly_investment = min(
                remaining_cost / max(1, initiative.months_remaining),
                monthly_sustainability_budget
            )
            
            if monthly_investment > 0:
                # Invest in initiative
                initiative.invested_amount += monthly_investment
                initiative.months_remaining = max(0, initiative.months_remaining - 1)
                
                total_sustainability_spending += monthly_investment
                monthly_sustainability_budget -= monthly_investment
                
                # Check if initiative is completed
                if (initiative.invested_amount >= initiative.total_cost or 
                    initiative.months_remaining <= 0):
                    initiative.complete_initiative(
                        self.session.current_month,
                        self.session.current_year
                    )
                    self._create_sustainability_completion_transaction(initiative, monthly_investment)
                else:
                    initiative.save()
                    self._create_sustainability_investment_transaction(initiative, monthly_investment)
        
        # Add ongoing sustainability costs
        ongoing_costs = sustainability_profile.sustainability_investment_monthly
        total_sustainability_spending += ongoing_costs
        
        # Update sustainability profile monthly
        sustainability_profile.update_sustainability_score()
        
        # Update total sustainability investment
        business_strategy.total_sustainability_investment += total_sustainability_spending
        business_strategy.save()
        
        # Deduct from session balance
        if total_sustainability_spending > 0:
            self.session.balance -= total_sustainability_spending
            self.session.save()
            
            if ongoing_costs > 0:
                Transaction.objects.create(
                    session=self.session,
                    transaction_type='expense',
                    category='Nachhaltigkeit',
                    amount=ongoing_costs,
                    description='Laufende Nachhaltigkeitskosten',
                    month=self.session.current_month,
                    year=self.session.current_year
                )
    
    def _update_competitive_analysis(self):
        """Update monthly competitive analysis"""
        business_strategy = BusinessStrategy.objects.get(session=self.session)
        sustainability_profile = SustainabilityProfile.objects.get(session=self.session)
        
        # Get or create competitive analysis for current month
        competitive_analysis, created = CompetitiveAnalysis.objects.get_or_create(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year,
            defaults={
                'market_share_estimate': 10.0,
                'brand_recognition_level': 1,
                'customer_satisfaction_score': 5.0,
            }
        )
        
        # Update competitive metrics based on business strategy investments
        # R&D competitiveness
        competitive_analysis.innovation_competitiveness = min(10.0, business_strategy.innovation_advantage)
        
        # Marketing competitiveness (brand strength)
        competitive_analysis.brand_recognition_level = min(10, int(business_strategy.brand_strength / 10) + 1)
        
        # Sustainability competitiveness
        competitive_analysis.sustainability_competitiveness = sustainability_profile.sustainability_score / 10
        
        # Simulate market intelligence with some randomness
        competitive_analysis.competitor_rd_activity = max(0, min(100, 
            competitive_analysis.competitor_rd_activity + random.uniform(-5, 5)))
        competitive_analysis.competitor_marketing_intensity = max(0, min(100,
            competitive_analysis.competitor_marketing_intensity + random.uniform(-5, 5)))
        competitive_analysis.market_sustainability_trend = max(0, min(100,
            competitive_analysis.market_sustainability_trend + random.uniform(-2, 3)))  # Slight upward trend
        
        competitive_analysis.save()
    
    def _update_business_strategy_metrics(self):
        """Update overall business strategy performance metrics"""
        business_strategy = BusinessStrategy.objects.get(session=self.session)
        sustainability_profile = SustainabilityProfile.objects.get(session=self.session)
        
        # Update innovation advantage based on completed R&D projects
        research_benefits = ResearchBenefit.objects.filter(
            session=self.session,
            is_active=True
        )
        
        total_innovation_bonus = sum(
            benefit.production_efficiency_bonus + benefit.quality_bonus + benefit.cost_reduction_bonus
            for benefit in research_benefits
        )
        business_strategy.innovation_advantage = total_innovation_bonus
        
        # Update brand strength based on marketing campaigns
        recent_campaign_effects = CampaignEffect.objects.filter(
            session=self.session,
            year=self.session.current_year
        )
        
        total_brand_boost = sum(effect.brand_awareness_boost for effect in recent_campaign_effects)
        business_strategy.brand_strength = min(100.0, total_brand_boost)
        
        # Update sustainability reputation
        business_strategy.sustainability_reputation = sustainability_profile.sustainability_score
        
        business_strategy.save()
    
    def _create_rd_investment_transaction(self, project, amount):
        """Create transaction record for R&D investment"""
        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Forschung & Entwicklung',
            amount=amount,
            description=f'F&E Investment: {project.name}',
            month=self.session.current_month,
            year=self.session.current_year
        )
    
    def _create_project_completion_transaction(self, project, amount):
        """Create transaction record for completed R&D project"""
        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Forschung & Entwicklung',
            amount=amount,
            description=f'F&E Projekt abgeschlossen: {project.name}',
            month=self.session.current_month,
            year=self.session.current_year
        )
    
    def _create_marketing_transaction(self, campaign, amount):
        """Create transaction record for marketing spend"""
        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Marketing',
            amount=amount,
            description=f'Marketing Kampagne: {campaign.name}',
            month=self.session.current_month,
            year=self.session.current_year
        )
    
    def _create_sustainability_investment_transaction(self, initiative, amount):
        """Create transaction record for sustainability investment"""
        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Nachhaltigkeit',
            amount=amount,
            description=f'Nachhaltigkeits-Initiative: {initiative.name}',
            month=self.session.current_month,
            year=self.session.current_year
        )
    
    def _create_sustainability_completion_transaction(self, initiative, amount):
        """Create transaction record for completed sustainability initiative"""
        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Nachhaltigkeit',
            amount=amount,
            description=f'Nachhaltigkeits-Initiative abgeschlossen: {initiative.name}',
            month=self.session.current_month,
            year=self.session.current_year
        )
    
    def get_rd_production_bonuses(self):
        """Get production bonuses from completed R&D projects"""
        research_benefits = ResearchBenefit.objects.filter(
            session=self.session,
            is_active=True
        )
        
        total_efficiency_bonus = sum(benefit.production_efficiency_bonus for benefit in research_benefits)
        total_quality_bonus = sum(benefit.quality_bonus for benefit in research_benefits)
        total_cost_reduction = sum(benefit.cost_reduction_bonus for benefit in research_benefits)
        
        return {
            'efficiency_bonus': total_efficiency_bonus,
            'quality_bonus': total_quality_bonus,
            'cost_reduction': total_cost_reduction,
        }
    
    def get_marketing_demand_bonuses(self):
        """Get demand bonuses from active marketing campaigns"""
        active_campaigns = MarketingCampaign.objects.filter(
            session=self.session,
            status='active'
        )
        
        total_demand_boost = sum(campaign.immediate_demand_boost for campaign in active_campaigns)
        total_price_tolerance = sum(campaign.price_premium_tolerance for campaign in active_campaigns)
        
        return {
            'demand_boost': total_demand_boost,
            'price_tolerance': total_price_tolerance,
        }
    
    def get_sustainability_effects(self):
        """Get sustainability effects on customer demand and pricing"""
        try:
            sustainability_profile = SustainabilityProfile.objects.get(session=self.session)
            return {
                'demand_modifier': sustainability_profile.calculate_customer_demand_modifier(),
                'price_premium': sustainability_profile.calculate_price_premium_tolerance(),
                'eco_appeal': sustainability_profile.eco_customer_appeal,
                'brand_reputation': sustainability_profile.brand_reputation_bonus,
            }
        except SustainabilityProfile.DoesNotExist:
            return {
                'demand_modifier': 1.0,
                'price_premium': 0.0,
                'eco_appeal': 0.0,
                'brand_reputation': 0.0,
            }
    
    def get_combined_business_effects(self):
        """Get combined effects of all business strategy systems"""
        rd_effects = self.get_rd_production_bonuses()
        marketing_effects = self.get_marketing_demand_bonuses()
        sustainability_effects = self.get_sustainability_effects()
        
        return {
            'production': rd_effects,
            'marketing': marketing_effects,
            'sustainability': sustainability_effects,
            'combined_demand_modifier': (
                (1.0 + marketing_effects['demand_boost'] / 100) *
                sustainability_effects['demand_modifier']
            ),
            'combined_cost_reduction': rd_effects['cost_reduction'] / 100,
            'combined_quality_bonus': rd_effects['quality_bonus'] / 100,
        }


def create_predefined_rd_projects(session):
    """Create a set of predefined R&D projects for new sessions"""
    predefined_projects = [
        {
            'name': 'Automatisierte Produktion',
            'project_type': 'automation',
            'description': 'Entwicklung automatisierter Produktionslinien zur Effizienzsteigerung',
            'total_investment_required': Decimal('50000'),
            'duration_months': 8,
            'production_efficiency_bonus': 15.0,
            'cost_reduction_bonus': 10.0,
        },
        {
            'name': 'Leichtbaurahmen-Technologie',
            'project_type': 'materials',
            'description': 'Entwicklung fortschrittlicher Leichtbaumaterialien für Fahrradrahmen',
            'total_investment_required': Decimal('35000'),
            'duration_months': 6,
            'quality_bonus': 20.0,
            'sustainability_bonus': 10.0,
        },
        {
            'name': 'Smart E-Bike System',
            'project_type': 'new_component',
            'description': 'Entwicklung intelligenter E-Bike Steuerungssysteme',
            'total_investment_required': Decimal('75000'),
            'duration_months': 12,
            'quality_bonus': 25.0,
            'production_efficiency_bonus': 5.0,
        },
        {
            'name': 'Nachhaltige Lackierung',
            'project_type': 'sustainability',
            'description': 'Entwicklung umweltfreundlicher Lackierungsverfahren',
            'total_investment_required': Decimal('25000'),
            'duration_months': 4,
            'sustainability_bonus': 15.0,
            'cost_reduction_bonus': 5.0,
        },
        {
            'name': 'Qualitätskontroll-KI',
            'project_type': 'quality',
            'description': 'KI-basierte Qualitätskontrolle zur Fehlererkennung',
            'total_investment_required': Decimal('40000'),
            'duration_months': 6,
            'quality_bonus': 30.0,
            'production_efficiency_bonus': 10.0,
        },
    ]
    
    created_projects = []
    for project_data in predefined_projects:
        project = ResearchProject.objects.create(
            session=session,
            name=project_data['name'],
            project_type=project_data['project_type'],
            description=project_data['description'],
            total_investment_required=project_data['total_investment_required'],
            duration_months=project_data['duration_months'],
            months_remaining=project_data['duration_months'],
            production_efficiency_bonus=project_data.get('production_efficiency_bonus', 0.0),
            quality_bonus=project_data.get('quality_bonus', 0.0),
            cost_reduction_bonus=project_data.get('cost_reduction_bonus', 0.0),
            sustainability_bonus=project_data.get('sustainability_bonus', 0.0),
        )
        created_projects.append(project)
    
    return created_projects


def create_predefined_marketing_campaigns(session):
    """Create predefined marketing campaign templates"""
    predefined_campaigns = [
        {
            'name': 'Frühjahrskampagne',
            'campaign_type': 'seasonal',
            'target_segment': 'all',
            'description': 'Saisonale Marketingkampagne für den Frühling',
            'total_budget': Decimal('15000'),
            'duration_months': 3,
            'immediate_demand_boost': 8.0,
            'brand_awareness_boost': 5.0,
        },
        {
            'name': 'Nachhaltigkeit im Fokus',
            'campaign_type': 'sustainability',
            'target_segment': 'eco_conscious',
            'description': 'Bewerbung unserer nachhaltigen Praktiken',
            'total_budget': Decimal('20000'),
            'duration_months': 4,
            'immediate_demand_boost': 12.0,
            'brand_awareness_boost': 8.0,
            'price_premium_tolerance': 5.0,
        },
        {
            'name': 'Premium E-Bike Launch',
            'campaign_type': 'product_launch',
            'target_segment': 'premium',
            'description': 'Markteinführung neuer Premium E-Bikes',
            'total_budget': Decimal('25000'),
            'duration_months': 2,
            'immediate_demand_boost': 15.0,
            'brand_awareness_boost': 10.0,
            'price_premium_tolerance': 8.0,
        },
        {
            'name': 'Social Media Boost',
            'campaign_type': 'social_media',
            'target_segment': 'urban',
            'description': 'Verstärkte Social Media Präsenz',
            'total_budget': Decimal('10000'),
            'duration_months': 6,
            'immediate_demand_boost': 5.0,
            'brand_awareness_boost': 12.0,
        },
    ]
    
    created_campaigns = []
    for campaign_data in predefined_campaigns:
        campaign = MarketingCampaign.objects.create(
            session=session,
            name=campaign_data['name'],
            campaign_type=campaign_data['campaign_type'],
            target_segment=campaign_data['target_segment'],
            description=campaign_data['description'],
            total_budget=campaign_data['total_budget'],
            duration_months=campaign_data['duration_months'],
            months_remaining=campaign_data['duration_months'],
            monthly_spend=campaign_data['total_budget'] / campaign_data['duration_months'],
            immediate_demand_boost=campaign_data.get('immediate_demand_boost', 0.0),
            brand_awareness_boost=campaign_data.get('brand_awareness_boost', 0.0),
            price_premium_tolerance=campaign_data.get('price_premium_tolerance', 0.0),
        )
        created_campaigns.append(campaign)
    
    return created_campaigns


def create_predefined_sustainability_initiatives(session):
    """Create predefined sustainability initiatives"""
    sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
        session=session,
        defaults={'sustainability_score': 50.0}
    )
    
    predefined_initiatives = [
        {
            'name': 'Solaranlage Installation',
            'initiative_type': 'renewable_energy',
            'description': 'Installation von Solarpanels auf dem Fabrikdach',
            'total_cost': Decimal('30000'),
            'implementation_months': 3,
            'renewable_energy_bonus': 25.0,
            'sustainability_score_bonus': 15.0,
            'monthly_cost': Decimal('100'),  # Maintenance
            'requires_ongoing_investment': True,
        },
        {
            'name': 'Abfallreduktionsprogramm',
            'initiative_type': 'waste_reduction',
            'description': 'Umfassendes Programm zur Abfallreduktion',
            'total_cost': Decimal('15000'),
            'implementation_months': 2,
            'waste_reduction_bonus': 3.0,
            'sustainability_score_bonus': 10.0,
        },
        {
            'name': 'Lokale Lieferantennetzwerk',
            'initiative_type': 'local_sourcing',
            'description': 'Aufbau eines lokalen Lieferantennetzwerks',
            'total_cost': Decimal('20000'),
            'implementation_months': 4,
            'local_sourcing_bonus': 30.0,
            'sustainability_score_bonus': 12.0,
        },
        {
            'name': 'Umweltzertifizierung ISO 14001',
            'initiative_type': 'certification',
            'description': 'Erlangung der ISO 14001 Umweltzertifizierung',
            'total_cost': Decimal('25000'),
            'implementation_months': 6,
            'certification_level_bonus': 2,
            'sustainability_score_bonus': 20.0,
            'monthly_cost': Decimal('200'),  # Ongoing compliance
            'requires_ongoing_investment': True,
        },
    ]
    
    created_initiatives = []
    for initiative_data in predefined_initiatives:
        initiative = SustainabilityInitiative.objects.create(
            sustainability_profile=sustainability_profile,
            session=session,
            name=initiative_data['name'],
            initiative_type=initiative_data['initiative_type'],
            description=initiative_data['description'],
            total_cost=initiative_data['total_cost'],
            implementation_months=initiative_data['implementation_months'],
            months_remaining=initiative_data['implementation_months'],
            renewable_energy_bonus=initiative_data.get('renewable_energy_bonus', 0.0),
            waste_reduction_bonus=initiative_data.get('waste_reduction_bonus', 0.0),
            local_sourcing_bonus=initiative_data.get('local_sourcing_bonus', 0.0),
            certification_level_bonus=initiative_data.get('certification_level_bonus', 0),
            sustainability_score_bonus=initiative_data.get('sustainability_score_bonus', 0.0),
            monthly_cost=initiative_data.get('monthly_cost', Decimal('0')),
            requires_ongoing_investment=initiative_data.get('requires_ongoing_investment', False),
        )
        created_initiatives.append(initiative)
    
    return created_initiatives