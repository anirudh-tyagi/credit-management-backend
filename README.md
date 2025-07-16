# Django Credit Approval System

A comprehensive Django-based credit approval system with REST API support for customer registration, loan eligibility checking, and loan management. Built with Django REST Framework and designed for scalability with Docker containerization.

##  Features

- **Customer Management**: Register and manage customer profiles with financial information
- **Credit Score Calculation**: Intelligent credit scoring based on loan history and payment behavior
- **Loan Eligibility**: Real-time loan eligibility assessment with personalized terms
- **Loan Management**: Complete loan lifecycle management from application to approval
- **RESTful API**: Clean, well-documented API endpoints
- **Docker Support**: Full containerization for development and production
- **Background Tasks**: Celery integration for asynchronous processing
- **Comprehensive Testing**: 100% test coverage with pytest

##  Tech Stack

- **Backend**: Django 5.2, Django REST Framework 3.14+
- **Database**: PostgreSQL 15 (Production), SQLite (Testing)
- **Cache & Message Broker**: Redis 7
- **Task Queue**: Celery 5.3+
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx (Production), Gunicorn
- **Testing**: pytest, pytest-django, pytest-cov

##  Prerequisites

- Docker 20.10+ and Docker Compose v2+
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)
- Git

##  Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/anirudh-tyagi/credit-management-backend
   cd credit-management-backend
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   ./docker.sh dev
   ```

4. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - API Documentation: http://localhost:8000/api/docs/

### Credit Scoring Algorithm

The system uses a sophisticated credit scoring algorithm based on:

1. **Payment History (35%)**: Past loan payment behavior
2. **Loan Count (15%)**: Number of previous loans
3. **Loan Activity (15%)**: Current year loan activity
4. **Loan Volume (20%)**: Total approved amount vs. approved limit
5. **Current Debt (15%)**: Current debt to approved limit ratio

Credit scores range from 0-100, with different approval thresholds:
- **Score > 50**: Approved at requested interest rate
- **Score 30-50**: Approved with higher interest rate (>16%)
- **Score 10-30**: Approved with highest interest rate (>16%)
- **Score < 10**: Rejected
