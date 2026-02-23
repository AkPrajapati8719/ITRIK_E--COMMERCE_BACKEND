import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from content.models import ContactMessage

# Test data
test_message = ContactMessage.objects.create(
    name="Test User",
    mobile="9876543210",
    message="This is a test message from the contact form"
)

print(f"✅ Test message created successfully!")
print(f"ID: {test_message.id}")
print(f"Name: {test_message.name}")
print(f"Mobile: {test_message.mobile}")
print(f"Message: {test_message.message}")
print(f"Created at: {test_message.created_at}")

# Verify it's in the database
all_messages = ContactMessage.objects.all()
print(f"\n📋 Total messages in database: {all_messages.count()}")
for msg in all_messages:
    print(f"  - {msg.name} ({msg.mobile}): {msg.message[:50]}...")
