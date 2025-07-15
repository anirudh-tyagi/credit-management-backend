# API Testing Guide

## Quick Start

1. **Start the development server:**
   ```bash
   ./docker.sh dev
   ```

2. **Wait for containers to start (about 20 seconds)**

3. **Test all endpoints using the examples below**

##  Complete API Testing Examples

### 1. Customer Registration

**Endpoint:** `POST /api/register/`

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Johnson", 
    "phone_number": "7778889999",
    "monthly_income": 60000,
    "age": 28
  }'
```

**Expected Response:**
```json
{
  "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
  "name": "Alice Johnson",
  "age": 28,
  "monthly_income": "60000.00",
  "approved_limit": "2200000.00",
  "phone_number": "7778889999"
}
```

### 2. Check Loan Eligibility

**Endpoint:** `POST /api/check-eligibility/`

```bash
curl -X POST http://localhost:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
    "loan_amount": 150000,
    "interest_rate": 14.0,
    "tenure": 36
  }'
```

**Expected Response:**
```json
{
  "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
  "approval": true,
  "interest_rate": "14.00",
  "corrected_interest_rate": null,
  "tenure": 36,
  "monthly_installment": "5126.64"
}
```

### 3. Create Loan

**Endpoint:** `POST /api/create-loan/`

```bash
curl -X POST http://localhost:8000/api/create-loan/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
    "loan_amount": 150000,
    "interest_rate": 14.0,
    "tenure": 36
  }'
```

**Expected Response:**
```json
{
  "loan_id": "0140bcd5-b987-4090-a297-a27bdda6ed33",
  "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
  "loan_approved": true,
  "message": "",
  "monthly_installment": "5126.64"
}
```

### 4. View Loan Details

**Endpoint:** `GET /api/view-loan/{loan_id}/`

```bash
curl -X GET http://localhost:8000/api/view-loan/0140bcd5-b987-4090-a297-a27bdda6ed33/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "loan_id": "0140bcd5-b987-4090-a297-a27bdda6ed33",
  "loan_amount": "150000.00",
  "interest_rate": "14.00",
  "tenure": 36,
  "monthly_installment": "5126.64",
  "customer": {
    "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
    "first_name": "Alice",
    "last_name": "Johnson",
    "age": 28,
    "phone_number": "7778889999"
  }
}
```

### 5. View Customer Loans

**Endpoint:** `GET /api/view-loans/{customer_id}/`

```bash
curl -X GET http://localhost:8000/api/view-loans/c887f3c0-17d5-44e8-800f-b8f19a2a0d10/ \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "customer_id": "c887f3c0-17d5-44e8-800f-b8f19a2a0d10",
  "total_loans": 1,
  "loans": [
    {
      "loan_id": "0140bcd5-b987-4090-a297-a27bdda6ed33",
      "loan_amount": "150000.00",
      "interest_rate": "14.00",
      "monthly_installment": "5126.64",
      "repayments_left": 36
    }
  ]
}
```

## 🌐 Browser Testing

You can also test the API directly in your browser:

1. **Open:** http://localhost:8000/api/register/
2. **You'll see the Django REST Framework browsable API**
3. **Use the HTML form to test POST requests**
4. **Navigate to other endpoints using the URL bar**

## 📊 Using Tools

### Postman
1. Import the endpoints as a collection
2. Set base URL to `http://localhost:8000`
3. Use the JSON payloads from examples above

### Insomnia
1. Create a new request collection
2. Set up requests with the examples above
3. Save customer_id and loan_id for subsequent tests

### HTTPie
```bash
# Customer Registration
http POST localhost:8000/api/register/ \
  first_name=Alice \
  last_name=Johnson \
  phone_number=7778889999 \
  monthly_income:=60000 \
  age:=28

# Loan Eligibility
http POST localhost:8000/api/check-eligibility/ \
  customer_id=c887f3c0-17d5-44e8-800f-b8f19a2a0d10 \
  loan_amount:=150000 \
  interest_rate:=14.0 \
  tenure:=36
```

## 🔧 Testing Script

Save this as `test_api.sh` and run it:

```bash
#!/bin/bash
echo "=== Credit Management API Testing ==="
echo ""

# Test customer registration
echo "1. Testing Customer Registration..."
CUSTOMER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User", 
    "phone_number": "1111111111",
    "monthly_income": 50000,
    "age": 25
  }')

echo "Response: $CUSTOMER_RESPONSE"
CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | grep -o '"customer_id":"[^"]*' | cut -d'"' -f4)
echo "Customer ID: $CUSTOMER_ID"
echo ""

# Test loan eligibility
echo "2. Testing Loan Eligibility..."
ELIGIBILITY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"$CUSTOMER_ID\",
    \"loan_amount\": 100000,
    \"interest_rate\": 12.5,
    \"tenure\": 24
  }")

echo "Response: $ELIGIBILITY_RESPONSE"
echo ""

# Test loan creation
echo "3. Testing Loan Creation..."
LOAN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/create-loan/ \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"$CUSTOMER_ID\",
    \"loan_amount\": 100000,
    \"interest_rate\": 12.5,
    \"tenure\": 24
  }")

echo "Response: $LOAN_RESPONSE"
LOAN_ID=$(echo "$LOAN_RESPONSE" | grep -o '"loan_id":"[^"]*' | cut -d'"' -f4)
echo "Loan ID: $LOAN_ID"
echo ""

# Test loan details
echo "4. Testing Loan Details..."
curl -s -X GET "http://localhost:8000/api/view-loan/$LOAN_ID/" \
  -H "Content-Type: application/json"
echo ""
echo ""

# Test customer loans
echo "5. Testing Customer Loans..."
curl -s -X GET "http://localhost:8000/api/view-loans/$CUSTOMER_ID/" \
  -H "Content-Type: application/json"
echo ""
echo ""

echo "=== All tests completed! ==="
```

##  Common Issues

### 1. Authentication Error
If you get "Authentication credentials were not provided":
- Check that `AllowAny` permission is set in views.py
- Restart the Docker containers

### 2. Database Connection Error
If you get database connection errors:
- Wait for containers to fully start (20-30 seconds)
- Check `./docker.sh logs` for errors

### 3. Port Already in Use
If port 8000 is busy:
- Stop other services: `./docker.sh down`
- Kill processes: `lsof -ti:8000 | xargs kill`

### 4. Invalid JSON
Common JSON format issues:
- Use double quotes for strings
- Ensure proper escaping
- Check for trailing commas

## 🧪 Advanced Testing

### Load Testing with Apache Bench
```bash
# Test customer registration endpoint
ab -n 100 -c 10 -p customer_data.json -T application/json \
  http://localhost:8000/api/register/
```

### Unit Testing
```bash
# Run the full test suite
./docker.sh test

# Run specific test
docker-compose exec web python -m pytest core/tests.py::test_customer_registration -v
```

##  Monitoring

### View Logs
```bash
# View all logs
./docker.sh logs

# View specific service logs
docker-compose logs web
docker-compose logs celery
```

### Performance Metrics
```bash
# Monitor container stats
docker stats

# Check database connections
docker-compose exec db psql -U user -d credit_db -c "SELECT * FROM pg_stat_activity;"
```

##  Automation

### CI/CD Pipeline Testing
```yaml
# .github/workflows/test.yml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: ./docker.sh dev
      - name: Run API tests
        run: ./test_api.sh
```

### Integration Testing
```bash
# Test all endpoints in sequence
./docker.sh test-integration

# Test specific workflow
./docker.sh test-workflow customer-loan-flow
```

This guide provides comprehensive testing instructions for all API endpoints in your Django Credit Approval System!
