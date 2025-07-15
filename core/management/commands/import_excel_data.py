from django.core.management.base import BaseCommand
from django.conf import settings
import os
from core.tasks import import_excel_data

class Command(BaseCommand):
    help = 'Import customer and loan data from Excel files using Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-file',
            default='customer_data.xlsx',
            help='Path to the customer data Excel file'
        )
        parser.add_argument(
            '--loan-file',
            default='loan_data.xlsx',
            help='Path to the loan data Excel file'
        )

    def handle(self, *args, **options):
        customer_file = options['customer_file']
        loan_file = options['loan_file']

        # Check if files exist
        if not os.path.exists(customer_file):
            self.stderr.write(self.style.ERROR(f'Customer file not found: {customer_file}'))
            return
        if not os.path.exists(loan_file):
            self.stderr.write(self.style.ERROR(f'Loan file not found: {loan_file}'))
            return

        # Get absolute paths
        customer_file = os.path.abspath(customer_file)
        loan_file = os.path.abspath(loan_file)

        self.stdout.write(self.style.SUCCESS('Starting data import task...'))
        
        # Launch Celery task
        task = import_excel_data.delay(customer_file, loan_file)
        
        self.stdout.write(self.style.SUCCESS(
            f'Data import task launched successfully. Task ID: {task.id}\n'
            f'Use "celery -A credit_approval worker --loglevel=info" to start the worker and process the task.'
        ))
