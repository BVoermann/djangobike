from django.urls import path
from . import views

app_name = 'bikeshop'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload-parameters/', views.upload_parameters, name='upload_parameters'),
    path('create-session/', views.create_session, name='create_session'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
]
