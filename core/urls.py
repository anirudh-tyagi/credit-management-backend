from django.urls import path
from .views import (
    CustomerRegistrationView, LoanEligibilityView,
    LoanCreationView, LoanDetailsView, CustomerLoanListView
)

urlpatterns = [
    path('register/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('check-eligibility/', LoanEligibilityView.as_view(), name='check-loan-eligibility'),
    path('create-loan/', LoanCreationView.as_view(), name='create-loan'),
    path('view-loan/<uuid:loan_id>/', LoanDetailsView.as_view(), name='view-loan'),
    path('view-loans/<uuid:customer_id>/', CustomerLoanListView.as_view(), name='view-customer-loans'),
]
