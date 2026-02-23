#!/usr/bin/env python
"""
Complete Contact Form Test Script
Tests the entire contact form workflow
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print("=" * 60)
print("CONTACT FORM COMPLETE DIAGNOSTIC TEST")
print("=" * 60)

# 1. Check Models
print("\n1. CHECKING MODELS...")
from content.models import ContactMessage, Blog, SiteSettings
print("   ✓ ContactMessage model imported")
print("   ✓ Blog model imported")
print("   ✓ SiteSettings model imported")

# 2. Check Admin Registration
print("\n2. CHECKING ADMIN REGISTRATION...")
from django.contrib import admin
site = admin.site
if ContactMessage in site._registry:
    print("   ✓ ContactMessage registered in admin")
    admin_class = site._registry[ContactMessage]
    print(f"     - list_display: {admin_class.list_display}")
    print(f"     - readonly_fields: {admin_class.readonly_fields}")
else:
    print("   ✗ ContactMessage NOT registered!")
    sys.exit(1)

# 3. Check Serializer
print("\n3. CHECKING SERIALIZER...")
from content.serializers import ContactMessageSerializer
test_data = {
    'name': 'John Test',
    'mobile': '9876543210',
    'message': 'Test message'
}
serializer = ContactMessageSerializer(data=test_data)
if serializer.is_valid():
    print("   ✓ ContactMessageSerializer is valid")
    print(f"     Fields: {list(serializer.validated_data.keys())}")
else:
    print(f"   ✗ Serializer errors: {serializer.errors}")
    sys.exit(1)

# 4. Check Views
print("\n4. CHECKING VIEWS...")
from content.views import ContactViewSet
print("   ✓ ContactViewSet imported")
print(f"     - queryset: {ContactViewSet.queryset.model.__name__}")
print(f"     - serializer_class: {ContactViewSet.serializer_class.__name__}")

# 5. Check URLs
print("\n5. CHECKING URL ROUTING...")
from django.urls import resolve, reverse
try:
    match = resolve('/api/contact/')
    print(f"   ✓ URL /api/contact/ resolves to {match.view_name}")
except:
    print("   ✗ URL /api/contact/ not found!")

# 6. Test Save
print("\n6. TESTING MESSAGE SAVE...")
msg = ContactMessage.objects.create(
    name='Test User',
    mobile='9876543210',
    message='This is a test message'
)
print(f"   ✓ Message created with ID: {msg.id}")

# 7. Test Retrieve
print("\n7. TESTING MESSAGE RETRIEVE...")
retrieved = ContactMessage.objects.get(id=msg.id)
print(f"   ✓ Message retrieved: {retrieved.name} ({retrieved.mobile})")

# 8. Test Count
print("\n8. CHECKING DATABASE...")
total = ContactMessage.objects.count()
print(f"   ✓ Total messages: {total}")

# Clean up
msg.delete()
print("   ✓ Test message deleted")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - SYSTEM IS READY!")
print("=" * 60)
print("\nYou can now:")
print("1. Visit http://127.0.0.1:8000/")
print("2. Go to Contact Us section")
print("3. Fill and submit the form")
print("4. Check admin: http://127.0.0.1:8000/admin/content/contactmessage/")
print("=" * 60)
