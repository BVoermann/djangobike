from django.urls import path
from . import views

app_name = 'simulation'

urlpatterns = [
    path('<uuid:session_id>/advance/', views.advance_month, name='advance_month'),
    path('<uuid:session_id>/summary/', views.month_summary, name='month_summary'),
]
