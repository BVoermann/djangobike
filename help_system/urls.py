from django.urls import path
from . import views

app_name = 'help_system'

urlpatterns = [
    # Main help pages
    path('', views.help_dashboard, name='dashboard'),
    path('videos/', views.video_library, name='video_library'),
    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
    path('guides/', views.interactive_guides, name='interactive_guides'),
    path('guides/<int:guide_id>/', views.guide_detail, name='guide_detail'),
    path('documentation/', views.documentation, name='documentation'),
    path('mock-simulation/', views.mock_simulation, name='mock_simulation'),
    path('mock-simulation/<str:mock_type>/', views.mock_simulation, name='mock_simulation_typed'),
    
    # API endpoints for contextual help
    path('api/contextual-help/', views.contextual_help_api, name='contextual_help_api'),
    path('api/tooltip-help/', views.tooltip_help_api, name='tooltip_help_api'),
    path('api/search/', views.help_search_api, name='help_search_api'),
    
    # API endpoints for interactive guides
    path('api/guides/<int:guide_id>/start/', views.start_guide_api, name='start_guide_api'),
    path('api/guides/<int:guide_id>/progress/', views.update_guide_progress_api, name='update_guide_progress_api'),
    
    # API endpoints for tracking and feedback
    path('api/videos/<int:video_id>/watched/', views.mark_video_watched_api, name='mark_video_watched_api'),
    path('api/feedback/', views.submit_feedback_api, name='submit_feedback_api'),
    path('api/preferences/', views.update_help_preferences_api, name='update_help_preferences_api'),
    path('api/interactions/', views.record_help_interaction_api, name='record_help_interaction_api'),
]