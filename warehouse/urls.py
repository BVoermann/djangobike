from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('<uuid:session_id>/', views.warehouse_view, name='warehouse'),
]
