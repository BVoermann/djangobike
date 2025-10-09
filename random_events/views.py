from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from bikeshop.models import GameSession
from .models import (
    EventOccurrence, RandomEvent, RegulationTimeline, RegulationCompliance,
    MarketOpportunity, EventChoice, EventCategory
)
from .event_engine import RandomEventsEngine
from .event_factory import initialize_all_events_and_regulations


@login_required
def events_dashboard(request, session_id):
    """Main events dashboard showing active events, regulations, and opportunities"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get active events
    active_events = EventOccurrence.objects.filter(
        session=session,
        status='active',
        is_acknowledged=True
    ).select_related('event').order_by('-triggered_year', '-triggered_month')
    
    # Get unacknowledged events (need player attention)
    unacknowledged_events = EventOccurrence.objects.filter(
        session=session,
        status='active',
        is_acknowledged=False
    ).select_related('event').order_by('-triggered_year', '-triggered_month')
    
    # Get active regulations
    current_regulations = RegulationTimeline.objects.filter(
        status__in=['grace_period', 'active']
    ).order_by('implementation_year', 'implementation_month')
    
    # Get compliance status
    compliance_records = RegulationCompliance.objects.filter(
        session=session,
        regulation__status__in=['grace_period', 'active']
    ).select_related('regulation')
    
    # Get available market opportunities
    available_opportunities = MarketOpportunity.objects.filter(
        session=session,
        is_accepted=False
    )
    current_opportunities = [
        opp for opp in available_opportunities 
        if opp.is_available(session.current_month, session.current_year)
    ]
    
    # Get recent event history
    recent_events = EventOccurrence.objects.filter(
        session=session,
        status__in=['completed', 'active']
    ).select_related('event').order_by('-triggered_year', '-triggered_month')[:10]
    
    # Get events engine for modifiers
    events_engine = RandomEventsEngine(session)
    production_modifiers = events_engine.get_production_modifiers()
    market_modifiers = events_engine.get_market_modifiers()
    
    context = {
        'session': session,
        'active_events': active_events,
        'unacknowledged_events': unacknowledged_events,
        'current_regulations': current_regulations,
        'compliance_records': compliance_records,
        'current_opportunities': current_opportunities,
        'recent_events': recent_events,
        'production_modifiers': production_modifiers,
        'market_modifiers': market_modifiers,
    }
    
    return render(request, 'random_events/dashboard.html', context)


@login_required
def event_detail(request, session_id, event_occurrence_id):
    """View detailed information about a specific event occurrence"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    event_occurrence = get_object_or_404(
        EventOccurrence, 
        id=event_occurrence_id, 
        session=session
    )
    
    # Get available choices for this event
    event_choices = EventChoice.objects.filter(
        event=event_occurrence.event
    ).order_by('order')
    
    # Handle player response
    if request.method == 'POST':
        if 'acknowledge' in request.POST:
            event_occurrence.is_acknowledged = True
            event_occurrence.save()
            messages.success(request, f'Event "{event_occurrence.event.title}" acknowledged.')
            return redirect('random_events:dashboard', session_id=session_id)
        
        elif 'choice_id' in request.POST:
            choice_id = request.POST.get('choice_id')
            try:
                chosen_choice = EventChoice.objects.get(id=choice_id, event=event_occurrence.event)
                
                # Check if player can afford this choice
                if (chosen_choice.required_balance and 
                    session.balance < chosen_choice.required_balance):
                    messages.error(request, 'Insufficient funds for this choice.')
                    return redirect('random_events:event_detail', 
                                  session_id=session_id, 
                                  event_occurrence_id=event_occurrence_id)
                
                # Apply choice effects
                with transaction.atomic():
                    _apply_choice_effects(session, event_occurrence, chosen_choice)
                    
                    event_occurrence.player_response = {
                        'choice_id': str(chosen_choice.id),
                        'choice_text': chosen_choice.choice_text,
                        'chosen_at_month': session.current_month,
                        'chosen_at_year': session.current_year
                    }
                    event_occurrence.is_acknowledged = True
                    event_occurrence.save()
                
                messages.success(request, f'Choice made: {chosen_choice.choice_text}')
                return redirect('random_events:dashboard', session_id=session_id)
                
            except EventChoice.DoesNotExist:
                messages.error(request, 'Invalid choice selected.')
    
    context = {
        'session': session,
        'event_occurrence': event_occurrence,
        'event_choices': event_choices,
        'months_remaining': event_occurrence.get_months_remaining(
            session.current_month, session.current_year
        ),
    }
    
    return render(request, 'random_events/event_detail.html', context)


@login_required
def regulations_overview(request, session_id):
    """Overview of all regulations and compliance status"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get all regulations with their status
    all_regulations = RegulationTimeline.objects.all().order_by(
        'announcement_year', 'announcement_month'
    )
    
    # Get compliance records for this session
    compliance_records = RegulationCompliance.objects.filter(
        session=session
    ).select_related('regulation')
    
    compliance_dict = {
        comp.regulation.id: comp for comp in compliance_records
    }
    
    # Categorize regulations
    upcoming_regulations = []
    active_regulations = []
    expired_regulations = []
    
    for regulation in all_regulations:
        if regulation.is_active(session.current_month, session.current_year):
            active_regulations.append({
                'regulation': regulation,
                'compliance': compliance_dict.get(regulation.id)
            })
        elif regulation.is_in_grace_period(session.current_month, session.current_year):
            upcoming_regulations.append({
                'regulation': regulation,
                'months_until_active': regulation.get_months_until_implementation(
                    session.current_month, session.current_year
                ),
                'compliance': compliance_dict.get(regulation.id)
            })
        elif regulation.status == 'expired':
            expired_regulations.append({
                'regulation': regulation,
                'compliance': compliance_dict.get(regulation.id)
            })
    
    context = {
        'session': session,
        'upcoming_regulations': upcoming_regulations,
        'active_regulations': active_regulations,
        'expired_regulations': expired_regulations,
    }
    
    return render(request, 'random_events/regulations_overview.html', context)


@login_required
def market_opportunities(request, session_id):
    """View and manage market opportunities"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get all opportunities for this session
    all_opportunities = MarketOpportunity.objects.filter(
        session=session
    ).order_by('-created_at')
    
    # Categorize opportunities
    current_opportunities = []
    accepted_opportunities = []
    expired_opportunities = []
    
    for opp in all_opportunities:
        if opp.is_accepted:
            accepted_opportunities.append(opp)
        elif opp.is_available(session.current_month, session.current_year):
            current_opportunities.append(opp)
        else:
            expired_opportunities.append(opp)
    
    # Handle opportunity acceptance
    if request.method == 'POST' and 'accept_opportunity' in request.POST:
        opp_id = request.POST.get('opportunity_id')
        try:
            opportunity = MarketOpportunity.objects.get(id=opp_id, session=session)
            
            # Check if player can afford the investment
            if session.balance < opportunity.required_investment:
                messages.error(request, 'Insufficient funds for this opportunity.')
            elif not opportunity.is_available(session.current_month, session.current_year):
                messages.error(request, 'This opportunity is no longer available.')
            else:
                # Accept the opportunity
                with transaction.atomic():
                    session.balance -= opportunity.required_investment
                    session.save()
                    
                    opportunity.is_accepted = True
                    opportunity.save()
                    
                    # Create transaction record
                    from finance.models import Transaction
                    Transaction.objects.create(
                        session=session,
                        transaction_type='expense',
                        category='Marktchancen',
                        amount=opportunity.required_investment,
                        description=f'Investment: {opportunity.title}',
                        month=session.current_month,
                        year=session.current_year
                    )
                
                messages.success(request, f'Opportunity accepted: {opportunity.title}')
                return redirect('random_events:market_opportunities', session_id=session_id)
                
        except MarketOpportunity.DoesNotExist:
            messages.error(request, 'Opportunity not found.')
    
    context = {
        'session': session,
        'current_opportunities': current_opportunities,
        'accepted_opportunities': accepted_opportunities,
        'expired_opportunities': expired_opportunities,
    }
    
    return render(request, 'random_events/market_opportunities.html', context)


@login_required
def event_history(request, session_id):
    """View historical events for the session"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get all events for this session
    all_events = EventOccurrence.objects.filter(
        session=session
    ).select_related('event').order_by('-triggered_year', '-triggered_month')
    
    # Filter by category if specified
    category_filter = request.GET.get('category')
    if category_filter:
        all_events = all_events.filter(event__category__category_type=category_filter)
    
    # Filter by status if specified
    status_filter = request.GET.get('status')
    if status_filter:
        all_events = all_events.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(all_events, 20)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    # Get available categories for filtering
    categories = EventCategory.objects.all()
    
    context = {
        'session': session,
        'events': events,
        'categories': categories,
        'current_category': category_filter,
        'current_status': status_filter,
    }
    
    return render(request, 'random_events/event_history.html', context)


@login_required
def initialize_events(request, session_id):
    """Initialize predefined events and regulations for the game"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        try:
            results = initialize_all_events_and_regulations()
            
            messages.success(request, 
                f'Events system initialized: '
                f'{len(results["categories"])} categories, '
                f'{len(results["innovation_events"])} innovation events, '
                f'{len(results["market_events"])} market events, '
                f'{len(results["supply_chain_events"])} supply chain events, '
                f'{len(results["promotional_events"])} promotional events, '
                f'{len(results["crisis_events"])} crisis events, '
                f'{len(results["regulations"])} regulations created.'
            )
            
        except Exception as e:
            messages.error(request, f'Failed to initialize events: {str(e)}')
    
    return redirect('random_events:dashboard', session_id=session_id)


@login_required
def trigger_test_event(request, session_id):
    """Manually trigger a test event for debugging purposes"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    try:
        # Check if events exist, if not initialize them
        if not RandomEvent.objects.exists():
            messages.info(request, 'Initializing events system...')
            initialize_all_events_and_regulations()
        
        # Get a random event to trigger (prefer events that aren't crisis events)
        random_event = RandomEvent.objects.filter(
            category__category_type__in=['market', 'supply_chain', 'innovation', 'promotional']
        ).order_by('?').first()
        
        if not random_event:
            # Fallback to any event
            random_event = RandomEvent.objects.order_by('?').first()
            
        if not random_event:
            messages.error(request, 'No events available to trigger. Please initialize the events system first.')
            return redirect('random_events:dashboard', session_id=session_id)
        
        engine = RandomEventsEngine(session)
        
        # Create event occurrence
        event_occurrence = engine._trigger_event(random_event)
        if event_occurrence:
            messages.success(request, f'Test event triggered: {random_event.title}')
        else:
            messages.error(request, 'Failed to trigger test event')
            
    except Exception as e:
        messages.error(request, f'Failed to trigger test event: {str(e)}')
    
    return redirect('random_events:dashboard', session_id=session_id)


def _apply_choice_effects(session, event_occurrence, choice):
    """Apply the effects of a player's choice on an event"""
    from finance.models import Transaction
    
    # Apply financial effects
    if choice.financial_effects:
        if 'one_time_cost' in choice.financial_effects:
            amount = choice.financial_effects['one_time_cost']
            session.balance -= amount
            
            Transaction.objects.create(
                session=session,
                transaction_type='expense',
                category='Ereignis-Entscheidung',
                amount=amount,
                description=f'Entscheidung: {choice.choice_text}',
                month=session.current_month,
                year=session.current_year
            )
        
        if 'one_time_income' in choice.financial_effects:
            amount = choice.financial_effects['one_time_income']
            session.balance += amount
            
            Transaction.objects.create(
                session=session,
                transaction_type='income',
                category='Ereignis-Entscheidung',
                amount=amount,
                description=f'Ertrag: {choice.choice_text}',
                month=session.current_month,
                year=session.current_year
            )
        
        session.save()
    
    # Update event occurrence with choice effects
    current_effects = event_occurrence.applied_effects.copy()
    
    # Merge choice effects into applied effects
    if choice.production_effects:
        current_effects['production'] = current_effects.get('production', {})
        current_effects['production'].update(choice.production_effects)
    
    if choice.market_effects:
        current_effects['market'] = current_effects.get('market', {})
        current_effects['market'].update(choice.market_effects)
    
    if choice.regulatory_effects:
        current_effects['regulatory'] = current_effects.get('regulatory', {})
        current_effects['regulatory'].update(choice.regulatory_effects)
    
    # Store the choice that was made
    current_effects['player_choice'] = {
        'choice_id': str(choice.id),
        'choice_text': choice.choice_text,
        'effects_applied': True
    }
    
    event_occurrence.applied_effects = current_effects
    event_occurrence.save()


@login_required
def ajax_event_status(request, session_id):
    """AJAX endpoint to check for new events"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Count unacknowledged events
    unacknowledged_count = EventOccurrence.objects.filter(
        session=session,
        status='active',
        is_acknowledged=False
    ).count()
    
    # Get latest unacknowledged events
    latest_events = EventOccurrence.objects.filter(
        session=session,
        status='active',
        is_acknowledged=False
    ).select_related('event').order_by('-created_at')[:3]
    
    events_data = [
        {
            'id': str(event.id),
            'title': event.event.title,
            'description': event.event.description,
            'severity': event.event.severity,
            'triggered_month': event.triggered_month,
            'triggered_year': event.triggered_year,
        }
        for event in latest_events
    ]
    
    return JsonResponse({
        'unacknowledged_count': unacknowledged_count,
        'latest_events': events_data
    })