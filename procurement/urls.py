from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('<uuid:session_id>/', views.procurement_view, name='procurement'),
]
