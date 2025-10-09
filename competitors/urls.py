from django.urls import path
from . import views

app_name = 'competitors'

urlpatterns = [
    path('<uuid:session_id>/dashboard/', views.competitors_dashboard, name='dashboard'),
    path('<uuid:session_id>/competitor/<int:competitor_id>/', views.competitor_detail, name='detail'),
    path('<uuid:session_id>/market-analysis/', views.market_analysis, name='market_analysis'),
    path('<uuid:session_id>/api/data/', views.competitor_api_data, name='api_data'),
]