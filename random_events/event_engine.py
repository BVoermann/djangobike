"""
Random Events Engine - Processes monthly random events and regulatory changes
"""
from django.db import transaction
from decimal import Decimal
import random
import logging
from datetime import datetime
from .models import (
    EventCategory, RandomEvent, EventOccurrence, RegulationTimeline,
    RegulationCompliance, MarketOpportunity, EventChoice
)
from finance.models import Transaction

logger = logging.getLogger(__name__)


class RandomEventsEngine:
    """Engine for processing random events and regulatory changes"""
    
    def __init__(self, session):
        self.session = session
    
    def process_monthly_events(self):
        """Process all random events and regulatory changes for the current month"""
        with transaction.atomic():
            # Process regulatory timeline updates
            self._update_regulatory_status()
            
            # Check for new regulatory announcements
            self._check_regulatory_announcements()
            
            # Process compliance assessments
            self._assess_regulatory_compliance()
            
            # Trigger random events
            triggered_events = self._trigger_random_events()
            
            # Process active event effects
            self._process_active_events()
            
            # Clean up expired events
            self._cleanup_expired_events()
            
            return {
                'triggered_events': triggered_events,
                'active_regulations': self._get_active_regulations(),
                'compliance_status': self._get_compliance_summary()
            }
    
    def _update_regulatory_status(self):
        """Update status of regulations based on current game time"""
        regulations = RegulationTimeline.objects.filter(is_global=True)
        
        for regulation in regulations:
            old_status = regulation.status
            
            if regulation.is_in_grace_period(self.session.current_month, self.session.current_year):
                regulation.status = 'grace_period'
            elif regulation.is_active(self.session.current_month, self.session.current_year):
                regulation.status = 'active'
            elif (regulation.expiration_month and regulation.expiration_year and
                  (self.session.current_year > regulation.expiration_year or 
                   (self.session.current_year == regulation.expiration_year and 
                    self.session.current_month >= regulation.expiration_month))):
                regulation.status = 'expired'
            
            if old_status != regulation.status:
                regulation.save()
                logger.info(f"Regulation {regulation.title} status changed from {old_status} to {regulation.status}")
    
    def _check_regulatory_announcements(self):
        """Check for regulations that should be announced this month"""
        announced_regulations = RegulationTimeline.objects.filter(
            announcement_month=self.session.current_month,
            announcement_year=self.session.current_year,
            status='announced'
        )
        
        for regulation in announced_regulations:
            # Create a regulatory announcement event
            self._create_regulatory_announcement_event(regulation)
            logger.info(f"New regulation announced: {regulation.title}")
    
    def _create_regulatory_announcement_event(self, regulation):
        """Create an event occurrence for a regulatory announcement"""
        # Try to find a regulatory announcement event template
        try:
            from .models import RandomEvent
            regulatory_category = EventCategory.objects.get(category_type='regulatory')
            announcement_event = RandomEvent.objects.filter(
                category=regulatory_category,
                title__icontains='Regulatory Announcement'
            ).first()
            
            if announcement_event:
                # Create custom event occurrence for this regulation
                event_occurrence = EventOccurrence.objects.create(
                    session=self.session,
                    event=announcement_event,
                    triggered_month=self.session.current_month,
                    triggered_year=self.session.current_year,
                    applied_effects={
                        'regulation_id': str(regulation.id),
                        'regulation_title': regulation.title,
                        'implementation_date': f"{regulation.implementation_month}/{regulation.implementation_year}",
                        'grace_period_months': regulation.get_months_until_implementation(
                            self.session.current_month, self.session.current_year
                        )
                    }
                )
                
                # Initialize compliance tracking
                RegulationCompliance.objects.get_or_create(
                    session=self.session,
                    regulation=regulation,
                    defaults={
                        'compliance_level': 'non_compliant',
                        'compliance_score': 0.0,
                        'last_assessment_month': self.session.current_month,
                        'last_assessment_year': self.session.current_year,
                    }
                )
                
                return event_occurrence
        
        except Exception as e:
            logger.error(f"Failed to create regulatory announcement event: {e}")
        
        return None
    
    def _assess_regulatory_compliance(self):
        """Assess session compliance with active regulations"""
        active_regulations = RegulationTimeline.objects.filter(
            status__in=['grace_period', 'active']
        )
        
        for regulation in active_regulations:
            compliance, created = RegulationCompliance.objects.get_or_create(
                session=self.session,
                regulation=regulation,
                defaults={
                    'compliance_level': 'non_compliant',
                    'compliance_score': 0.0,
                    'last_assessment_month': self.session.current_month,
                    'last_assessment_year': self.session.current_year,
                }
            )
            
            # Calculate compliance score
            new_score = self._calculate_compliance_score(regulation)
            
            # Apply penalties or benefits based on compliance
            if regulation.status == 'active':
                self._apply_compliance_effects(compliance, new_score)
            
            # Update compliance record
            compliance.compliance_score = new_score
            compliance.compliance_level = self._get_compliance_level(new_score)
            compliance.last_assessment_month = self.session.current_month
            compliance.last_assessment_year = self.session.current_year
            compliance.save()
    
    def _calculate_compliance_score(self, regulation):
        """Calculate compliance score for a regulation"""
        score = 0.0
        
        if regulation.regulation_type == 'component_ban':
            # Check if session is using banned components
            banned_components = regulation.affected_components.all()
            if banned_components.exists():
                # Check production and inventory for banned components
                from production.models import ProducedBike
                from warehouse.models import ComponentStock
                
                # Check recent production (last 3 months)
                recent_bikes = ProducedBike.objects.filter(
                    session=self.session,
                    production_year=self.session.current_year,
                    production_month__gte=max(1, self.session.current_month - 3)
                )
                
                total_bikes = recent_bikes.count()
                compliant_bikes = total_bikes  # Assume compliant unless proven otherwise
                
                # For now, assume perfect compliance (would need detailed component tracking)
                score = 100.0 if total_bikes == 0 else 80.0
        
        elif regulation.regulation_type == 'environmental_standard':
            # Check sustainability profile
            try:
                from business_strategy.models import SustainabilityProfile
                sustainability_profile = SustainabilityProfile.objects.get(session=self.session)
                
                # Base compliance on sustainability score
                required_score = regulation.compliance_requirements.get('min_sustainability_score', 60)
                if sustainability_profile.sustainability_score >= required_score:
                    score = 100.0
                else:
                    score = (sustainability_profile.sustainability_score / required_score) * 100
                    
            except Exception:
                score = 20.0  # Low compliance if no sustainability profile
        
        elif regulation.regulation_type == 'certification_requirement':
            # Check if session has required certifications
            required_certs = regulation.compliance_requirements.get('required_certifications', [])
            if not required_certs:
                score = 100.0
            else:
                # For now, assume partial compliance
                score = 60.0
        
        else:
            # Default compliance assessment
            score = 70.0
        
        return min(100.0, max(0.0, score))
    
    def _get_compliance_level(self, score):
        """Convert compliance score to compliance level"""
        if score >= 90:
            return 'exemplary'
        elif score >= 70:
            return 'compliant'
        elif score >= 40:
            return 'partial'
        else:
            return 'non_compliant'
    
    def _apply_compliance_effects(self, compliance, new_score):
        """Apply financial effects based on compliance level"""
        regulation = compliance.regulation
        
        # Calculate penalties for non-compliance
        if new_score < 70 and regulation.status == 'active':
            penalty_rate = regulation.penalties.get('monthly_penalty_rate', 0.01)
            base_penalty = Decimal(str(regulation.penalties.get('base_penalty', 5000)))
            
            # Penalty increases with lower compliance
            compliance_factor = max(0.1, (70 - new_score) / 70)
            monthly_penalty = base_penalty * Decimal(str(compliance_factor))
            
            if monthly_penalty > 0:
                self.session.balance -= monthly_penalty
                self.session.save()
                
                compliance.penalties_paid += monthly_penalty
                
                # Create transaction record
                Transaction.objects.create(
                    session=self.session,
                    transaction_type='expense',
                    category='Strafen & Bußgelder',
                    amount=monthly_penalty,
                    description=f'Regulatorische Strafe: {regulation.title}',
                    month=self.session.current_month,
                    year=self.session.current_year
                )
        
        # Apply benefits for good compliance
        elif new_score >= 80:
            benefit_amount = Decimal(str(regulation.benefits.get('compliance_bonus', 0)))
            if benefit_amount > 0:
                self.session.balance += benefit_amount
                self.session.save()
                
                compliance.benefits_received += benefit_amount
                
                # Create transaction record
                Transaction.objects.create(
                    session=self.session,
                    transaction_type='income',
                    category='Regulatorische Vorteile',
                    amount=benefit_amount,
                    description=f'Compliance-Bonus: {regulation.title}',
                    month=self.session.current_month,
                    year=self.session.current_year
                )
    
    def _trigger_random_events(self):
        """Trigger random events based on probability"""
        triggered_events = []
        
        # Get all active event categories
        categories = EventCategory.objects.filter(is_active=True)
        
        for category in categories:
            # Check if this category should trigger an event this month
            if random.random() * 100 < category.base_probability:
                # Get eligible events from this category
                eligible_events = self._get_eligible_events(category)
                
                if eligible_events:
                    # Select event based on weighted probability
                    selected_event = self._select_weighted_event(eligible_events)
                    
                    if selected_event:
                        # Check if event is mutually exclusive with already triggered events
                        if not self._conflicts_with_triggered_events(selected_event, triggered_events):
                            event_occurrence = self._trigger_event(selected_event)
                            if event_occurrence:
                                triggered_events.append(event_occurrence)
        
        return triggered_events
    
    def _get_eligible_events(self, category):
        """Get events from category that are eligible to trigger"""
        events = RandomEvent.objects.filter(
            category=category,
            is_active=True
        )
        
        eligible_events = []
        for event in events:
            if event.get_effective_probability(self.session) > 0:
                # Check if event hasn't occurred recently
                recent_occurrence = EventOccurrence.objects.filter(
                    session=self.session,
                    event=event,
                    triggered_year=self.session.current_year,
                    triggered_month__gte=max(1, self.session.current_month - 6)  # Within last 6 months
                ).exists()
                
                if not recent_occurrence:
                    eligible_events.append(event)
        
        return eligible_events
    
    def _select_weighted_event(self, events):
        """Select an event based on weighted probability"""
        if not events:
            return None
        
        # Calculate total weight
        total_weight = sum(event.probability_weight for event in events)
        
        if total_weight <= 0:
            return random.choice(events)
        
        # Select based on weighted random
        random_value = random.random() * total_weight
        current_weight = 0
        
        for event in events:
            current_weight += event.probability_weight
            if random_value <= current_weight:
                return event
        
        return events[-1]  # Fallback
    
    def _conflicts_with_triggered_events(self, event, triggered_events):
        """Check if event conflicts with already triggered events"""
        triggered_event_objects = [occurrence.event for occurrence in triggered_events]
        
        for triggered_event in triggered_event_objects:
            if event in triggered_event.mutually_exclusive_with.all():
                return True
            if triggered_event in event.mutually_exclusive_with.all():
                return True
        
        return False
    
    def _trigger_event(self, event):
        """Create an event occurrence and apply initial effects"""
        try:
            # Calculate expiration based on duration type
            expires_month, expires_year = self._calculate_event_expiration(event)
            
            # Create event occurrence
            event_occurrence = EventOccurrence.objects.create(
                session=self.session,
                event=event,
                triggered_month=self.session.current_month,
                triggered_year=self.session.current_year,
                expires_month=expires_month,
                expires_year=expires_year,
                applied_effects={}
            )
            
            # Apply immediate effects
            self._apply_event_effects(event_occurrence)
            
            # Create market opportunities if specified
            self._create_market_opportunities(event_occurrence)
            
            logger.info(f"Event triggered: {event.title} for session {self.session.name}")
            
            return event_occurrence
            
        except Exception as e:
            logger.error(f"Failed to trigger event {event.title}: {e}")
            return None
    
    def _calculate_event_expiration(self, event):
        """Calculate when an event expires based on its duration type"""
        current_month = self.session.current_month
        current_year = self.session.current_year
        
        if event.duration_type == 'instant':
            return current_month, current_year
        elif event.duration_type == 'temporary':
            # 1-3 months
            duration = random.randint(1, 3)
        elif event.duration_type == 'medium_term':
            # 3-6 months
            duration = random.randint(3, 6)
        else:  # permanent
            return None, None
        
        expires_month = current_month + duration
        expires_year = current_year
        
        while expires_month > 12:
            expires_month -= 12
            expires_year += 1
        
        return expires_month, expires_year
    
    def _apply_event_effects(self, event_occurrence):
        """Apply the effects of an event occurrence"""
        event = event_occurrence.event
        applied_effects = {}
        
        # Apply financial effects
        if event.financial_effects:
            financial_applied = self._apply_financial_effects(event.financial_effects)
            applied_effects['financial'] = financial_applied
        
        # Apply production effects (store for ongoing application)
        if event.production_effects:
            applied_effects['production'] = event.production_effects
        
        # Apply market effects (store for ongoing application)
        if event.market_effects:
            applied_effects['market'] = event.market_effects
        
        # Apply regulatory effects
        if event.regulatory_effects:
            regulatory_applied = self._apply_regulatory_effects(event.regulatory_effects)
            applied_effects['regulatory'] = regulatory_applied
        
        # Update applied effects
        event_occurrence.applied_effects = applied_effects
        event_occurrence.save()
    
    def _apply_financial_effects(self, financial_effects):
        """Apply financial effects of an event"""
        applied = {}
        
        # One-time income
        if 'one_time_income' in financial_effects:
            amount = Decimal(str(financial_effects['one_time_income']))
            self.session.balance += amount
            applied['one_time_income'] = float(amount)
            
            Transaction.objects.create(
                session=self.session,
                transaction_type='income',
                category='Zufallsereignisse',
                amount=amount,
                description='Einmaliger Ertrag durch Ereignis',
                month=self.session.current_month,
                year=self.session.current_year
            )
        
        # One-time cost
        if 'one_time_cost' in financial_effects:
            amount = Decimal(str(financial_effects['one_time_cost']))
            self.session.balance -= amount
            applied['one_time_cost'] = float(amount)
            
            Transaction.objects.create(
                session=self.session,
                transaction_type='expense',
                category='Zufallsereignisse',
                amount=amount,
                description='Einmalige Kosten durch Ereignis',
                month=self.session.current_month,
                year=self.session.current_year
            )
        
        # Monthly income/expenses are handled in ongoing effects
        if 'monthly_income' in financial_effects:
            applied['monthly_income'] = financial_effects['monthly_income']
        
        if 'monthly_cost' in financial_effects:
            applied['monthly_cost'] = financial_effects['monthly_cost']
        
        self.session.save()
        return applied
    
    def _apply_regulatory_effects(self, regulatory_effects):
        """Apply regulatory effects of an event"""
        applied = {}
        
        # For now, just store the effects to be processed by the regulatory system
        if 'new_regulations' in regulatory_effects:
            applied['new_regulations'] = regulatory_effects['new_regulations']
        
        if 'temporary_exemptions' in regulatory_effects:
            applied['temporary_exemptions'] = regulatory_effects['temporary_exemptions']
        
        return applied
    
    def _create_market_opportunities(self, event_occurrence):
        """Create market opportunities triggered by an event"""
        event = event_occurrence.event
        
        # Check if this event creates market opportunities
        market_effects = event.market_effects
        if not market_effects or 'creates_opportunities' not in market_effects:
            return
        
        opportunities = market_effects['creates_opportunities']
        for opp_data in opportunities:
            try:
                opportunity = MarketOpportunity.objects.create(
                    session=self.session,
                    triggering_event=event_occurrence,
                    title=opp_data.get('title', 'New Market Opportunity'),
                    description=opp_data.get('description', ''),
                    opportunity_type=opp_data.get('type', 'new_segment'),
                    available_from_month=self.session.current_month,
                    available_from_year=self.session.current_year,
                    expires_month=self.session.current_month + opp_data.get('duration', 6),
                    expires_year=self.session.current_year,
                    required_investment=Decimal(str(opp_data.get('required_investment', 0))),
                    potential_revenue=Decimal(str(opp_data.get('potential_revenue', 0))),
                    required_capabilities=opp_data.get('required_capabilities', []),
                    market_effects=opp_data.get('market_effects', {})
                )
                
                # Adjust expiration date if it goes beyond December
                if opportunity.expires_month > 12:
                    opportunity.expires_month -= 12
                    opportunity.expires_year += 1
                    opportunity.save()
                
                logger.info(f"Market opportunity created: {opportunity.title}")
                
            except Exception as e:
                logger.error(f"Failed to create market opportunity: {e}")
    
    def _process_active_events(self):
        """Process ongoing effects of active events"""
        active_events = EventOccurrence.objects.filter(
            session=self.session,
            status='active'
        )
        
        for event_occurrence in active_events:
            # Check if event has expired
            if event_occurrence.is_expired(self.session.current_month, self.session.current_year):
                event_occurrence.status = 'completed'
                event_occurrence.save()
                continue
            
            # Apply ongoing effects
            self._apply_ongoing_effects(event_occurrence)
    
    def _apply_ongoing_effects(self, event_occurrence):
        """Apply ongoing monthly effects of an active event"""
        applied_effects = event_occurrence.applied_effects
        
        # Apply monthly financial effects
        if 'financial' in applied_effects:
            financial = applied_effects['financial']
            
            if 'monthly_income' in financial:
                amount = Decimal(str(financial['monthly_income']))
                self.session.balance += amount
                
                Transaction.objects.create(
                    session=self.session,
                    transaction_type='income',
                    category='Zufallsereignisse',
                    amount=amount,
                    description=f'Monatlicher Ertrag: {event_occurrence.event.title}',
                    month=self.session.current_month,
                    year=self.session.current_year
                )
            
            if 'monthly_cost' in financial:
                amount = Decimal(str(financial['monthly_cost']))
                self.session.balance -= amount
                
                Transaction.objects.create(
                    session=self.session,
                    transaction_type='expense',
                    category='Zufallsereignisse',
                    amount=amount,
                    description=f'Monatliche Kosten: {event_occurrence.event.title}',
                    month=self.session.current_month,
                    year=self.session.current_year
                )
            
            self.session.save()
    
    def _cleanup_expired_events(self):
        """Clean up expired events and opportunities"""
        # Mark expired events as completed
        expired_events = EventOccurrence.objects.filter(
            session=self.session,
            status='active'
        )
        
        for event_occurrence in expired_events:
            if event_occurrence.is_expired(self.session.current_month, self.session.current_year):
                event_occurrence.status = 'completed'
                event_occurrence.save()
        
        # Mark expired market opportunities
        expired_opportunities = MarketOpportunity.objects.filter(
            session=self.session,
            is_accepted=False
        )
        
        for opportunity in expired_opportunities:
            if not opportunity.is_available(self.session.current_month, self.session.current_year):
                # Opportunity expired without being accepted
                pass  # Keep for historical record
    
    def _get_active_regulations(self):
        """Get list of currently active regulations"""
        return RegulationTimeline.objects.filter(
            status__in=['grace_period', 'active']
        )
    
    def _get_compliance_summary(self):
        """Get summary of compliance status"""
        compliances = RegulationCompliance.objects.filter(session=self.session)
        
        summary = {
            'total_regulations': compliances.count(),
            'compliant': compliances.filter(compliance_level__in=['compliant', 'exemplary']).count(),
            'non_compliant': compliances.filter(compliance_level='non_compliant').count(),
            'total_penalties': sum(c.penalties_paid for c in compliances),
            'total_benefits': sum(c.benefits_received for c in compliances),
        }
        
        return summary
    
    def get_production_modifiers(self):
        """Get production modifiers from active events"""
        active_events = EventOccurrence.objects.filter(
            session=self.session,
            status='active'
        )
        
        modifiers = {
            'efficiency_modifier': 1.0,
            'cost_modifier': 1.0,
            'quality_modifier': 1.0,
        }
        
        for event_occurrence in active_events:
            if not event_occurrence.is_expired(self.session.current_month, self.session.current_year):
                production_effects = event_occurrence.applied_effects.get('production', {})
                
                if 'efficiency_modifier' in production_effects:
                    modifiers['efficiency_modifier'] *= production_effects['efficiency_modifier']
                
                if 'cost_modifier' in production_effects:
                    modifiers['cost_modifier'] *= production_effects['cost_modifier']
                
                if 'quality_modifier' in production_effects:
                    modifiers['quality_modifier'] *= production_effects['quality_modifier']
        
        return modifiers
    
    def get_market_modifiers(self):
        """Get market modifiers from active events"""
        active_events = EventOccurrence.objects.filter(
            session=self.session,
            status='active'
        )
        
        modifiers = {
            'demand_modifier': 1.0,
            'price_modifier': 1.0,
            'new_segments': [],
        }
        
        for event_occurrence in active_events:
            if not event_occurrence.is_expired(self.session.current_month, self.session.current_year):
                market_effects = event_occurrence.applied_effects.get('market', {})
                
                if 'demand_modifier' in market_effects:
                    modifiers['demand_modifier'] *= market_effects['demand_modifier']
                
                if 'price_modifier' in market_effects:
                    modifiers['price_modifier'] *= market_effects['price_modifier']
                
                if 'new_segments' in market_effects:
                    modifiers['new_segments'].extend(market_effects['new_segments'])
        
        return modifiers