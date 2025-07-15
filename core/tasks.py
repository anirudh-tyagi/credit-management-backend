import pandas as pd
from celery import shared_task
from datetime import datetime
from django.db import transaction
from .models import Customer, Loan

@shared_task
def example_task():
    """Example task to demonstrate Celery integration."""
    return "Task completed successfully!"

@shared_task
def import_excel_data(customer_file_path, loan_file_path):
    """
    Import customer and loan data from Excel files.
    """
    try:
        # Read customer data
        df_customers = pd.read_excel(customer_file_path)
        df_loans = pd.read_excel(loan_file_path)
        
        # Process customers first
        with transaction.atomic():
            for _, row in df_customers.iterrows():
                customer = Customer(
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    phone_number=str(row['phone_number']),  # Convert to string in case it's numeric
                    monthly_salary=float(row['monthly_salary']),
                    age=int(row['age'])
                )
                customer.save()  # This will auto-calculate approved_limit
        
        # Process loans
        with transaction.atomic():
            for _, row in df_loans.iterrows():
                # Get customer by phone number (assuming it's unique)
                try:
                    customer = Customer.objects.get(phone_number=str(row['customer_phone_number']))
                    
                    # Parse dates
                    start_date = pd.to_datetime(row['start_date']).date()
                    # Calculate end date based on tenure if not provided
                    if 'end_date' in row:
                        end_date = pd.to_datetime(row['end_date']).date()
                    else:
                        end_date = pd.to_datetime(row['start_date']).date() + pd.DateOffset(months=int(row['tenure']))
                    
                    loan = Loan(
                        customer=customer,
                        loan_amount=float(row['loan_amount']),
                        tenure=int(row['tenure']),
                        interest_rate=float(row['interest_rate']),
                        start_date=start_date,
                        end_date=end_date,
                        emis_paid_on_time=int(row.get('emis_paid_on_time', 0)),
                        status=row.get('status', 'APPROVED')
                    )
                    loan.save()  # This will auto-calculate monthly_installment
                    
                except Customer.DoesNotExist:
                    print(f"Customer with phone number {row['customer_phone_number']} not found")
                except Exception as e:
                    print(f"Error processing loan: {str(e)}")
        
        return "Data import completed successfully"
    
    except Exception as e:
        return f"Error importing data: {str(e)}"
