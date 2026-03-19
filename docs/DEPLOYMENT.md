# Django Blog Application - Deployment Guide

This comprehensive guide covers deploying the Django blog application to production environments with proper security, performance, and reliability configurations.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Setup and Migrations](#database-setup-and-migrations)
3. [Static File Collection](#static-file-collection)
4. [Redis Setup](#redis-setup)
5. [Environment Configuration](#environment-configuration)
6. [Deployment Procedures](#deployment-procedures)
7. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure the following items are completed:

### Security Requirements

- [ ] Generate a unique `DJANGO_SECRET_KEY` for production (never reuse development keys)
- [ ] Set `DJANGO_DEBUG=False` in production environment
- [ ] Configure `DJANGO_ALLOWED_HOSTS` with your production domain(s)
- [ ] SSL/TLS certificate installed and configured on web server
- [ ] Firewall rules configured (allow only necessary ports: 80, 443)
- [ ] Database credentials use strong passwords (minimum 16 characters)
- [ ] Redis password configured (if exposed to network)

### Infrastructure Requirements

- [ ] PostgreSQL 12+ or MySQL 8+ database server running
- [ ] Redis 6+ server running and accessible
- [ ] Python 3.10+ installed on production server
- [ ] Web server (nginx/Apache) configured as reverse proxy
- [ ] WSGI server (Gunicorn/uWSGI) configured
- [ ] Sufficient disk space (minimum 10GB for logs, media, backups)
- [ ] Sufficient memory (minimum 2GB RAM recommended)

### Application Requirements

- [ ] All dependencies installed from `requirements.txt`
- [ ] Environment variables file (`.env`) created and configured
- [ ] Static files directory writable by application user
- [ ] Media files directory writable by application user
- [ ] Logs directory created with appropriate permissions
- [ ] Database migrations tested in staging environment
- [ ] Backup strategy documented and tested

### Testing Requirements

- [ ] All unit tests passing (`python manage.py test`)
- [ ] All property-based tests passing
- [ ] Security scan completed (no critical vulnerabilities)
- [ ] Load testing completed (application handles expected traffic)
- [ ] Staging environment deployment successful

---

## Database Setup and Migrations

### Supported Databases

The application supports PostgreSQL (recommended) and MySQL for production deployments.

#### PostgreSQL Setup (Recommended)

**1. Install PostgreSQL:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**2. Create Database and User:**

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE blogdb;
CREATE USER bloguser WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
ALTER ROLE bloguser SET client_encoding TO 'utf8';
ALTER ROLE bloguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE bloguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;

-- Exit PostgreSQL shell
\q
```

**3. Configure PostgreSQL for Remote Access (if needed):**

Edit `/etc/postgresql/[version]/main/postgresql.conf`:
```
listen_addresses = 'localhost'  # Or specific IP for remote access
```

Edit `/etc/postgresql/[version]/main/pg_hba.conf`:
```
# Allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

**4. Set Environment Variable:**

```bash
# In .env file
DATABASE_URL=postgresql://bloguser:your_secure_password_here@localhost:5432/blogdb
```

#### MySQL Setup (Alternative)

**1. Install MySQL:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld
```

**2. Create Database and User:**

```bash
# Login to MySQL
sudo mysql -u root -p

# In MySQL shell:
CREATE DATABASE blogdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bloguser'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON blogdb.* TO 'bloguser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**3. Set Environment Variable:**

```bash
# In .env file
DATABASE_URL=mysql://bloguser:your_secure_password_here@localhost:3306/blogdb
```

### Running Database Migrations

**CRITICAL: Always backup your database before running migrations in production!**

#### Migration Sequence

The application includes the following key migrations:

1. **0001_initial.py** - Initial schema (Tags, Category, BlogPost, Comment models)
2. **0002_alter_blogpost_content.py** - Change content field to HTMLField
3. **0003_category_image.py** - Add image field to Category
4. **0004_add_slug.py** - Add slug field to BlogPost
5. **0005_add_featured_field.py** - Add is_featured field to BlogPost
6. **0006_comment_ip_address_comment_user_agent_and_more.py** - Add visitor tracking fields
7. **0007_alter_blogpost_options_alter_comment_options_and_more.py** - Add database indexes

#### Step-by-Step Migration Process

**1. Backup Database (REQUIRED):**

```bash
# PostgreSQL backup
pg_dump -U bloguser -h localhost blogdb > backup_$(date +%Y%m%d_%H%M%S).sql

# MySQL backup
mysqldump -u bloguser -p blogdb > backup_$(date +%Y%m%d_%H%M%S).sql
```

**2. Check Migration Status:**

```bash
# Activate virtual environment
source venv/bin/activate  # or: source .venv/bin/activate

# Check which migrations are applied
python manage.py showmigrations blog

# Expected output shows [X] for applied, [ ] for pending:
# blog
#  [X] 0001_initial
#  [X] 0002_alter_blogpost_content
#  ...
```

**3. Test Migrations (Dry Run):**

```bash
# Check for migration issues without applying
python manage.py migrate --plan

# This shows what will be executed
```

**4. Apply Migrations:**

```bash
# Apply all pending migrations
python manage.py migrate

# Or apply specific app migrations
python manage.py migrate blog

# Expected output:
# Running migrations:
#   Applying blog.0006_comment_ip_address_comment_user_agent_and_more... OK
#   Applying blog.0007_alter_blogpost_options_alter_comment_options_and_more... OK
```

**5. Verify Migration Success:**

```bash
# Check migration status again
python manage.py showmigrations blog

# All migrations should show [X]

# Verify database schema
python manage.py dbshell
# Then run: \dt (PostgreSQL) or SHOW TABLES; (MySQL)
```

#### Migration Rollback Procedures

If a migration fails or causes issues, you can rollback:

**1. Rollback to Specific Migration:**

```bash
# Rollback to migration 0005 (undoes 0006 and 0007)
python manage.py migrate blog 0005
```

**2. Restore from Backup (if rollback fails):**

```bash
# PostgreSQL restore
psql -U bloguser -h localhost blogdb < backup_20240101_120000.sql

# MySQL restore
mysql -u bloguser -p blogdb < backup_20240101_120000.sql
```

**3. Verify Application After Rollback:**

```bash
# Run tests to ensure application works
python manage.py test blog

# Check admin interface
python manage.py runserver
# Visit http://localhost:8000/admin
```

#### Common Migration Issues

**Issue: "Table already exists" error**

```bash
# Solution: Fake the migration (mark as applied without running)
python manage.py migrate blog 0006 --fake
```

**Issue: "Column does not exist" error**

```bash
# Solution: Check if migration was partially applied
# Restore from backup and re-run migrations
```

**Issue: Data loss during migration**

```bash
# Prevention: Always backup before migrations
# Recovery: Restore from backup
```

---

## Static File Collection

Static files (CSS, JavaScript, images) must be collected and served efficiently in production.

### WhiteNoise Configuration

The application uses WhiteNoise for serving static files directly from Django (no separate web server needed for static files).

**WhiteNoise is already configured in `config/settings/base.py`:**

```python
# Middleware includes WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be after SecurityMiddleware
    # ... other middleware
]

# Static file storage with compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Collecting Static Files

**1. Create Static Files Directory:**

```bash
# Directory is created automatically, but ensure permissions
mkdir -p staticfiles
chmod 755 staticfiles
```

**2. Collect Static Files:**

```bash
# Activate virtual environment
source venv/bin/activate

# Collect all static files to STATIC_ROOT
python manage.py collectstatic --noinput

# Expected output:
# 120 static files copied to '/path/to/project/staticfiles'
# Post-processed 'css/style.css' as 'css/style.abc123.css'
```

**3. Verify Static Files:**

```bash
# Check staticfiles directory
ls -la staticfiles/

# Should contain:
# - admin/ (Django admin static files)
# - css/ (your CSS files)
# - js/ (your JavaScript files)
# - images/ (your image files)
# - staticfiles.json (manifest file)
```

### Static File Serving Options

#### Option 1: WhiteNoise (Recommended for Small to Medium Sites)

**Advantages:**
- No additional web server configuration needed
- Automatic compression and caching headers
- Simplified deployment

**Configuration (already set in production.py):**

```python
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for immutable files
WHITENOISE_COMPRESS_OFFLINE = True  # Pre-compress files
```

**No additional steps needed - WhiteNoise serves files automatically.**

#### Option 2: Nginx (Recommended for High-Traffic Sites)

**Advantages:**
- Better performance for high traffic
- More control over caching and compression
- Can serve media files separately

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    # Static files
    location /static/ {
        alias /path/to/project/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /path/to/project/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Proxy to Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Media Files Handling

Media files (user uploads: blog banners, category images) require special handling.

**1. Create Media Directory:**

```bash
mkdir -p media/blog_banners media/category_images
chmod 755 media
chmod 755 media/blog_banners media/category_images
```

**2. Set Ownership (if using dedicated user):**

```bash
# If running as 'www-data' user
sudo chown -R www-data:www-data media/
```

**3. Configure Backup for Media Files:**

Media files should be backed up separately from the database (see Backup section).

---

## Redis Setup

Redis is used for caching, session storage, and rate limiting.

### Installing Redis

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install redis-server

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

**CentOS/RHEL:**

```bash
sudo yum install redis

# Start and enable Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

### Redis Configuration

**1. Configure Redis for Production:**

Edit `/etc/redis/redis.conf`:

```conf
# Bind to localhost only (if Redis is on same server)
bind 127.0.0.1

# Set a password (RECOMMENDED)
requirepass your_redis_password_here

# Enable persistence (save data to disk)
save 900 1      # Save after 900 seconds if at least 1 key changed
save 300 10     # Save after 300 seconds if at least 10 keys changed
save 60 10000   # Save after 60 seconds if at least 10000 keys changed

# Set max memory (adjust based on available RAM)
maxmemory 256mb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Enable AOF persistence for better durability
appendonly yes
appendfsync everysec
```

**2. Restart Redis:**

```bash
sudo systemctl restart redis-server
```

**3. Test Redis Connection:**

```bash
# Without password
redis-cli ping

# With password
redis-cli -a your_redis_password_here ping

# Test set/get
redis-cli -a your_redis_password_here
> SET test "Hello"
> GET test
> DEL test
> EXIT
```

**4. Configure Django to Use Redis:**

In `.env` file:

```bash
# Without password
REDIS_URL=redis://127.0.0.1:6379/1

# With password
REDIS_URL=redis://:your_redis_password_here@127.0.0.1:6379/1
```

### Redis Monitoring

**Check Redis Status:**

```bash
# Connection info
redis-cli -a your_redis_password_here INFO

# Memory usage
redis-cli -a your_redis_password_here INFO memory

# Connected clients
redis-cli -a your_redis_password_here CLIENT LIST

# Monitor commands in real-time
redis-cli -a your_redis_password_here MONITOR
```

**Common Redis Commands:**

```bash
# Clear all cache (use with caution!)
redis-cli -a your_redis_password_here FLUSHDB

# Check specific key
redis-cli -a your_redis_password_here GET "blog_prod:1:blog:filters"

# List all keys (use with caution on large datasets!)
redis-cli -a your_redis_password_here KEYS "*"

# Get number of keys
redis-cli -a your_redis_password_here DBSIZE
```

### Redis Backup

Redis automatically saves data to disk based on configuration. For additional safety:

```bash
# Manual save
redis-cli -a your_redis_password_here SAVE

# Background save (non-blocking)
redis-cli -a your_redis_password_here BGSAVE

# Backup Redis dump file
cp /var/lib/redis/dump.rdb /backup/redis_dump_$(date +%Y%m%d_%H%M%S).rdb
```

---

## Environment Configuration

### Environment Variables

All sensitive configuration must be stored in environment variables, never in code.

**1. Copy Example Environment File:**

```bash
cp .env.example .env
```

**2. Generate Secret Key:**

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**3. Configure Production Environment Variables:**

Edit `.env` file with production values:

```bash
# REQUIRED: Django Secret Key (generate unique key for production)
DJANGO_SECRET_KEY=your-generated-secret-key-50-plus-characters

# REQUIRED: Debug Mode (MUST be False in production)
DJANGO_DEBUG=False

# REQUIRED: Allowed Hosts (comma-separated domains)
DJANGO_ALLOWED_HOSTS=example.com,www.example.com

# REQUIRED: Database URL
DATABASE_URL=postgresql://bloguser:password@localhost:5432/blogdb

# OPTIONAL: Redis URL (defaults to localhost)
REDIS_URL=redis://:password@127.0.0.1:6379/1

# OPTIONAL: Sentry Error Tracking
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/7890123
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_ENVIRONMENT=production
```

**4. Secure Environment File:**

```bash
# Set restrictive permissions (only owner can read)
chmod 600 .env

# Verify .env is in .gitignore
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

**5. Verify Configuration:**

```bash
# Test that Django can load settings
python manage.py check --deploy

# This command checks for common deployment issues
# Fix any warnings or errors before deploying
```

### Settings Module Selection

The application uses different settings for different environments:

**Development:**
```bash
# Uses config/settings/base.py (default)
python manage.py runserver
```

**Production:**
```bash
# Set DJANGO_SETTINGS_MODULE environment variable
export DJANGO_SETTINGS_MODULE=config.settings.production

# Or in .env file:
echo "DJANGO_SETTINGS_MODULE=config.settings.production" >> .env

# Or specify when running commands:
python manage.py migrate --settings=config.settings.production
```

---

## Deployment Procedures

### Deployment Architecture

```
Internet → Load Balancer/CDN → Nginx → Gunicorn → Django Application
                                  ↓
                            Static Files
                                  ↓
                            Media Files

Django Application connects to:
- PostgreSQL/MySQL Database
- Redis Cache
```

### Initial Deployment

**1. Prepare Server:**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install python3.10 python3.10-venv python3-pip postgresql redis-server nginx

# Create application user (optional but recommended)
sudo useradd -m -s /bin/bash blogapp
sudo usermod -aG www-data blogapp
```

**2. Clone Application:**

```bash
# Switch to application user
sudo su - blogapp

# Clone repository
git clone https://github.com/yourusername/blog-app.git
cd blog-app

# Or upload files via SCP/SFTP
```

**3. Create Virtual Environment:**

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**4. Install Dependencies:**

```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
pip list
```

**5. Configure Environment:**

```bash
# Copy and edit .env file
cp .env.example .env
nano .env  # Edit with your production values
```

**6. Create Required Directories:**

```bash
# Create logs directory
mkdir -p logs
chmod 755 logs

# Create media directories
mkdir -p media/blog_banners media/category_images
chmod 755 media media/blog_banners media/category_images

# Create staticfiles directory
mkdir -p staticfiles
chmod 755 staticfiles
```

**7. Run Database Migrations:**

```bash
# Set settings module
export DJANGO_SETTINGS_MODULE=config.settings.production

# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

**8. Collect Static Files:**

```bash
python manage.py collectstatic --noinput
```

**9. Test Application:**

```bash
# Run development server to test
python manage.py runserver 0.0.0.0:8000

# Visit http://your-server-ip:8000
# Verify application loads correctly
# Press Ctrl+C to stop
```

### Gunicorn Configuration

Gunicorn is a production-grade WSGI server for running Django applications.

**1. Install Gunicorn:**

```bash
# Should already be in requirements.txt
pip install gunicorn
```

**2. Create Gunicorn Configuration File:**

Create `gunicorn_config.py` in project root:

```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "blog_app"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn instead of nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

**3. Create Systemd Service File:**

Create `/etc/systemd/system/blog.service`:

```ini
[Unit]
Description=Django Blog Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=blogapp
Group=www-data
WorkingDirectory=/home/blogapp/blog-app
Environment="PATH=/home/blogapp/blog-app/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/home/blogapp/blog-app/venv/bin/gunicorn \
    --config /home/blogapp/blog-app/gunicorn_config.py \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**4. Enable and Start Service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable blog

# Start service
sudo systemctl start blog

# Check status
sudo systemctl status blog

# View logs
sudo journalctl -u blog -f
```

### Nginx Configuration

**1. Install Nginx:**

```bash
sudo apt install nginx
```

**2. Create Nginx Configuration:**

Create `/etc/nginx/sites-available/blog`:

```nginx
# Upstream to Gunicorn
upstream blog_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com www.example.com;

    # SSL certificates (use Let's Encrypt certbot)
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /home/blogapp/blog-app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /home/blogapp/blog-app/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Proxy to Django application
    location / {
        proxy_pass http://blog_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health/ {
        proxy_pass http://blog_app;
        access_log off;
    }
}
```

**3. Enable Site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

**4. SSL Certificate with Let's Encrypt:**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com

# Test automatic renewal
sudo certbot renew --dry-run

# Certbot automatically adds renewal to cron
```

### Updating Deployed Application

**1. Pull Latest Changes:**

```bash
# Switch to application user
sudo su - blogapp
cd blog-app

# Activate virtual environment
source venv/bin/activate

# Pull changes
git pull origin main

# Or upload new files via SCP/SFTP
```

**2. Update Dependencies:**

```bash
# Install/update packages
pip install -r requirements.txt --upgrade
```

**3. Run Migrations:**

```bash
# ALWAYS backup database first!
pg_dump -U bloguser -h localhost blogdb > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate
```

**4. Collect Static Files:**

```bash
# Collect updated static files
python manage.py collectstatic --noinput
```

**5. Restart Application:**

```bash
# Restart Gunicorn
sudo systemctl restart blog

# Or reload for zero-downtime (if supported)
sudo systemctl reload blog

# Verify application is running
sudo systemctl status blog
```

**6. Clear Cache (if needed):**

```bash
# Clear Redis cache
redis-cli -a your_redis_password_here FLUSHDB

# Or clear specific cache keys via Django shell
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

---

## Backup and Disaster Recovery

### Backup Strategy

A comprehensive backup strategy includes database, media files, and configuration.

#### Database Backups

**Automated Daily Backups:**

Create `/home/blogapp/scripts/backup_database.sh`:

```bash
#!/bin/bash
# Database backup script

# Configuration
BACKUP_DIR="/home/blogapp/backups/database"
DB_NAME="blogdb"
DB_USER="bloguser"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/blogdb_$(date +%Y%m%d_%H%M%S).sql"

# Perform backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Delete backups older than retention period
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup
echo "$(date): Database backup completed: $BACKUP_FILE.gz" >> $BACKUP_DIR/backup.log
```

**Make Script Executable:**

```bash
chmod +x /home/blogapp/scripts/backup_database.sh
```

**Schedule with Cron:**

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/blogapp/scripts/backup_database.sh

# Add weekly backup to remote storage (example with rsync)
0 3 * * 0 rsync -avz /home/blogapp/backups/ user@backup-server:/backups/blog/
```

**Manual Database Backup:**

```bash
# PostgreSQL
pg_dump -U bloguser -h localhost blogdb > backup_$(date +%Y%m%d_%H%M%S).sql
gzip backup_*.sql

# MySQL
mysqldump -u bloguser -p blogdb > backup_$(date +%Y%m%d_%H%M%S).sql
gzip backup_*.sql
```

#### Media Files Backup

**Automated Media Backup:**

Create `/home/blogapp/scripts/backup_media.sh`:

```bash
#!/bin/bash
# Media files backup script

# Configuration
BACKUP_DIR="/home/blogapp/backups/media"
MEDIA_DIR="/home/blogapp/blog-app/media"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/media_$(date +%Y%m%d_%H%M%S).tar.gz"

# Create compressed archive
tar -czf $BACKUP_FILE -C $(dirname $MEDIA_DIR) $(basename $MEDIA_DIR)

# Delete backups older than retention period
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log backup
echo "$(date): Media backup completed: $BACKUP_FILE" >> $BACKUP_DIR/backup.log
```

**Schedule Media Backup:**

```bash
# Add to crontab (daily at 3 AM)
0 3 * * * /home/blogapp/scripts/backup_media.sh
```

#### Configuration Backup

**Backup Critical Configuration Files:**

```bash
# Create configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    .env \
    gunicorn_config.py \
    /etc/nginx/sites-available/blog \
    /etc/systemd/system/blog.service

# Store in secure location
mv config_backup_*.tar.gz /home/blogapp/backups/config/
```

### Disaster Recovery Procedures

#### Complete System Recovery

**1. Prepare New Server:**

```bash
# Install required packages
sudo apt update
sudo apt install python3.10 python3.10-venv postgresql redis-server nginx
```

**2. Restore Database:**

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE blogdb;
CREATE USER bloguser WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
\q

# Restore from backup
gunzip -c backup_20240101_020000.sql.gz | psql -U bloguser -h localhost blogdb
```

**3. Restore Application:**

```bash
# Clone or copy application files
git clone https://github.com/yourusername/blog-app.git
cd blog-app

# Create virtual environment and install dependencies
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Restore configuration
tar -xzf config_backup_20240101.tar.gz
```

**4. Restore Media Files:**

```bash
# Extract media backup
tar -xzf media_20240101_030000.tar.gz -C /home/blogapp/blog-app/
```

**5. Configure Services:**

```bash
# Copy systemd service file
sudo cp blog.service /etc/systemd/system/

# Copy nginx configuration
sudo cp blog /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/

# Reload services
sudo systemctl daemon-reload
sudo systemctl enable blog
sudo systemctl start blog
sudo systemctl reload nginx
```

**6. Verify Recovery:**

```bash
# Check application status
sudo systemctl status blog

# Test database connection
python manage.py dbshell

# Test application
curl http://localhost:8000/health/
```

#### Partial Recovery Scenarios

**Scenario 1: Database Corruption**

```bash
# Stop application
sudo systemctl stop blog

# Restore database from latest backup
gunzip -c backup_latest.sql.gz | psql -U bloguser -h localhost blogdb

# Restart application
sudo systemctl start blog
```

**Scenario 2: Lost Media Files**

```bash
# Extract media backup
tar -xzf media_backup_latest.tar.gz -C /home/blogapp/blog-app/

# Fix permissions
chmod -R 755 /home/blogapp/blog-app/media/
```

**Scenario 3: Configuration Loss**

```bash
# Restore from configuration backup
tar -xzf config_backup_latest.tar.gz

# Reload services
sudo systemctl daemon-reload
sudo systemctl restart blog
sudo nginx -t && sudo systemctl reload nginx
```

### Backup Testing

**Regularly test backups to ensure they work:**

```bash
# Test database restore (on test server)
createdb test_restore
gunzip -c backup_latest.sql.gz | psql -U bloguser test_restore

# Verify data
psql -U bloguser test_restore
SELECT COUNT(*) FROM blog_blogpost;
\q

# Clean up
dropdb test_restore
```

### Off-Site Backup Recommendations

**1. Cloud Storage (AWS S3, Google Cloud Storage, Azure Blob):**

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Sync backups to S3
aws s3 sync /home/blogapp/backups/ s3://your-bucket/blog-backups/
```

**2. Remote Server (rsync):**

```bash
# Sync to remote server
rsync -avz --delete /home/blogapp/backups/ user@backup-server:/backups/blog/
```

**3. Backup Rotation Strategy:**

- **Daily backups:** Keep for 7 days
- **Weekly backups:** Keep for 4 weeks
- **Monthly backups:** Keep for 12 months
- **Yearly backups:** Keep indefinitely (or per compliance requirements)

---

## Post-Deployment Verification

After deployment, verify all components are working correctly.

### Automated Verification Checklist

**1. Application Health:**

```bash
# Check application is running
curl -I https://example.com/

# Expected: HTTP/2 200

# Check health endpoint
curl https://example.com/health/

# Expected: {"status": "healthy", "database": "ok", "cache": "ok"}
```

**2. Database Connectivity:**

```bash
# Test database connection
python manage.py dbshell
\dt  # List tables (PostgreSQL)
\q   # Exit

# Or run a simple query
python manage.py shell
>>> from blog.models import BlogPost
>>> BlogPost.objects.count()
>>> exit()
```

**3. Redis Connectivity:**

```bash
# Test Redis connection
redis-cli -a your_redis_password_here ping
# Expected: PONG

# Test cache from Django
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'
>>> exit()
```

**4. Static Files:**

```bash
# Check static files are accessible
curl -I https://example.com/static/css/style.css
# Expected: HTTP/2 200

# Verify cache headers
curl -I https://example.com/static/css/style.css | grep -i cache-control
# Expected: Cache-Control: public, max-age=31536000, immutable
```

**5. Media Files:**

```bash
# Check media files are accessible (if any exist)
curl -I https://example.com/media/blog_banners/test.jpg
# Expected: HTTP/2 200
```

**6. SSL/HTTPS:**

```bash
# Test SSL certificate
openssl s_client -connect example.com:443 -servername example.com

# Check SSL rating (external tool)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=example.com
```

**7. Security Headers:**

```bash
# Check security headers
curl -I https://example.com/ | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
```

**8. Admin Interface:**

```bash
# Access admin interface
curl -I https://example.com/admin/

# Expected: HTTP/2 200 or 302 (redirect to login)

# Login and verify functionality
# Visit: https://example.com/admin/
```

**9. Blog Functionality:**

```bash
# Test blog list page
curl https://example.com/blog/ | grep -i "blog"

# Test blog detail page (replace with actual slug)
curl https://example.com/blog/post/test-post/ | grep -i "test"

# Test API endpoints
curl -X POST https://example.com/blog/post/test-post/like/ \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: your-csrf-token"
```

**10. Rate Limiting:**

```bash
# Test comment rate limiting (submit 4 comments quickly)
# Expected: First 3 succeed, 4th returns HTTP 429

# Test like/dislike rate limiting (perform 11 actions quickly)
# Expected: First 10 succeed, 11th returns HTTP 429
```

**11. Logging:**

```bash
# Check log files exist and are being written
ls -lh logs/

# View recent errors
tail -n 50 logs/errors.log

# View recent general logs
tail -n 50 logs/general.log

# View recent security logs
tail -n 50 logs/security.log

# Monitor logs in real-time
tail -f logs/general.log
```

**12. Performance:**

```bash
# Test response time
time curl -s https://example.com/ > /dev/null

# Expected: < 1 second for cached pages

# Test database query performance
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> from blog.models import BlogPost
>>> with CaptureQueriesContext(connection) as queries:
...     list(BlogPost.objects.select_related('category').prefetch_related('tags')[:10])
...     print(f"Queries: {len(queries)}")
>>> exit()

# Expected: Minimal queries (< 5 for optimized views)
```

### Manual Verification Checklist

- [ ] Homepage loads correctly
- [ ] Blog list page displays posts
- [ ] Blog detail page shows post content
- [ ] View counter increments on first visit
- [ ] Like/dislike buttons work
- [ ] Comment submission works
- [ ] Comment form validation works (test invalid inputs)
- [ ] Rate limiting works (test by exceeding limits)
- [ ] Admin interface accessible and functional
- [ ] Static files load (CSS, JavaScript, images)
- [ ] Media files display correctly
- [ ] HTTPS redirect works (HTTP → HTTPS)
- [ ] Mobile responsiveness works
- [ ] Browser console shows no errors
- [ ] All links work (no 404 errors)

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Application Won't Start

**Symptoms:**
- `systemctl status blog` shows "failed" or "inactive"
- Gunicorn errors in logs

**Diagnosis:**

```bash
# Check service status
sudo systemctl status blog

# View detailed logs
sudo journalctl -u blog -n 100 --no-pager

# Check Gunicorn logs
tail -n 50 logs/gunicorn_error.log
```

**Common Causes and Solutions:**

**1. Missing environment variables:**

```bash
# Verify .env file exists and has correct values
cat .env

# Check DJANGO_SECRET_KEY is set
grep DJANGO_SECRET_KEY .env
```

**2. Database connection failure:**

```bash
# Test database connection
psql -U bloguser -h localhost blogdb

# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Verify PostgreSQL is running
sudo systemctl status postgresql
```

**3. Permission issues:**

```bash
# Fix ownership
sudo chown -R blogapp:www-data /home/blogapp/blog-app

# Fix permissions
chmod 755 /home/blogapp/blog-app
chmod 600 /home/blogapp/blog-app/.env
```

**4. Python module import errors:**

```bash
# Verify virtual environment is activated
which python
# Should show: /home/blogapp/blog-app/venv/bin/python

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue 2: Static Files Not Loading

**Symptoms:**
- CSS/JavaScript not loading
- 404 errors for static files
- Unstyled pages

**Diagnosis:**

```bash
# Check static files exist
ls -la staticfiles/

# Check nginx configuration
sudo nginx -t

# Check nginx error log
sudo tail -n 50 /var/log/nginx/error.log
```

**Solutions:**

**1. Collect static files:**

```bash
source venv/bin/activate
python manage.py collectstatic --noinput
```

**2. Fix static file permissions:**

```bash
chmod -R 755 staticfiles/
```

**3. Verify nginx configuration:**

```nginx
# In /etc/nginx/sites-available/blog
location /static/ {
    alias /home/blogapp/blog-app/staticfiles/;  # Must end with /
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**4. Reload nginx:**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### Issue 3: Database Migration Errors

**Symptoms:**
- Migration fails with errors
- "Table already exists" errors
- "Column does not exist" errors

**Diagnosis:**

```bash
# Check migration status
python manage.py showmigrations

# Check database schema
python manage.py dbshell
\dt  # PostgreSQL
SHOW TABLES;  # MySQL
```

**Solutions:**

**1. Fake migration (if table already exists):**

```bash
python manage.py migrate blog 0006 --fake
```

**2. Rollback and retry:**

```bash
# Rollback to previous migration
python manage.py migrate blog 0005

# Re-run migration
python manage.py migrate blog 0006
```

**3. Reset migrations (CAUTION: data loss):**

```bash
# Backup database first!
pg_dump -U bloguser blogdb > backup_before_reset.sql

# Drop and recreate database
sudo -u postgres psql
DROP DATABASE blogdb;
CREATE DATABASE blogdb;
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
\q

# Run all migrations
python manage.py migrate
```

#### Issue 4: Redis Connection Errors

**Symptoms:**
- Cache errors in logs
- Rate limiting not working
- Session errors

**Diagnosis:**

```bash
# Check Redis is running
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Redis logs
sudo tail -n 50 /var/log/redis/redis-server.log
```

**Solutions:**

**1. Start Redis:**

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**2. Check Redis configuration:**

```bash
# Verify bind address
grep "^bind" /etc/redis/redis.conf

# Should be: bind 127.0.0.1
```

**3. Verify REDIS_URL:**

```bash
grep REDIS_URL .env
# Should match Redis configuration
```

**4. Test connection from Django:**

```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
>>> exit()
```

#### Issue 5: High Memory Usage

**Symptoms:**
- Server running out of memory
- Application crashes
- Slow performance

**Diagnosis:**

```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -n 10

# Check Gunicorn workers
ps aux | grep gunicorn
```

**Solutions:**

**1. Reduce Gunicorn workers:**

Edit `gunicorn_config.py`:

```python
# Reduce workers if memory constrained
workers = 2  # Instead of multiprocessing.cpu_count() * 2 + 1
```

**2. Configure Redis max memory:**

Edit `/etc/redis/redis.conf`:

```conf
maxmemory 128mb  # Adjust based on available RAM
maxmemory-policy allkeys-lru
```

**3. Enable swap (if not already enabled):**

```bash
# Create swap file (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**4. Optimize database queries:**

```bash
# Check for N+1 queries
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> # Test your views and check query count
```

#### Issue 6: Slow Performance

**Symptoms:**
- Pages load slowly
- High response times
- Database queries taking too long

**Diagnosis:**

```bash
# Check slow query log
tail -n 50 logs/general.log | grep "slow query"

# Check database connections
python manage.py dbshell
SELECT count(*) FROM pg_stat_activity;  # PostgreSQL
SHOW PROCESSLIST;  # MySQL

# Check cache hit rate
redis-cli INFO stats | grep keyspace
```

**Solutions:**

**1. Enable query optimization:**

Verify views use `select_related()` and `prefetch_related()`:

```python
# In views.py
posts = BlogPost.objects.select_related('category').prefetch_related('tags', 'comments')
```

**2. Increase cache TTL:**

Edit `config/settings/base.py`:

```python
CACHE_TTL = {
    'blog_list': 600,  # Increase from 300 to 600 seconds
    'filters': 1800,   # Increase from 900 to 1800 seconds
}
```

**3. Add database indexes:**

Check that all indexes are created:

```bash
python manage.py sqlmigrate blog 0007
# Verify CREATE INDEX statements
```

**4. Optimize images:**

```bash
# Install image optimization tools
sudo apt install optipng jpegoptim

# Optimize existing images
find media/ -name "*.png" -exec optipng {} \;
find media/ -name "*.jpg" -exec jpegoptim --strip-all {} \;
```

#### Issue 7: SSL Certificate Errors

**Symptoms:**
- Browser shows "Not Secure"
- SSL certificate expired
- Certificate mismatch

**Diagnosis:**

```bash
# Check certificate expiration
openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates

# Check certificate details
sudo certbot certificates
```

**Solutions:**

**1. Renew certificate:**

```bash
# Manual renewal
sudo certbot renew

# Force renewal (if not expired yet)
sudo certbot renew --force-renewal

# Reload nginx
sudo systemctl reload nginx
```

**2. Fix automatic renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Check cron/systemd timer
sudo systemctl list-timers | grep certbot
```

**3. Reconfigure certificate:**

```bash
# Delete and recreate
sudo certbot delete --cert-name example.com
sudo certbot --nginx -d example.com -d www.example.com
```

#### Issue 8: 502 Bad Gateway

**Symptoms:**
- Nginx shows "502 Bad Gateway"
- Application not responding

**Diagnosis:**

```bash
# Check if Gunicorn is running
sudo systemctl status blog

# Check nginx error log
sudo tail -n 50 /var/log/nginx/error.log

# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000
```

**Solutions:**

**1. Restart application:**

```bash
sudo systemctl restart blog
```

**2. Check Gunicorn bind address:**

In `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"  # Must match nginx proxy_pass
```

**3. Check nginx upstream:**

In `/etc/nginx/sites-available/blog`:

```nginx
upstream blog_app {
    server 127.0.0.1:8000 fail_timeout=0;  # Must match Gunicorn bind
}
```

**4. Check firewall:**

```bash
# Ensure port 8000 is accessible locally
sudo ufw status
```

#### Issue 9: Rate Limiting Not Working

**Symptoms:**
- Users can submit unlimited comments
- Like/dislike spam not blocked

**Diagnosis:**

```bash
# Check Redis is working
redis-cli ping

# Check rate limit keys in Redis
redis-cli KEYS "ratelimit:*"

# Test rate limiting manually
python manage.py shell
>>> from blog.utils.rate_limiter import RateLimiter
>>> RateLimiter.check_rate_limit("test_id", "comment", 3, 600)
>>> exit()
```

**Solutions:**

**1. Verify Redis connection:**

```bash
# Test from Django
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
>>> exit()
```

**2. Check rate limiter decorator:**

Verify views use `@rate_limit` decorator:

```python
from blog.utils.rate_limiter import rate_limit

@rate_limit('comment', limit=3, window=600)
def submit_comment(request, slug):
    # ...
```

**3. Clear rate limit cache:**

```bash
redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL
```

### Getting Help

**Log Files to Check:**

1. **Application logs:** `logs/general.log`, `logs/errors.log`
2. **Gunicorn logs:** `logs/gunicorn_error.log`, `logs/gunicorn_access.log`
3. **Nginx logs:** `/var/log/nginx/error.log`, `/var/log/nginx/access.log`
4. **System logs:** `sudo journalctl -u blog -n 100`
5. **PostgreSQL logs:** `/var/log/postgresql/postgresql-*.log`
6. **Redis logs:** `/var/log/redis/redis-server.log`

**Useful Commands:**

```bash
# Check all services status
sudo systemctl status blog postgresql redis-server nginx

# View real-time logs
sudo journalctl -u blog -f

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check network connections
sudo netstat -tlnp

# Check open files
sudo lsof -p $(pgrep -f gunicorn)
```

**Support Resources:**

- Django Documentation: https://docs.djangoproject.com/
- Gunicorn Documentation: https://docs.gunicorn.org/
- Nginx Documentation: https://nginx.org/en/docs/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Redis Documentation: https://redis.io/documentation

---

## Appendix

### Environment-Specific Configurations

#### Development Environment

```bash
# .env for development
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://bloguser:password@localhost:5432/blogdb_dev
REDIS_URL=redis://127.0.0.1:6379/0
```

#### Staging Environment

```bash
# .env for staging
DJANGO_SECRET_KEY=staging-unique-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=staging.example.com
DATABASE_URL=postgresql://bloguser:password@staging-db:5432/blogdb_staging
REDIS_URL=redis://staging-redis:6379/1
SENTRY_DSN=https://abc@sentry.io/123
SENTRY_ENVIRONMENT=staging
```

#### Production Environment

```bash
# .env for production
DJANGO_SECRET_KEY=production-unique-secret-key-50-plus-characters
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DATABASE_URL=postgresql://bloguser:secure_password@prod-db:5432/blogdb
REDIS_URL=redis://:redis_password@prod-redis:6379/1
SENTRY_DSN=https://abc@sentry.io/123
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Security Checklist

- [ ] SECRET_KEY is unique and not committed to version control
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured with production domains only
- [ ] SSL/TLS certificate installed and valid
- [ ] HTTPS redirect enabled
- [ ] HSTS headers configured
- [ ] Secure cookie settings enabled
- [ ] CSP headers configured
- [ ] Database uses strong passwords
- [ ] Redis uses password authentication
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] SSH key-based authentication (password auth disabled)
- [ ] Regular security updates applied
- [ ] Backups encrypted and stored securely
- [ ] Error tracking configured (Sentry)
- [ ] Rate limiting enabled
- [ ] Input validation and sanitization implemented
- [ ] SQL injection protection (Django ORM)
- [ ] XSS protection enabled
- [ ] CSRF protection enabled

### Performance Optimization Checklist

- [ ] Database indexes created
- [ ] Query optimization (select_related, prefetch_related)
- [ ] Redis caching enabled
- [ ] Static file compression enabled (WhiteNoise)
- [ ] Browser caching headers configured
- [ ] Image optimization implemented
- [ ] Pagination enabled
- [ ] Lazy loading for images
- [ ] Database connection pooling configured
- [ ] Gunicorn worker count optimized
- [ ] CDN configured (optional)
- [ ] Gzip compression enabled

### Monitoring Checklist

- [ ] Health check endpoint configured
- [ ] Application logs configured
- [ ] Error tracking configured (Sentry)
- [ ] Slow query logging enabled
- [ ] Security event logging enabled
- [ ] Log rotation configured
- [ ] Disk space monitoring
- [ ] Memory usage monitoring
- [ ] CPU usage monitoring
- [ ] Database performance monitoring
- [ ] Cache hit rate monitoring
- [ ] Uptime monitoring (external service)
- [ ] SSL certificate expiration monitoring

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying the Django blog application to production. Follow each section carefully, and use the troubleshooting section when issues arise.

**Key Takeaways:**

1. **Always backup before making changes** - Database, media files, and configuration
2. **Test in staging first** - Never deploy untested changes to production
3. **Monitor continuously** - Use logs, metrics, and error tracking
4. **Keep security updated** - Regular updates and security patches
5. **Document changes** - Keep deployment notes for future reference

For additional help, refer to the official documentation for each component or consult the troubleshooting section.

**Last Updated:** 2024
**Version:** 1.0
