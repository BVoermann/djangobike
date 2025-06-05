from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('<uuid:session_id>/', views.sales_view, name='sales'),
]
