#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Create a superuser automatically (Uses environment variables)
# This will fail gracefully if the user already exists
python manage.py createsuperuser --no-input || true

# 🔥 NEW: Force the user to have admin permissions
# This ensures the user can actually log into /admin/
python manage.py shell -c "from accounts.models import User; u=User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').first(); 
if u: 
    u.is_staff=True; 
    u.is_superuser=True; 
    u.save(); 
    print('Admin permissions granted to:', u.email)"