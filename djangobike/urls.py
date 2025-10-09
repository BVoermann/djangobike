"""
URL configuration for djangobike project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('bikeshop.urls')),
    path('procurement/', include('procurement.urls')),
    path('production/', include('production.urls')),
    path('warehouse/', include('warehouse.urls')),
    path('finance/', include('finance.urls')),
    path('sales/', include('sales.urls')),
    path('simulation/', include('simulation.urls')),
    path('workers/', include('workers.urls')),  # Neue workers URLs hinzugefügt
    path('competitors/', include('competitors.urls')),
    path('multiplayer/', include('multiplayer.urls')),
    path('business-strategy/', include('business_strategy.urls')),
    path('events/', include('random_events.urls')),
    path('help/', include('help_system.urls')),
    path('objectives/', include('game_objectives.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)