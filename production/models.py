from django.db import models
from bikeshop.models import GameSession, BikeType
from django.core.validators import MinValueValidator


class ProductionPlan(models.Model):
    """Produktionsplan für einen Monat"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'month', 'year']


class ProductionOrder(models.Model):
    """Produktionsauftrag für einen Fahrradtyp"""
    plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='orders')
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    quantity_planned = models.IntegerField(validators=[MinValueValidator(0)])
    quantity_produced = models.IntegerField(default=0)


class ProducedBike(models.Model):
    """Produziertes Fahrrad"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    production_month = models.IntegerField()
    production_year = models.IntegerField()
    warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.CASCADE, null=True, blank=True)
    is_sold = models.BooleanField(default=False)
    production_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)