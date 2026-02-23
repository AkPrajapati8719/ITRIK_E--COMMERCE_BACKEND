# ITRIK Backend - Deployment & Setup Guide

## 🖥️ Local Development Setup

### Prerequisites
- Python 3.9+
- pip & virtualenv
- PostgreSQL (optional, for production)
- Git

### Step 1: Clone & Install

```bash
cd itrik_backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy .env file
cp .env .env.local

# Edit .env.local with your settings
# For development, default settings are fine
```

### Step 3: Database Setup

```bash
# Apply migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser

# Optional: Load sample data
python manage.py loaddata sample_data.json
```

### Step 4: Run Development Server

```bash
python manage.py runserver

# Server runs at http://localhost:8000
# Admin at http://localhost:8000/admin
```

---

## 🚀 Production Deployment (AWS)

### Phase 1: Prepare AWS Environment

#### 1.1 Create RDS PostgreSQL Database
```bash
# AWS RDS Setup
- Engine: PostgreSQL
- Version: 15.x
- Instance class: db.t3.micro (free tier)
- Storage: 20 GB
- Multi-AZ: No (for cost)
- DB Name: itrik_db
- Master username: postgres
- Save endpoint for later
```

#### 1.2 Create S3 Bucket for Media
```bash
# AWS S3 Setup
- Bucket name: itrik-media-{your-name}
- Region: us-east-1
- Block public access: OFF
- Enable versioning: YES
- Create CORS configuration:

[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["https://yourdomain.com"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

#### 1.3 Create IAM User for S3 Access
```bash
# IAM Setup
- Create new user: itrik-s3-user
- Attach policy: AmazonS3FullAccess
- Create access keys
- Save Access Key ID & Secret Access Key
```

#### 1.4 Create EC2 Instance
```bash
# EC2 Setup
- AMI: Ubuntu 22.04 LTS
- Instance type: t3.micro (free tier)
- Key pair: Create new, save .pem file
- Security group: Allow HTTP (80), HTTPS (443), SSH (22)
- Elastic IP: Allocate static IP
- Storage: 20 GB gp3
```

### Phase 2: Deploy Application

#### 2.1 SSH into EC2

```bash
chmod 600 your-key.pem
ssh -i your-key.pem ubuntu@your-elastic-ip
```

#### 2.2 Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql-client
sudo apt install -y nginx
sudo apt install -y supervisor
sudo apt install -y git
sudo apt install -y certbot python3-certbot-nginx
```

#### 2.3 Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/yourusername/itrik.git
cd itrik/itrik_backend
```

#### 2.4 Setup Python Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.5 Configure Environment Variables

```bash
# Edit .env file
nano .env

# Set these for production:
SECRET_KEY=your-django-secret-key-generate-one
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-ip

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=itrik_db
DB_USER=postgres
DB_PASSWORD=your-rds-password
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=your-iam-access-key
AWS_SECRET_ACCESS_KEY=your-iam-secret-key
AWS_STORAGE_BUCKET_NAME=itrik-media-yourname
AWS_S3_REGION_NAME=us-east-1

# Frontend
FRONTEND_URL=https://yourdomain.com
```

#### 2.6 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 2.7 Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Phase 3: Configure Web Server (Nginx)

#### 3.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/itrik
```

```nginx
upstream itrik_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 50M;

    location / {
        proxy_pass http://itrik_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/itrik/itrik_backend/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/itrik/itrik_backend/media/;
    }
}
```

#### 3.2 Enable Nginx Configuration

```bash
sudo ln -s /etc/nginx/sites-available/itrik /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Phase 4: Configure Application Server (Gunicorn)

#### 4.1 Install Gunicorn

```bash
source venv/bin/activate
pip install gunicorn
```

#### 4.2 Create Gunicorn Systemd Service

```bash
sudo nano /etc/systemd/system/itrik.service
```

```ini
[Unit]
Description=ITRIK Django Application
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/itrik/itrik_backend
Environment="PATH=/home/ubuntu/itrik/itrik_backend/venv/bin"
ExecStart=/home/ubuntu/itrik/itrik_backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    core.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4.3 Start Gunicorn Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable itrik
sudo systemctl start itrik
sudo systemctl status itrik
```

### Phase 5: Setup HTTPS (SSL Certificate)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl restart nginx
```

### Phase 6: Setup Log Monitoring

```bash
# Create logs directory
mkdir -p /home/ubuntu/itrik/logs

# View logs
tail -f /home/ubuntu/itrik/logs/debug.log

# Monitor Gunicorn
journalctl -u itrik -f
```

---

## 📊 Database Backup & Maintenance

### Backup PostgreSQL (RDS)

```bash
# Create backup via AWS console or:
aws rds create-db-snapshot \
  --db-instance-identifier itrik-db \
  --db-snapshot-identifier itrik-db-backup-$(date +%Y%m%d)
```

### Monitor RDS

```bash
aws rds describe-db-instances \
  --db-instance-identifier itrik-db
```

---

## 🔒 Security Checklist

- [ ] Update Django SECRET_KEY (use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set DEBUG=False
- [ ] Configure SECURE_SSL_REDIRECT=True
- [ ] Set SECURE_HSTS_SECONDS=31536000
- [ ] Enable SECURE_COOKIE_HTTPONLY=True
- [ ] Setup firewall rules (Security Groups)
- [ ] Enable CloudFront CDN for S3 media
- [ ] Setup AWS WAF for additional protection
- [ ] Configure VPC security
- [ ] Enable RDS encryption
- [ ] Setup database backups

---

## 📈 Performance Optimization

### Caching with Redis

```bash
# Install Redis on EC2
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Update settings.py:
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
```

### CDN for Static/Media

```python
# settings.py
AWS_CLOUDFRONT_DOMAIN = "your-cloudfront-id.cloudfront.net"
STATIC_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/static/"
MEDIA_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/media/"
```

### Database Optimization

```sql
-- Create indexes (already in models)
CREATE INDEX idx_orders_user_status ON orders_order(user_id, status);
CREATE INDEX idx_products_featured ON store_product(is_featured);
```

---

## 🐛 Troubleshooting

### 502 Bad Gateway
```bash
# Check Gunicorn status
sudo systemctl status itrik

# Check logs
journalctl -u itrik -n 50
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h your-rds-endpoint.amazonaws.com -U postgres -d itrik_db -c "SELECT 1;"
```

### S3 Upload Failures
```bash
# Test S3 credentials
aws s3 ls --profile default
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --noinput --clear
sudo systemctl restart nginx
```

---

## 📱 Frontend Integration

### Update API URL in Frontend

```javascript
// In your frontend (index.html)
const API_URL = 'https://yourdomain.com/api';  // Change from localhost
```

### CORS Configuration

Already configured in `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## 📞 Monitoring & Alerts

### Setup CloudWatch Monitoring

```bash
# Monitor CPU, Memory, Disk
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=your-instance-id \
  --start-time 2026-01-17T00:00:00Z \
  --end-time 2026-01-17T23:59:59Z \
  --period 3600 \
  --statistics Average
```

### Setup Application Monitoring

```bash
# Install Sentry for error tracking
pip install sentry-sdk

# Add to settings.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1
)
```

---

## 🔄 Continuous Deployment

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_IP }}
          username: ubuntu
          key: ${{ secrets.EC2_KEY }}
          script: |
            cd /home/ubuntu/itrik
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart itrik
```

---

## 💰 Cost Optimization

- Use EC2 t3.micro for low traffic (free tier)
- Set S3 lifecycle policies (delete old media)
- Use RDS Multi-AZ only for production
- Setup CloudFront for media delivery
- Monitor and optimize database queries
- Use auto-scaling for traffic spikes

---

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [AWS RDS Guide](https://docs.aws.amazon.com/rds/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/)
- [Certbot Documentation](https://certbot.eff.org/)

---

**Your ITRIK backend is now production-ready! 🚀**
