from django.db import models
from bikeshop.models import GameSession

class SimulationSettings(models.Model):
    """Simulationseinstellungen"""
    session = models.OneToOneField(GameSession, on_delete=models.CASCADE)
    max_months = models.IntegerField(default=24)
    seasonal_effects = models.BooleanField(default=True)
    market_trends = models.BooleanField(default=True)
