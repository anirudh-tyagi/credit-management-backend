from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import IntegrityError, transaction, models
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from .models import Customer, Loan
from .serializers import (
    CustomerRegistrationSerializer, CustomerResponseSerializer,
    LoanEligibilityRequestSerializer, LoanEligibilityResponseSerializer,
    LoanCreationRequestSerializer, LoanCreationResponseSerializer,
    LoanDetailsSerializer, CustomerLoanListSerializer
)


class BaseLoanEligibilityMixin:
    def calculate_credit_score(self, customer, current_year_start):
        """
        Calculate credit score based on customer's loan history.
        Returns a score between 0 and 100.
        """
        loans = customer.loans.all()
        
        if not loans:
            # No loan history - moderate score
            return 50
            
        # Get loan statistics
        total_loans = loans.count()
        total_emis = sum(loan.tenure for loan in loans)  # Total EMIs across all loans
        emis_paid_on_time = sum(loan.emis_paid_on_time for loan in loans)
        current_year_loans = loans.filter(start_date__gte=current_year_start).count()
        total_approved_amount = loans.aggregate(total=Sum('loan_amount'))['total'] or 0
        current_debt = customer.current_debt

        # Check if current debt exceeds approved limit - Immediate disqualification
        if current_debt > customer.approved_limit:
            return 0

        # 1. Past Loans paid on time (35%)
        if total_emis > 0:
            payment_score = (emis_paid_on_time / total_emis) * 35
        else:
            payment_score = 17.5  # Neutral score for no history

        # 2. Number of loans taken in past (15%)
        # More loans means more credit history, but not too many
        loan_count_score = min(total_loans * 5, 15)

        # 3. Loan activity in current year (15%)
        # Moderate activity is good, too many loans in current year is risky
        current_year_score = 15 * (1 - min(current_year_loans / 4, 1))  # Penalize if more than 4 loans in current year

        # 4. Loan approved volume vs salary (35%)
        # Check if total approved amount is reasonable compared to annual salary
        annual_salary = float(customer.monthly_salary) * 12
        loan_volume_ratio = float(total_approved_amount) / annual_salary if annual_salary > 0 else float('inf')
        
        if loan_volume_ratio <= 3:  # Up to 3 years of salary is ideal
            volume_score = 35
        elif loan_volume_ratio <= 5:  # Up to 5 years of salary is okay
            volume_score = 25
        elif loan_volume_ratio <= 8:  # Up to 8 years of salary is risky
            volume_score = 15
        else:  # More than 8 years of salary is very risky
            volume_score = 5

        # Combine all scores
        credit_score = payment_score + loan_count_score + current_year_score + volume_score
        
        # Final adjustments
        credit_score = min(max(credit_score, 0), 100)  # Ensure score is between 0 and 100
        
        return credit_score

    def calculate_monthly_installment(self, principal, annual_rate, tenure):
        """Calculate EMI using compound interest formula"""
        monthly_rate = float(annual_rate) / (12 * 100)
        if monthly_rate > 0:
            emi = float(principal) * (monthly_rate * (1 + monthly_rate) ** tenure) / ((1 + monthly_rate) ** tenure - 1)
        else:
            emi = float(principal) / tenure
        return round(emi, 2)

    def get_corrected_interest_rate(self, credit_score, requested_rate):
        """
        Get minimum allowed interest rate based on credit score slabs:
        - credit_score > 50: any rate
        - 30 < credit_score <= 50: min 12%
        - 10 < credit_score <= 30: min 16%
        - credit_score <= 10: no loan
        """
        requested_rate = float(requested_rate)
        
        if credit_score <= 10:
            return None  # Loan will be denied
        elif credit_score <= 30:
            return max(16.0, requested_rate)  # Minimum 16% for this slab
        elif credit_score <= 50:
            return max(12.0, requested_rate)  # Minimum 12% for this slab
        return requested_rate  # Any rate is acceptable for credit_score > 50

    def check_loan_eligibility(self, customer, loan_amount, interest_rate, tenure):
        """
        Check loan eligibility based on credit score and EMI constraints.
        Returns a tuple of (is_eligible, message, corrected_rate, monthly_installment)
        
        Credit score rules:
        - credit_score > 50: approve at any rate
        - 30 < credit_score <= 50: approve if rate >= 12%
        - 10 < credit_score <= 30: approve if rate >= 16%
        - credit_score <= 10: no approval
        """
        current_year_start = timezone.now().replace(month=1, day=1)
        credit_score = self.calculate_credit_score(customer, current_year_start)
        interest_rate = float(interest_rate)
        corrected_rate = None
        
        # First check: Credit score based approval
        if credit_score <= 10:
            return False, "Low credit score (≤ 10), loan cannot be approved", None, None
        
        # Determine corrected interest rate based on credit score bands
        if 10 < credit_score <= 30 and interest_rate < 16:
            corrected_rate = 16.0  # Minimum rate for this band
        elif 30 < credit_score <= 50 and interest_rate < 12:
            corrected_rate = 12.0  # Minimum rate for this band
        
        # Use corrected rate if needed, otherwise use original rate
        final_rate = corrected_rate if corrected_rate else interest_rate
        
        # Calculate monthly installment using final rate
        monthly_installment = self.calculate_monthly_installment(
            loan_amount,
            final_rate,
            tenure
        )
        
        # Check if total EMIs exceed 50% of monthly salary
        current_emis = customer.loans.filter(
            status='APPROVED'
        ).aggregate(
            total_emi=Sum('monthly_installment')
        )['total_emi'] or 0
        
        total_emi_with_new_loan = float(current_emis) + monthly_installment
        if total_emi_with_new_loan > (float(customer.monthly_salary) * 0.5):
            return False, "Total EMIs would exceed 50% of monthly salary", corrected_rate, monthly_installment
        
        # Final approval decision based on credit score bands and interest rates
        if credit_score > 50:
            # Approve at any interest rate
            return True, None, corrected_rate, monthly_installment
        elif 30 < credit_score <= 50:
            # Must have at least 12% interest rate
            if interest_rate < 12:
                return False, "Interest rate must be at least 12% for credit score between 31-50", 12.0, monthly_installment
            return True, None, corrected_rate, monthly_installment
        elif 10 < credit_score <= 30:
            # Must have at least 16% interest rate
            if interest_rate < 16:
                return False, "Interest rate must be at least 16% for credit score between 11-30", 16.0, monthly_installment
            return True, None, corrected_rate, monthly_installment
            
        return False, "Invalid credit score scenario", None, None  # Fallback case


class CustomerRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = CustomerRegistrationSerializer(data=request.data)
        
        try:
            if serializer.is_valid():
                customer = serializer.save()
                response_serializer = CustomerResponseSerializer(customer)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError:
            return Response(
                {"error": "A customer with this phone number already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoanEligibilityView(BaseLoanEligibilityMixin, APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Validate request data
        request_serializer = LoanEligibilityRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = request_serializer.validated_data
        
        try:
            # Get customer
            customer = Customer.objects.get(customer_id=data['customer_id'])
            
            # Check eligibility
            is_eligible, message, corrected_rate, monthly_installment = self.check_loan_eligibility(
                customer,
                data['loan_amount'],
                data['interest_rate'],
                data['tenure']
            )
            
            response_data = {
                'customer_id': customer.customer_id,
                'approval': is_eligible,
                'interest_rate': data['interest_rate'],
                'corrected_interest_rate': corrected_rate if corrected_rate != float(data['interest_rate']) else None,
                'tenure': data['tenure'],
                'monthly_installment': monthly_installment or 0
            }
            
            response_serializer = LoanEligibilityResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class LoanCreationView(BaseLoanEligibilityMixin, APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Validate request data
        request_serializer = LoanCreationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = request_serializer.validated_data
        
        try:
            # Get customer
            customer = Customer.objects.get(customer_id=data['customer_id'])
            
            # Check eligibility
            is_eligible, message, corrected_rate, monthly_installment = self.check_loan_eligibility(
                customer,
                data['loan_amount'],
                data['interest_rate'],
                data['tenure']
            )
            
            # Prepare base response data
            response_data = {
                'customer_id': customer.customer_id,
                'loan_id': None,
                'loan_approved': False,
                'monthly_installment': None,
                'message': ''
            }
            
            if not is_eligible:
                response_data['message'] = message
                return Response(response_data)
            
            # Create the loan
            with transaction.atomic():
                # Create loan
                loan = Loan.objects.create(
                    customer=customer,
                    loan_amount=data['loan_amount'],
                    interest_rate=corrected_rate or data['interest_rate'],
                    tenure=data['tenure'],
                    monthly_installment=monthly_installment,
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timezone.timedelta(days=30*data['tenure']),
                    status='APPROVED'
                )
                
                # Update customer's current debt
                customer.current_debt = models.F('current_debt') + data['loan_amount']
                customer.save()
            
            # Update response for approved loan
            response_data.update({
                'loan_id': loan.loan_id,
                'loan_approved': True,
                'monthly_installment': monthly_installment
            })
            
            response_serializer = LoanCreationResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class LoanDetailsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, loan_id, *args, **kwargs):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
            serializer = LoanDetailsSerializer(loan)
            return Response(serializer.data)
        except Loan.DoesNotExist:
            return Response(
                {'error': 'Loan not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CustomerLoanListView(APIView):
    """
    API endpoint to list all active loans for a specific customer.
    
    Returns a list of loans with their details including:
    - loan_id
    - loan_amount
    - interest_rate
    - monthly_installment
    - repayments_left (tenure - emis_paid_on_time)
    """
    permission_classes = [AllowAny]
    
    def get(self, request, customer_id):
        """
        Get all active loans for a customer.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            200: List of active loans
            404: If customer not found
            400: If customer_id is invalid
        """
        try:
            # Verify customer exists
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid customer ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Customer.DoesNotExist:
                return Response(
                    {"error": "Customer not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all active loans for the customer
            loans = Loan.objects.filter(
                customer=customer,
                status='APPROVED'
            ).order_by('-created_at')
            
            # Even if no loans found, return empty list with 200 status
            serializer = CustomerLoanListSerializer(loans, many=True)
            return Response(
                {
                    "customer_id": str(customer_id),
                    "total_loans": len(serializer.data),
                    "loans": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Log the unexpected error here
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
