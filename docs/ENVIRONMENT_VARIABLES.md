# Environment Variables Documentation

This document describes all environment variables required to run the Django blog application in production.

## Table of Contents

- [Required Variables](#required-variables)
- [Optional Variables](#optional-variables)
- [Database Configuration](#database-configuration)
- [Cache Configuration](#cache-configuration)
- [Error Tracking](#error-tracking)
- [Security Best Practices](#security-best-practices)
- [Example Configuration](#example-configuration)

---

## Required Variables

These environment variables **must** be set for the application to run in production.

### DJANGO_SECRET_KEY

**Description:** Secret key used for cryptographic signing in Django (sessions, cookies, CSRF tokens, etc.).

**Format:** String (50+ characters recommended)

**Example:** `django-insecure-abc123xyz789...`

**How to generate:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Security Notes:**
- Must be kept secret and never committed to version control
- Should be unique per environment (development, staging, production)
- Changing this value will invalidate all existing sessions and signed data

---

### DJANGO_ALLOWED_HOSTS

**Description:** Comma-separated list of host/domain names that Django will serve.

**Format:** Comma-separated string

**Example:** `example.com,www.example.com,blog.example.com`

**Security Notes:**
- Required for production (prevents HTTP Host header attacks)
- Do not use wildcards in production
- Include all domains and subdomains where the application will be accessed

---

### Database Configuration (Option 1: DATABASE_URL)

**Description:** Complete database connection URL in a single variable.

**Format:** `<engine>://<user>:<password>@<host>:<port>/<database>`

**Examples:**
- PostgreSQL: `postgresql://bloguser:password123@localhost:5432/blogdb`
- MySQL: `mysql://bloguser:password123@localhost:3306/blogdb`

**Supported Engines:**
- `postgresql` - PostgreSQL (recommended)
- `mysql` - MySQL/MariaDB

**Notes:**
- This is the recommended approach (simpler configuration)
- If set, individual DB_* variables are ignored
- Requires `dj-database-url` package

---

### Database Configuration (Option 2: Individual Variables)

If `DATABASE_URL` is not set, these variables are required:

#### DB_NAME

**Description:** Database name

**Example:** `blogdb`

---

#### DB_USER

**Description:** Database username

**Example:** `bloguser`

---

#### DB_PASSWORD

**Description:** Database password

**Example:** `secure_password_123`

**Security Notes:**
- Use strong passwords (16+ characters, mixed case, numbers, symbols)
- Never commit passwords to version control

---

#### DB_HOST

**Description:** Database server hostname or IP address

**Default:** `localhost`

**Example:** `db.example.com` or `10.0.1.50`

---

#### DB_PORT

**Description:** Database server port

**Default:** `5432` (PostgreSQL) or `3306` (MySQL)

**Example:** `5432`

---

#### DB_ENGINE

**Description:** Django database backend engine

**Default:** `django.db.backends.postgresql`

**Options:**
- `django.db.backends.postgresql` - PostgreSQL
- `django.db.backends.mysql` - MySQL/MariaDB

---

## Optional Variables

These variables have sensible defaults but can be customized.

### DJANGO_DEBUG

**Description:** Enable/disable debug mode

**Format:** Boolean string (`True`, `False`, `1`, `0`, `yes`, `no`)

**Default:** `False`

**Example:** `False`

**Security Notes:**
- **MUST be `False` in production**
- Debug mode exposes sensitive information (stack traces, settings, SQL queries)
- Only enable for local development

---

### REDIS_URL

**Description:** Redis connection URL for caching and session storage

**Format:** `redis://<host>:<port>/<db>`

**Default:** `redis://127.0.0.1:6379/1`

**Example:** `redis://redis.example.com:6379/1`

**Notes:**
- Redis is used for caching, rate limiting, and session storage
- Database number (0-15) can be used to separate environments
- Supports password authentication: `redis://:password@host:port/db`

---

### SENTRY_DSN

**Description:** Sentry Data Source Name for error tracking

**Format:** URL provided by Sentry

**Example:** `https://abc123@o123456.ingest.sentry.io/7890123`

**Notes:**
- Optional but highly recommended for production
- Requires `sentry-sdk` package
- Get DSN from your Sentry project settings

---

### SENTRY_TRACES_SAMPLE_RATE

**Description:** Percentage of transactions to send to Sentry for performance monitoring

**Format:** Float between 0.0 and 1.0

**Default:** `0.1` (10%)

**Example:** `0.1`

**Notes:**
- `1.0` = 100% of transactions (high quota usage)
- `0.1` = 10% of transactions (recommended for production)
- `0.0` = Disable performance monitoring

---

### SENTRY_ENVIRONMENT

**Description:** Environment name for Sentry error tracking

**Default:** `production`

**Example:** `production`, `staging`, `development`

**Notes:**
- Helps filter errors by environment in Sentry dashboard

---

## Database Configuration

### Connection Pooling

The application uses persistent database connections with the following settings:

- **Connection Max Age:** 600 seconds (10 minutes)
- **Connection Health Checks:** Enabled
- **Connection Timeout:** 10 seconds
- **Query Timeout:** 30 seconds (PostgreSQL only)

### PostgreSQL Specific

PostgreSQL connections include:
- Statement timeout: 30 seconds
- Automatic connection health checks

### MySQL Specific

MySQL connections include:
- Strict transaction tables mode
- Connection timeout: 10 seconds

---

## Cache Configuration

### Redis Cache Settings

The application uses Redis for:
- **Page caching** (blog list, filters)
- **Session storage**
- **Rate limiting** (comment spam, like/dislike abuse)

**Cache Configuration:**
- Max connections: 50
- Socket timeout: 5 seconds
- Connection timeout: 5 seconds
- Default TTL: 300 seconds (5 minutes)
- Key prefix: `blog_prod`

---

## Error Tracking

### Sentry Integration

When `SENTRY_DSN` is configured, the application sends:
- Error events (ERROR level and above)
- Performance traces (based on sample rate)
- Stack traces attached to messages

**PII Handling:**
- Default PII (IP addresses, cookies) is **not sent** by default
- User information is anonymized

---

## Security Best Practices

### Secret Management

1. **Never commit secrets to version control**
   - Use `.env` files locally (add to `.gitignore`)
   - Use environment variables in production
   - Use secret management services (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **Rotate secrets regularly**
   - Change `DJANGO_SECRET_KEY` periodically
   - Rotate database passwords
   - Update API keys and tokens

3. **Use strong passwords**
   - Database passwords: 16+ characters
   - Mix uppercase, lowercase, numbers, symbols
   - Avoid dictionary words

### Environment Separation

Use different values for each environment:

| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `DJANGO_DEBUG` | `True` | `False` | `False` |
| `DJANGO_SECRET_KEY` | Dev key | Staging key | Production key |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | `staging.example.com` | `example.com,www.example.com` |
| `DATABASE_URL` | Local DB | Staging DB | Production DB |
| `REDIS_URL` | Local Redis | Staging Redis | Production Redis |
| `SENTRY_ENVIRONMENT` | `development` | `staging` | `production` |

### HTTPS Requirements

In production, the following security features are automatically enabled:

- **HTTPS redirect:** All HTTP requests redirect to HTTPS
- **HSTS:** Browsers will only use HTTPS for 1 year
- **Secure cookies:** Session and CSRF cookies only sent over HTTPS
- **CSP headers:** Content Security Policy prevents XSS attacks

**Prerequisites:**
- SSL/TLS certificate installed on web server
- Reverse proxy (nginx, Apache) configured for HTTPS
- `X-Forwarded-Proto` header set by proxy

---

## Example Configuration

### Example .env File

See `.env.example` in the project root for a complete example.

### Minimal Production Configuration

```bash
# Required
DJANGO_SECRET_KEY=your-secret-key-here-50-plus-characters-recommended
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DATABASE_URL=postgresql://bloguser:password@localhost:5432/blogdb

# Optional (with defaults)
DJANGO_DEBUG=False
REDIS_URL=redis://127.0.0.1:6379/1
```

### Full Production Configuration

```bash
# Django Core Settings
DJANGO_SECRET_KEY=your-secret-key-here-50-plus-characters-recommended
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,blog.example.com

# Database Configuration (Option 1: Single URL)
DATABASE_URL=postgresql://bloguser:secure_password@db.example.com:5432/blogdb

# Database Configuration (Option 2: Individual Variables)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=blogdb
# DB_USER=bloguser
# DB_PASSWORD=secure_password
# DB_HOST=db.example.com
# DB_PORT=5432

# Cache Configuration
REDIS_URL=redis://redis.example.com:6379/1

# Error Tracking
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/7890123
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_ENVIRONMENT=production
```

---

## Deployment Checklist

Before deploying to production, verify:

- [ ] `DJANGO_SECRET_KEY` is set and unique
- [ ] `DJANGO_DEBUG` is set to `False`
- [ ] `DJANGO_ALLOWED_HOSTS` includes all production domains
- [ ] Database credentials are configured (via `DATABASE_URL` or individual variables)
- [ ] Database is accessible from application server
- [ ] Redis is running and accessible
- [ ] SSL/TLS certificate is installed
- [ ] Web server is configured for HTTPS
- [ ] Static files are collected (`python manage.py collectstatic`)
- [ ] Database migrations are applied (`python manage.py migrate`)
- [ ] Sentry DSN is configured (optional but recommended)
- [ ] Log directories exist and are writable (`logs/`)
- [ ] Environment variables are loaded before starting application

---

## Troubleshooting

### Application won't start

**Error:** `ValueError: DJANGO_SECRET_KEY environment variable must be set`

**Solution:** Set the `DJANGO_SECRET_KEY` environment variable.

---

**Error:** `ValueError: DJANGO_ALLOWED_HOSTS environment variable must be set`

**Solution:** Set `DJANGO_ALLOWED_HOSTS` with your domain names.

---

**Error:** `ValueError: Database configuration required`

**Solution:** Set either `DATABASE_URL` or all individual database variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`).

---

### Database connection fails

**Error:** `django.db.utils.OperationalError: could not connect to server`

**Solution:**
1. Verify database server is running
2. Check `DB_HOST` and `DB_PORT` are correct
3. Verify firewall allows connections
4. Test connection manually: `psql -h <host> -U <user> -d <database>`

---

### Redis connection fails

**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
1. Verify Redis server is running
2. Check `REDIS_URL` is correct
3. Test connection: `redis-cli -h <host> -p <port> ping`

---

### Static files not loading

**Issue:** CSS/JS files return 404 errors

**Solution:**
1. Run `python manage.py collectstatic`
2. Verify `STATIC_ROOT` directory exists
3. Configure web server to serve static files
4. Check `STATIC_URL` matches web server configuration

---

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Django Security Settings](https://docs.djangoproject.com/en/5.2/topics/security/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Sentry Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
