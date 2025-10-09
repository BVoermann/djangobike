from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bikeshop.models import GameSession
from .models import AICompetitor, CompetitorProduction, CompetitorSale, MarketCompetition
from django.db import models
from datetime import datetime


@login_required
def competitors_dashboard(request, session_id):
    """Dashboard für Konkurrenten-Übersicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Alle Konkurrenten der Session
    competitors = AICompetitor.objects.filter(session=session).order_by('name')
    
    # Aktuelle Markt-Wettbewerbssituation
    current_competition = MarketCompetition.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).select_related('market', 'bike_type')
    
    # Verkäufe der letzten 3 Monate
    recent_sales = CompetitorSale.objects.filter(
        competitor__session=session,
        year=session.current_year,
        month__gte=max(1, session.current_month - 2)
    ).select_related('competitor', 'market', 'bike_type').order_by('-month', '-total_revenue')
    
    # Marktanteile berechnen
    market_shares = []
    total_market_revenue = 0
    competitor_revenues = {}
    
    for sale in recent_sales:
        comp_name = sale.competitor.name
        if comp_name not in competitor_revenues:
            competitor_revenues[comp_name] = 0
        competitor_revenues[comp_name] += float(sale.total_revenue)
        total_market_revenue += float(sale.total_revenue)
    
    if total_market_revenue > 0:
        for comp_name, revenue in competitor_revenues.items():
            share = (revenue / total_market_revenue) * 100
            market_shares.append({
                'name': comp_name,
                'revenue': revenue,
                'share': round(share, 1)
            })
    
    market_shares.sort(key=lambda x: x['revenue'], reverse=True)
    
    context = {
        'session': session,
        'competitors': competitors,
        'current_competition': current_competition,
        'recent_sales': recent_sales[:20],  # Begrenzt auf 20 Einträge
        'market_shares': market_shares,
        'total_market_revenue': total_market_revenue
    }
    
    return render(request, 'competitors/dashboard.html', context)


@login_required
def competitor_detail(request, session_id, competitor_id):
    """Detailansicht für einen Konkurrenten"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    competitor = get_object_or_404(AICompetitor, id=competitor_id, session=session)
    
    # Produktionshistorie
    productions = CompetitorProduction.objects.filter(
        competitor=competitor,
        year=session.current_year
    ).select_related('bike_type').order_by('-month')
    
    # Verkaufshistorie
    sales = CompetitorSale.objects.filter(
        competitor=competitor,
        year=session.current_year
    ).select_related('market', 'bike_type').order_by('-month', '-total_revenue')
    
    # Performance-Statistiken
    monthly_stats = []
    for month in range(1, 13):
        month_production = productions.filter(month=month).aggregate(
            total_produced=models.Sum('quantity_produced')
        )['total_produced'] or 0
        
        month_sales = sales.filter(month=month).aggregate(
            total_sold=models.Sum('quantity_sold'),
            total_revenue=models.Sum('total_revenue')
        )
        
        monthly_stats.append({
            'month': month,
            'produced': month_production,
            'sold': month_sales['total_sold'] or 0,
            'revenue': float(month_sales['total_revenue'] or 0)
        })
    
    context = {
        'session': session,
        'competitor': competitor,
        'productions': productions[:12],  # Aktuelles Jahr
        'sales': sales[:20],  # Begrenzt auf 20 Einträge
        'monthly_stats': monthly_stats
    }
    
    return render(request, 'competitors/detail.html', context)


@login_required
def market_analysis(request, session_id):
    """Marktanalyse mit Wettbewerbsdaten"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Aktuelle Markt-Wettbewerbssituation
    competitions = MarketCompetition.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).select_related('market', 'bike_type').order_by('market__name', 'bike_type__name', 'price_segment')
    
    # Gruppiere nach Märkten
    market_data = {}
    for comp in competitions:
        market_name = comp.market.name
        if market_name not in market_data:
            market_data[market_name] = []
        
        market_data[market_name].append({
            'bike_type': comp.bike_type.name,
            'price_segment': comp.get_price_segment_display(),
            'total_supply': comp.total_supply,
            'estimated_demand': comp.estimated_demand,
            'saturation_level': round(comp.saturation_level, 2),
            'price_pressure': round(comp.price_pressure, 2),
            'competition_intensity': 'Hoch' if comp.saturation_level > 1.2 else 'Mittel' if comp.saturation_level > 0.8 else 'Niedrig'
        })
    
    context = {
        'session': session,
        'market_data': market_data,
        'current_month': session.current_month,
        'current_year': session.current_year
    }
    
    return render(request, 'competitors/market_analysis.html', context)


@login_required
def competitor_api_data(request, session_id):
    """API-Endpunkt für Konkurrenten-Daten (für Charts)"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Marktanteils-Daten für Pie-Chart
    recent_sales = CompetitorSale.objects.filter(
        competitor__session=session,
        year=session.current_year,
        month__gte=max(1, session.current_month - 2)
    ).values('competitor__name').annotate(
        total_revenue=models.Sum('total_revenue'),
        total_sold=models.Sum('quantity_sold')
    ).order_by('-total_revenue')
    
    # Monatliche Entwicklung für Line-Chart
    monthly_data = []
    for month in range(1, session.current_month + 1):
        month_sales = CompetitorSale.objects.filter(
            competitor__session=session,
            year=session.current_year,
            month=month
        ).aggregate(
            total_revenue=models.Sum('total_revenue'),
            total_sold=models.Sum('quantity_sold')
        )
        
        monthly_data.append({
            'month': month,
            'revenue': float(month_sales['total_revenue'] or 0),
            'units_sold': month_sales['total_sold'] or 0
        })
    
    return JsonResponse({
        'market_shares': list(recent_sales),
        'monthly_trends': monthly_data,
        'current_month': session.current_month,
        'current_year': session.current_year
    })
