#!/usr/bin/env python
"""
Create Spielleiter admin account
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from authentication.models import CustomUser

# Create spielleiter admin user
spielleiter, created = CustomUser.objects.get_or_create(
    username='spielleiter',
    defaults={
        'email': 'spielleiter@example.com',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    spielleiter.set_password('SLPW')
    spielleiter.save()
    print(f'✓ Spielleiter admin user created successfully!')
    print(f'  Username: spielleiter')
    print(f'  Password: SLPW')
    print(f'  Role: Spielleitung (Admin)')
else:
    # Update password if user already exists
    spielleiter.set_password('SLPW')
    spielleiter.role = 'admin'
    spielleiter.is_staff = True
    spielleiter.is_superuser = True
    spielleiter.save()
    print(f'✓ Spielleiter user already exists - password updated to SLPW')
    print(f'  Username: spielleiter')
    print(f'  Password: SLPW')
    print(f'  Role: Spielleitung (Admin)')
