from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import MultiplayerGame
from bikeshop.models import GameSession


@receiver(pre_delete, sender=MultiplayerGame)
def cleanup_game_sessions_on_multiplayer_game_delete(sender, instance, **kwargs):
    """
    When a multiplayer game is deleted, also delete all associated GameSession objects.

    Each player in a multiplayer game has a GameSession object that contains their
    individual game state. These need to be cleaned up when the multiplayer game is deleted.
    """
    # Find all GameSessions that belong to this multiplayer game
    # They are identified by having the game name in their name field
    game_sessions = GameSession.objects.filter(name__contains=instance.name)

    # Also find sessions by looking at all players in this game
    player_sessions = instance.players.all()
    for player_session in player_sessions:
        if player_session.user:
            # Delete any GameSession objects for this user related to this game
            user_game_sessions = GameSession.objects.filter(
                user=player_session.user,
                name__contains=instance.name
            )
            user_game_sessions.delete()

    # Delete the initially found sessions
    game_sessions.delete()
