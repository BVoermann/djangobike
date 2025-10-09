from django.urls import path
from . import views

app_name = 'game_objectives'

urlpatterns = [
    # Main objectives dashboard
    path('<uuid:session_id>/', views.objectives_dashboard, name='objectives_dashboard'),
    
    # Game mode selection
    path('<uuid:session_id>/select-mode/', views.select_game_mode, name='select_game_mode'),
    
    # Game results
    path('<uuid:session_id>/results/', views.game_result, name='game_result'),
    
    # API endpoints
    path('<uuid:session_id>/api/objectives/', views.objectives_api, name='objectives_api'),
    path('<uuid:session_id>/api/check-victory/', views.check_victory_conditions, name='check_victory_conditions'),
    path('<uuid:session_id>/api/bankruptcy-status/', views.bankruptcy_status, name='bankruptcy_status'),
    
    # Leaderboard
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]