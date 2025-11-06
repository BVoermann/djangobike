from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model with role-based access"""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Spielleitung'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        help_text='User role: user for players, admin for Spielleitung'
    )

    company_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Default company name for new games'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def is_spielleitung(self):
        """Check if user has admin (Spielleitung) role"""
        return self.role == 'admin'

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.username} ({role_display})"
