from django.db import models
from bikeshop.models import GameSession, Component
from production.models import ProducedBike


class Warehouse(models.Model):
    """Lager"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    capacity_m2 = models.FloatField()
    rent_per_month = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.location})"

    @property
    def current_usage(self):
        """Aktuelle Lagernutzung berechnen"""
        component_usage = sum([
            stock.quantity * stock.component.component_type.storage_space_per_unit
            for stock in self.component_stocks.all()
        ])
        bike_usage = sum([
            1 * bike.bike.bike_type.storage_space_per_unit
            for bike in self.stored_bikes.all()
        ])
        return component_usage + bike_usage

    @property
    def remaining_capacity(self):
        return self.capacity_m2 - self.current_usage


class ComponentStock(models.Model):
    """Lagerbestand Komponenten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='component_stocks')
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['session', 'warehouse', 'component']


class BikeStock(models.Model):
    """Lagerbestand Fahrräder"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stored_bikes')
    bike = models.OneToOneField(ProducedBike, on_delete=models.CASCADE)
