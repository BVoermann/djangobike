from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('<uuid:session_id>/', views.production_view, name='production'),
]
