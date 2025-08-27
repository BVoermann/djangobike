from django.urls import path
from . import views

app_name = 'workers'

urlpatterns = [
    path('', views.worker_dashboard, name='dashboard'),
    path('add/', views.add_worker, name='add_worker'),
    path('quick-hire/', views.quick_hire, name='quick_hire'),
    path('worker/<int:worker_id>/', views.worker_detail, name='worker_detail'),
    path('fire/<int:worker_id>/', views.fire_worker, name='fire_worker'),
    path('fired/', views.fired_workers, name='fired_workers'),
]