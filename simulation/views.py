from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from bikeshop.models import GameSession
from .engine import SimulationEngine


@login_required
def advance_month(request, session_id):
    """Führt Simulation für einen Monat aus"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    if request.method == 'POST':
        try:
            engine = SimulationEngine(session)
            engine.process_month()

            messages.success(request, f'Monat {session.current_month}/{session.current_year} erfolgreich simuliert!')

        except Exception as e:
            messages.error(request, f'Fehler bei der Simulation: {str(e)}')

    return redirect('bikeshop:session_detail', session_id=session.id)
