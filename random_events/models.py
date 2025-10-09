from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import json


class EventCategory(models.Model):
    """Categories for different types of random events"""
    
    CATEGORY_TYPES = [
        ('innovation', 'Product Innovation'),
        ('market', 'Market Changes'),
        ('competition', 'Competition'),
        ('promotion', 'Promotional Opportunities'),
        ('supply_chain', 'Supply Chain Disruptions'),
        ('regulatory', 'Regulatory Changes'),
        ('economic', 'Economic Events'),
        ('environmental', 'Environmental Events'),
        ('technology', 'Technology Breakthroughs'),
        ('crisis', 'Crisis Events'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField()
    base_probability = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Base probability percentage for this category per month"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Event Categories"
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class RandomEvent(models.Model):
    """Definition of a random event that can occur"""
    
    SEVERITY_LEVELS = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    
    DURATION_TYPES = [
        ('instant', 'Instant Effect'),
        ('temporary', 'Temporary (1-3 months)'),
        ('medium_term', 'Medium Term (3-6 months)'),
        ('permanent', 'Permanent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name='events')
    
    # Event definition
    title = models.CharField(max_length=200)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='moderate')
    duration_type = models.CharField(max_length=20, choices=DURATION_TYPES, default='temporary')
    
    # Probability and conditions
    probability_weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Multiplier for category base probability"
    )
    min_game_month = models.IntegerField(
        default=1,
        help_text="Minimum game month before this event can trigger"
    )
    max_game_month = models.IntegerField(
        null=True, blank=True,
        help_text="Maximum game month after which this event won't trigger"
    )
    
    # Prerequisites and exclusions
    requires_session_balance_min = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Minimum session balance required for this event"
    )
    requires_session_balance_max = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Maximum session balance for this event (for crisis events)"
    )
    mutually_exclusive_with = models.ManyToManyField(
        'self', blank=True, symmetrical=True,
        help_text="Events that cannot occur in the same month"
    )
    
    # Effects (JSON fields for flexibility)
    financial_effects = models.JSONField(
        default=dict,
        help_text="Financial impacts: income, expenses, one_time_cost, etc."
    )
    production_effects = models.JSONField(
        default=dict,
        help_text="Production impacts: efficiency, cost_modifier, quality_bonus, etc."
    )
    market_effects = models.JSONField(
        default=dict,
        help_text="Market impacts: demand_modifier, new_segments, price_changes, etc."
    )
    regulatory_effects = models.JSONField(
        default=dict,
        help_text="Regulatory impacts: banned_components, required_certifications, etc."
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"
    
    def get_effective_probability(self, session):
        """Calculate effective probability for this event given session state"""
        base_prob = self.category.base_probability * self.probability_weight
        
        # Check balance requirements
        if self.requires_session_balance_min and session.balance < self.requires_session_balance_min:
            return 0.0
        if self.requires_session_balance_max and session.balance > self.requires_session_balance_max:
            return 0.0
        
        # Check game month constraints
        total_months = (session.current_year - 2024) * 12 + session.current_month
        if total_months < self.min_game_month:
            return 0.0
        if self.max_game_month and total_months > self.max_game_month:
            return 0.0
        
        return base_prob


class RegulationTimeline(models.Model):
    """Timeline for regulatory changes that affect the game"""
    
    REGULATION_TYPES = [
        ('component_ban', 'Component Ban'),
        ('technology_restriction', 'Technology Restriction'),
        ('certification_requirement', 'New Certification Requirement'),
        ('environmental_standard', 'Environmental Standard'),
        ('safety_regulation', 'Safety Regulation'),
        ('trade_restriction', 'Trade Restriction'),
        ('subsidy_program', 'Government Subsidy Program'),
        ('tax_change', 'Tax Policy Change'),
    ]
    
    STATUS_CHOICES = [
        ('announced', 'Announced'),
        ('grace_period', 'Grace Period'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Regulation details
    title = models.CharField(max_length=200)
    description = models.TextField()
    regulation_type = models.CharField(max_length=30, choices=REGULATION_TYPES)
    
    # Timeline
    announcement_month = models.IntegerField(help_text="Game month when regulation is announced")
    announcement_year = models.IntegerField(help_text="Game year when regulation is announced")
    implementation_month = models.IntegerField(help_text="Game month when regulation takes effect")
    implementation_year = models.IntegerField(help_text="Game year when regulation takes effect")
    expiration_month = models.IntegerField(
        null=True, blank=True,
        help_text="Game month when regulation expires (if applicable)"
    )
    expiration_year = models.IntegerField(
        null=True, blank=True,
        help_text="Game year when regulation expires (if applicable)"
    )
    
    # Effects
    affected_components = models.ManyToManyField('bikeshop.Component', blank=True)
    affected_bike_types = models.ManyToManyField('bikeshop.BikeType', blank=True)
    affected_suppliers = models.ManyToManyField('bikeshop.Supplier', blank=True)
    
    # Regulatory details (JSON for flexibility)
    restrictions = models.JSONField(
        default=dict,
        help_text="Specific restrictions: banned_items, required_certifications, etc."
    )
    compliance_requirements = models.JSONField(
        default=dict,
        help_text="What companies need to do to comply"
    )
    penalties = models.JSONField(
        default=dict,
        help_text="Penalties for non-compliance"
    )
    benefits = models.JSONField(
        default=dict,
        help_text="Benefits for compliance (subsidies, tax breaks, etc.)"
    )
    
    # Metadata
    is_global = models.BooleanField(
        default=True,
        help_text="Whether this regulation affects all sessions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='announced')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['announcement_year', 'announcement_month']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def get_months_until_implementation(self, current_month, current_year):
        """Get number of months until regulation takes effect"""
        current_total = (current_year - 2024) * 12 + current_month
        implementation_total = (self.implementation_year - 2024) * 12 + self.implementation_month
        return implementation_total - current_total
    
    def is_in_grace_period(self, current_month, current_year):
        """Check if regulation is in grace period (announced but not yet active)"""
        current_total = (current_year - 2024) * 12 + current_month
        announcement_total = (self.announcement_year - 2024) * 12 + self.announcement_month
        implementation_total = (self.implementation_year - 2024) * 12 + self.implementation_month
        
        return announcement_total <= current_total < implementation_total
    
    def is_active(self, current_month, current_year):
        """Check if regulation is currently active"""
        current_total = (current_year - 2024) * 12 + current_month
        implementation_total = (self.implementation_year - 2024) * 12 + self.implementation_month
        
        if current_total < implementation_total:
            return False
        
        if self.expiration_month and self.expiration_year:
            expiration_total = (self.expiration_year - 2024) * 12 + self.expiration_month
            return current_total < expiration_total
        
        return True


class EventOccurrence(models.Model):
    """Record of when random events actually occurred in game sessions"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    event = models.ForeignKey(RandomEvent, on_delete=models.CASCADE)
    
    # Occurrence details
    triggered_month = models.IntegerField()
    triggered_year = models.IntegerField()
    expires_month = models.IntegerField(null=True, blank=True)
    expires_year = models.IntegerField(null=True, blank=True)
    
    # Player interaction
    player_response = models.JSONField(
        default=dict,
        help_text="How the player chose to respond to this event"
    )
    is_acknowledged = models.BooleanField(default=False)
    
    # Effects tracking
    applied_effects = models.JSONField(
        default=dict,
        help_text="Track which effects have been applied"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session', 'event', 'triggered_month', 'triggered_year']
        ordering = ['-triggered_year', '-triggered_month']
    
    def __str__(self):
        return f"{self.event.title} in {self.session.name} ({self.triggered_month}/{self.triggered_year})"
    
    def is_expired(self, current_month, current_year):
        """Check if this event occurrence has expired"""
        if not self.expires_month or not self.expires_year:
            return False
        
        current_total = (current_year - 2024) * 12 + current_month
        expiry_total = (self.expires_year - 2024) * 12 + self.expires_month
        
        return current_total >= expiry_total
    
    def get_months_remaining(self, current_month, current_year):
        """Get number of months until this event expires"""
        if not self.expires_month or not self.expires_year:
            return None
        
        current_total = (current_year - 2024) * 12 + current_month
        expiry_total = (self.expires_year - 2024) * 12 + self.expires_month
        
        return max(0, expiry_total - current_total)


class RegulationCompliance(models.Model):
    """Track session compliance with regulatory requirements"""
    
    COMPLIANCE_LEVELS = [
        ('non_compliant', 'Non-Compliant'),
        ('partial', 'Partially Compliant'),
        ('compliant', 'Compliant'),
        ('exemplary', 'Exemplary Compliance'),
    ]
    
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    regulation = models.ForeignKey(RegulationTimeline, on_delete=models.CASCADE)
    
    compliance_level = models.CharField(max_length=20, choices=COMPLIANCE_LEVELS, default='non_compliant')
    compliance_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage compliance score"
    )
    
    # Compliance actions taken
    actions_taken = models.JSONField(
        default=list,
        help_text="List of compliance actions the session has taken"
    )
    
    # Financial impact
    compliance_costs = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Total cost spent on compliance"
    )
    penalties_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Total penalties paid for non-compliance"
    )
    benefits_received = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Total benefits received for compliance"
    )
    
    # Tracking
    last_assessment_month = models.IntegerField()
    last_assessment_year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session', 'regulation']
    
    def __str__(self):
        return f"{self.session.name} - {self.regulation.title} ({self.get_compliance_level_display()})"


class EventChoice(models.Model):
    """Multiple choice options for events that require player decisions"""
    
    event = models.ForeignKey(RandomEvent, on_delete=models.CASCADE, related_name='choices')
    
    choice_text = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    # Effects of choosing this option
    financial_effects = models.JSONField(default=dict)
    production_effects = models.JSONField(default=dict)
    market_effects = models.JSONField(default=dict)
    regulatory_effects = models.JSONField(default=dict)
    
    # Requirements
    required_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Minimum balance required to choose this option"
    )
    required_research = models.ManyToManyField(
        'business_strategy.ResearchProject', blank=True,
        help_text="Research projects required to unlock this choice"
    )
    
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default choice if player doesn't respond"
    )
    
    order = models.IntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.event.title} - {self.choice_text[:50]}"


class MarketOpportunity(models.Model):
    """Special market opportunities that can be triggered by events"""
    
    OPPORTUNITY_TYPES = [
        ('new_segment', 'New Market Segment'),
        ('export_market', 'Export Market Opening'),
        ('government_contract', 'Government Contract'),
        ('bulk_order', 'Large Bulk Order'),
        ('partnership', 'Strategic Partnership'),
        ('technology_license', 'Technology Licensing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('bikeshop.GameSession', on_delete=models.CASCADE)
    triggering_event = models.ForeignKey(
        EventOccurrence, on_delete=models.CASCADE, null=True, blank=True
    )
    
    # Opportunity details
    title = models.CharField(max_length=200)
    description = models.TextField()
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    
    # Timeline
    available_from_month = models.IntegerField()
    available_from_year = models.IntegerField()
    expires_month = models.IntegerField()
    expires_year = models.IntegerField()
    
    # Requirements
    required_investment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    required_bike_types = models.ManyToManyField('bikeshop.BikeType', blank=True)
    required_capabilities = models.JSONField(
        default=list,
        help_text="Required capabilities (certifications, research, etc.)"
    )
    
    # Rewards
    potential_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_effects = models.JSONField(
        default=dict,
        help_text="Long-term market effects if opportunity is taken"
    )
    
    # Status
    is_accepted = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} for {self.session.name}"
    
    def is_available(self, current_month, current_year):
        """Check if opportunity is currently available"""
        current_total = (current_year - 2024) * 12 + current_month
        available_total = (self.available_from_year - 2024) * 12 + self.available_from_month
        expires_total = (self.expires_year - 2024) * 12 + self.expires_month
        
        return available_total <= current_total < expires_total
    
    def get_months_remaining(self, current_month, current_year):
        """Get number of months until opportunity expires"""
        current_total = (current_year - 2024) * 12 + current_month
        expires_total = (self.expires_year - 2024) * 12 + self.expires_month
        
        return max(0, expires_total - current_total)