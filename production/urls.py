from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('<uuid:session_id>/', views.production_view, name='production'),
    path('<uuid:session_id>/hire_worker/', views.hire_worker, name='hire_worker'),
]
