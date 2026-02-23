from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, unique=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('content', models.TextField()),
                ('excerpt', models.CharField(blank=True, max_length=500)),
                ('featured_image', models.ImageField(blank=True, null=True, upload_to='blog/images/')),
                ('author', models.CharField(max_length=100)),
                ('published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('hero_title', models.CharField(default='Welcome to Our Store', max_length=200)),
                ('hero_subtitle', models.CharField(blank=True, default='Best products for you', max_length=300)),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='site/hero/')),
                ('hero_button_text', models.CharField(default='Shop Now', max_length=50)),
                ('about_text', models.TextField(blank=True, default='')),
                ('contact_email', models.EmailField(blank=True, default='', max_length=254)),
                ('contact_phone', models.CharField(blank=True, default='', max_length=20)),
                ('contact_address', models.CharField(blank=True, default='', max_length=500)),
                ('social_links', models.JSONField(default=dict, blank=True)),
            ],
        ),
    ]
