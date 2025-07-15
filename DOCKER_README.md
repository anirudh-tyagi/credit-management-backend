# Credit Management Backend - Docker Guide

This guide covers Docker setup and deployment for the Credit Management Backend system.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- Environment variables configured in `.env` file

## Quick Start

### Development Environment

```bash
# Start development environment
./docker.sh dev

# Or manually:
docker-compose -f docker-compose.dev.yml up --build
```

### Production Environment

```bash
# Start production environment
./docker.sh prod

# Or manually:
docker-compose -f docker-compose.prod.yml up --build -d
```

## Docker Files Overview

### Main Files

- `Dockerfile` - Development container configuration
- `Dockerfile.prod` - Production container configuration  
- `docker-compose.yml` - Base Docker Compose configuration
- `docker-compose.dev.yml` - Development environment
- `docker-compose.prod.yml` - Production environment with Nginx
- `entrypoint.sh` - Container initialization script
- `docker.sh` - Management script for common operations

### Configuration Files

- `nginx.conf` - Nginx configuration for production
- `.dockerignore` - Files to exclude from Docker build context

## Services

### Web Service
- **Development**: Django development server on port 8000
- **Production**: Gunicorn WSGI server behind Nginx on port 80
- **Health checks**: Database connectivity and migration status

### Database Service
- **Image**: PostgreSQL 15
- **Port**: 5432
- **Data**: Persistent volume `postgres_data`

### Redis Service
- **Image**: Redis 7 Alpine
- **Port**: 6379
- **Data**: Persistent volume `redis_data`

### Celery Service
- **Purpose**: Background task processing
- **Workers**: Configurable worker count
- **Dependencies**: Redis and Database

### Nginx Service (Production Only)
- **Purpose**: Reverse proxy and static file serving
- **Port**: 80
- **SSL**: Ready for SSL certificate configuration

## Common Commands

### Using docker.sh Script

```bash
# Start development environment
./docker.sh dev

# Start production environment
./docker.sh prod

# Run tests
./docker.sh test

# Build images
./docker.sh build

# Stop all containers
./docker.sh stop

# Clean up (remove containers and volumes)
./docker.sh clean

# View logs
./docker.sh logs
./docker.sh logs web  # specific service

# Open shell in web container
./docker.sh shell

# Run migrations
./docker.sh migrate

# Create superuser
./docker.sh createsuperuser
```

### Manual Docker Commands

```bash
# Build and start development environment
docker-compose -f docker-compose.dev.yml up --build

# Build and start production environment
docker-compose -f docker-compose.prod.yml up --build -d

# Run tests
docker-compose -f docker-compose.dev.yml run --rm web python run_tests.py core/tests.py -v

# Execute commands in running container
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# View logs
docker-compose -f docker-compose.dev.yml logs -f web

# Stop and remove containers
docker-compose -f docker-compose.dev.yml down

# Stop and remove containers with volumes
docker-compose -f docker-compose.dev.yml down -v
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
DEBUG=1
SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=credit_db
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

## Development vs Production

### Development
- Django development server
- Debug mode enabled
- Hot reload for code changes
- Direct database access on port 5432
- No SSL/HTTPS

### Production
- Gunicorn WSGI server
- Debug mode disabled
- Nginx reverse proxy
- SSL-ready configuration
- Static file serving via Nginx
- Health checks and restart policies

## Troubleshooting

### Common Issues

1. **Database connection failed**
   ```bash
   # Check if database is running
   docker-compose -f docker-compose.dev.yml ps db
   
   # Check database logs
   docker-compose -f docker-compose.dev.yml logs db
   ```

2. **Permission denied errors**
   ```bash
   # Fix file permissions
   chmod +x docker.sh entrypoint.sh
   ```

3. **Port already in use**
   ```bash
   # Stop conflicting services
   ./docker.sh stop
   
   # Or change ports in docker-compose files
   ```

4. **Build failures**
   ```bash
   # Clean build cache
   docker system prune -f
   
   # Rebuild from scratch
   docker-compose -f docker-compose.dev.yml build --no-cache
   ```

### Debugging

```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# View all logs
docker-compose -f docker-compose.dev.yml logs

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec web bash

# Check Django settings
docker-compose -f docker-compose.dev.yml exec web python manage.py diffsettings
```

## Testing in Docker

```bash
# Run all tests
./docker.sh test

# Run specific test
docker-compose -f docker-compose.dev.yml run --rm web python run_tests.py core/tests.py::TestCustomerRegistration -v

# Run tests with coverage
docker-compose -f docker-compose.dev.yml run --rm web python -m pytest core/tests.py --cov=core --cov-report=html
```

## Data Persistence

- Database data: `postgres_data` volume
- Redis data: `redis_data` volume
- Static files: `static_volume` volume (production)
- Media files: `media_volume` volume (production)

## Scaling

### Horizontal Scaling

```bash
# Scale web service
docker-compose -f docker-compose.prod.yml up --scale web=3

# Scale celery workers
docker-compose -f docker-compose.prod.yml up --scale celery=3
```

### Resource Limits

Add resource limits to docker-compose files:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Monitoring

### Health Checks

```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Check individual service
curl http://localhost:8000/admin/
```

### Logs

```bash
# Follow logs
docker-compose -f docker-compose.prod.yml logs -f

# Export logs
docker-compose -f docker-compose.prod.yml logs > app.log
```

## Security

- Non-root user in containers
- Minimal base images
- Security headers via Nginx
- Environment variable management
- Regular security updates

## Performance Optimization

- Multi-stage builds for production
- Optimized Python package installation
- Static file serving via Nginx
- Database connection pooling
- Redis caching

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U admin credit_db > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U admin credit_db < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v credit-management-backend_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```
