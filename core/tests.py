import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from .models import Customer, Loan

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_customer_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "age": 30,
        "monthly_income": 50000,
        "phone_number": "1234567890"
    }

@pytest.mark.django_db
class TestCustomerRegistration:
    def test_successful_registration(self, api_client, sample_customer_data):
        url = reverse('customer-register')
        response = api_client.post(url, sample_customer_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'customer_id' in response.data
        assert response.data['name'] == "John Doe"
        assert response.data['monthly_income'] == "50000.00"
        assert response.data['approved_limit'] == "1800000.00"  # 36 * monthly_income
        
        # Verify customer was created in database
        customer = Customer.objects.get(phone_number="1234567890")
        assert customer.first_name == "John"
        assert customer.monthly_salary == 50000

    def test_duplicate_phone_number(self, api_client, sample_customer_data):
        # First registration
        url = reverse('customer-register')
        api_client.post(url, sample_customer_data, format='json')
        
        # Try registering with same phone number
        response = api_client.post(url, sample_customer_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone number already exists" in response.data['phone_number'][0].lower()

    @pytest.mark.parametrize("field,value,error_key", [
        ("age", 17, "age"),  # Too young
        ("age", 121, "age"),  # Too old
        ("monthly_income", -1000, "monthly_income"),  # Negative income
        ("phone_number", "abc", "phone_number"),  # Invalid phone format
        ("first_name", "", "first_name"),  # Empty name
    ])
    def test_invalid_inputs(self, api_client, sample_customer_data, field, value, error_key):
        url = reverse('customer-register')
        data = sample_customer_data.copy()
        data[field] = value
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_key in response.data

@pytest.mark.django_db
class TestLoanEligibility:
    @pytest.fixture
    def registered_customer(self, api_client, sample_customer_data):
        url = reverse('customer-register')
        response = api_client.post(url, sample_customer_data, format='json')
        return response.data['customer_id']

    @pytest.fixture
    def loan_request_data(self, registered_customer):
        return {
            "customer_id": registered_customer,
            "loan_amount": 500000,
            "interest_rate": 12.5,
            "tenure": 24
        }

    def test_successful_eligibility_check(self, api_client, loan_request_data):
        url = reverse('check-loan-eligibility')
        response = api_client.post(url, loan_request_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'approval' in response.data
        assert 'interest_rate' in response.data
        assert 'monthly_installment' in response.data
        assert response.data['customer_id'] == loan_request_data['customer_id']

    def test_nonexistent_customer(self, api_client, loan_request_data):
        url = reverse('check-loan-eligibility')
        data = loan_request_data.copy()
        data['customer_id'] = "00000000-0000-0000-0000-000000000000"
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("field,value,expected_status,error_key", [
        ("loan_amount", -1000, status.HTTP_400_BAD_REQUEST, "loan_amount"),
        ("loan_amount", 0, status.HTTP_400_BAD_REQUEST, "loan_amount"),
        ("interest_rate", -5, status.HTTP_400_BAD_REQUEST, "interest_rate"),
        ("interest_rate", 0, status.HTTP_400_BAD_REQUEST, "interest_rate"),
        ("tenure", 0, status.HTTP_400_BAD_REQUEST, "tenure"),
        ("tenure", 361, status.HTTP_400_BAD_REQUEST, "tenure"),  # More than 30 years
    ])
    def test_invalid_loan_parameters(self, api_client, loan_request_data, field, value, expected_status, error_key):
        url = reverse('check-loan-eligibility')
        data = loan_request_data.copy()
        data[field] = value
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == expected_status
        assert error_key in response.data
        assert response.data[error_key] is not None  # Ensure error message exists

@pytest.mark.django_db
class TestLoanCreation:
    @pytest.fixture
    def registered_customer(self, api_client, sample_customer_data):
        url = reverse('customer-register')
        response = api_client.post(url, sample_customer_data, format='json')
        return response.data['customer_id']

    @pytest.fixture
    def loan_request_data(self, registered_customer):
        return {
            "customer_id": registered_customer,
            "loan_amount": 500000,
            "interest_rate": 12.5,
            "tenure": 24
        }

    def test_successful_loan_creation(self, api_client, loan_request_data):
        url = reverse('create-loan')
        response = api_client.post(url, loan_request_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['loan_approved'] is True
        assert response.data['loan_id'] is not None
        assert 'monthly_installment' in response.data
        
        # Verify loan was created in database
        loan = Loan.objects.get(loan_id=response.data['loan_id'])
        assert loan.loan_amount == Decimal('500000.00')
        assert loan.status == 'APPROVED'

    def test_loan_above_approved_limit(self, api_client, loan_request_data):
        # Try to create a loan for more than 36 times monthly income
        data = loan_request_data.copy()
        data['loan_amount'] = 2000000  # More than approved limit (36 * 50000)
        url = reverse('create-loan')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK  # Changed from 201
        assert response.data['loan_approved'] is False
        assert 'message' in response.data

    def test_loan_with_bad_credit_score(self, api_client, loan_request_data, registered_customer):
        # First create a loan and don't pay EMIs to lower credit score
        url = reverse('create-loan')
        first_loan = api_client.post(url, loan_request_data, format='json')
        
        # Create another loan - should be rejected due to unpaid EMIs
        response = api_client.post(url, loan_request_data, format='json')
        assert response.status_code == status.HTTP_200_OK  # Changed from 201
        assert response.data['loan_approved'] is False
        assert 'message' in response.data

    @pytest.mark.parametrize("field,value,expected_status,error_key", [
        ("customer_id", "00000000-0000-0000-0000-000000000000", status.HTTP_404_NOT_FOUND, "error"),
        ("loan_amount", -1000, status.HTTP_400_BAD_REQUEST, "loan_amount"),
        ("interest_rate", -5, status.HTTP_400_BAD_REQUEST, "interest_rate"),
        ("tenure", 0, status.HTTP_400_BAD_REQUEST, "tenure"),
        ("tenure", 361, status.HTTP_400_BAD_REQUEST, "tenure"),  # More than 30 years
    ])
    def test_invalid_inputs(self, api_client, loan_request_data, field, value, expected_status, error_key):
        url = reverse('create-loan')
        data = loan_request_data.copy()
        data[field] = value
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == expected_status
        # For 404, check error message
        if expected_status == status.HTTP_404_NOT_FOUND:
            assert "customer not found" in response.data[error_key].lower()
        else:
            # For 400, check field-specific validation error
            assert error_key in response.data
