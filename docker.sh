#!/bin/bash

# Docker management script for credit approval system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev         Start development environment"
    echo "  prod        Start production environment"
    echo "  test        Run tests in Docker container"
    echo "  build       Build Docker images"
    echo "  stop        Stop all containers"
    echo "  clean       Remove containers and volumes"
    echo "  logs        Show logs from containers"
    echo "  shell       Open shell in web container"
    echo "  migrate     Run database migrations"
    echo "  createsuperuser Create Django superuser"
    echo ""
    echo "Options:"
    echo "  -h, --help  Show this help message"
    echo ""
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

case "$1" in
    "dev")
        log "Starting development environment..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "prod")
        log "Starting production environment..."
        docker-compose -f docker-compose.prod.yml up --build -d
        ;;
    "test")
        log "Running tests in Docker container..."
        docker-compose -f docker-compose.dev.yml run --rm web python run_tests.py core/tests.py -v
        ;;
    "build")
        log "Building Docker images..."
        docker-compose build
        ;;
    "stop")
        log "Stopping all containers..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.prod.yml down
        ;;
    "clean")
        log "Cleaning up containers and volumes..."
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose -f docker-compose.prod.yml down -v
        docker system prune -f
        ;;
    "logs")
        if [ -n "$2" ]; then
            docker-compose -f docker-compose.dev.yml logs -f "$2"
        else
            docker-compose -f docker-compose.dev.yml logs -f
        fi
        ;;
    "shell")
        log "Opening shell in web container..."
        docker-compose -f docker-compose.dev.yml exec web bash
        ;;
    "migrate")
        log "Running database migrations..."
        docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
        ;;
    "createsuperuser")
        log "Creating Django superuser..."
        docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
        ;;
    "-h"|"--help"|"")
        print_help
        ;;
    *)
        error "Unknown command: $1"
        print_help
        exit 1
        ;;
esac
