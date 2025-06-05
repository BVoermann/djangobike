from django.db import models
from bikeshop.models import GameSession, Supplier, Component
from django.core.validators import MinValueValidator


class ProcurementOrder(models.Model):
    """Bestellung von Komponenten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bestellung {self.id} - {self.supplier.name}"


class ProcurementOrderItem(models.Model):
    """Einzelne Artikel in einer Bestellung"""
    order = models.ForeignKey(ProcurementOrder, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity_ordered = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_delivered = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_defective = models.BooleanField(default=False)

    @property
    def total_price(self):
        return self.quantity_delivered * self.unit_price
