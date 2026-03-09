#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# 1. Create a superuser automatically (Uses environment variables)
# This fails gracefully if the user already exists
python manage.py createsuperuser --no-input || true

# 2. 🔥 FORCE UPDATE: Fixes unusable passwords and grants staff access
# This uses your Render Environment Variables to update the record
# ... inside your build.sh ...

python manage.py shell -c "
from accounts.models import User
import os

# Use the exact email from your Render Env Var
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

# This forces the user to be exactly what you need
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
print(f'Done! User {email} is now a Staff Superuser with a fresh password.')
"