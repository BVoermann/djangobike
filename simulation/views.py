from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from bikeshop.models import GameSession
from .engine import SimulationEngine
from sales.models import SalesOrder
from decimal import Decimal


@login_required
def advance_month(request, session_id):
    """Führt Simulation für einen Monat aus"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    if request.method == 'POST':
        try:
            engine = SimulationEngine(session)
            engine.process_month()
            
            # Refresh session from database to get updated month/year
            session.refresh_from_db()

            messages.success(request, f'Monat {session.current_month}/{session.current_year} erfolgreich simuliert!')

        except Exception as e:
            messages.error(request, f'Fehler bei der Simulation: {str(e)}')

    return redirect('bikeshop:session_detail', session_id=session.id)


@login_required
def month_summary(request, session_id):
    """Liefert Zusammenfassung des aktuellen Monats für Popup"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get sales for current month
    sales = SalesOrder.objects.filter(
        session=session,
        sale_month=session.current_month,
        sale_year=session.current_year,
        is_completed=True
    )
    
    # Calculate totals
    total_bikes_sold = sales.count()
    total_revenue = sum(sale.sale_price for sale in sales)
    
    # Get previous balance to calculate profit/loss
    previous_balance = session.balance
    
    # Simple profit calculation (revenue minus any costs would be more accurate)
    # For now, we'll show the balance change potential
    profit_loss = total_revenue  # This is simplified - in reality would include costs
    
    return JsonResponse({
        'bikes_sold': total_bikes_sold,
        'revenue': float(total_revenue),
        'profit_loss': float(profit_loss),
        'current_month': session.current_month,
        'current_year': session.current_year
    })
