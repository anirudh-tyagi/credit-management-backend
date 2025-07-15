#!/usr/bin/env python
"""
Test runner script that uses SQLite instead of PostgreSQL for testing.
"""
import os
import sys
import django

# Remove .env file database configuration
env_vars_to_remove = [
    'DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT'
]

for var in env_vars_to_remove:
    if var in os.environ:
        del os.environ[var]

# Set Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_approval.test_settings')

# Setup Django
django.setup()

if __name__ == '__main__':
    import pytest
    # Run pytest with the provided arguments
    sys.exit(pytest.main(sys.argv[1:]))
