from django.db import models
from bikeshop.models import GameSession, BikeType, Component
from sales.models import Market
from decimal import Decimal
import random


class AICompetitor(models.Model):
    """AI-gesteuerter Konkurrent"""
    STRATEGY_CHOICES = [
        ('cheap_only', 'Billig-Strategie'),
        ('balanced', 'Ausgewogene Strategie'),
        ('premium_focus', 'Premium-Fokus'),
        ('e_bike_specialist', 'E-Bike Spezialist'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES)
    financial_resources = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    market_presence = models.FloatField(default=15.0)  # Marktanteil in %
    aggressiveness = models.FloatField(default=0.5)  # 0.0 - 1.0, wie aggressiv der Konkurrent ist
    efficiency = models.FloatField(default=0.7)  # 0.0 - 1.0, Produktionseffizienz
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Performance tracking
    total_bikes_produced = models.IntegerField(default=0)
    total_bikes_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.name} ({self.get_strategy_display()})"
    
    def get_production_capacity(self):
        """Berechnet Produktionskapazität basierend auf Ressourcen und Effizienz"""
        base_capacity = int(self.financial_resources / 1000)  # Basis: 1 Fahrrad pro 1000€
        return int(base_capacity * self.efficiency * (0.5 + self.market_presence / 100))
    
    def get_price_adjustment_factor(self):
        """Faktor für Preisanpassungen basierend auf Strategie"""
        strategy_factors = {
            'cheap_only': 0.7,
            'balanced': 1.0,
            'premium_focus': 1.3,
            'e_bike_specialist': 1.1,
        }
        return strategy_factors.get(self.strategy, 1.0)


class CompetitorProduction(models.Model):
    """Produktion eines Konkurrenten in einem Monat"""
    competitor = models.ForeignKey(AICompetitor, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    month = models.IntegerField()
    year = models.IntegerField()
    quantity_planned = models.IntegerField()
    quantity_produced = models.IntegerField(default=0)
    quantity_in_inventory = models.IntegerField(default=0, help_text="Unsold bikes remaining in inventory")
    production_cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2)
    months_in_inventory = models.IntegerField(default=0, help_text="Age of inventory in months")
    
    def get_inventory_age_penalty(self):
        """Returns price penalty for aged inventory"""
        if self.months_in_inventory <= 1:
            return 1.0
        elif self.months_in_inventory <= 3:
            return 0.95
        elif self.months_in_inventory <= 6:
            return 0.90
        else:
            return 0.85
    
    def update_inventory_age(self, current_month, current_year):
        """Updates inventory age"""
        months_diff = (current_year - self.year) * 12 + (current_month - self.month)
        self.months_in_inventory = max(0, months_diff)
        self.save()
    
    class Meta:
        unique_together = ['competitor', 'bike_type', 'price_segment', 'month', 'year']
    
    def __str__(self):
        return f"{self.competitor.name} - {self.bike_type.name} ({self.month}/{self.year})"


class CompetitorSale(models.Model):
    """Verkauf eines Konkurrenten"""
    competitor = models.ForeignKey(AICompetitor, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    month = models.IntegerField()
    year = models.IntegerField()
    quantity_offered = models.IntegerField()
    quantity_sold = models.IntegerField(default=0)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.competitor.name} - {self.market.name} ({self.month}/{self.year})"


class MarketCompetition(models.Model):
    """Wettbewerbssituation in einem Markt"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Gesamtangebot und Nachfrage
    total_supply = models.IntegerField(default=0)  # Alle Anbieter zusammen
    estimated_demand = models.IntegerField(default=0)
    maximum_market_volume = models.IntegerField(default=0, help_text="Maximum sales possible in this market segment")
    actual_sales_volume = models.IntegerField(default=0, help_text="Actual bikes sold this period")
    saturation_level = models.FloatField(default=0.0)  # 0.0 - 1.0+
    
    # Preisdruck und Nachfragekurve
    average_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price_pressure = models.FloatField(default=0.0)  # -1.0 bis 1.0
    demand_curve_elasticity = models.FloatField(default=1.0, help_text="Price elasticity of demand")
    optimal_price_point = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Price that maximizes volume")
    
    class Meta:
        unique_together = ['session', 'market', 'bike_type', 'price_segment', 'month', 'year']


class CompetitorStrategy:
    """Helper-Klasse für AI-Strategien"""
    
    @staticmethod
    def get_bike_type_preferences(strategy, bike_types):
        """Gibt Präferenzen für Fahrradtypen basierend auf Strategie zurück"""
        preferences = {}
        
        for bike_type in bike_types:
            name = bike_type.name.lower()
            
            if strategy == 'cheap_only':
                # Einfache, günstige Bikes bevorzugen
                if 'city' in name or 'basic' in name:
                    preferences[bike_type.id] = 0.8
                elif 'e-' in name or 'mountain' in name:
                    preferences[bike_type.id] = 0.2
                else:
                    preferences[bike_type.id] = 0.5
                    
            elif strategy == 'premium_focus':
                # Hochwertige Bikes bevorzugen
                if 'mountain' in name or 'racing' in name:
                    preferences[bike_type.id] = 0.9
                elif 'e-' in name:
                    preferences[bike_type.id] = 0.7
                else:
                    preferences[bike_type.id] = 0.3
                    
            elif strategy == 'e_bike_specialist':
                # E-Bikes stark bevorzugen
                if 'e-' in name:
                    preferences[bike_type.id] = 0.9
                else:
                    preferences[bike_type.id] = 0.1
                    
            else:  # balanced
                preferences[bike_type.id] = 0.6
                
        return preferences
    
    @staticmethod
    def get_price_segment_preferences(strategy):
        """Gibt Präferenzen für Preissegmente zurück"""
        if strategy == 'cheap_only':
            return {'cheap': 0.8, 'standard': 0.2, 'premium': 0.0}
        elif strategy == 'premium_focus':
            return {'cheap': 0.1, 'standard': 0.3, 'premium': 0.6}
        elif strategy == 'e_bike_specialist':
            return {'cheap': 0.2, 'standard': 0.5, 'premium': 0.3}
        else:  # balanced
            return {'cheap': 0.3, 'standard': 0.5, 'premium': 0.2}
    
    @staticmethod
    def calculate_production_cost(bike_type, strategy, efficiency):
        """Berechnet Produktionskosten für Konkurrenten"""
        # Basis-Materialkosten (vereinfacht)
        base_cost = 200  # Grundkosten für Komponenten
        
        # Arbeitskosten (Konkurrenten haben andere Lohnstrukturen)
        labor_cost = (bike_type.skilled_worker_hours * 15 + 
                     bike_type.unskilled_worker_hours * 10)
        
        # Effizienz-Faktor
        total_cost = (base_cost + labor_cost) / efficiency
        
        # Strategie-spezifische Anpassungen
        if strategy == 'cheap_only':
            total_cost *= 0.8  # Günstigere Produktion
        elif strategy == 'premium_focus':
            total_cost *= 1.2  # Höhere Qualität = höhere Kosten
        
        return Decimal(str(round(total_cost, 2)))


class StrategyConfiguration(models.Model):
    """Strategiekonfiguration aus Excel"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    strategy = models.CharField(max_length=50)
    designation = models.CharField(max_length=100)
    cheap_ratio = models.FloatField()
    standard_ratio = models.FloatField()
    premium_ratio = models.FloatField()
    price_factor = models.FloatField()
    production_volume = models.FloatField()
    quality_focus = models.FloatField()
    marketing_budget = models.FloatField()

    class Meta:
        unique_together = ['session', 'strategy']


class MarketDynamicsSettings(models.Model):
    """Marktdynamik-Einstellungen aus Excel"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=100)
    value = models.FloatField()
    description = models.TextField()

    class Meta:
        unique_together = ['session', 'parameter']


class BikeTypePreference(models.Model):
    """Fahrradtyp-Vorlieben für Strategien"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    strategy = models.CharField(max_length=50)
    bike_type_name = models.CharField(max_length=100)
    preference = models.FloatField()
    production_probability = models.FloatField()

    class Meta:
        unique_together = ['session', 'strategy', 'bike_type_name']
