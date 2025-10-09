from django.urls import path
from . import views

app_name = 'business_strategy'

urlpatterns = [
    # Main dashboard
    path('<uuid:session_id>/', views.business_strategy_dashboard, name='dashboard'),
    
    # R&D Management
    path('<uuid:session_id>/research-development/', views.research_development, name='research_development'),
    path('<uuid:session_id>/research-development/create/', views.create_research_project, name='create_research_project'),
    path('<uuid:session_id>/research-development/project/<uuid:project_id>/', views.project_detail, name='project_detail'),
    
    # Marketing Campaigns
    path('<uuid:session_id>/marketing/', views.marketing_campaigns, name='marketing_campaigns'),
    path('<uuid:session_id>/marketing/create/', views.create_marketing_campaign, name='create_marketing_campaign'),
    path('<uuid:session_id>/marketing/campaign/<uuid:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    
    # Sustainability Management
    path('<uuid:session_id>/sustainability/', views.sustainability_management, name='sustainability_management'),
    path('<uuid:session_id>/sustainability/create/', views.create_sustainability_initiative, name='create_sustainability_initiative'),
    path('<uuid:session_id>/sustainability/initiative/<uuid:initiative_id>/', views.initiative_detail, name='initiative_detail'),
    
    # Strategy Settings and Analysis
    path('<uuid:session_id>/settings/', views.strategy_settings, name='strategy_settings'),
    path('<uuid:session_id>/competitive-analysis/', views.competitive_analysis_view, name='competitive_analysis'),
    
    # Utility
    path('<uuid:session_id>/initialize/', views.initialize_predefined_content, name='initialize_predefined_content'),
]