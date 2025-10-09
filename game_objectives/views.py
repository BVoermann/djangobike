from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
import json

from bikeshop.models import GameSession
from .models import GameMode, SessionGameMode, GameResult, BankruptcyEvent
from .bankruptcy_engine import BankruptcyChecker
from .victory_checker import VictoryChecker


@login_required
def objectives_dashboard(request, session_id):
    """Dashboard showing current objectives and progress"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get or create session game mode
    session_game_mode = getattr(session, 'game_mode_config', None)
    
    if not session_game_mode:
        # Redirect to game mode selection if not set
        return redirect('game_objectives:select_game_mode', session_id=session_id)
    
    # Update monthly progress
    session_game_mode.update_monthly_progress()
    
    # Check victory/failure conditions
    session_game_mode.check_victory_conditions()
    
    # Get current objectives progress
    objectives = session_game_mode.game_mode.objectives.filter(is_active=True).order_by('order')
    objective_progress = []
    
    for objective in objectives:
        current_value = objective.get_current_value(session)
        target_value = float(objective.target_value)
        is_met = objective.evaluate(session)
        
        # Calculate progress percentage
        if target_value > 0:
            progress_pct = min((current_value / target_value) * 100, 200)
        else:
            progress_pct = 100 if is_met else 0
        
        objective_progress.append({
            'objective': objective,
            'current_value': current_value,
            'target_value': target_value,
            'is_met': is_met,
            'progress_percentage': progress_pct,
            'status_class': 'success' if is_met else ('warning' if progress_pct > 50 else 'danger')
        })
    
    # Get recent score history
    monthly_scores = session_game_mode.monthly_scores[-6:] if session_game_mode.monthly_scores else []
    
    context = {
        'session': session,
        'session_game_mode': session_game_mode,
        'game_mode': session_game_mode.game_mode,
        'objective_progress': objective_progress,
        'monthly_scores': monthly_scores,
        'current_score': float(session_game_mode.calculate_final_score()),
        'completion_percentage': float(session_game_mode.calculate_completion_percentage()),
        'bankruptcy_risk': calculate_bankruptcy_risk(session, session_game_mode.game_mode),
        'is_game_over': session_game_mode.is_completed or session_game_mode.is_failed,
    }
    
    return render(request, 'game_objectives/dashboard.html', context)


@login_required
def select_game_mode(request, session_id):
    """Select game mode for a session"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Check if session already has a game mode
    if hasattr(session, 'game_mode_config'):
        return redirect('game_objectives:objectives_dashboard', session_id=session_id)
    
    if request.method == 'POST':
        game_mode_id = request.POST.get('game_mode_id')
        game_mode = get_object_or_404(GameMode, id=game_mode_id, is_active=True)
        
        # Create session game mode
        session_game_mode = SessionGameMode.objects.create(
            session=session,
            game_mode=game_mode
        )
        
        # Update session starting balance if different
        if session.balance != game_mode.starting_balance:
            session.balance = game_mode.starting_balance
            session.save()
        
        messages.success(request, f'Spielmodus "{game_mode.name}" wurde aktiviert!')
        return redirect('game_objectives:objectives_dashboard', session_id=session_id)
    
    # Get available game modes
    game_modes = GameMode.objects.filter(is_active=True).order_by('name')
    
    context = {
        'session': session,
        'game_modes': game_modes,
    }
    
    return render(request, 'game_objectives/select_game_mode.html', context)


@login_required
def game_result(request, session_id):
    """Show final game results"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    session_game_mode = get_object_or_404(SessionGameMode, session=session)
    
    if not (session_game_mode.is_completed or session_game_mode.is_failed):
        return redirect('game_objectives:objectives_dashboard', session_id=session_id)
    
    # Get game result
    game_result = getattr(session_game_mode, 'result', None)
    
    if not game_result:
        # Create result if missing
        if session_game_mode.is_completed:
            session_game_mode.complete_game()
        else:
            session_game_mode.fail_game("Unbekannter Grund")
        game_result = session_game_mode.result
    
    # Get detailed objective results
    objective_results = []
    for objective in session_game_mode.game_mode.objectives.filter(is_active=True):
        current_value = objective.get_current_value(session)
        is_met = objective.evaluate(session)
        
        objective_results.append({
            'objective': objective,
            'current_value': current_value,
            'target_value': float(objective.target_value),
            'is_met': is_met,
            'achievement_percentage': min((current_value / float(objective.target_value)) * 100, 200) if objective.target_value > 0 else (100 if is_met else 0)
        })
    
    # Get bankruptcy events if any
    bankruptcy_events = session.bankruptcy_events.all().order_by('-created_at')
    
    context = {
        'session': session,
        'session_game_mode': session_game_mode,
        'game_result': game_result,
        'objective_results': objective_results,
        'bankruptcy_events': bankruptcy_events,
        'monthly_scores': session_game_mode.monthly_scores or [],
    }
    
    return render(request, 'game_objectives/game_result.html', context)


@login_required
def objectives_api(request, session_id):
    """API endpoint for objectives data"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    session_game_mode = getattr(session, 'game_mode_config', None)
    
    if not session_game_mode:
        return JsonResponse({'error': 'No game mode configured'}, status=400)
    
    # Update progress
    session_game_mode.update_monthly_progress()
    
    objectives_data = []
    for objective in session_game_mode.game_mode.objectives.filter(is_active=True):
        current_value = objective.get_current_value(session)
        target_value = float(objective.target_value)
        is_met = objective.evaluate(session)
        
        objectives_data.append({
            'id': objective.id,
            'name': objective.name,
            'description': objective.description,
            'type': objective.get_objective_type_display(),
            'current_value': current_value,
            'target_value': target_value,
            'is_met': is_met,
            'is_primary': objective.is_primary,
            'is_failure_condition': objective.is_failure_condition,
            'progress_percentage': min((current_value / target_value) * 100, 200) if target_value > 0 else (100 if is_met else 0),
            'comparison_operator': objective.get_comparison_operator_display(),
        })
    
    return JsonResponse({
        'objectives': objectives_data,
        'game_mode': {
            'name': session_game_mode.game_mode.name,
            'type': session_game_mode.game_mode.get_mode_type_display(),
            'duration_months': session_game_mode.game_mode.duration_months,
        },
        'progress': {
            'current_score': float(session_game_mode.calculate_final_score()),
            'completion_percentage': float(session_game_mode.calculate_completion_percentage()),
            'months_remaining': max(0, session_game_mode.game_mode.duration_months - session.current_month),
        },
        'status': {
            'is_active': session_game_mode.is_active,
            'is_completed': session_game_mode.is_completed,
            'is_failed': session_game_mode.is_failed,
        }
    })


@login_required
@require_POST
def check_victory_conditions(request, session_id):
    """Manually trigger victory condition check"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    session_game_mode = getattr(session, 'game_mode_config', None)
    
    if not session_game_mode:
        return JsonResponse({'error': 'No game mode configured'}, status=400)
    
    # Check conditions
    session_game_mode.check_victory_conditions()
    
    return JsonResponse({
        'success': True,
        'is_completed': session_game_mode.is_completed,
        'is_failed': session_game_mode.is_failed,
        'message': 'Victory conditions checked'
    })


@login_required
def bankruptcy_status(request, session_id):
    """Check bankruptcy risk and status"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    session_game_mode = getattr(session, 'game_mode_config', None)
    
    if not session_game_mode:
        return JsonResponse({'error': 'No game mode configured'}, status=400)
    
    bankruptcy_checker = BankruptcyChecker(session, session_game_mode.game_mode)
    risk_assessment = bankruptcy_checker.assess_bankruptcy_risk()
    
    return JsonResponse({
        'current_balance': float(session.balance),
        'bankruptcy_threshold': float(session_game_mode.game_mode.bankruptcy_threshold),
        'risk_level': risk_assessment['risk_level'],
        'risk_factors': risk_assessment['risk_factors'],
        'recommendations': risk_assessment['recommendations'],
        'months_until_bankruptcy': risk_assessment.get('months_until_bankruptcy'),
        'is_bankrupt': session.balance < session_game_mode.game_mode.bankruptcy_threshold,
    })


@login_required
def leaderboard(request):
    """Show leaderboard of best performances"""
    # Get top results across all game modes
    top_results = GameResult.objects.select_related(
        'session_game_mode__session__user',
        'session_game_mode__game_mode'
    ).filter(
        result_type='victory'
    ).order_by('-final_score')[:50]
    
    # Group by game mode
    leaderboard_by_mode = {}
    for result in top_results:
        mode_name = result.session_game_mode.game_mode.name
        if mode_name not in leaderboard_by_mode:
            leaderboard_by_mode[mode_name] = []
        leaderboard_by_mode[mode_name].append(result)
    
    # Limit each mode to top 10
    for mode_name in leaderboard_by_mode:
        leaderboard_by_mode[mode_name] = leaderboard_by_mode[mode_name][:10]
    
    context = {
        'leaderboard_by_mode': leaderboard_by_mode,
        'user_best_results': GameResult.objects.filter(
            session_game_mode__session__user=request.user
        ).order_by('-final_score')[:5] if request.user.is_authenticated else [],
    }
    
    return render(request, 'game_objectives/leaderboard.html', context)


def calculate_bankruptcy_risk(session, game_mode):
    """Calculate bankruptcy risk level"""
    current_balance = float(session.balance)
    threshold = float(game_mode.bankruptcy_threshold)
    
    if current_balance < threshold:
        return {'level': 'critical', 'message': 'Bankrott!'}
    
    # Calculate distance to bankruptcy
    distance_to_bankruptcy = current_balance - threshold
    
    if distance_to_bankruptcy < 5000:
        return {'level': 'high', 'message': 'Hohes Risiko'}
    elif distance_to_bankruptcy < 15000:
        return {'level': 'medium', 'message': 'Mittleres Risiko'}
    elif distance_to_bankruptcy < 30000:
        return {'level': 'low', 'message': 'Niedriges Risiko'}
    else:
        return {'level': 'minimal', 'message': 'Minimales Risiko'}
