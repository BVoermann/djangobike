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
    
    # Inventory aging and carryover
    months_in_inventory = models.IntegerField(default=0, help_text="How many months this bike has been in inventory")
    storage_cost_accumulated = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Accumulated storage costs")
    
    def get_age_penalty_factor(self):
        """Returns price penalty factor based on inventory age"""
        if self.months_in_inventory <= 1:
            return 1.0
        elif self.months_in_inventory <= 3:
            return 0.95  # 5% penalty
        elif self.months_in_inventory <= 6:
            return 0.90  # 10% penalty
        else:
            return 0.85  # 15% penalty for very old inventory
    
    def update_inventory_age(self, current_month, current_year):
        """Updates inventory age and calculates storage costs"""
        # Calculate months since production
        months_diff = (current_year - self.production_year) * 12 + (current_month - self.production_month)
        self.months_in_inventory = max(0, months_diff)
        
        # Calculate storage costs (2% of production cost per month)
        from decimal import Decimal
        monthly_storage_cost = self.production_cost * Decimal('0.02')
        self.storage_cost_accumulated = monthly_storage_cost * self.months_in_inventory
        self.save()