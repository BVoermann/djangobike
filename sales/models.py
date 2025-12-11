from django.db import models
from bikeshop.models import GameSession, BikeType
from production.models import ProducedBike

class Market(models.Model):
    """Markt"""
    LOCATION_TYPE_CHOICES = [
        ('urban', 'Urban (City)'),
        ('suburban', 'Suburban'),
        ('rural', 'Rural'),
        ('mountainous', 'Mountainous'),
        ('coastal', 'Coastal'),
    ]

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    transport_cost_home = models.DecimalField(max_digits=6, decimal_places=2)
    transport_cost_foreign = models.DecimalField(max_digits=6, decimal_places=2)

    # Market volume constraints
    monthly_volume_capacity = models.IntegerField(default=200, help_text="Maximum bikes that can be sold per month")
    price_elasticity_factor = models.FloatField(default=1.0, help_text="Price sensitivity factor for demand curves")

    # Location characteristics for bike type demand
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, default='urban', help_text="Type of location affecting bike demand")
    green_city_factor = models.FloatField(default=1.0, help_text="Multiplier for e-bike demand (0.0-2.0, 1.0=neutral, >1.0=higher demand)")
    mountain_bike_factor = models.FloatField(default=1.0, help_text="Multiplier for mountain bike demand (0.0-2.0)")
    road_bike_factor = models.FloatField(default=1.0, help_text="Multiplier for road/racing bike demand (0.0-2.0)")
    city_bike_factor = models.FloatField(default=1.0, help_text="Multiplier for city/commuter bike demand (0.0-2.0)")

    def get_bike_type_demand_multiplier(self, bike_type_name):
        """Get demand multiplier based on bike type and location characteristics"""
        bike_type_lower = bike_type_name.lower()

        # E-bikes affected by green_city_factor
        if 'e-' in bike_type_lower or 'elektro' in bike_type_lower:
            return self.green_city_factor

        # Mountain bikes
        if 'mountain' in bike_type_lower or 'mtb' in bike_type_lower:
            return self.mountain_bike_factor

        # Road/Racing bikes
        if 'road' in bike_type_lower or 'racing' in bike_type_lower or 'rennrad' in bike_type_lower:
            return self.road_bike_factor

        # City/Commuter bikes
        if 'city' in bike_type_lower or 'urban' in bike_type_lower or 'commuter' in bike_type_lower or 'stadt' in bike_type_lower:
            return self.city_bike_factor

        # Default to 1.0 (no adjustment) for other bike types
        return 1.0

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

class SalesDecision(models.Model):
    """Player's sales decision - not yet executed"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike_type = models.ForeignKey('bikeshop.BikeType', on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    quantity = models.IntegerField()
    desired_price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Player's desired selling price per bike")
    transport_cost = models.DecimalField(max_digits=6, decimal_places=2, help_text="Transport cost per shipment (one-time cost for delivery to market)")
    decision_month = models.IntegerField(help_text="Month when decision was made")
    decision_year = models.IntegerField(help_text="Year when decision was made")
    is_processed = models.BooleanField(default=False, help_text="Whether this decision has been processed by market simulation")

    # Results after processing
    quantity_sold = models.IntegerField(default=0, help_text="How many bikes actually sold")
    actual_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Actual revenue received")
    unsold_reason = models.CharField(max_length=100, blank=True, help_text="Reason bikes didn't sell (e.g. 'market_oversaturated')")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.name} - {self.bike_type.name} ({self.price_segment}) x{self.quantity} to {self.market.name}"

    class Meta:
        ordering = ['-created_at']


class SalesOrder(models.Model):
    """Verkaufsauftrag"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike = models.ForeignKey(ProducedBike, on_delete=models.CASCADE)
    sale_month = models.IntegerField()
    sale_year = models.IntegerField()
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    transport_cost = models.DecimalField(max_digits=6, decimal_places=2, help_text="Transport cost (only set on first bike of shipment, others have 0)")
    is_completed = models.BooleanField(default=False)


# Import market research models
from .models_market_research import MarketResearch, MarketResearchTransaction
