from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import GameSession
from .forms import ParameterUploadForm, SessionCreateForm
from .utils import process_parameter_zip
import json
import zipfile
import os
from django.conf import settings
import tempfile


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


@login_required
def delete_session(request, session_id):
    """Spielsession löschen"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        session_name = session.name
        session.delete()
        messages.success(request, f'Session "{session_name}" wurde erfolgreich gelöscht.')
        return redirect('bikeshop:dashboard')
    
    return render(request, 'bikeshop/confirm_delete.html', {'session': session})


@login_required
def download_default_parameters(request):
    """Download ZIP file containing default XLSX parameter files"""
    
    # Define the XLSX files that should be included
    xlsx_files = [
        'lieferanten.xlsx',
        'fahrraeder.xlsx', 
        'preise_verkauf.xlsx',
        'lager.xlsx',
        'maerkte.xlsx',
        'personal.xlsx',
        'finanzen.xlsx'
    ]
    
    # Create a temporary ZIP file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add each XLSX file to the ZIP
            for xlsx_file in xlsx_files:
                file_path = os.path.join(settings.BASE_DIR, xlsx_file)
                if os.path.exists(file_path):
                    zipf.write(file_path, xlsx_file)
                else:
                    messages.warning(request, f'File {xlsx_file} not found and skipped.')
        
        # Read the ZIP file content
        temp_zip.seek(0)
        with open(temp_zip.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up temporary file
        os.unlink(temp_zip.name)
        
        # Create HTTP response with ZIP file
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="bikeshop_default_parameters.zip"'
        response['Content-Length'] = len(zip_content)
        
        return response
