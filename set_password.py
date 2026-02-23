import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
user = User.objects.get(mobile_number='123456890')
user.set_password('admin')
user.save()
print("✅ Password set to 'admin' for user 123456890")
