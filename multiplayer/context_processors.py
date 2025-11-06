"""
Context processor to provide multiplayer game context to all templates.
"""
from .models import MultiplayerGame, PlayerSession


def multiplayer_context(request):
    """
    Add multiplayer game context if the user is viewing a multiplayer page.
    """
    context = {
        'game': None,
        'is_player': False,
        'player_session': None,
    }

    # First check if context was set by wrapper views
    if hasattr(request, 'multiplayer_game'):
        context['game'] = request.multiplayer_game
        context['is_player'] = True
        context['player_session'] = getattr(request, 'multiplayer_player_session', None)
    # Otherwise, check if we're in a multiplayer URL pattern
    elif hasattr(request, 'resolver_match') and request.resolver_match:
        if request.resolver_match.namespace == 'multiplayer':
            # Try to get game_id from URL kwargs
            game_id = request.resolver_match.kwargs.get('game_id')

            if game_id and request.user.is_authenticated:
                try:
                    game = MultiplayerGame.objects.get(id=game_id)
                    context['game'] = game

                    # Check if user is a player in this game
                    try:
                        player_session = PlayerSession.objects.get(
                            multiplayer_game=game,
                            user=request.user
                        )
                        context['is_player'] = True
                        context['player_session'] = player_session
                    except PlayerSession.DoesNotExist:
                        pass

                except MultiplayerGame.DoesNotExist:
                    pass

    return context
