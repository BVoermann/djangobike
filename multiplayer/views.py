from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import json
import uuid

from .models import (
    MultiplayerGame, PlayerSession, TurnState, GameEvent, 
    MultiplayerGameInvitation, PlayerCommunication
)
from .simulation_engine import MultiplayerSimulationEngine, MultiplayerTurnManager
from .bankruptcy_manager import BankruptcyPreventionSystem
from .ai_manager import MultiplayerAIManager
from django.contrib.auth.models import User


@login_required
def multiplayer_lobby(request):
    """Main lobby view for multiplayer games."""
    # Get available games
    available_games = MultiplayerGame.objects.filter(
        status__in=['setup', 'waiting']
    ).exclude(
        players__user=request.user
    )
    
    # Get user's current games
    user_games = MultiplayerGame.objects.filter(
        players__user=request.user
    ).distinct()
    
    # Get pending invitations
    pending_invitations = MultiplayerGameInvitation.objects.filter(
        invited_user=request.user,
        status='pending'
    )
    
    context = {
        'available_games': available_games,
        'user_games': user_games,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, 'multiplayer/lobby.html', context)


@login_required
def create_game(request):
    """Create a new multiplayer game."""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            max_players = int(request.POST.get('max_players', 6))
            human_players = int(request.POST.get('human_players', 2))
            ai_players = max_players - human_players
            difficulty = request.POST.get('difficulty', 'medium')
            turn_deadline = int(request.POST.get('turn_deadline', 24))
            max_months = int(request.POST.get('max_months', 60))
            starting_balance = float(request.POST.get('starting_balance', 80000))
            bankruptcy_threshold = float(request.POST.get('bankruptcy_threshold', -50000))
            
            # Validate input
            if max_players < 2 or max_players > 10:
                messages.error(request, 'Maximum players must be between 2 and 10.')
                return render(request, 'multiplayer/create_game.html')
            
            if human_players < 1 or human_players > max_players:
                messages.error(request, 'Invalid number of human players.')
                return render(request, 'multiplayer/create_game.html')
            
            # Create the game
            game = MultiplayerGame.objects.create(
                name=name,
                description=description,
                max_players=max_players,
                human_players_count=human_players,
                ai_players_count=ai_players,
                difficulty=difficulty,
                turn_deadline_hours=turn_deadline,
                max_months=max_months,
                starting_balance=starting_balance,
                bankruptcy_threshold=bankruptcy_threshold,
                created_by=request.user,
                status='setup'
            )
            
            # Add creator as first player
            PlayerSession.objects.create(
                multiplayer_game=game,
                user=request.user,
                company_name=f"{request.user.username}'s Company",
                player_type='human',
                balance=starting_balance
            )
            
            # Create initial game event
            GameEvent.objects.create(
                multiplayer_game=game,
                event_type='game_started',
                message=f"Game '{name}' created by {request.user.username}",
                data={'creator': request.user.username}
            )
            
            messages.success(request, f"Game '{name}' created successfully!")
            return redirect('multiplayer:game_detail', game_id=game.id)
            
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error creating game: {str(e)}")
    
    return render(request, 'multiplayer/create_game.html')


@login_required
def game_detail(request, game_id):
    """Detailed view of a multiplayer game."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    # Check if user is a player in this game
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
        is_player = True
    except PlayerSession.DoesNotExist:
        player_session = None
        is_player = False
    
    # Get game statistics
    players = game.players.all().order_by('joined_at')
    active_players = game.players.filter(is_active=True, is_bankrupt=False)
    
    # Get recent events
    recent_events = GameEvent.objects.filter(
        multiplayer_game=game
    ).order_by('-timestamp')[:20]
    
    # Get turn status if game is active
    turn_status = None
    if game.status == 'active' and is_player:
        turn_manager = MultiplayerTurnManager(game)
        turn_status = turn_manager.check_turn_ready_status()
    
    # Get player's financial health if applicable
    financial_health = None
    if is_player and player_session:
        bankruptcy_prevention = BankruptcyPreventionSystem(game)
        financial_health = bankruptcy_prevention.get_financial_health_dashboard(player_session)
    
    context = {
        'game': game,
        'is_player': is_player,
        'player_session': player_session,
        'players': players,
        'active_players': active_players,
        'recent_events': recent_events,
        'turn_status': turn_status,
        'financial_health': financial_health,
        'can_join': not is_player and not game.is_full and game.status in ['setup', 'waiting'],
        'can_start': (
            is_player and 
            game.created_by == request.user and 
            game.status == 'setup' and 
            players.count() >= 2
        )
    }
    
    return render(request, 'multiplayer/game_detail.html', context)


@login_required
def join_game(request, game_id):
    """Join an existing multiplayer game."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    # Check if user can join
    if game.is_full:
        messages.error(request, "Game is full.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if game.status not in ['setup', 'waiting']:
        messages.error(request, "Cannot join a game that has already started.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    # Check if user is already in the game
    if PlayerSession.objects.filter(multiplayer_game=game, user=request.user).exists():
        messages.error(request, "You are already in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if request.method == 'POST':
        company_name = request.POST.get('company_name', f"{request.user.username}'s Company")
        
        # Create player session
        player_session = PlayerSession.objects.create(
            multiplayer_game=game,
            user=request.user,
            company_name=company_name,
            player_type='human',
            balance=game.starting_balance
        )
        
        # Create join event
        GameEvent.objects.create(
            multiplayer_game=game,
            event_type='player_joined',
            message=f"{company_name} joined the game",
            data={
                'player_id': str(player_session.id),
                'company_name': company_name,
                'username': request.user.username
            }
        )
        
        messages.success(request, f"Successfully joined game as {company_name}!")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    return render(request, 'multiplayer/join_game.html', {'game': game})


@login_required
def start_game(request, game_id):
    """Start a multiplayer game (add AI players and begin)."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    # Check permissions
    if game.created_by != request.user:
        messages.error(request, "Only the game creator can start the game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if game.status != 'setup':
        messages.error(request, "Game has already been started.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    current_players = game.players.count()
    if current_players < 2:
        messages.error(request, "Need at least 2 players to start the game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    try:
        with transaction.atomic():
            # Add AI players to fill remaining slots
            ai_players_needed = game.max_players - current_players
            ai_manager = MultiplayerAIManager(game)
            
            # Create AI players with different strategies
            ai_strategies = ['aggressive', 'conservative', 'innovative', 'balanced']
            
            for i in range(min(ai_players_needed, game.ai_players_count)):
                strategy = ai_strategies[i % len(ai_strategies)]
                
                ai_player = PlayerSession.objects.create(
                    multiplayer_game=game,
                    user=None,  # AI players have no user
                    company_name=f"AI Corp {i+1} ({strategy.title()})",
                    player_type='ai',
                    ai_strategy=strategy,
                    balance=game.starting_balance,
                    ai_difficulty=1.0 if game.difficulty == 'medium' else {
                        'easy': 0.6,
                        'hard': 1.3,
                        'expert': 1.5
                    }.get(game.difficulty, 1.0)
                )
                
                # Initialize AI player
                ai_manager.initialize_ai_player(ai_player)
            
            # Update game status
            game.status = 'active'
            game.started_at = timezone.now()
            game.save()
            
            # Create game start event
            GameEvent.objects.create(
                multiplayer_game=game,
                event_type='game_started',
                message=f"Game started with {game.players.count()} players",
                data={
                    'total_players': game.players.count(),
                    'human_players': game.players.filter(player_type='human').count(),
                    'ai_players': game.players.filter(player_type='ai').count()
                }
            )
            
            messages.success(request, "Game started successfully!")
            
    except Exception as e:
        messages.error(request, f"Error starting game: {str(e)}")
    
    return redirect('multiplayer:game_detail', game_id=game_id)


@login_required
def submit_decisions(request, game_id):
    """Submit player decisions for the current turn."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if game.status != 'active':
        messages.error(request, "Game is not active.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if player_session.is_bankrupt:
        messages.error(request, "Bankrupt players cannot submit decisions.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    # Get or create turn state
    turn_state, created = TurnState.objects.get_or_create(
        multiplayer_game=game,
        player_session=player_session,
        month=game.current_month,
        year=game.current_year,
        defaults={'decisions_submitted': False}
    )
    
    if request.method == 'POST':
        try:
            # Parse decision data from POST
            production_decisions = json.loads(request.POST.get('production_decisions', '{}'))
            procurement_decisions = json.loads(request.POST.get('procurement_decisions', '{}'))
            sales_decisions = json.loads(request.POST.get('sales_decisions', '{}'))
            hr_decisions = json.loads(request.POST.get('hr_decisions', '{}'))
            finance_decisions = json.loads(request.POST.get('finance_decisions', '{}'))
            
            # Update turn state
            turn_state.production_decisions = production_decisions
            turn_state.procurement_decisions = procurement_decisions
            turn_state.sales_decisions = sales_decisions
            turn_state.hr_decisions = hr_decisions
            turn_state.finance_decisions = finance_decisions
            turn_state.decisions_submitted = True
            turn_state.submitted_at = timezone.now()
            turn_state.save()
            
            # Check if all players have submitted and process turn if ready
            turn_manager = MultiplayerTurnManager(game)
            process_result = turn_manager.process_turn_if_ready()
            
            if process_result.get('processed'):
                messages.success(request, "Decisions submitted and turn processed!")
            else:
                messages.success(request, "Decisions submitted successfully! Waiting for other players.")
            
        except json.JSONDecodeError:
            messages.error(request, "Invalid decision data format.")
        except Exception as e:
            messages.error(request, f"Error submitting decisions: {str(e)}")
        
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    # GET request - show decision form
    context = {
        'game': game,
        'player_session': player_session,
        'turn_state': turn_state,
        'has_submitted': turn_state.decisions_submitted,
    }
    
    return render(request, 'multiplayer/submit_decisions.html', context)


@login_required
@require_http_methods(["POST"])
def process_turn(request, game_id):
    """Manually process turn (for game admin/creator)."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    if game.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if game.status != 'active':
        return JsonResponse({'error': 'Game is not active'}, status=400)
    
    try:
        turn_manager = MultiplayerTurnManager(game)
        result = turn_manager.process_turn_if_ready()
        
        return JsonResponse({
            'success': True,
            'processed': result.get('processed', False),
            'result': result
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def game_events(request, game_id):
    """Get recent game events (AJAX endpoint)."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    # Check if user is a player
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        return JsonResponse({'error': 'Not a player in this game'}, status=403)
    
    # Get events since last check
    since = request.GET.get('since')
    events_query = GameEvent.objects.filter(multiplayer_game=game)
    
    if since:
        try:
            since_time = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            events_query = events_query.filter(timestamp__gt=since_time)
        except ValueError:
            pass
    
    events = events_query.order_by('-timestamp')[:50]
    
    events_data = []
    for event in events:
        # Check if event is visible to this player
        if event.visible_to_all or event.visible_to.filter(id=player_session.id).exists():
            events_data.append({
                'id': event.id,
                'type': event.event_type,
                'message': event.message,
                'timestamp': event.timestamp.isoformat(),
                'data': event.data
            })
    
    return JsonResponse({
        'events': events_data,
        'game_status': game.status,
        'current_turn': f"{game.current_year}/{game.current_month:02d}",
        'active_players': game.active_players_count
    })


@login_required
def leaderboard(request, game_id):
    """Show game leaderboard and statistics."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    # Get all players ordered by various metrics
    players_by_balance = game.players.all().order_by('-balance')
    players_by_revenue = game.players.all().order_by('-total_revenue')
    players_by_profit = game.players.all().order_by('-total_profit')
    players_by_market_share = game.players.all().order_by('-market_share')
    
    # Calculate rankings
    rankings = {}
    for i, player in enumerate(players_by_balance, 1):
        rankings[player.id] = {
            'balance_rank': i,
            'player': player
        }
    
    for i, player in enumerate(players_by_revenue, 1):
        rankings[player.id]['revenue_rank'] = i
    
    for i, player in enumerate(players_by_profit, 1):
        rankings[player.id]['profit_rank'] = i
    
    for i, player in enumerate(players_by_market_share, 1):
        rankings[player.id]['market_share_rank'] = i
    
    context = {
        'game': game,
        'rankings': rankings,
        'players_by_balance': players_by_balance,
    }
    
    return render(request, 'multiplayer/leaderboard.html', context)


@login_required
def financial_dashboard(request, game_id):
    """Show detailed financial dashboard for player."""
    game = get_object_or_404(MultiplayerGame, id=game_id)
    
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    # Get financial health analysis
    bankruptcy_prevention = BankruptcyPreventionSystem(game)
    financial_health = bankruptcy_prevention.get_financial_health_dashboard(player_session)
    
    # Get recent turn states for performance history
    recent_turns = TurnState.objects.filter(
        multiplayer_game=game,
        player_session=player_session
    ).order_by('-year', '-month')[:12]
    
    context = {
        'game': game,
        'player_session': player_session,
        'financial_health': financial_health,
        'recent_turns': recent_turns,
    }
    
    return render(request, 'multiplayer/financial_dashboard.html', context)
