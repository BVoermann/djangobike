from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('<uuid:session_id>/', views.warehouse_view, name='warehouse'),
    path('<uuid:session_id>/purchase/', views.purchase_warehouse, name='purchase_warehouse'),
]
