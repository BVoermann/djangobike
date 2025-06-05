from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class GameSession(models.Model):
    """Hauptsession für das Spiel"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    current_month = models.IntegerField(default=1)
    current_year = models.IntegerField(default=2024)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=80000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - Monat {self.current_month}/{self.current_year}"


class Supplier(models.Model):
    """Lieferant"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    payment_terms = models.IntegerField(default=30)  # Zahlungsziel in Tagen
    delivery_time = models.IntegerField(default=30)  # Lieferzeit in Tagen
    complaint_probability = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # Reklamationswahrscheinlichkeit in %
    complaint_quantity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # Reklamationsanzahl in %
    quality = models.CharField(max_length=20, choices=[
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])

    def __str__(self):
        return self.name


class ComponentType(models.Model):
    """Komponententyp (Laufradsatz, Rahmen, etc.)"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    storage_space_per_unit = models.FloatField()  # Lagerplatz pro Einheit in m²

    def __str__(self):
        return self.name


class Component(models.Model):
    """Einzelne Komponente"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    component_type = models.ForeignKey(ComponentType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.component_type.name} - {self.name}"


class SupplierPrice(models.Model):
    """Preise der Lieferanten für Komponenten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ['session', 'supplier', 'component']


class BikeType(models.Model):
    """Fahrradtyp"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    skilled_worker_hours = models.FloatField()
    unskilled_worker_hours = models.FloatField()
    storage_space_per_unit = models.FloatField()

    # Benötigte Komponenten
    wheel_set = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_wheel')
    frame = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_frame')
    handlebar = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_handlebar')
    saddle = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_saddle')
    gearshift = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_gearshift')
    motor = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_motor', null=True, blank=True)

    def __str__(self):
        return self.name


class BikePrice(models.Model):
    """Verkaufspreise für Fahrräder"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ['session', 'bike_type', 'price_segment']


class Worker(models.Model):
    """Arbeiter"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    worker_type = models.CharField(max_length=20, choices=[
        ('skilled', 'Facharbeiter'),
        ('unskilled', 'Hilfsarbeiter')
    ])
    hourly_wage = models.DecimalField(max_digits=6, decimal_places=2)
    monthly_hours = models.IntegerField(default=150)
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['session', 'worker_type']

    def __str__(self):
        worker_type_display = dict(self._meta.get_field('worker_type').choices)[self.worker_type]
        return f"{worker_type_display} ({self.count} Arbeiter, {self.hourly_wage}€/h)"
