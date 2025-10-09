from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class ResearchProject(models.Model):
    """Research & Development projects with time delays and benefits"""
    
    PROJECT_TYPES = [
        ('efficiency', 'Production Efficiency'),
        ('quality', 'Quality Improvement'),
        ('sustainability', 'Sustainability Innovation'),
        ('new_component', 'New Component Development'),
        ('cost_reduction', 'Cost Reduction'),
        ('automation', 'Automation Technology'),
        ('materials', 'Advanced Materials'),
        ('design', 'Design Innovation'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    description = models.TextField()
    
    # Investment and timing
    total_investment_required = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_investment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Time tracking
    duration_months = models.IntegerField()  # Total duration
    months_remaining = models.IntegerField()
    start_month = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    completion_month = models.IntegerField(null=True, blank=True)
    completion_year = models.IntegerField(null=True, blank=True)
    
    # Status and effects
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    progress_percentage = models.FloatField(default=0.0)
    
    # Benefits (applied when completed)
    production_efficiency_bonus = models.FloatField(default=0.0)  # % reduction in production time
    quality_bonus = models.FloatField(default=0.0)  # % improvement in quality
    cost_reduction_bonus = models.FloatField(default=0.0)  # % reduction in production cost
    sustainability_bonus = models.FloatField(default=0.0)  # sustainability points
    
    # Target specifics (optional - if project targets specific bike types or components)
    target_bike_types = models.ManyToManyField('bikeshop.BikeType', blank=True)
    target_components = models.ManyToManyField('bikeshop.Component', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_monthly_investment_requirement(self):
        """Calculate monthly investment needed to complete on time"""
        if self.months_remaining <= 0:
            return Decimal('0')
        remaining_investment = self.total_investment_required - self.invested_amount
        return remaining_investment / self.months_remaining
    
    def can_afford_monthly_investment(self, session_balance):
        """Check if session can afford the monthly investment"""
        return session_balance >= self.get_monthly_investment_requirement()
    
    def invest_monthly(self, amount):
        """Invest amount and update progress"""
        self.invested_amount += amount
        self.progress_percentage = min(100.0, (float(self.invested_amount) / float(self.total_investment_required)) * 100)
        
        if self.invested_amount >= self.total_investment_required:
            self.status = 'completed'
            self.months_remaining = 0
        else:
            self.months_remaining = max(0, self.months_remaining - 1)
        
        self.save()
    
    def complete_project(self, current_month, current_year):
        """Mark project as completed and apply benefits"""
        self.status = 'completed'
        self.completion_month = current_month
        self.completion_year = current_year
        self.progress_percentage = 100.0
        self.save()
        
        # Create research benefit record
        ResearchBenefit.objects.create(
            session=self.session,
            research_project=self,
            production_efficiency_bonus=self.production_efficiency_bonus,
            quality_bonus=self.quality_bonus,
            cost_reduction_bonus=self.cost_reduction_bonus,
            sustainability_bonus=self.sustainability_bonus,
            activation_month=current_month,
            activation_year=current_year
        )


class ResearchBenefit(models.Model):
    """Active research benefits that affect production"""
    
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    research_project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE)
    
    production_efficiency_bonus = models.FloatField(default=0.0)
    quality_bonus = models.FloatField(default=0.0)
    cost_reduction_bonus = models.FloatField(default=0.0)
    sustainability_bonus = models.FloatField(default=0.0)
    
    activation_month = models.IntegerField()
    activation_year = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Benefits from {self.research_project.name}"


class MarketingCampaign(models.Model):
    """Marketing and advertising campaigns"""
    
    CAMPAIGN_TYPES = [
        ('brand_awareness', 'Brand Awareness'),
        ('product_launch', 'Product Launch'),
        ('seasonal', 'Seasonal Campaign'),
        ('sustainability', 'Sustainability Marketing'),
        ('social_media', 'Social Media Campaign'),
        ('traditional', 'Traditional Advertising'),
        ('influencer', 'Influencer Marketing'),
        ('event_sponsorship', 'Event Sponsorship'),
    ]
    
    TARGET_SEGMENTS = [
        ('all', 'All Segments'),
        ('cheap', 'Budget Segment'),
        ('standard', 'Standard Segment'),
        ('premium', 'Premium Segment'),
        ('eco_conscious', 'Eco-Conscious Customers'),
        ('performance', 'Performance Enthusiasts'),
        ('urban', 'Urban Commuters'),
        ('recreational', 'Recreational Riders'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    target_segment = models.CharField(max_length=20, choices=TARGET_SEGMENTS)
    description = models.TextField()
    
    # Investment and timing
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Campaign duration
    duration_months = models.IntegerField()
    months_remaining = models.IntegerField()
    start_month = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_month = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Effects (immediate and long-term)
    immediate_demand_boost = models.FloatField(default=0.0)  # % increase in demand this month
    brand_awareness_boost = models.FloatField(default=0.0)  # long-term brand recognition
    customer_loyalty_bonus = models.FloatField(default=0.0)  # repeat customer rate
    price_premium_tolerance = models.FloatField(default=0.0)  # customers accept higher prices
    
    # Target markets and products
    target_markets = models.ManyToManyField('sales.Market', blank=True)
    target_bike_types = models.ManyToManyField('bikeshop.BikeType', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def activate_campaign(self, current_month, current_year):
        """Start the campaign"""
        self.status = 'active'
        self.start_month = current_month
        self.start_year = current_year
        self.save()
    
    def process_monthly_effects(self):
        """Process monthly campaign effects"""
        if self.status == 'active' and self.months_remaining > 0:
            # Spend monthly budget
            monthly_spend = min(self.monthly_spend, self.total_budget - self.spent_amount)
            self.spent_amount += monthly_spend
            self.months_remaining -= 1
            
            if self.months_remaining <= 0 or self.spent_amount >= self.total_budget:
                self.status = 'completed'
            
            self.save()
            
            # Create campaign effect record
            return CampaignEffect.objects.create(
                session=self.session,
                campaign=self,
                demand_boost=self.immediate_demand_boost,
                brand_awareness_boost=self.brand_awareness_boost,
                month=self.session.current_month,
                year=self.session.current_year
            )
        return None


class CampaignEffect(models.Model):
    """Track effects of marketing campaigns by month"""
    
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE)
    
    demand_boost = models.FloatField(default=0.0)
    brand_awareness_boost = models.FloatField(default=0.0)
    month = models.IntegerField()
    year = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'campaign', 'month', 'year']


class SustainabilityProfile(models.Model):
    """Track company's sustainability practices and their effects"""
    
    session = models.OneToOneField('bikeshop.GameSession', on_delete=models.CASCADE)
    
    # Core sustainability metrics
    sustainability_score = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    eco_certification_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Material choices impact
    sustainable_materials_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    recycled_materials_usage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    local_supplier_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Production practices
    renewable_energy_usage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    waste_reduction_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    carbon_footprint_reduction = models.FloatField(default=0.0)  # percentage reduction from baseline
    
    # Customer perception effects
    eco_customer_appeal = models.FloatField(default=0.0)  # bonus demand from eco-conscious customers
    premium_eco_pricing = models.FloatField(default=0.0)  # % price premium customers accept for sustainability
    brand_reputation_bonus = models.FloatField(default=0.0)  # overall brand boost
    
    # Penalties and costs
    sustainability_investment_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compliance_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Sustainability Profile - Score: {self.sustainability_score}"
    
    def calculate_customer_demand_modifier(self):
        """Calculate how sustainability affects customer demand"""
        base_modifier = 1.0
        
        # Eco-conscious customers (assume 25% of market)
        eco_boost = (self.sustainability_score / 100) * 0.25 * 1.5  # Up to 37.5% boost from eco customers
        
        # General brand reputation effect (smaller but affects all customers)
        general_boost = (self.sustainability_score / 100) * 0.1  # Up to 10% general boost
        
        # Penalties for low sustainability
        if self.sustainability_score < 30:
            penalty = (30 - self.sustainability_score) / 100 * 0.2  # Up to 6% penalty
            return base_modifier + eco_boost + general_boost - penalty
        
        return base_modifier + eco_boost + general_boost
    
    def calculate_price_premium_tolerance(self):
        """Calculate how much price premium customers accept for sustainability"""
        if self.sustainability_score >= 80:
            return 0.15  # 15% premium for excellent sustainability
        elif self.sustainability_score >= 60:
            return 0.10  # 10% premium for good sustainability
        elif self.sustainability_score >= 40:
            return 0.05  # 5% premium for moderate sustainability
        return 0.0
    
    def update_sustainability_score(self):
        """Recalculate sustainability score based on various factors"""
        score = 0.0
        
        # Material choices (40% of score)
        material_score = (
            self.sustainable_materials_percentage * 0.15 +
            self.recycled_materials_usage * 0.15 +
            self.local_supplier_percentage * 0.10
        )
        
        # Production practices (40% of score)
        production_score = (
            self.renewable_energy_usage * 0.20 +
            (self.waste_reduction_level / 10) * 100 * 0.10 +
            max(0, self.carbon_footprint_reduction) * 0.10
        )
        
        # Certifications and compliance (20% of score)
        certification_score = (self.eco_certification_level / 5) * 20
        
        self.sustainability_score = min(100, material_score + production_score + certification_score)
        
        # Update customer appeal based on new score
        self.eco_customer_appeal = self.calculate_customer_demand_modifier() - 1.0
        self.premium_eco_pricing = self.calculate_price_premium_tolerance()
        self.brand_reputation_bonus = (self.sustainability_score / 100) * 0.1
        
        self.save()


class SustainabilityInitiative(models.Model):
    """Specific sustainability initiatives/investments"""
    
    INITIATIVE_TYPES = [
        ('renewable_energy', 'Renewable Energy Installation'),
        ('waste_reduction', 'Waste Reduction Program'),
        ('sustainable_materials', 'Sustainable Materials Sourcing'),
        ('local_sourcing', 'Local Supplier Development'),
        ('carbon_offset', 'Carbon Offset Programs'),
        ('certification', 'Environmental Certification'),
        ('employee_training', 'Sustainability Training'),
        ('packaging', 'Sustainable Packaging'),
        ('transport_optimization', 'Green Transportation'),
        ('facility_upgrade', 'Green Facility Upgrades'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sustainability_profile = models.ForeignKey(SustainabilityProfile, on_delete=models.CASCADE, related_name='initiatives')
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200)
    initiative_type = models.CharField(max_length=30, choices=INITIATIVE_TYPES)
    description = models.TextField()
    
    # Investment
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ongoing costs
    
    # Timeline
    implementation_months = models.IntegerField()
    months_remaining = models.IntegerField()
    start_month = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    completion_month = models.IntegerField(null=True, blank=True)
    completion_year = models.IntegerField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Benefits when completed
    sustainability_score_bonus = models.FloatField(default=0.0)
    renewable_energy_bonus = models.FloatField(default=0.0)
    waste_reduction_bonus = models.FloatField(default=0.0)
    sustainable_materials_bonus = models.FloatField(default=0.0)
    local_sourcing_bonus = models.FloatField(default=0.0)
    certification_level_bonus = models.IntegerField(default=0)
    
    # Potential penalties if not maintained
    requires_ongoing_investment = models.BooleanField(default=False)
    penalty_if_neglected = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def complete_initiative(self, current_month, current_year):
        """Complete the initiative and apply benefits"""
        self.status = 'completed'
        self.completion_month = current_month
        self.completion_year = current_year
        self.save()
        
        # Apply benefits to sustainability profile
        profile = self.sustainability_profile
        profile.renewable_energy_usage += self.renewable_energy_bonus
        profile.waste_reduction_level += self.waste_reduction_bonus
        profile.sustainable_materials_percentage += self.sustainable_materials_bonus
        profile.local_supplier_percentage += self.local_sourcing_bonus
        profile.eco_certification_level += self.certification_level_bonus
        
        # Add ongoing costs if required
        if self.requires_ongoing_investment:
            profile.sustainability_investment_monthly += self.monthly_cost
        
        # Recalculate sustainability score
        profile.update_sustainability_score()


class BusinessStrategy(models.Model):
    """Overall business strategy settings and performance tracking"""
    
    session = models.OneToOneField('bikeshop.GameSession', on_delete=models.CASCADE)
    
    # Strategy focus areas (weights from 0-100, should sum to 100)
    rd_focus_percentage = models.FloatField(default=25.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    marketing_focus_percentage = models.FloatField(default=25.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    sustainability_focus_percentage = models.FloatField(default=25.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    operational_focus_percentage = models.FloatField(default=25.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Budget allocations
    rd_monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    marketing_monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    sustainability_monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    
    # Performance tracking
    total_rd_investment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_marketing_investment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sustainability_investment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Competitive advantages gained
    innovation_advantage = models.FloatField(default=0.0)  # from R&D
    brand_strength = models.FloatField(default=0.0)  # from marketing
    sustainability_reputation = models.FloatField(default=0.0)  # from sustainability
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Business Strategy for {self.session.name}"
    
    def validate_focus_distribution(self):
        """Ensure focus percentages sum to 100"""
        total = (self.rd_focus_percentage + self.marketing_focus_percentage + 
                self.sustainability_focus_percentage + self.operational_focus_percentage)
        return abs(total - 100.0) < 0.1
    
    def get_monthly_strategy_effects(self):
        """Calculate monthly effects of current strategy"""
        effects = {
            'rd_efficiency': self.innovation_advantage * 0.1,  # 10% of innovation advantage
            'marketing_reach': self.brand_strength * 0.05,  # 5% demand boost per brand strength point
            'sustainability_appeal': self.sustainability_reputation * 0.03,  # 3% eco-customer appeal
            'operational_cost_reduction': self.operational_focus_percentage * 0.002,  # 0.2% cost reduction per percentage point
        }
        return effects


class CompetitiveAnalysis(models.Model):
    """Track competitive positioning and market intelligence"""
    
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    
    # Market position
    market_share_estimate = models.FloatField(default=10.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    brand_recognition_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    customer_satisfaction_score = models.FloatField(default=5.0, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Competitive advantages/disadvantages
    price_competitiveness = models.FloatField(default=0.0)  # relative to market average
    quality_competitiveness = models.FloatField(default=0.0)
    innovation_competitiveness = models.FloatField(default=0.0)
    sustainability_competitiveness = models.FloatField(default=0.0)
    
    # Market intelligence (updated monthly)
    competitor_rd_activity = models.FloatField(default=50.0)  # market average R&D activity level
    competitor_marketing_intensity = models.FloatField(default=50.0)  # market average marketing spend
    market_sustainability_trend = models.FloatField(default=50.0)  # how important sustainability is becoming
    
    month = models.IntegerField()
    year = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']
    
    def __str__(self):
        return f"Competitive Analysis {self.month}/{self.year} - Market Share: {self.market_share_estimate}%"