from django.urls import path
from . import views

app_name = 'bikeshop'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload-parameters/', views.upload_parameters, name='upload_parameters'),
    path('download-default-parameters/', views.download_default_parameters, name='download_default_parameters'),
    path('create-session/', views.create_session, name='create_session'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('session/<uuid:session_id>/delete/', views.delete_session, name='delete_session'),
]
