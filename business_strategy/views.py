from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from bikeshop.models import GameSession
from .models import (
    ResearchProject, MarketingCampaign, SustainabilityInitiative,
    BusinessStrategy, SustainabilityProfile, ResearchBenefit,
    CampaignEffect, CompetitiveAnalysis
)
from .forms import (
    ResearchProjectForm, StartResearchProjectForm, MarketingCampaignForm,
    StartMarketingCampaignForm, SustainabilityInitiativeForm,
    StartSustainabilityInitiativeForm, BusinessStrategyForm,
    SustainabilityProfileForm, QuickStartProjectForm,
    QuickStartCampaignForm, QuickStartInitiativeForm
)
from .business_engine import (
    BusinessStrategyEngine, create_predefined_rd_projects,
    create_predefined_marketing_campaigns, create_predefined_sustainability_initiatives
)


@login_required
def business_strategy_dashboard(request, session_id):
    """Main business strategy dashboard"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Initialize business strategy components if they don't exist
    business_strategy, created = BusinessStrategy.objects.get_or_create(
        session=session,
        defaults={
            'rd_monthly_budget': Decimal('5000'),
            'marketing_monthly_budget': Decimal('5000'),
            'sustainability_monthly_budget': Decimal('2000'),
        }
    )
    
    sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
        session=session,
        defaults={'sustainability_score': 50.0}
    )
    
    # Get current projects and campaigns
    active_rd_projects = ResearchProject.objects.filter(session=session, status='active')
    planned_rd_projects = ResearchProject.objects.filter(session=session, status='planned')
    completed_rd_projects = ResearchProject.objects.filter(session=session, status='completed')
    
    active_campaigns = MarketingCampaign.objects.filter(session=session, status='active')
    planned_campaigns = MarketingCampaign.objects.filter(session=session, status='planned')
    completed_campaigns = MarketingCampaign.objects.filter(session=session, status='completed')
    
    active_initiatives = SustainabilityInitiative.objects.filter(session=session, status='active')
    planned_initiatives = SustainabilityInitiative.objects.filter(session=session, status='planned')
    completed_initiatives = SustainabilityInitiative.objects.filter(session=session, status='completed')
    
    # Get research benefits
    research_benefits = ResearchBenefit.objects.filter(session=session, is_active=True)
    
    # Get competitive analysis
    competitive_analysis = CompetitiveAnalysis.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).first()
    
    # Get business strategy engine effects
    engine = BusinessStrategyEngine(session)
    combined_effects = engine.get_combined_business_effects()
    
    context = {
        'session': session,
        'business_strategy': business_strategy,
        'sustainability_profile': sustainability_profile,
        
        'active_rd_projects': active_rd_projects,
        'planned_rd_projects': planned_rd_projects,
        'completed_rd_projects': completed_rd_projects,
        
        'active_campaigns': active_campaigns,
        'planned_campaigns': planned_campaigns,
        'completed_campaigns': completed_campaigns,
        
        'active_initiatives': active_initiatives,
        'planned_initiatives': planned_initiatives,
        'completed_initiatives': completed_initiatives,
        
        'research_benefits': research_benefits,
        'competitive_analysis': competitive_analysis,
        'combined_effects': combined_effects,
    }
    
    return render(request, 'business_strategy/dashboard.html', context)


@login_required
def research_development(request, session_id):
    """R&D management page"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Handle quick start form
    if request.method == 'POST' and 'quick_start' in request.POST:
        quick_form = QuickStartProjectForm(request.POST)
        if quick_form.is_valid():
            project_type = quick_form.cleaned_data['project_type']
            
            # Create predefined projects if they don't exist
            if not ResearchProject.objects.filter(session=session).exists():
                create_predefined_rd_projects(session)
            
            # Start the selected project
            project_mapping = {
                'automation': 'Automatisierte Produktion',
                'materials': 'Leichtbaurahmen-Technologie',
                'smart_ebike': 'Smart E-Bike System',
                'sustainable_paint': 'Nachhaltige Lackierung',
                'quality_ai': 'Qualitätskontroll-KI',
            }
            
            try:
                project = ResearchProject.objects.get(
                    session=session,
                    name=project_mapping[project_type],
                    status='planned'
                )
                project.status = 'active'
                project.start_month = session.current_month
                project.start_year = session.current_year
                project.save()
                
                messages.success(request, f'F&E Projekt "{project.name}" wurde gestartet!')
            except ResearchProject.DoesNotExist:
                messages.error(request, 'Projekt nicht gefunden oder bereits gestartet.')
            
            return redirect('business_strategy:research_development', session_id=session_id)
    
    # Handle project start form
    if request.method == 'POST' and 'start_project' in request.POST:
        start_form = StartResearchProjectForm(request.POST, session=session)
        if start_form.is_valid():
            project = start_form.cleaned_data['project']
            project.status = 'active'
            project.start_month = session.current_month
            project.start_year = session.current_year
            project.save()
            
            messages.success(request, f'F&E Projekt "{project.name}" wurde gestartet!')
            return redirect('business_strategy:research_development', session_id=session_id)
    else:
        start_form = StartResearchProjectForm(session=session)
        quick_form = QuickStartProjectForm()
    
    # Get all projects
    projects = ResearchProject.objects.filter(session=session).order_by('-created_at')
    research_benefits = ResearchBenefit.objects.filter(session=session, is_active=True)
    
    # Get business strategy for budget info
    business_strategy = BusinessStrategy.objects.get(session=session)
    
    context = {
        'session': session,
        'projects': projects,
        'research_benefits': research_benefits,
        'start_form': start_form,
        'quick_form': quick_form,
        'business_strategy': business_strategy,
    }
    
    return render(request, 'business_strategy/research_development.html', context)


@login_required
def create_research_project(request, session_id):
    """Create new R&D project"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        form = ResearchProjectForm(request.POST, session=session)
        if form.is_valid():
            project = form.save(commit=False)
            project.session = session
            project.months_remaining = project.duration_months
            project.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'F&E Projekt "{project.name}" wurde erstellt!')
            return redirect('business_strategy:research_development', session_id=session_id)
    else:
        form = ResearchProjectForm(session=session)
    
    context = {
        'session': session,
        'form': form,
        'title': 'Neues F&E Projekt erstellen'
    }
    
    return render(request, 'business_strategy/create_project.html', context)


@login_required
def marketing_campaigns(request, session_id):
    """Marketing campaigns management page"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Handle quick start form
    if request.method == 'POST' and 'quick_start' in request.POST:
        quick_form = QuickStartCampaignForm(request.POST)
        if quick_form.is_valid():
            campaign_type = quick_form.cleaned_data['campaign_type']
            
            # Create predefined campaigns if they don't exist
            if not MarketingCampaign.objects.filter(session=session).exists():
                create_predefined_marketing_campaigns(session)
            
            # Start the selected campaign
            campaign_mapping = {
                'spring': 'Frühjahrskampagne',
                'sustainability': 'Nachhaltigkeit im Fokus',
                'premium_launch': 'Premium E-Bike Launch',
                'social_media': 'Social Media Boost',
            }
            
            try:
                campaign = MarketingCampaign.objects.get(
                    session=session,
                    name=campaign_mapping[campaign_type],
                    status='planned'
                )
                campaign.activate_campaign(session.current_month, session.current_year)
                
                messages.success(request, f'Marketing Kampagne "{campaign.name}" wurde gestartet!')
            except MarketingCampaign.DoesNotExist:
                messages.error(request, 'Kampagne nicht gefunden oder bereits gestartet.')
            
            return redirect('business_strategy:marketing_campaigns', session_id=session_id)
    
    # Handle campaign start form
    if request.method == 'POST' and 'start_campaign' in request.POST:
        start_form = StartMarketingCampaignForm(request.POST, session=session)
        if start_form.is_valid():
            campaign = start_form.cleaned_data['campaign']
            campaign.activate_campaign(session.current_month, session.current_year)
            
            messages.success(request, f'Marketing Kampagne "{campaign.name}" wurde gestartet!')
            return redirect('business_strategy:marketing_campaigns', session_id=session_id)
    else:
        start_form = StartMarketingCampaignForm(session=session)
        quick_form = QuickStartCampaignForm()
    
    # Get all campaigns
    campaigns = MarketingCampaign.objects.filter(session=session).order_by('-created_at')
    
    # Get recent campaign effects
    campaign_effects = CampaignEffect.objects.filter(
        session=session,
        year=session.current_year
    ).order_by('-month')[:10]
    
    # Get business strategy for budget info
    business_strategy = BusinessStrategy.objects.get(session=session)
    
    context = {
        'session': session,
        'campaigns': campaigns,
        'campaign_effects': campaign_effects,
        'start_form': start_form,
        'quick_form': quick_form,
        'business_strategy': business_strategy,
    }
    
    return render(request, 'business_strategy/marketing_campaigns.html', context)


@login_required
def create_marketing_campaign(request, session_id):
    """Create new marketing campaign"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        form = MarketingCampaignForm(request.POST, session=session)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.session = session
            campaign.months_remaining = campaign.duration_months
            campaign.monthly_spend = campaign.total_budget / campaign.duration_months
            campaign.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'Marketing Kampagne "{campaign.name}" wurde erstellt!')
            return redirect('business_strategy:marketing_campaigns', session_id=session_id)
    else:
        form = MarketingCampaignForm(session=session)
    
    context = {
        'session': session,
        'form': form,
        'title': 'Neue Marketing Kampagne erstellen'
    }
    
    return render(request, 'business_strategy/create_campaign.html', context)


@login_required
def sustainability_management(request, session_id):
    """Sustainability management page"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Ensure sustainability profile exists
    sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
        session=session,
        defaults={'sustainability_score': 50.0}
    )
    
    # Handle quick start form
    if request.method == 'POST' and 'quick_start' in request.POST:
        quick_form = QuickStartInitiativeForm(request.POST)
        if quick_form.is_valid():
            initiative_type = quick_form.cleaned_data['initiative_type']
            
            # Create predefined initiatives if they don't exist
            if not SustainabilityInitiative.objects.filter(session=session).exists():
                create_predefined_sustainability_initiatives(session)
            
            # Start the selected initiative
            initiative_mapping = {
                'solar': 'Solaranlage Installation',
                'waste_reduction': 'Abfallreduktionsprogramm',
                'local_suppliers': 'Lokale Lieferantennetzwerk',
                'iso_certification': 'Umweltzertifizierung ISO 14001',
            }
            
            try:
                initiative = SustainabilityInitiative.objects.get(
                    session=session,
                    name=initiative_mapping[initiative_type],
                    status='planned'
                )
                initiative.status = 'active'
                initiative.start_month = session.current_month
                initiative.start_year = session.current_year
                initiative.save()
                
                messages.success(request, f'Nachhaltigkeits-Initiative "{initiative.name}" wurde gestartet!')
            except SustainabilityInitiative.DoesNotExist:
                messages.error(request, 'Initiative nicht gefunden oder bereits gestartet.')
            
            return redirect('business_strategy:sustainability_management', session_id=session_id)
    
    # Handle initiative start form
    if request.method == 'POST' and 'start_initiative' in request.POST:
        start_form = StartSustainabilityInitiativeForm(request.POST, session=session)
        if start_form.is_valid():
            initiative = start_form.cleaned_data['initiative']
            initiative.status = 'active'
            initiative.start_month = session.current_month
            initiative.start_year = session.current_year
            initiative.save()
            
            messages.success(request, f'Nachhaltigkeits-Initiative "{initiative.name}" wurde gestartet!')
            return redirect('business_strategy:sustainability_management', session_id=session_id)
    else:
        start_form = StartSustainabilityInitiativeForm(session=session)
        quick_form = QuickStartInitiativeForm()
    
    # Get all initiatives
    initiatives = SustainabilityInitiative.objects.filter(session=session).order_by('-created_at')
    
    # Get business strategy for budget info
    business_strategy = BusinessStrategy.objects.get(session=session)
    
    # Calculate sustainability effects
    engine = BusinessStrategyEngine(session)
    sustainability_effects = engine.get_sustainability_effects()
    
    context = {
        'session': session,
        'sustainability_profile': sustainability_profile,
        'initiatives': initiatives,
        'start_form': start_form,
        'quick_form': quick_form,
        'business_strategy': business_strategy,
        'sustainability_effects': sustainability_effects,
    }
    
    return render(request, 'business_strategy/sustainability_management.html', context)


@login_required
def create_sustainability_initiative(request, session_id):
    """Create new sustainability initiative"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Ensure sustainability profile exists
    sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
        session=session,
        defaults={'sustainability_score': 50.0}
    )
    
    if request.method == 'POST':
        form = SustainabilityInitiativeForm(request.POST)
        if form.is_valid():
            initiative = form.save(commit=False)
            initiative.session = session
            initiative.sustainability_profile = sustainability_profile
            initiative.months_remaining = initiative.implementation_months
            initiative.save()
            
            messages.success(request, f'Nachhaltigkeits-Initiative "{initiative.name}" wurde erstellt!')
            return redirect('business_strategy:sustainability_management', session_id=session_id)
    else:
        form = SustainabilityInitiativeForm()
    
    context = {
        'session': session,
        'form': form,
        'title': 'Neue Nachhaltigkeits-Initiative erstellen'
    }
    
    return render(request, 'business_strategy/create_initiative.html', context)


@login_required
def strategy_settings(request, session_id):
    """Business strategy settings page"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    business_strategy, created = BusinessStrategy.objects.get_or_create(
        session=session,
        defaults={
            'rd_monthly_budget': Decimal('5000'),
            'marketing_monthly_budget': Decimal('5000'),
            'sustainability_monthly_budget': Decimal('2000'),
        }
    )
    
    sustainability_profile, created = SustainabilityProfile.objects.get_or_create(
        session=session,
        defaults={'sustainability_score': 50.0}
    )
    
    if request.method == 'POST':
        strategy_form = BusinessStrategyForm(request.POST, instance=business_strategy)
        
        if strategy_form.is_valid():
            strategy_form.save()
            messages.success(request, 'Geschäftsstrategie wurde aktualisiert!')
            return redirect('business_strategy:strategy_settings', session_id=session_id)
    else:
        strategy_form = BusinessStrategyForm(instance=business_strategy)
        sustainability_form = SustainabilityProfileForm(instance=sustainability_profile)
    
    # Get competitive analysis
    competitive_analysis = CompetitiveAnalysis.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).first()
    
    context = {
        'session': session,
        'strategy_form': strategy_form,
        'sustainability_form': sustainability_form,
        'business_strategy': business_strategy,
        'sustainability_profile': sustainability_profile,
        'competitive_analysis': competitive_analysis,
    }
    
    return render(request, 'business_strategy/strategy_settings.html', context)


@login_required
def competitive_analysis_view(request, session_id):
    """Competitive analysis and market intelligence"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get recent competitive analyses
    competitive_analyses = CompetitiveAnalysis.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]  # Last 12 months
    
    # Get current month analysis
    current_analysis = CompetitiveAnalysis.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).first()
    
    # Get business strategy metrics
    business_strategy = BusinessStrategy.objects.get(session=session)
    
    # Get sustainability profile
    sustainability_profile = SustainabilityProfile.objects.get(session=session)
    
    context = {
        'session': session,
        'competitive_analyses': competitive_analyses,
        'current_analysis': current_analysis,
        'business_strategy': business_strategy,
        'sustainability_profile': sustainability_profile,
    }
    
    return render(request, 'business_strategy/competitive_analysis.html', context)


@login_required
def initialize_predefined_content(request, session_id):
    """Initialize predefined R&D projects, campaigns, and initiatives"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    with transaction.atomic():
        # Create predefined R&D projects
        if not ResearchProject.objects.filter(session=session).exists():
            projects = create_predefined_rd_projects(session)
            messages.success(request, f'{len(projects)} vordefinierte F&E Projekte wurden erstellt.')
        
        # Create predefined marketing campaigns
        if not MarketingCampaign.objects.filter(session=session).exists():
            campaigns = create_predefined_marketing_campaigns(session)
            messages.success(request, f'{len(campaigns)} vordefinierte Marketing Kampagnen wurden erstellt.')
        
        # Create predefined sustainability initiatives
        if not SustainabilityInitiative.objects.filter(session=session).exists():
            initiatives = create_predefined_sustainability_initiatives(session)
            messages.success(request, f'{len(initiatives)} vordefinierte Nachhaltigkeits-Initiativen wurden erstellt.')
    
    return redirect('business_strategy:dashboard', session_id=session_id)


@login_required
def project_detail(request, session_id, project_id):
    """View detailed information about a specific R&D project"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    project = get_object_or_404(ResearchProject, id=project_id, session=session)
    
    # Get research benefits if project is completed
    research_benefit = None
    if project.status == 'completed':
        research_benefit = ResearchBenefit.objects.filter(
            research_project=project
        ).first()
    
    context = {
        'session': session,
        'project': project,
        'research_benefit': research_benefit,
    }
    
    return render(request, 'business_strategy/project_detail.html', context)


@login_required
def campaign_detail(request, session_id, campaign_id):
    """View detailed information about a specific marketing campaign"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, session=session)
    
    # Get campaign effects
    campaign_effects = CampaignEffect.objects.filter(
        campaign=campaign
    ).order_by('-year', '-month')
    
    context = {
        'session': session,
        'campaign': campaign,
        'campaign_effects': campaign_effects,
    }
    
    return render(request, 'business_strategy/campaign_detail.html', context)


@login_required
def initiative_detail(request, session_id, initiative_id):
    """View detailed information about a specific sustainability initiative"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    initiative = get_object_or_404(SustainabilityInitiative, id=initiative_id, session=session)
    
    context = {
        'session': session,
        'initiative': initiative,
    }
    
    return render(request, 'business_strategy/initiative_detail.html', context)