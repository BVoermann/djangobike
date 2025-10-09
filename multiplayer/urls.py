from django.urls import path
from . import views

app_name = 'multiplayer'

urlpatterns = [
    # Main lobby and game management
    path('', views.multiplayer_lobby, name='lobby'),
    path('create/', views.create_game, name='create_game'),
    path('game/<uuid:game_id>/', views.game_detail, name='game_detail'),
    path('game/<uuid:game_id>/join/', views.join_game, name='join_game'),
    path('game/<uuid:game_id>/start/', views.start_game, name='start_game'),
    
    # Gameplay
    path('game/<uuid:game_id>/submit/', views.submit_decisions, name='submit_decisions'),
    path('game/<uuid:game_id>/process-turn/', views.process_turn, name='process_turn'),
    
    # Information and analytics
    path('game/<uuid:game_id>/leaderboard/', views.leaderboard, name='leaderboard'),
    path('game/<uuid:game_id>/dashboard/', views.financial_dashboard, name='financial_dashboard'),
    
    # AJAX endpoints
    path('game/<uuid:game_id>/events/', views.game_events, name='game_events'),
]