from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, LoginForm


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        # Redirect based on role
        if request.user.is_spielleitung():
            return redirect('authentication:admin_dashboard')
        return redirect('bikeshop:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Willkommen, {user.username}!')

                # Redirect based on role
                if user.is_spielleitung():
                    return redirect('authentication:admin_dashboard')
                return redirect('bikeshop:dashboard')
            else:
                messages.error(request, 'Ungültiger Benutzername oder Passwort.')
    else:
        form = LoginForm()

    return render(request, 'authentication/login.html', {'form': form})


def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('bikeshop:dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Konto erfolgreich erstellt! Willkommen, {user.username}!')
            return redirect('bikeshop:dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'authentication/register.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'Sie wurden erfolgreich abgemeldet.')
    return redirect('authentication:login')


@login_required
def admin_dashboard(request):
    """Dashboard for Spielleitung (admins)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame
    from authentication.models import CustomUser

    # Get all multiplayer games
    games = MultiplayerGame.objects.all().order_by('-created_at')

    # Get all users
    users = CustomUser.objects.filter(role='user').order_by('username')

    # Count games by status
    active_games_count = games.filter(status='active').count()
    waiting_games_count = games.filter(status='waiting').count()

    context = {
        'games': games,
        'users': users,
        'active_games_count': active_games_count,
        'waiting_games_count': waiting_games_count,
    }

    return render(request, 'authentication/admin_dashboard.html', context)


@login_required
def create_game(request):
    """Create a new multiplayer game (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame, GameParameters, GameEvent
    from multiplayer.forms import MultiplayerGameForm
    from bikeshop.utils import process_parameter_zip
    from django.utils import timezone

    if request.method == 'POST':
        form = MultiplayerGameForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate ZIP file
            zip_file = request.FILES.get('parameters_file')
            if not zip_file:
                messages.error(request, 'Bitte wählen Sie eine ZIP-Datei mit Parametern aus.')
                return render(request, 'authentication/create_game.html', {'form': form})

            # Validate file extension
            if not zip_file.name.endswith('.zip'):
                messages.error(request, 'Bitte laden Sie eine ZIP-Datei hoch.')
                return render(request, 'authentication/create_game.html', {'form': form})

            try:
                # Process the ZIP file to validate it
                parameters = process_parameter_zip(zip_file)

                # Create the game
                game = form.save(commit=False)
                game.created_by = request.user
                game.parameters_uploaded = True
                game.parameters_uploaded_at = timezone.now()
                game.save()

                # Create default parameters for the game
                GameParameters.objects.create(
                    multiplayer_game=game,
                    last_modified_by=request.user
                )

                # Create event for parameter upload
                GameEvent.objects.create(
                    multiplayer_game=game,
                    event_type='system_message',
                    message=f"Spiel erstellt und Parameter hochgeladen von {request.user.username}",
                    data={'filename': zip_file.name}
                )

                messages.success(request, f'Spiel "{game.name}" erfolgreich erstellt und Parameter hochgeladen!')
                return redirect('authentication:assign_users', game_id=game.id)

            except Exception as e:
                messages.error(request, f'Fehler beim Verarbeiten der Parameter-Datei: {str(e)}')
                return render(request, 'authentication/create_game.html', {'form': form})
    else:
        form = MultiplayerGameForm()

    return render(request, 'authentication/create_game.html', {'form': form})


@login_required
def assign_users(request, game_id):
    """Assign users to a multiplayer game (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame
    from authentication.models import CustomUser

    try:
        game = MultiplayerGame.objects.get(id=game_id)
    except MultiplayerGame.DoesNotExist:
        messages.error(request, 'Das Spiel existiert nicht mehr oder wurde gelöscht.')
        return redirect('authentication:admin_dashboard')

    all_users = CustomUser.objects.filter(role='user').order_by('username')
    assigned_user_ids = list(game.assigned_users.values_list('id', flat=True))

    if request.method == 'POST':
        selected_user_ids = request.POST.getlist('users')
        game.assigned_users.set(selected_user_ids)
        messages.success(request, f'{len(selected_user_ids)} Benutzer wurden dem Spiel zugewiesen.')
        return redirect('authentication:admin_dashboard')

    # Calculate remaining slots for AI players
    from multiplayer.models import PlayerSession
    human_count = game.assigned_users.count()
    ai_count = game.players.filter(player_type='ai', is_active=True).count()
    remaining_slots = game.max_players - human_count - ai_count

    context = {
        'game': game,
        'all_users': all_users,
        'assigned_user_ids': assigned_user_ids,
        'remaining_slots': max(0, remaining_slots),  # Ensure non-negative
    }

    return render(request, 'authentication/assign_users.html', context)


@login_required
def fill_with_ai(request, game_id):
    """Fill remaining player slots with AI players (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame, PlayerSession
    from authentication.models import CustomUser

    try:
        game = MultiplayerGame.objects.get(id=game_id)
    except MultiplayerGame.DoesNotExist:
        messages.error(request, 'Das Spiel existiert nicht mehr oder wurde gelöscht.')
        return redirect('authentication:admin_dashboard')

    # Count current human players (assigned users)
    human_count = game.assigned_users.count()

    # Count current AI players
    ai_count = game.players.filter(player_type='ai', is_active=True).count()

    # Calculate remaining slots
    total_current = human_count + ai_count
    remaining_slots = game.max_players - total_current

    if remaining_slots <= 0:
        messages.warning(request, 'Das Spiel ist bereits voll. Keine weiteren Spieler können hinzugefügt werden.')
        return redirect('authentication:assign_users', game_id=game.id)

    # AI company names
    ai_company_names = [
        "CycleTech GmbH",
        "VeloMax AG",
        "BikeInnovate",
        "SpeedCycles Pro",
        "EcoBike Solutions",
        "TurboRides Inc.",
        "MountainMasters",
        "UrbanCycling Co.",
        "ElektroBikes Plus",
        "RaceWheels AG"
    ]

    # AI strategies (rotate through them)
    ai_strategies = [
        'balanced',
        'cheap_only',
        'premium_focus',
        'e_bike_specialist',
        'innovative',
        'aggressive',
    ]

    # Get AI companies that are already used in this game
    existing_ai_companies = set(
        game.players.filter(player_type='ai')
        .values_list('company_name', flat=True)
    )

    # Filter out already used company names
    available_names = [name for name in ai_company_names if name not in existing_ai_companies]

    # Create AI players
    created_count = 0
    for i in range(remaining_slots):
        # Choose company name
        if available_names:
            company_name = available_names[i % len(available_names)]
        else:
            company_name = f"AI Competitor {ai_count + i + 1}"

        # Choose strategy (rotate through)
        strategy = ai_strategies[i % len(ai_strategies)]

        # Create AI player
        PlayerSession.objects.create(
            multiplayer_game=game,
            user=None,  # AI players have no user
            company_name=company_name,
            player_type='ai',
            ai_strategy=strategy,
            balance=game.starting_balance,
            is_active=True,
            is_bankrupt=False,
            ai_difficulty=1.0,
            ai_aggressiveness=0.5,
            ai_risk_tolerance=0.5
        )
        created_count += 1

    messages.success(request, f'{created_count} KI-Spieler wurden erfolgreich hinzugefügt!')
    return redirect('authentication:assign_users', game_id=game.id)


@login_required
def edit_parameters(request, game_id):
    """Edit game parameters (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame, GameParameters
    from multiplayer.forms import GameParametersForm

    try:
        game = MultiplayerGame.objects.get(id=game_id)
    except MultiplayerGame.DoesNotExist:
        messages.error(request, 'Das Spiel existiert nicht mehr oder wurde gelöscht.')
        return redirect('authentication:admin_dashboard')

    # Get or create parameters
    parameters, created = GameParameters.objects.get_or_create(
        multiplayer_game=game,
        defaults={'last_modified_by': request.user}
    )

    if request.method == 'POST':
        form = GameParametersForm(request.POST, instance=parameters)
        if form.is_valid():
            # Log changes
            old_instance = GameParameters.objects.get(pk=parameters.pk)
            parameters = form.save(commit=False)
            parameters.last_modified_by = request.user

            # Log each changed field
            for field in form.changed_data:
                old_value = getattr(old_instance, field)
                new_value = getattr(parameters, field)
                parameters.log_change(request.user, field, old_value, new_value)

            parameters.save()
            messages.success(request, 'Parameter erfolgreich aktualisiert!')
            return redirect('authentication:admin_dashboard')
    else:
        form = GameParametersForm(instance=parameters)

    context = {
        'game': game,
        'form': form,
        'parameters': parameters,
    }

    return render(request, 'authentication/edit_parameters.html', context)


@login_required
def edit_game(request, game_id):
    """Edit multiplayer game settings (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from multiplayer.models import MultiplayerGame
    from multiplayer.forms import MultiplayerGameForm

    try:
        game = MultiplayerGame.objects.get(id=game_id)
    except MultiplayerGame.DoesNotExist:
        messages.error(request, 'Das Spiel existiert nicht mehr oder wurde gelöscht.')
        return redirect('authentication:admin_dashboard')

    if request.method == 'POST':
        form = MultiplayerGameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, f'Spiel "{game.name}" erfolgreich aktualisiert!')
            return redirect('authentication:admin_dashboard')
    else:
        form = MultiplayerGameForm(instance=game)

    context = {
        'game': game,
        'form': form,
    }

    return render(request, 'authentication/edit_game.html', context)


@login_required
def manage_users(request):
    """Manage users (Spielleitung only)"""
    if not request.user.is_spielleitung():
        messages.error(request, 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.')
        return redirect('bikeshop:dashboard')

    from authentication.models import CustomUser

    users = CustomUser.objects.all().order_by('username')
    admin_count = users.filter(role='admin').count()
    player_count = users.filter(role='user').count()

    context = {
        'users': users,
        'admin_count': admin_count,
        'player_count': player_count,
    }

    return render(request, 'authentication/manage_users.html', context)
