#!/usr/bin/env python
"""
Create test users for the authentication system
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangobike.settings')
django.setup()

from authentication.models import CustomUser

# Create admin user (Spielleitung)
admin, created = CustomUser.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
    print(f'✓ Admin user created: username=admin, password=admin123')
else:
    print('✓ Admin user already exists')

# Create regular user
user1, created = CustomUser.objects.get_or_create(
    username='player1',
    defaults={
        'email': 'player1@example.com',
        'role': 'user',
        'company_name': 'Test Bikes GmbH',
    }
)
if created:
    user1.set_password('player123')
    user1.save()
    print(f'✓ User created: username=player1, password=player123')
else:
    print('✓ User player1 already exists')

# Create another regular user
user2, created = CustomUser.objects.get_or_create(
    username='player2',
    defaults={
        'email': 'player2@example.com',
        'role': 'user',
        'company_name': 'Cycle Masters AG',
    }
)
if created:
    user2.set_password('player123')
    user2.save()
    print(f'✓ User created: username=player2, password=player123')
else:
    print('✓ User player2 already exists')

print('\nTest users created successfully!')
print('Login as admin: username=admin, password=admin123')
print('Login as user: username=player1, password=player123')
print('Login as user: username=player2, password=player123')
