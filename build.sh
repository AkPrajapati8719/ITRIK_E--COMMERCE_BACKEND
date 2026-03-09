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
python manage.py shell -c "
from accounts.models import User
import os

email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

u = User.objects.filter(email=email).first()
if u:
    u.set_password(password) # Overwrites unusable password markers
    u.is_staff = True        # Grants access to /admin/
    u.is_superuser = True    # Grants all permissions
    u.is_active = True       # Ensures account isn't locked
    u.save()
    print(f'✅ Successfully updated and activated admin: {email}')
else:
    print('❌ Admin user not found. Check DJANGO_SUPERUSER_EMAIL in Render.')
"