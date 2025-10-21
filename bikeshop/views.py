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
def monthly_report(request, session_id):
    """Monthly report showing last month's business activity"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get last month data
    if session.current_month > 1:
        report_month = session.current_month - 1
        report_year = session.current_year
    else:
        report_month = 12
        report_year = session.current_year - 1
    
    from finance.models import MonthlyReport
    
    # Try to get saved monthly report first
    try:
        monthly_report = MonthlyReport.objects.get(
            session=session,
            month=report_month,
            year=report_year
        )
        
        # Use saved data from comprehensive monthly report
        balance_change = monthly_report.closing_balance - monthly_report.opening_balance
        
        # Convert JSON fields back to usable format
        production_summary = monthly_report.production_summary or {}
        sales_summary = monthly_report.sales_summary or {}
        procurement_summary = monthly_report.procurement_summary or {}
        detailed_transactions = monthly_report.detailed_transactions or []
        
        # Extract planned sales data from detailed transactions
        planned_sales_summary = {}
        filtered_transactions = []
        for transaction in detailed_transactions:
            if transaction.get('type') == 'planned_sales_data':
                planned_sales_summary = transaction.get('planned_sales_summary', {})
            else:
                filtered_transactions.append(transaction)
        detailed_transactions = filtered_transactions
        
        # Create bought_items from procurement_summary for template compatibility
        bought_items = []
        for component, data in procurement_summary.items():
            bought_items.append({
                'component': component,
                'quantity': data['quantity'],
                'total_cost': data['cost'],
                'supplier': data.get('supplier', 'Unknown')
            })
        
        context = {
            'session': session,
            'report_month': report_month,
            'report_year': report_year,
            'monthly_report': monthly_report,
            'balance_change': balance_change,
            'profit_loss': monthly_report.profit_loss,
            
            # Procurement data
            'bought_items': bought_items,
            'total_bought_amount': monthly_report.total_procurement_cost,
            
            # Production data
            'production_summary': production_summary,
            'total_production_cost': monthly_report.total_production_cost,
            'bikes_produced_count': monthly_report.bikes_produced_count,
            
            # Sales data - ACTUAL completed sales
            'sales_summary': sales_summary,
            'total_sales_revenue': monthly_report.total_sales_revenue,
            'bikes_sold_count': monthly_report.bikes_sold_count,
            
            # Planned sales data - sales orders created this month
            'planned_sales_summary': planned_sales_summary,
            
            # Transaction data
            'transactions': detailed_transactions,
            'has_saved_report': True,
        }
        
    except MonthlyReport.DoesNotExist:
        # No saved report - show message that report is not available yet
        context = {
            'session': session,
            'report_month': report_month,
            'report_year': report_year,
            'monthly_report': None,
            'balance_change': 0,
            'profit_loss': 0,
            'bought_items': [],
            'total_bought_amount': 0,
            'production_summary': {},
            'total_production_cost': 0,
            'bikes_produced_count': 0,
            'sales_summary': {},
            'total_sales_revenue': 0,
            'bikes_sold_count': 0,
            'planned_sales_summary': {},
            'transactions': [],
            'has_saved_report': False,
        }
    
    return render(request, 'bikeshop/monthly_report.html', context)


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
        'finanzen.xlsx',
        'konkurrenten.xlsx'
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


@login_required
def api_sessions(request):
    """API endpoint to get user's active sessions"""
    sessions = GameSession.objects.filter(user=request.user, is_active=True)
    
    sessions_data = [
        {
            'id': str(session.id),
            'name': session.name,
            'current_month': session.current_month,
            'current_year': session.current_year,
            'balance': float(session.balance)
        }
        for session in sessions
    ]
    
    return JsonResponse({
        'success': True,
        'sessions': sessions_data
    })
