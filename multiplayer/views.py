from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import json
import uuid
import tempfile
import os

from .models import (
    MultiplayerGame, PlayerSession, TurnState, GameEvent,
    MultiplayerGameInvitation, PlayerCommunication
)
from .simulation_engine import MultiplayerSimulationEngine, MultiplayerTurnManager
from .bankruptcy_manager import BankruptcyPreventionSystem
from .ai_manager import MultiplayerAIManager
from .player_state_manager import PlayerStateManager
from django.contrib.auth.models import User
from functools import wraps


def handle_deleted_game(view_func):
    """Decorator to handle deleted/non-existent multiplayer games gracefully."""
    @wraps(view_func)
    def wrapper(request, game_id, *args, **kwargs):
        try:
            return view_func(request, game_id, *args, **kwargs)
        except MultiplayerGame.DoesNotExist:
            messages.error(request, 'Das Spiel existiert nicht mehr oder wurde gelöscht.')
            return redirect('bikeshop:dashboard')
    return wrapper


@login_required
def multiplayer_lobby(request):
    """Main lobby view for multiplayer games."""
    # Get available games
    available_games = MultiplayerGame.objects.filter(
        status__in=['setup', 'waiting']
    ).exclude(
        players__user=request.user
    )

    # Get user's current games (games where user is actively playing)
    user_games = MultiplayerGame.objects.filter(
        players__user=request.user
    ).distinct()

    # Get games assigned to user by admin
    assigned_games = MultiplayerGame.objects.filter(
        assigned_users=request.user
    ).exclude(
        players__user=request.user  # Exclude games already joined
    ).distinct()

    # Get pending invitations
    pending_invitations = MultiplayerGameInvitation.objects.filter(
        invited_user=request.user,
        status='pending'
    )

    context = {
        'available_games': available_games,
        'user_games': user_games,
        'assigned_games': assigned_games,
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

            messages.success(request, f"Game '{name}' created successfully! Please upload game parameters to continue.")
            # Redirect to parameter upload page to enforce the workflow
            return redirect('multiplayer:upload_parameters', game_id=game.id)
            
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error creating game: {str(e)}")
    
    return render(request, 'multiplayer/create_game.html')


@login_required
@handle_deleted_game
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

    # Check if user is assigned to this game by admin
    is_assigned = game.assigned_users.filter(id=request.user.id).exists()
    
    # Get game statistics
    players = game.players.all().order_by('joined_at')
    active_players = game.players.filter(is_active=True, is_bankrupt=False)
    
    # Get recent events
    recent_events = GameEvent.objects.filter(
        multiplayer_game=game
    ).order_by('-timestamp')[:20]
    
    # Auto-process turn if deadline has passed (check on every page load)
    if game.status == 'active':
        turn_manager = MultiplayerTurnManager(game)

        # Check if deadline has passed
        if turn_manager._is_deadline_passed():
            try:
                # Automatically process the turn
                process_result = turn_manager.process_turn_if_ready()
                if process_result.get('processed'):
                    messages.info(request, "Turn deadline expired. Turn has been automatically processed!")
                    # Refresh the game object to get updated state
                    game.refresh_from_db()
            except Exception as e:
                messages.warning(request, f"Turn deadline passed but auto-process failed: {str(e)}")

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

    # Get turn countdown if applicable
    turn_countdown = None
    can_process_turn = True
    if game.status == 'active':
        can_process_turn, _ = game.can_process_next_turn()
        if not can_process_turn:
            turn_countdown = game.get_next_turn_countdown()

    # Check if parameters are uploaded (required for joining and starting)
    parameters_uploaded = game.parameters_uploaded and game.parameters_file

    context = {
        'game': game,
        'is_player': is_player,
        'is_assigned': is_assigned,
        'player_session': player_session,
        'players': players,
        'active_players': active_players,
        'recent_events': recent_events,
        'turn_status': turn_status,
        'financial_health': financial_health,
        'turn_countdown': turn_countdown,
        'can_process_turn': can_process_turn,
        'parameters_uploaded': parameters_uploaded,
        'can_join': (
            parameters_uploaded and  # Parameters must be uploaded before joining
            (not is_player and not game.is_full and game.status in ['setup', 'waiting']) or
            (is_assigned and not is_player)
        ),
        'can_start': (
            game.created_by == request.user and
            game.status == 'setup' and
            parameters_uploaded and  # Parameters must be uploaded before starting
            players.count() >= 1  # Allow starting with just 1 human player (AI will fill the rest)
        ),
        'is_creator': game.created_by == request.user
    }

    return render(request, 'multiplayer/game_detail.html', context)


@login_required
@handle_deleted_game
def join_game(request, game_id):
    """Join an existing multiplayer game."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check if user is assigned to this game
    is_assigned = game.assigned_users.filter(id=request.user.id).exists()

    # CRITICAL: Check if parameters have been uploaded (REQUIRED before joining)
    if not game.parameters_uploaded or not game.parameters_file:
        messages.error(request, "Cannot join this game yet. The game administrator must upload game parameters (Excel files) before players can join.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Check if user can join
    if not is_assigned and game.is_full:
        messages.error(request, "Game is full.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if not is_assigned and game.status not in ['setup', 'waiting']:
        messages.error(request, "Cannot join a game that has already started.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Assigned users can join even if game is in other states
    if is_assigned and game.status not in ['setup', 'waiting', 'active']:
        messages.error(request, "This game is not accepting players.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Check if user is already in the game
    if PlayerSession.objects.filter(multiplayer_game=game, user=request.user).exists():
        messages.error(request, "You are already in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    if request.method == 'POST':
        # Use user's default company name if available
        default_company = request.user.company_name if hasattr(request.user, 'company_name') and request.user.company_name else f"{request.user.username}'s Company"
        company_name = request.POST.get('company_name', default_company)
        
        # Create player session
        player_session = PlayerSession.objects.create(
            multiplayer_game=game,
            user=request.user,
            company_name=company_name,
            player_type='human',
            balance=game.starting_balance
        )

        # Initialize player game state
        state_manager = PlayerStateManager(game)
        state_manager.initialize_player_game_state(player_session)

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

        messages.success(request, f"Successfully joined game as {company_name}! Your game state has been initialized.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    return render(request, 'multiplayer/join_game.html', {'game': game})


@login_required
@handle_deleted_game
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

    # Check if parameters have been uploaded (REQUIRED)
    if not game.parameters_uploaded or not game.parameters_file:
        messages.error(request, "You must upload game parameters before starting the game. Please upload the Excel parameter files.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    current_players = game.players.count()
    if current_players < 1:
        messages.error(request, "Need at least 1 player to start the game.")
        return redirect('multiplayer:game_detail', game_id=game_id)
    
    try:
        with transaction.atomic():
            # Add AI players to fill remaining slots
            ai_players_needed = game.max_players - current_players
            ai_manager = MultiplayerAIManager(game)
            state_manager = PlayerStateManager(game)

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

                # Initialize AI player game state (AI players also need game state)
                # Note: AI players won't have a user, so we'll need to handle that
                # For now, AI players will share or have simulated state
                # state_manager.initialize_player_game_state(ai_player)

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
@handle_deleted_game
def submit_decisions(request, game_id):
    """Submit player decisions for the current turn - shows full game interface."""
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
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    if player_session.is_bankrupt:
        messages.error(request, "Bankrupt players cannot submit decisions.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Auto-process turn if deadline has passed (check on every page load)
    turn_manager = MultiplayerTurnManager(game)
    if turn_manager._is_deadline_passed():
        try:
            process_result = turn_manager.process_turn_if_ready()
            if process_result.get('processed'):
                messages.info(request, "Turn deadline expired. Turn has been automatically processed!")
                game.refresh_from_db()
        except Exception as e:
            messages.warning(request, f"Turn deadline passed but auto-process failed: {str(e)}")

    # Get or create turn state
    turn_state, created = TurnState.objects.get_or_create(
        multiplayer_game=game,
        player_session=player_session,
        month=game.current_month,
        year=game.current_year,
        defaults={'decisions_submitted': False}
    )

    # Get game data for display
    from simulation.engine import SimulationEngine
    sim_engine = SimulationEngine(game_session)
    dashboard_data = sim_engine.get_dashboard_data()

    if request.method == 'POST':
        if request.POST.get('action') == 'submit_turn':
            try:
                # Mark turn as submitted
                turn_state.decisions_submitted = True
                turn_state.submitted_at = timezone.now()
                turn_state.save()

                # Check if all players have submitted and process turn if ready
                turn_manager = MultiplayerTurnManager(game)
                process_result = turn_manager.process_turn_if_ready()

                if process_result.get('processed'):
                    messages.success(request, "Decisions submitted and turn processed! Game advanced to next month.")
                else:
                    messages.success(request, "Decisions submitted successfully! Waiting for other players.")

            except Exception as e:
                messages.error(request, f"Error submitting decisions: {str(e)}")

            return redirect('multiplayer:game_detail', game_id=game_id)

    # GET request - show game interface
    context = {
        'game': game,
        'player_session': player_session,
        'session': game_session,
        'turn_state': turn_state,
        'has_submitted': turn_state.decisions_submitted,
        'dashboard_data': dashboard_data,
    }

    return render(request, 'multiplayer/submit_decisions.html', context)


@login_required
@handle_deleted_game
@require_http_methods(["POST"])
def process_turn(request, game_id):
    """Manually process turn (for game admin/creator)."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check permissions - only game creator or staff can manually advance
    if game.created_by != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if game.status != 'active':
        return JsonResponse({'error': 'Game is not active'}, status=400)

    # Check if this is a forced advancement
    force_advance = request.POST.get('force', 'false').lower() == 'true'

    try:
        turn_manager = MultiplayerTurnManager(game)

        if force_advance:
            # Force process the turn regardless of submission status
            from .simulation_engine import MultiplayerSimulationEngine
            sim_engine = MultiplayerSimulationEngine(game)
            result = sim_engine.process_multiplayer_turn()

            # Check if processing was successful
            if result.get('success', False):
                # Log the forced advancement
                from .models import GameEvent
                GameEvent.objects.create(
                    multiplayer_game=game,
                    event_type='system_message',
                    message=f"Administrator {request.user.username} hat den Zug manuell vorangetrieben",
                    data={'forced': True, 'month': game.current_month, 'year': game.current_year}
                )

                return JsonResponse({
                    'success': True,
                    'processed': True,
                    'forced': True,
                    'result': result
                })
            else:
                # Processing failed
                return JsonResponse({
                    'success': False,
                    'processed': False,
                    'error': result.get('error', 'Turn processing failed'),
                    'result': result
                })
        else:
            # Normal processing - only if ready
            result = turn_manager.process_turn_if_ready()

            return JsonResponse({
                'success': True,
                'processed': result.get('processed', False),
                'forced': False,
                'result': result
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@handle_deleted_game
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
@handle_deleted_game
def leaderboard(request, game_id):
    """Show game leaderboard and statistics."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Allow viewing leaderboard for all game states except cancelled (players may want to see final standings)
    if game.status == 'cancelled':
        messages.error(request, "This game has been cancelled.")
        return redirect('multiplayer:lobby')

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
@handle_deleted_game
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

    # Allow viewing dashboard for all game states except cancelled (informational view only)
    if game.status == 'cancelled':
        messages.error(request, "This game has been cancelled.")
        return redirect('multiplayer:lobby')

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


@login_required
@handle_deleted_game
def multiplayer_procurement(request, game_id):
    """Procurement view for multiplayer games - based on single player implementation."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check if user is a player in this game
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if game.status != 'active':
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Import models needed for procurement
    from bikeshop.models import Supplier, SupplierPrice, BikeType, Component, ComponentType
    from procurement.models import ProcurementOrder, ProcurementOrderItem
    from warehouse.models import Warehouse, ComponentStock

    suppliers = Supplier.objects.filter(session=game_session)
    bike_types = BikeType.objects.filter(session=game_session)

    # Create bike type component mapping using new flexible system
    bike_component_mapping = {}
    for bike_type in bike_types:
        compatible_component_ids = []

        requirements = bike_type.get_required_components()

        if not requirements:
            # Fallback: use legacy system if available
            legacy_components = []
            if bike_type.wheel_set:
                legacy_components.append(bike_type.wheel_set.id)
            if bike_type.frame:
                legacy_components.append(bike_type.frame.id)
            if bike_type.handlebar:
                legacy_components.append(bike_type.handlebar.id)
            if bike_type.saddle:
                legacy_components.append(bike_type.saddle.id)
            if bike_type.gearshift:
                legacy_components.append(bike_type.gearshift.id)
            if bike_type.motor:
                legacy_components.append(bike_type.motor.id)

            if legacy_components:
                compatible_component_ids = legacy_components
            else:
                # Ultimate fallback: include all components
                all_components = Component.objects.filter(session=game_session)
                compatible_component_ids = [c.id for c in all_components]
        else:
            # Use the new requirements system
            for component_type_name, compatible_names in requirements.items():
                component_type = ComponentType.objects.filter(
                    session=game_session,
                    name=component_type_name
                ).first()

                if component_type:
                    compatible_components = Component.objects.filter(
                        session=game_session,
                        component_type=component_type,
                        name__in=compatible_names
                    )
                    compatible_component_ids.extend([c.id for c in compatible_components])

        bike_component_mapping[bike_type.id] = compatible_component_ids

    # Get supplier data
    supplier_data = {}
    supplier_data_json = {}
    for supplier in suppliers:
        prices = SupplierPrice.objects.filter(session=game_session, supplier=supplier).select_related(
            'component__component_type')
        supplier_data[supplier.id] = {
            'supplier': supplier,
            'prices': prices
        }

        # Create JSON-serializable version for JavaScript
        supplier_data_json[str(supplier.id)] = {
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'quality': supplier.quality,
                'delivery_time': supplier.delivery_time,
                'payment_terms': supplier.payment_terms,
                'complaint_probability': float(supplier.complaint_probability)
            },
            'prices': [
                {
                    'component': {
                        'id': price.component.id,
                        'name': price.component.name,
                        'component_type': {
                            'name': price.component.component_type.name
                        }
                    },
                    'price': float(price.price)
                }
                for price in prices
            ]
        }

    if request.method == 'POST':
        try:
            with transaction.atomic():
                order_data = json.loads(request.body)
                total_cost = Decimal('0')

                # Get all warehouses for this session
                warehouses = Warehouse.objects.filter(session=game_session)

                # Create warehouse if none exist
                if not warehouses.exists():
                    warehouse = Warehouse.objects.create(
                        session=game_session,
                        name='Hauptlager',
                        location='Standort 1',
                        capacity_m2=200.0,
                        rent_per_month=Decimal('2500.00')
                    )
                    warehouses = [warehouse]

                # Calculate total remaining capacity across all warehouses
                total_remaining_capacity = sum(w.remaining_capacity for w in warehouses)
                total_current_usage = sum(w.current_usage for w in warehouses)
                total_capacity = sum(w.capacity_m2 for w in warehouses)

                # First pass: Check warehouse capacity for all items
                total_required_space = 0
                for supplier_id, items in order_data.items():
                    if not items:
                        continue

                    for item in items:
                        component_id = item['component_id']
                        quantity = int(item['quantity'])

                        if quantity <= 0:
                            continue

                        price_obj = SupplierPrice.objects.filter(
                            session=game_session,
                            supplier_id=supplier_id,
                            component_id=component_id
                        ).first()

                        if price_obj:
                            required_space = warehouses[0].get_required_space_for_components(price_obj.component, quantity)
                            total_required_space += required_space

                # Check if total order would exceed total warehouse capacity
                if total_required_space > total_remaining_capacity:
                    current_percentage = (total_current_usage / total_capacity * 100) if total_capacity > 0 else 100
                    new_usage = total_current_usage + total_required_space
                    new_percentage = (new_usage / total_capacity) * 100 if total_capacity > 0 else 100

                    return JsonResponse({
                        'success': False,
                        'error': f'Lagerkapazität überschritten! Diese Bestellung würde {total_required_space:.1f}m² benötigen, aber nur {total_remaining_capacity:.1f}m² sind in allen Lagern verfügbar. Aktuelle Auslastung: {current_percentage:.1f}%, nach Bestellung: {new_percentage:.1f}%. Bitte kaufen Sie zusätzliche Lagerkapazität oder reduzieren Sie die Bestellmenge.'
                    })

                # Second pass: Create orders (capacity check passed)
                for supplier_id, items in order_data.items():
                    if not items:
                        continue

                    supplier = get_object_or_404(Supplier, id=supplier_id, session=game_session)
                    order = ProcurementOrder.objects.create(
                        session=game_session,
                        supplier=supplier,
                        month=game_session.current_month,
                        year=game_session.current_year
                    )

                    order_total = Decimal('0')
                    for item in items:
                        component_id = item['component_id']
                        quantity = int(item['quantity'])

                        if quantity <= 0:
                            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'})

                        price_obj = get_object_or_404(SupplierPrice,
                                                      session=game_session,
                                                      supplier=supplier,
                                                      component_id=component_id
                                                      )

                        ProcurementOrderItem.objects.create(
                            order=order,
                            component=price_obj.component,
                            quantity_ordered=quantity,
                            quantity_delivered=quantity,
                            unit_price=price_obj.price
                        )

                        # Find a warehouse with available capacity
                        required_space = warehouses[0].get_required_space_for_components(price_obj.component, quantity)
                        target_warehouse = None

                        for wh in warehouses:
                            if wh.remaining_capacity >= required_space:
                                target_warehouse = wh
                                break

                        # If no single warehouse has enough space, use the one with most space
                        if not target_warehouse:
                            target_warehouse = max(warehouses, key=lambda w: w.remaining_capacity)

                        # Add to warehouse inventory (track supplier for quality!)
                        component_stock, created = ComponentStock.objects.get_or_create(
                            session=game_session,
                            warehouse=target_warehouse,
                            component=price_obj.component,
                            supplier=supplier,  # Track which supplier this came from
                            defaults={'quantity': 0}
                        )
                        component_stock.quantity += quantity
                        component_stock.save()

                        order_total += price_obj.price * quantity

                    order.total_cost = order_total
                    order.save()
                    total_cost += order_total

                # Reduce balance
                game_session.balance -= total_cost
                game_session.save()

                # Update turn state to track procurement decisions
                turn_state, created = TurnState.objects.get_or_create(
                    multiplayer_game=game,
                    player_session=player_session,
                    month=game.current_month,
                    year=game.current_year,
                    defaults={'decisions_submitted': False}
                )

                # Store procurement decisions
                if not turn_state.procurement_decisions:
                    turn_state.procurement_decisions = {}
                turn_state.procurement_decisions['total_cost'] = float(total_cost)
                turn_state.procurement_decisions['timestamp'] = timezone.now().isoformat()
                turn_state.save()

                # Check if this is a single human player game and all decisions are submitted
                response_data = {'success': True, 'message': 'Bestellung erfolgreich aufgegeben und Komponenten ins Lager eingelagert!'}

                if game.is_single_human_player_game and turn_state.decisions_submitted:
                    # Auto-process the turn immediately
                    from .simulation_engine import MultiplayerTurnManager
                    turn_manager = MultiplayerTurnManager(game)
                    result = turn_manager.process_turn_if_ready()

                    if result.get('processed'):
                        response_data['turn_processed'] = True
                        response_data['message'] = 'Bestellung erfolgreich! Turn wurde automatisch verarbeitet.'

                return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    context = {
        'game': game,
        'player_session': player_session,
        'session': game_session,
        'supplier_data': supplier_data,
        'supplier_data_json': json.dumps(supplier_data_json),
        'bike_types': bike_types,
        'bike_component_mapping': json.dumps(bike_component_mapping)
    }

    return render(request, 'multiplayer/procurement.html', context)


@login_required
@handle_deleted_game
def multiplayer_production(request, game_id):
    """Production view for multiplayer games - based on single player implementation."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check if user is a player in this game
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if game.status != 'active':
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Import models needed for production
    from bikeshop.models import BikeType, Worker
    from production.models import ProductionPlan, ProductionOrder, ProducedBike
    from warehouse.models import Warehouse, ComponentStock, BikeStock

    bike_types = BikeType.objects.filter(session=game_session)
    workers = Worker.objects.filter(session=game_session)
    component_stocks = ComponentStock.objects.filter(session=game_session)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                production_data = json.loads(request.body)

                plan, created = ProductionPlan.objects.get_or_create(
                    session=game_session,
                    month=game_session.current_month,
                    year=game_session.current_year
                )

                # Delete old orders
                plan.orders.all().delete()

                total_skilled_hours = 0
                total_unskilled_hours = 0
                total_bikes_produced = 0

                # Check if upgrades are needed and collect upgrade information
                upgrades_needed = []
                component_requirements = {}

                # First pass: Calculate requirements and check feasibility
                for item in production_data:
                    bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=game_session)

                    for segment in ['cheap', 'standard', 'premium']:
                        quantity = int(item.get(f'quantity_{segment}', 0))

                        if quantity > 0:
                            # Calculate worker hours
                            total_skilled_hours += bike_type.skilled_worker_hours * quantity
                            total_unskilled_hours += bike_type.unskilled_worker_hours * quantity
                            total_bikes_produced += quantity

                            # Use the new flexible component matching system
                            component_match_result = bike_type.find_best_components_for_segment(game_session, segment)

                            # Check if any components are missing
                            if component_match_result['missing']:
                                missing_components = ', '.join(component_match_result['missing'])
                                return JsonResponse({
                                    'success': False,
                                    'error': f'Keine verfügbaren Komponenten für {segment} {bike_type.name}! Fehlend: {missing_components}'
                                })

                            # Collect upgrade information for confirmation
                            if component_match_result['upgrades']:
                                for upgrade in component_match_result['upgrades']:
                                    upgrade_info = {
                                        'bike_type': bike_type.name,
                                        'segment': segment,
                                        'component_type': upgrade['component_type'],
                                        'component_name': upgrade['component_name'],
                                        'component_quality': upgrade['component_quality'],
                                        'target_segment': upgrade['target_segment']
                                    }
                                    upgrades_needed.append(upgrade_info)

                            # Add component requirements
                            for component_type_name, component in component_match_result['components'].items():
                                if component.id not in component_requirements:
                                    component_requirements[component.id] = 0
                                component_requirements[component.id] += quantity

                # If upgrades are needed and user hasn't confirmed, ask for confirmation
                confirm_upgrades = request.GET.get('confirm_upgrades', '').lower() == 'true'
                if upgrades_needed and not confirm_upgrades:
                    return JsonResponse({
                        'success': False,
                        'upgrades_needed': True,
                        'upgrades': upgrades_needed,
                        'message': 'Qualitäts-Upgrades erforderlich. Bestätigung benötigt.'
                    })

                # Check worker capacity (remaining hours for this month)
                skilled_worker = workers.filter(worker_type='skilled').first()
                unskilled_worker = workers.filter(worker_type='unskilled').first()

                # Get remaining hours for current month
                skilled_capacity = skilled_worker.get_remaining_hours(game_session.current_month, game_session.current_year) if skilled_worker else 0
                unskilled_capacity = unskilled_worker.get_remaining_hours(game_session.current_month, game_session.current_year) if unskilled_worker else 0

                if total_skilled_hours > skilled_capacity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Nicht genügend Facharbeiter-Kapazität! Benötigt: {total_skilled_hours}h, Verfügbar: {skilled_capacity}h'
                    })

                if total_unskilled_hours > unskilled_capacity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Nicht genügend Hilfsarbeiter-Kapazität! Benötigt: {total_unskilled_hours}h, Verfügbar: {unskilled_capacity}h'
                    })

                # Check component availability
                component_stocks_dict = {}
                for stock in component_stocks:
                    component_stocks_dict[stock.component.id] = stock

                for component_id, required_quantity in component_requirements.items():
                    if component_id not in component_stocks_dict:
                        return JsonResponse({
                            'success': False,
                            'error': f'Komponente nicht im Lager vorhanden!'
                        })

                    available_quantity = component_stocks_dict[component_id].quantity
                    if available_quantity < required_quantity:
                        component_name = component_stocks_dict[component_id].component.name
                        return JsonResponse({
                            'success': False,
                            'error': f'Nicht genügend {component_name} im Lager! Benötigt: {required_quantity}, Verfügbar: {available_quantity}'
                        })

                # Get all warehouses for storage
                warehouses = Warehouse.objects.filter(session=game_session)
                if not warehouses.exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Kein Lager verfügbar!'
                    })

                # Calculate total remaining capacity across all warehouses
                total_remaining_capacity = sum(w.remaining_capacity for w in warehouses)
                total_current_usage = sum(w.current_usage for w in warehouses)
                total_capacity = sum(w.capacity_m2 for w in warehouses)

                # Check warehouse capacity for bikes
                total_bike_space_needed = 0
                for item in production_data:
                    bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=game_session)
                    for segment in ['cheap', 'standard', 'premium']:
                        quantity = int(item.get(f'quantity_{segment}', 0))
                        if quantity > 0:
                            bike_space = warehouses[0].get_required_space_for_bikes(bike_type, quantity)
                            total_bike_space_needed += bike_space

                # Check if production would exceed total warehouse capacity
                if total_bike_space_needed > total_remaining_capacity:
                    current_percentage = (total_current_usage / total_capacity * 100) if total_capacity > 0 else 100
                    new_usage = total_current_usage + total_bike_space_needed
                    new_percentage = (new_usage / total_capacity) * 100 if total_capacity > 0 else 100

                    return JsonResponse({
                        'success': False,
                        'error': f'Lagerkapazität überschritten! Die geplante Produktion würde {total_bike_space_needed:.1f}m² benötigen, aber nur {total_remaining_capacity:.1f}m² sind in allen Lagern verfügbar. Aktuelle Auslastung: {current_percentage:.1f}%, nach Produktion: {new_percentage:.1f}%. Bitte kaufen Sie zusätzliche Lagerkapazität oder reduzieren Sie die Produktionsmenge.'
                    })

                # Second pass: Actually produce bikes and update inventory
                for item in production_data:
                    bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=game_session)

                    for segment in ['cheap', 'standard', 'premium']:
                        quantity = int(item.get(f'quantity_{segment}', 0))

                        if quantity > 0:
                            # Create production order
                            production_order = ProductionOrder.objects.create(
                                plan=plan,
                                bike_type=bike_type,
                                price_segment=segment,
                                quantity_planned=quantity
                            )

                            # Produce individual bikes and add to warehouse
                            for _ in range(quantity):
                                produced_bike = ProducedBike.objects.create(
                                    session=game_session,
                                    bike_type=bike_type,
                                    price_segment=segment,
                                    production_month=game_session.current_month,
                                    production_year=game_session.current_year
                                )

                                # Find a warehouse with available capacity for this bike
                                bike_space_needed = bike_type.storage_space_per_unit
                                target_warehouse = None

                                for wh in warehouses:
                                    if wh.remaining_capacity >= bike_space_needed:
                                        target_warehouse = wh
                                        break

                                # If no single warehouse has enough space, use the one with most space
                                if not target_warehouse:
                                    target_warehouse = max(warehouses, key=lambda w: w.remaining_capacity)

                                # Add to warehouse inventory
                                BikeStock.objects.create(
                                    session=game_session,
                                    warehouse=target_warehouse,
                                    bike=produced_bike
                                )

                # Update component stocks (reduce quantities)
                for component_id, used_quantity in component_requirements.items():
                    stock = component_stocks_dict[component_id]
                    stock.quantity -= used_quantity
                    stock.save()

                # Subtract used hours from workers' available time for this month
                if skilled_worker and total_skilled_hours > 0:
                    skilled_worker.use_hours(total_skilled_hours, game_session.current_month, game_session.current_year)

                if unskilled_worker and total_unskilled_hours > 0:
                    unskilled_worker.use_hours(total_unskilled_hours, game_session.current_month, game_session.current_year)

                # Update turn state to track production decisions
                turn_state, created = TurnState.objects.get_or_create(
                    multiplayer_game=game,
                    player_session=player_session,
                    month=game.current_month,
                    year=game.current_year,
                    defaults={'decisions_submitted': False}
                )

                # Store production decisions
                if not turn_state.production_decisions:
                    turn_state.production_decisions = {}
                turn_state.production_decisions['total_bikes_produced'] = total_bikes_produced
                turn_state.production_decisions['timestamp'] = timezone.now().isoformat()
                turn_state.save()

                # Check if this is a single human player game and all decisions are submitted
                response_data = {
                    'success': True,
                    'message': f'Produktion erfolgreich! {total_bikes_produced} Fahrräder produziert und ins Lager eingelagert.'
                }

                if game.is_single_human_player_game and turn_state.decisions_submitted:
                    # Auto-process the turn immediately
                    from .simulation_engine import MultiplayerTurnManager
                    turn_manager = MultiplayerTurnManager(game)
                    result = turn_manager.process_turn_if_ready()

                    if result.get('processed'):
                        response_data['turn_processed'] = True
                        response_data['message'] = f'Produktion erfolgreich! {total_bikes_produced} Fahrräder produziert. Turn wurde automatisch verarbeitet.'

                return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Calculate remaining hours for each worker type
    skilled_worker = workers.filter(worker_type='skilled').first()
    unskilled_worker = workers.filter(worker_type='unskilled').first()

    skilled_remaining = skilled_worker.get_remaining_hours(game_session.current_month, game_session.current_year) if skilled_worker else 0
    unskilled_remaining = unskilled_worker.get_remaining_hours(game_session.current_month, game_session.current_year) if unskilled_worker else 0

    context = {
        'game': game,
        'player_session': player_session,
        'session': game_session,
        'bike_types': bike_types,
        'workers': workers,
        'component_stocks': component_stocks,
        'skilled_remaining': skilled_remaining,
        'unskilled_remaining': unskilled_remaining,
    }

    return render(request, 'multiplayer/production.html', context)


@login_required
@handle_deleted_game
def multiplayer_warehouse(request, game_id):
    """Warehouse view for multiplayer games - based on single player implementation."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check if user is a player in this game
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if game.status != 'active':
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Import warehouse models
    from warehouse.models import Warehouse, ComponentStock, BikeStock
    from django.db.models import Count

    warehouses = Warehouse.objects.filter(session=game_session)

    warehouse_data = []
    total_capacity = 0
    total_rent = 0

    for warehouse in warehouses:
        stocks = ComponentStock.objects.filter(warehouse=warehouse).select_related('component__component_type')

        # Group bikes by bike_type and price_segment
        bike_groups = BikeStock.objects.filter(
            warehouse=warehouse
        ).values(
            'bike__bike_type__id',
            'bike__bike_type__name',
            'bike__price_segment',
            'bike__bike_type__storage_space_per_unit'
        ).annotate(
            count=Count('id')
        ).order_by('bike__bike_type__name', 'bike__price_segment')

        warehouse_data.append({
            'warehouse': warehouse,
            'stocks': stocks,
            'bike_groups': bike_groups,
            'usage': warehouse.current_usage,
            'remaining': warehouse.remaining_capacity
        })
        total_capacity += warehouse.capacity_m2
        total_rent += warehouse.rent_per_month

    context = {
        'game': game,
        'player_session': player_session,
        'session': game_session,
        'warehouse_data': warehouse_data,
        'total_capacity': total_capacity,
        'total_rent': total_rent
    }

    return render(request, 'multiplayer/warehouse.html', context)


@login_required
@handle_deleted_game
def multiplayer_sales(request, game_id):
    """Sales view for multiplayer games - DEFERRED SALES SYSTEM.

    Stores sales decisions in TurnState and shows preview of expected sales.
    Actual sales are processed when turn advances using MarketSimulator.
    """
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check if user is a player in this game
    try:
        player_session = PlayerSession.objects.get(
            multiplayer_game=game,
            user=request.user
        )
    except PlayerSession.DoesNotExist:
        messages.error(request, "You are not a player in this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if game.status != 'active':
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Import models needed for sales
    from bikeshop.models import BikePrice, BikeType
    from sales.models import Market, MarketDemand, SalesOrder
    from production.models import ProducedBike
    from finance.models import Transaction
    from django.db.models import Count, Avg, Min, Sum
    from collections import defaultdict

    markets = Market.objects.filter(session=game_session)

    # Get or create current turn state
    turn_state, created = TurnState.objects.get_or_create(
        multiplayer_game=game,
        player_session=player_session,
        month=game.current_month,
        year=game.current_year,
        defaults={'decisions_submitted': False}
    )

    # Helper function for price ranges
    def get_price_range(bike_type, price_segment, session):
        """Calculate realistic price range for selling based on quality and base price"""
        try:
            base_price = BikePrice.objects.get(
                session=session,
                bike_type=bike_type,
                price_segment=price_segment
            ).price
        except BikePrice.DoesNotExist:
            # Fallback to default ranges if no base price found
            default_ranges = {
                'cheap': (200, 500),
                'standard': (400, 800),
                'premium': (600, 1200)
            }
            return default_ranges.get(price_segment, (200, 500))

        # Define multipliers for each quality level
        multipliers = {
            'cheap': (0.8, 1.2),
            'standard': (1.0, 1.5),
            'premium': (1.2, 2.0)
        }

        min_mult, max_mult = multipliers.get(price_segment, (0.8, 1.2))
        min_price = float(base_price * Decimal(str(min_mult)))
        max_price = float(base_price * Decimal(str(max_mult)))

        return (round(min_price, 2), round(max_price, 2))

    # Group available bikes by bike_type and price_segment
    bike_groups = ProducedBike.objects.filter(
        session=game_session,
        is_sold=False
    ).values(
        'bike_type__id',
        'bike_type__name',
        'price_segment'
    ).annotate(
        count=Count('id'),
        avg_production_cost=Avg('production_cost')
    ).order_by('bike_type__name', 'price_segment')

    # Add price range information to each group
    for group in bike_groups:
        bike_type = BikeType.objects.get(id=group['bike_type__id'])
        min_price, max_price = get_price_range(
            bike_type,
            group['price_segment'],
            game_session
        )
        group['min_price'] = min_price
        group['max_price'] = max_price
        group['suggested_price'] = round((min_price + max_price) / 2, 2)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                sales_data = json.loads(request.body)

                # Convert sales_data to decision format for TurnState
                decisions = []
                total_expected_revenue = 0
                total_quantity = 0

                for item in sales_data:
                    market_id = item['market_id']
                    market = get_object_or_404(Market, id=market_id, session=game_session)
                    bike_groups_to_sell = item['bike_groups']

                    for group_data in bike_groups_to_sell:
                        bike_type_id = group_data['bike_type_id']
                        price_segment = group_data['price_segment']
                        quantity = int(group_data['quantity'])
                        sale_price = Decimal(str(group_data['price']))
                        transport_cost = Decimal(str(group_data['transport_cost']))

                        # Get bike_type for validation
                        bike_type = get_object_or_404(BikeType, id=bike_type_id)

                        # Validate price is within acceptable range
                        min_price, max_price = get_price_range(bike_type, price_segment, game_session)

                        if sale_price < min_price:
                            return JsonResponse({
                                'success': False,
                                'error': f'Preis für {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) zu niedrig. Minimum: {min_price}€'
                            })

                        if sale_price > max_price:
                            return JsonResponse({
                                'success': False,
                                'error': f'Preis für {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) zu hoch. Maximum: {max_price}€'
                            })

                        # Check bike availability
                        available_bikes = ProducedBike.objects.filter(
                            session=game_session,
                            bike_type_id=bike_type_id,
                            price_segment=price_segment,
                            is_sold=False
                        ).count()

                        if available_bikes < quantity:
                            return JsonResponse({
                                'success': False,
                                'error': f'Nicht genügend {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) verfügbar. Verfügbar: {available_bikes}, Angefordert: {quantity}'
                            })

                        # Store decision (NOT executing sale yet!)
                        decision = {
                            'market_id': market_id,
                            'market_name': market.name,
                            'bike_type_id': bike_type_id,
                            'bike_type_name': bike_type.name,
                            'price_segment': price_segment,
                            'quantity': quantity,
                            'desired_price': float(sale_price),
                            'transport_cost': float(transport_cost),
                        }
                        decisions.append(decision)

                        # Calculate expected revenue for preview (transport cost is per shipment, not per bike)
                        expected_revenue = (sale_price * quantity) - transport_cost
                        total_expected_revenue += expected_revenue
                        total_quantity += quantity

                # Store decisions in TurnState
                turn_state.sales_decisions = decisions
                turn_state.decisions_submitted = True
                turn_state.submitted_at = timezone.now()
                turn_state.save()

                # Check if this is a single human player game
                if game.is_single_human_player_game:
                    # Auto-process the turn immediately
                    from .simulation_engine import MultiplayerTurnManager
                    turn_manager = MultiplayerTurnManager(game)
                    result = turn_manager.process_turn_if_ready()

                    if result.get('processed'):
                        return JsonResponse({
                            'success': True,
                            'turn_processed': True,
                            'message': 'Your sales decisions have been processed! Check the results below.',
                            'redirect': f'/multiplayer/game/{game.id}/',
                            'expected_revenue': float(total_expected_revenue),
                            'total_quantity': total_quantity
                        })

            return JsonResponse({
                'success': True,
                'message': f'Verkaufsentscheidungen gespeichert! Ihre Entscheidungen werden verarbeitet, wenn die Runde fortschreitet.',
                'deferred': True,
                'expected_revenue': float(total_expected_revenue),
                'total_quantity': total_quantity,
                'info': 'Sales will be processed when turn advances'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Calculate total available bikes count
    total_bikes_count = ProducedBike.objects.filter(session=game_session, is_sold=False).count()

    # Get pending sales decisions for current turn
    pending_decisions = turn_state.sales_decisions if isinstance(turn_state.sales_decisions, list) else []

    # Get previous turn's results
    previous_turn_state = TurnState.objects.filter(
        multiplayer_game=game,
        player_session=player_session,
        decisions_submitted=True
    ).exclude(
        month=game.current_month,
        year=game.current_year
    ).order_by('-year', '-month').first()

    previous_results = None
    if previous_turn_state and previous_turn_state.sales_results:
        previous_results = previous_turn_state.sales_results

    # Get sales history for current month (actual completed sales from previous processing)
    current_month_sales = SalesOrder.objects.filter(
        session=game_session,
        sale_month=game_session.current_month,
        sale_year=game_session.current_year
    ).select_related('market', 'bike__bike_type')

    # Calculate sales statistics
    sales_stats = current_month_sales.aggregate(
        total_bikes_sold=Count('id'),
        total_revenue=Sum('sale_price'),
        total_transport_costs=Sum('transport_cost')
    )

    # Calculate net revenue
    total_revenue = sales_stats['total_revenue'] or 0
    total_transport = sales_stats['total_transport_costs'] or 0
    net_revenue = total_revenue - total_transport

    sales_stats['net_revenue'] = net_revenue

    # Group sales by market and then by bike type/segment for detailed view
    sales_by_market = defaultdict(lambda: {'bikes': {}, 'total': 0, 'count': 0})

    for sale in current_month_sales:
        market_name = sale.market.name
        bike_key = f"{sale.bike.bike_type.name}_{sale.bike.price_segment}"

        # Initialize bike group if not exists
        if bike_key not in sales_by_market[market_name]['bikes']:
            sales_by_market[market_name]['bikes'][bike_key] = {
                'bike_type': sale.bike.bike_type.name,
                'price_segment': sale.bike.get_price_segment_display(),
                'count': 0,
                'total_sale_price': 0,
                'total_transport_cost': 0,
                'total_net_revenue': 0
            }

        # Add to grouped data
        sales_by_market[market_name]['bikes'][bike_key]['count'] += 1
        sales_by_market[market_name]['bikes'][bike_key]['total_sale_price'] += float(sale.sale_price)
        sales_by_market[market_name]['bikes'][bike_key]['total_transport_cost'] += float(sale.transport_cost)
        sales_by_market[market_name]['bikes'][bike_key]['total_net_revenue'] += float(sale.sale_price - sale.transport_cost)

        sales_by_market[market_name]['total'] += sale.sale_price - sale.transport_cost
        sales_by_market[market_name]['count'] += 1

    # Convert bikes dict to list for template
    for market_name in sales_by_market:
        sales_by_market[market_name]['bikes'] = list(sales_by_market[market_name]['bikes'].values())

    context = {
        'game': game,
        'player_session': player_session,
        'session': game_session,
        'turn_state': turn_state,
        'markets': markets,
        'bike_groups': bike_groups,
        'total_bikes_count': total_bikes_count,
        'pending_decisions': pending_decisions,
        'previous_results': previous_results,
        'current_month_sales': current_month_sales,
        'sales_stats': sales_stats,
        'sales_by_market': dict(sales_by_market)
    }

    return render(request, 'multiplayer/sales.html', context)



@login_required
@handle_deleted_game
def multiplayer_finance(request, game_id):
    """Wrapper view for finance in multiplayer context."""
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
        messages.error(request, f"This game is currently {game.get_status_display()}. You cannot perform any actions right now.")
        return redirect('multiplayer:lobby')

    # Get player's game session
    state_manager = PlayerStateManager(game)
    game_session = state_manager.get_player_game_session(player_session)

    # Store multiplayer context in request
    request.multiplayer_game = game
    request.multiplayer_player_session = player_session
    request.base_template = 'multiplayer/base_multiplayer.html'

    from finance import views as finance_views
    return finance_views.finance_view(request, game_session.id)


@login_required
@handle_deleted_game
def upload_parameters(request, game_id):
    """Upload game parameters (Excel files) for a multiplayer game - admin only."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check permissions - only game creator can upload parameters
    if game.created_by != request.user:
        messages.error(request, "Only the game creator can upload parameters.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Can only upload parameters during setup phase
    if game.status not in ['setup', 'waiting']:
        messages.error(request, "Parameters can only be uploaded during game setup.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    if request.method == 'POST':
        if 'parameter_file' not in request.FILES:
            messages.error(request, 'Please select a ZIP file to upload.')
            return render(request, 'multiplayer/upload_parameters.html', {'game': game})

        zip_file = request.FILES['parameter_file']

        # Validate file extension
        if not zip_file.name.endswith('.zip'):
            messages.error(request, 'Please upload a ZIP file.')
            return render(request, 'multiplayer/upload_parameters.html', {'game': game})

        try:
            # Import the parameter processing function from bikeshop utils
            from bikeshop.utils import process_parameter_zip

            # Process the ZIP file to validate it
            parameters = process_parameter_zip(zip_file)

            # Save the ZIP file to the game
            game.parameters_file = zip_file
            game.parameters_uploaded = True
            game.parameters_uploaded_at = timezone.now()
            game.save()

            # Create event
            GameEvent.objects.create(
                multiplayer_game=game,
                event_type='system_message',
                message=f"Game parameters uploaded by {request.user.username}",
                data={'filename': zip_file.name}
            )

            messages.success(request, 'Parameters uploaded successfully! Players who join will now have these parameters loaded.')
            return redirect('multiplayer:game_detail', game_id=game_id)

        except Exception as e:
            messages.error(request, f'Error processing parameter file: {str(e)}')

    return render(request, 'multiplayer/upload_parameters.html', {'game': game})


@login_required
@handle_deleted_game
@require_http_methods(["POST"])
def delete_game(request, game_id):
    """Delete a multiplayer game - admin/creator only."""
    game = get_object_or_404(MultiplayerGame, id=game_id)

    # Check permissions - only game creator or staff can delete
    if game.created_by != request.user and not request.user.is_staff:
        messages.error(request, "Only the game creator or administrators can delete this game.")
        return redirect('multiplayer:game_detail', game_id=game_id)

    # Delete the game
    try:
        with transaction.atomic():
            game_name = game.name

            # Get all players to delete their individual GameSessions
            players = PlayerSession.objects.filter(multiplayer_game=game)
            player_count = players.count()

            # Delete each player's GameSession (this will cascade to all their game data)
            from bikeshop.models import GameSession
            deleted_sessions = 0
            for player in players:
                if player.user:
                    # Find and delete the player's GameSession
                    try:
                        # More flexible search - look for sessions that might be related
                        game_sessions = GameSession.objects.filter(
                            user=player.user,
                            name__icontains=game.name
                        )
                        count = game_sessions.count()
                        if count > 0:
                            game_sessions.delete()
                            deleted_sessions += count
                    except Exception as session_error:
                        # Log but continue - we still want to delete the multiplayer game
                        print(f"Warning: Could not delete GameSession for {player.user.username}: {session_error}")

            # Delete the multiplayer game (this will cascade to PlayerSession, TurnState, GameEvent, etc.)
            game.delete()

            messages.success(request, f'Game "{game_name}" and all associated data for {player_count} players has been permanently deleted.')

            # Redirect staff users to dashboard, regular users to multiplayer lobby
            if request.user.is_staff:
                return redirect('bikeshop:dashboard')
            else:
                return redirect('multiplayer:lobby')

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error deleting game: {error_detail}")
        messages.error(request, f'Error deleting game: {str(e)}')
        return redirect('multiplayer:lobby')
