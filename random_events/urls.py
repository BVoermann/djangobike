from django.urls import path
from . import views

app_name = 'random_events'

urlpatterns = [
    # Main dashboard
    path('<uuid:session_id>/dashboard/', views.events_dashboard, name='dashboard'),
    
    # Event management
    path('<uuid:session_id>/event/<uuid:event_occurrence_id>/', views.event_detail, name='event_detail'),
    path('<uuid:session_id>/history/', views.event_history, name='event_history'),
    
    # Regulations
    path('<uuid:session_id>/regulations/', views.regulations_overview, name='regulations_overview'),
    
    # Market opportunities
    path('<uuid:session_id>/opportunities/', views.market_opportunities, name='market_opportunities'),
    
    # Administrative
    path('<uuid:session_id>/initialize/', views.initialize_events, name='initialize_events'),
    path('<uuid:session_id>/trigger-test/', views.trigger_test_event, name='trigger_test_event'),
    
    # AJAX endpoints
    path('<uuid:session_id>/ajax/status/', views.ajax_event_status, name='ajax_event_status'),
]