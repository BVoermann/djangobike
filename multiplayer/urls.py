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
    path('game/<uuid:game_id>/upload-parameters/', views.upload_parameters, name='upload_parameters'),
    path('game/<uuid:game_id>/delete/', views.delete_game, name='delete_game'),

    # Gameplay
    path('game/<uuid:game_id>/submit/', views.submit_decisions, name='submit_decisions'),
    path('game/<uuid:game_id>/process-turn/', views.process_turn, name='process_turn'),

    # Game tabs - access to full game functionality
    path('game/<uuid:game_id>/procurement/', views.multiplayer_procurement, name='procurement'),
    path('game/<uuid:game_id>/production/', views.multiplayer_production, name='production'),
    path('game/<uuid:game_id>/warehouse/', views.multiplayer_warehouse, name='warehouse'),
    path('game/<uuid:game_id>/sales/', views.multiplayer_sales, name='sales'),
    path('game/<uuid:game_id>/finance/', views.multiplayer_finance, name='finance'),

    # Information and analytics
    path('game/<uuid:game_id>/leaderboard/', views.leaderboard, name='leaderboard'),
    path('game/<uuid:game_id>/dashboard/', views.financial_dashboard, name='financial_dashboard'),

    # AJAX endpoints
    path('game/<uuid:game_id>/events/', views.game_events, name='game_events'),
]