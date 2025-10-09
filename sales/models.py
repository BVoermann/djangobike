from django.db import models
from bikeshop.models import GameSession, BikeType
from production.models import ProducedBike

class Market(models.Model):
    """Markt"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    transport_cost_home = models.DecimalField(max_digits=6, decimal_places=2)
    transport_cost_foreign = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Market volume constraints
    monthly_volume_capacity = models.IntegerField(default=200, help_text="Maximum bikes that can be sold per month")
    price_elasticity_factor = models.FloatField(default=1.0, help_text="Price sensitivity factor for demand curves")

class MarketDemand(models.Model):
    """Marktnachfrage"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    demand_percentage = models.FloatField()  # Anteil der Nachfrage für diesen Fahrradtyp

class MarketPriceSensitivity(models.Model):
    """Preissensibilität des Marktes"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    percentage = models.FloatField()

class SalesOrder(models.Model):
    """Verkaufsauftrag"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike = models.ForeignKey(ProducedBike, on_delete=models.CASCADE)
    sale_month = models.IntegerField()
    sale_year = models.IntegerField()
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    transport_cost = models.DecimalField(max_digits=6, decimal_places=2)
    is_completed = models.BooleanField(default=False)
