import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from content.models import ContactMessage

# Check if table exists
with connection.cursor() as cursor:
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Database Tables:')
    for table in tables:
        if 'contact' in table[0].lower():
            print(f'  ✓ {table[0]}')
            
    # Count messages
    cursor.execute('SELECT COUNT(*) FROM content_contactmessage')
    count = cursor.fetchone()[0]
    print(f'\nTotal messages: {count}')
    
    # Get messages
    cursor.execute('SELECT id, name, mobile, message FROM content_contactmessage LIMIT 5')
    messages = cursor.fetchall()
    print('\nMessages:')
    for msg in messages:
        print(f'  - {msg[1]} ({msg[2]}): {msg[3][:50]}...')

# Also check via ORM
print('\n\nUsing Django ORM:')
all_msgs = ContactMessage.objects.all()
print(f'Total: {all_msgs.count()}')
for msg in all_msgs:
    print(f'  - {msg.name} ({msg.mobile})')
