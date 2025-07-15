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

5. **Test the API endpoints** (see [API Testing Guide](API_TESTING_GUIDE.md))
   ```bash
   # Quick test - Customer Registration
   curl -X POST http://localhost:8000/api/register/ \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "phone_number": "1234567890",
       "monthly_salary": 50000,
       "age": 28
     }'
   ```

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start the server**
   ```bash
   python manage.py runserver
   ```

## 🐳 Docker Commands

Our project includes a convenient `docker.sh` script for common operations:

```bash
# Build and start development environment
./docker.sh dev

# Build and start production environment
./docker.sh prod

# Run tests with pytest
./docker.sh test

# View container logs
./docker.sh logs
./docker.sh logs web  # specific service

# Access Django shell
./docker.sh shell

# Stop all containers
./docker.sh down

# Rebuild containers and remove cache
./docker.sh rebuild

# Run migrations
./docker.sh migrate

# Create superuser
./docker.sh createsuperuser
```

##  API Documentation

### Base URL
- Development: `http://localhost:8000/api/`
- Production: `https://your-domain.com/api/`

### Authentication
Currently, the API endpoints are publicly accessible. For production, consider implementing token-based authentication.

---

### 1. Customer Registration

**POST** `/api/register/`

Register a new customer in the system.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "1234567890",
    "monthly_salary": 50000,
    "age": 28
}
```

**Response (201 Created):**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "age": 28,
    "phone_number": "1234567890",
    "monthly_salary": "50000.00",
    "approved_limit": "1800000.00"
}
```

**Error Response (400 Bad Request):**
```json
{
    "phone_number": ["Customer with this phone number already exists."]
}
```

---

### 2. Check Loan Eligibility

**POST** `/api/check-eligibility/`

Check if a customer is eligible for a loan and get personalized terms.

**Request Body:**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "loan_amount": 100000,
    "interest_rate": 12.5,
    "tenure": 24
}
```

**Response (200 OK):**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "approval": true,
    "interest_rate": 12.5,
    "corrected_interest_rate": 12.5,
    "tenure": 24,
    "monthly_installment": "4707.35"
}
```

**Rejected Loan Response:**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "approval": false,
    "interest_rate": 12.5,
    "corrected_interest_rate": null,
    "tenure": 24,
    "monthly_installment": "0.00"
}
```

---

### 3. Create Loan

**POST** `/api/create-loan/`

Create a new loan for an eligible customer.

**Request Body:**
```json
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "loan_amount": 100000,
    "interest_rate": 12.5,
    "tenure": 24
}
```

**Response (201 Created - Approved):**
```json
{
    "loan_id": "456e7890-e89b-12d3-a456-426614174000",
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": "4707.35"
}
```

**Response (200 OK - Rejected):**
```json
{
    "loan_id": null,
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "loan_approved": false,
    "message": "Loan rejected due to low credit score",
    "monthly_installment": "0.00"
}
```

---

### 4. View Loan Details

**GET** `/api/view-loan/{loan_id}/`

Get details of a specific loan.

**Response (200 OK):**
```json
{
    "loan_id": "456e7890-e89b-12d3-a456-426614174000",
    "customer": {
        "customer_id": "123e4567-e89b-12d3-a456-426614174000",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "1234567890",
        "age": 28
    },
    "loan_amount": "100000.00",
    "interest_rate": "12.50",
    "monthly_installment": "4707.35",
    "tenure": 24,
    "status": "APPROVED",
    "start_date": "2024-01-01",
    "end_date": "2025-12-01",
    "emis_paid_on_time": 0
}
```

---

### 5. View Customer Loans

**GET** `/api/view-loans/{customer_id}/`

Get all loans for a specific customer.

**Response (200 OK):**
```json
[
    {
        "loan_id": "456e7890-e89b-12d3-a456-426614174000",
        "loan_amount": "100000.00",
        "interest_rate": "12.50",
        "monthly_installment": "4707.35",
        "tenure": 24,
        "status": "APPROVED",
        "start_date": "2024-01-01",
        "end_date": "2025-12-01",
        "emis_paid_on_time": 0
    }
]
```

## 🧪 Testing

For detailed information about API testing, test cases, and examples, please refer to our comprehensive [API Testing Guide](API_TESTING_GUIDE.md).

### Quick Start with Tests

```bash
# Run tests in Docker (Recommended)
./docker.sh test

# Run tests locally
python -m pytest

# Run tests with coverage report
python -m pytest --cov=core --cov-report=html
```

## 📁 Project Structure

```
credit-management-backend/
├── core/                         # Main application
│   ├── models.py                # Customer and Loan models
│   ├── views.py                 # API views
│   ├── serializers.py           # DRF serializers
│   ├── tests.py                # Test suite
│   └── urls.py                 # URL routing
├── credit_approval/             # Django project settings
│   ├── settings.py             # Main settings
│   ├── test_settings.py        # Test-specific settings
│   ├── celery.py              # Celery configuration
│   └── urls.py                # Root URL config
├── docker-compose.dev.yml      # Development Docker setup
├── docker-compose.prod.yml     # Production Docker setup
├── docker-compose.yml          # Base Docker compose config
├── Dockerfile                  # Development Dockerfile
├── Dockerfile.prod            # Production Dockerfile
├── entrypoint.sh             # Container initialization
├── docker.sh                 # Docker management script
├── nginx.conf                # Nginx configuration
├── requirements.txt          # Python dependencies
├── pytest.ini               # Pytest configuration
├── .env.example            # Environment variables template
├── API_TESTING_GUIDE.md    # API testing documentation
├── DOCKER_README.md        # Docker setup guide
├── TEST_FIXES.md          # Known test issues and fixes
└── README.md              # This file
```

##  Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Configuration
DEBUG=1  # Set to 0 for production
SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=credit_db
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

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
