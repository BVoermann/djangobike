from django.urls import path
from . import views

app_name = 'simulation'

urlpatterns = [
    path('<uuid:session_id>/advance/', views.advance_month, name='advance_month'),
]
