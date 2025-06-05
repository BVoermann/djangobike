from django.db import models
from bikeshop.models import GameSession
from django.core.validators import MinValueValidator, MaxValueValidator


class Credit(models.Model):
    """Kredit"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    credit_type = models.CharField(max_length=20, choices=[
        ('short', 'Kurzfristig'),
        ('medium', 'Mittelfristig'),
        ('long', 'Langfristig')
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.FloatField()  # Zinssatz in %
    duration_months = models.IntegerField()
    remaining_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=8, decimal_places=2)
    taken_month = models.IntegerField()
    taken_year = models.IntegerField()
    is_active = models.BooleanField(default=True)


class Transaction(models.Model):
    """Transaktion für Finanzen"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=[
        ('income', 'Einnahme'),
        ('expense', 'Ausgabe')
    ])
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class MonthlyReport(models.Model):
    """Monatsbericht"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2)
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ['session', 'month', 'year']
