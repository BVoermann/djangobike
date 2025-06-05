from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('<uuid:session_id>/', views.finance_view, name='finance'),
]