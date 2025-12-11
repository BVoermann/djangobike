from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('<uuid:session_id>/', views.sales_view, name='sales'),
    path('<uuid:session_id>/market-research/estimates/', views.get_market_demand_estimates, name='market_demand_estimates'),
    path('<uuid:session_id>/market-research/purchase/', views.purchase_market_research_view, name='purchase_market_research'),
]
