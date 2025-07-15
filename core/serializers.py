from rest_framework import serializers
from decimal import Decimal
from .models import Customer, Loan

class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=18, max_value=120)
    monthly_income = serializers.IntegerField(min_value=0)
    phone_number = serializers.CharField(max_length=15)

    def create(self, validated_data):
        # Convert monthly_income to monthly_salary and calculate approved_limit
        monthly_salary = validated_data.pop('monthly_income')
        # Round to nearest lakh (100,000)
        approved_limit = round(36 * monthly_salary, -5)
        
        return Customer.objects.create(
            monthly_salary=monthly_salary,
            approved_limit=approved_limit,
            **validated_data
        )

    def validate_phone_number(self, value):
        # Remove any spaces or special characters
        cleaned_number = ''.join(filter(str.isdigit, str(value)))
        
        # Check if phone number has digits
        if not cleaned_number:
            raise serializers.ValidationError("Phone number must contain at least one digit.")
        
        # Check if phone number already exists
        if Customer.objects.filter(phone_number=cleaned_number).exists():
            raise serializers.ValidationError("A customer with this phone number already exists.")
        return cleaned_number


class CustomerResponseSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    monthly_income = serializers.DecimalField(source='monthly_salary', max_digits=12, decimal_places=2)
    
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class LoanEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    tenure = serializers.IntegerField(min_value=1, max_value=360)  # Max 30 years

class LoanEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)

class LoanCreationRequestSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    tenure = serializers.IntegerField(min_value=1, max_value=360)  # Max 30 years

class LoanCreationResponseSerializer(serializers.Serializer):
    loan_id = serializers.UUIDField(allow_null=True)  # Will be null if loan is not approved
    customer_id = serializers.UUIDField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField(allow_blank=True, required=False)  # Required only if loan is not approved
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)  # Will be null if loan is not approved

class LoanCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'age', 'phone_number']


class LoanDetailsSerializer(serializers.ModelSerializer):
    customer = LoanCustomerSerializer(read_only=True)
    
    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'tenure', 'monthly_installment', 'customer']


class CustomerLoanListSerializer(serializers.ModelSerializer):
    repayments_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left']
    
    def get_repayments_left(self, obj):
        return obj.tenure - obj.emis_paid_on_time
