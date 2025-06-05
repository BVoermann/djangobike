from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import GameSession
from .forms import ParameterUploadForm, SessionCreateForm
from .utils import process_parameter_zip
import json


@login_required
def dashboard(request):
    """Hauptdashboard"""
    sessions = GameSession.objects.filter(user=request.user, is_active=True)
    return render(request, 'dashboard.html', {
        'sessions': sessions
    })


@login_required
def upload_parameters(request):
    """Parameter-Upload"""
    if request.method == 'POST':
        form = ParameterUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                zip_file = request.FILES['parameter_file']
                parameters = process_parameter_zip(zip_file)
                request.session['uploaded_parameters'] = parameters
                messages.success(request, 'Parameter erfolgreich hochgeladen!')
                return redirect('bikeshop:create_session')
            except Exception as e:
                messages.error(request, f'Fehler beim Verarbeiten der Datei: {str(e)}')
    else:
        form = ParameterUploadForm()

    return render(request, 'bikeshop/upload_parameters.html', {'form': form})


@login_required
def create_session(request):
    """Neue Spielsession erstellen"""
    parameters = request.session.get('uploaded_parameters')
    if not parameters:
        messages.error(request, 'Bitte laden Sie zuerst Parameter hoch.')
        return redirect('bikeshop:upload_parameters')

    if request.method == 'POST':
        form = SessionCreateForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()

            # Initialize session with parameters
            from .utils import initialize_session_data
            initialize_session_data(session, parameters)

            messages.success(request, 'Neue Spielsession erstellt!')
            return redirect('bikeshop:session_detail', session_id=session.id)
    else:
        form = SessionCreateForm()

    return render(request, 'bikeshop/create_session.html', {'form': form})


@login_required
def session_detail(request, session_id):
    """Spielsession Details"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    # Hole aktuelle Daten für Dashboard
    from simulation.engine import SimulationEngine
    engine = SimulationEngine(session)
    dashboard_data = engine.get_dashboard_data()

    return render(request, 'bikeshop/session_detail.html', {
        'session': session,
        'dashboard_data': dashboard_data
    })
