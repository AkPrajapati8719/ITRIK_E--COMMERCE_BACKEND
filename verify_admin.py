import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib import admin
from content.models import ContactMessage
from content.admin import ContactMessageAdmin

# Check if admin is registered
site = admin.site

msg_admin = site._registry.get(ContactMessage)

if msg_admin:
    print("✓ ContactMessage is registered in admin")
    print(f"  Admin Class: {msg_admin.__class__.__name__}")
    print(f"  list_display: {msg_admin.list_display}")
    print(f"  fields: {msg_admin.fields}")
    print(f"  readonly_fields: {msg_admin.readonly_fields}")
else:
    print("✗ ContactMessage is NOT registered in admin")

# Check total messages
total = ContactMessage.objects.count()
print(f"\nTotal messages in database: {total}")

for msg in ContactMessage.objects.all():
    print(f"  - {msg.name} | {msg.mobile} | {msg.message[:30]}...")
