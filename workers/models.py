from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Worker(models.Model):
    WORKER_TYPES = [
        ('skilled', 'Facharbeiter'),
        ('unskilled', 'Hilfsarbeiter'),
    ]

    name = models.CharField(max_length=100, verbose_name="Name")
    worker_type = models.CharField(
        max_length=10,
        choices=WORKER_TYPES,
        verbose_name="Arbeitertyp"
    )
    hourly_wage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Stundenlohn",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    efficiency = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name="Effizienz (%)",
        help_text="Effizienz in Prozent (100% = Normal, 150% = sehr effizient)"
    )
    experience_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Erfahrungslevel",
        help_text="Level 1-10 (höher = erfahrener)"
    )
    hired_date = models.DateTimeField(auto_now_add=True, verbose_name="Einstellungsdatum")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    class Meta:
        verbose_name = "Arbeiter"
        verbose_name_plural = "Arbeiter"
        ordering = ['worker_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_worker_type_display()})"

    @property
    def monthly_cost(self):
        """Berechnet die monatlichen Kosten bei 160 Stunden/Monat"""
        return self.hourly_wage * 160

    @property
    def productivity_score(self):
        """Berechnet einen Produktivitätswert basierend auf Effizienz und Erfahrung"""
        return (self.efficiency * self.experience_level) / 100

    @classmethod
    def get_total_monthly_costs(cls):
        """Berechnet die gesamten monatlichen Arbeiterkosten"""
        active_workers = cls.objects.filter(is_active=True)
        return sum(worker.monthly_cost for worker in active_workers)

    @classmethod
    def get_worker_counts(cls):
        """Gibt die Anzahl aktiver Arbeiter nach Typ zurück"""
        return {
            'skilled': cls.objects.filter(is_active=True, worker_type='skilled').count(),
            'unskilled': cls.objects.filter(is_active=True, worker_type='unskilled').count(),
        }