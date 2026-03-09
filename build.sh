#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
# Ensure whitenoise is in your requirements.txt for this to work
pip install -r requirements.txt

# 2. Gather static files (Admin CSS/JS/Images)
# This uses WhiteNoise to fix the 404 errors in your logs
python manage.py collectstatic --no-input

# 3. Apply database migrations
# Syncs your PostgreSQL database with your Django models
python manage.py migrate

# 4. Create superuser automatically
# Fails gracefully if the user already exists
python manage.py createsuperuser --no-input || true

# 5. 🔥 FORCE UPDATE: Fixes unusable passwords and staff permissions
# This ensures access to /admin/ regardless of custom model logic
python manage.py shell -c "
from accounts.models import User
import os

email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if not email or not password:
    print('❌ ERROR: DJANGO_SUPERUSER_EMAIL or PASSWORD not set in Render Environment.')
else:
    user, created = User.objects.update_or_create(
        email=email,
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    user.set_password(password)
    user.save()
    print(f'✅ Done! User {email} is now a Staff Superuser with a fresh password.')
"