from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-game/', views.create_game, name='create_game'),
    path('admin/game/<uuid:game_id>/assign-users/', views.assign_users, name='assign_users'),
    path('admin/game/<uuid:game_id>/fill-ai/', views.fill_with_ai, name='fill_with_ai'),
    path('admin/game/<uuid:game_id>/edit/', views.edit_game, name='edit_game'),
    path('admin/game/<uuid:game_id>/parameters/', views.edit_parameters, name='edit_parameters'),
    path('admin/users/', views.manage_users, name='manage_users'),
]
