from django.db import models
from bikeshop.models import GameSession, Component
from production.models import ProducedBike
from decimal import Decimal


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

    @property
    def usage_percentage(self):
        """Calculate warehouse usage as percentage"""
        if self.capacity_m2 == 0:
            return 100.0
        return (self.current_usage / self.capacity_m2) * 100

    def can_store_components(self, component, quantity):
        """Check if warehouse has capacity to store additional components"""
        required_space = component.component_type.storage_space_per_unit * quantity
        return self.remaining_capacity >= required_space

    def can_store_bikes(self, bike_type, quantity):
        """Check if warehouse has capacity to store additional bikes"""
        required_space = bike_type.storage_space_per_unit * quantity
        return self.remaining_capacity >= required_space

    def get_required_space_for_components(self, component, quantity):
        """Calculate space required for components"""
        return component.component_type.storage_space_per_unit * quantity

    def get_required_space_for_bikes(self, bike_type, quantity):
        """Calculate space required for bikes"""
        return bike_type.storage_space_per_unit * quantity


class ComponentStock(models.Model):
    """Lagerbestand Komponenten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='component_stocks')
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    supplier = models.ForeignKey('bikeshop.Supplier', on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Supplier this component was purchased from (determines quality)")

    class Meta:
        unique_together = ['session', 'warehouse', 'component', 'supplier']

    def get_quality(self):
        """Get the quality of this component stock based on its supplier"""
        if self.supplier:
            return self.supplier.quality
        # Fallback to component's default quality
        return self.component.get_quality_for_session(self.session)


class BikeStock(models.Model):
    """Lagerbestand Fahrräder"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stored_bikes')
    bike = models.OneToOneField(ProducedBike, on_delete=models.CASCADE)


class WarehouseType(models.Model):
    """Lagertypen die gekauft werden können"""
    name = models.CharField(max_length=100)
    capacity_m2 = models.FloatField(help_text="Lagerkapazität in m²")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Einmaliger Kaufpreis")
    monthly_rent = models.DecimalField(max_digits=8, decimal_places=2, help_text="Monatliche Mietkosten")
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Sortierreihenfolge")

    class Meta:
        ordering = ['order', 'capacity_m2']

    def __str__(self):
        return f"{self.name} ({self.capacity_m2}m² - {self.purchase_price}€)"

    @classmethod
    def get_default_types(cls):
        """Returns default warehouse types if none exist"""
        return [
            {
                'name': 'Klein',
                'capacity_m2': 100.0,
                'purchase_price': Decimal('15000.00'),
                'monthly_rent': Decimal('1000.00'),
                'description': 'Kleines Lager für den Einstieg',
                'order': 1
            },
            {
                'name': 'Mittel',
                'capacity_m2': 250.0,
                'purchase_price': Decimal('35000.00'),
                'monthly_rent': Decimal('2200.00'),
                'description': 'Mittelgroßes Lager für wachsende Unternehmen',
                'order': 2
            },
            {
                'name': 'Groß',
                'capacity_m2': 500.0,
                'purchase_price': Decimal('65000.00'),
                'monthly_rent': Decimal('4000.00'),
                'description': 'Großes Lager für umfangreiche Produktion',
                'order': 3
            },
            {
                'name': 'Extra Groß',
                'capacity_m2': 1000.0,
                'purchase_price': Decimal('120000.00'),
                'monthly_rent': Decimal('7500.00'),
                'description': 'Sehr großes Lager für Großunternehmen',
                'order': 4
            },
        ]
