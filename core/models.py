from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Customer(models.Model):
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    approved_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    current_debt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(120)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

    def save(self, *args, **kwargs):
        # If this is a new customer, calculate approved limit
        if not self.approved_limit:
            # Approved limit is typically 36 times of monthly salary
            self.approved_limit = self.monthly_salary * 36
        super().save(*args, **kwargs)


class Loan(models.Model):
    LOAN_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CLOSED', 'Closed'),
    ]

    loan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tenure = models.PositiveIntegerField(
        help_text="Loan tenure in months",
        validators=[MinValueValidator(1), MaxValueValidator(360)]  # Max 30 years
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Annual interest rate in percentage"
    )
    monthly_installment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    emis_paid_on_time = models.PositiveIntegerField(
        default=0,
        help_text="Number of EMIs paid on time"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=LOAN_STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan {self.loan_id} - {self.customer.first_name} {self.customer.last_name}"

    def save(self, *args, **kwargs):
        if not self.monthly_installment:
            # Calculate monthly installment using compound interest formula
            # PMT = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
            # where P = Principal, r = monthly interest rate, n = number of months
            principal = float(self.loan_amount)
            annual_rate = float(self.interest_rate)
            monthly_rate = annual_rate / (12 * 100)  # Convert annual rate to monthly decimal
            n = self.tenure

            if monthly_rate > 0:
                monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
            else:
                monthly_payment = principal / n

            self.monthly_installment = round(monthly_payment, 2)

        super().save(*args, **kwargs)
