# Expense Tracker

A Django + PostgreSQL personal expense tracking application for managing income, expenses, categories, budgets, reports, and analytics.

## Technology

- Python
- Django
- PostgreSQL
- HTML / CSS / JavaScript
- ReportLab for PDF reports
- OpenPyXL for Excel reports

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   `pip install -r requirements.txt`

3. Copy `.env.example` to `.env`.
4. Set `DJANGO_SECRET_KEY` to a new random secret key.
5. Set `DB_PASSWORD` to your PostgreSQL password.
6. Make sure the `expense_tracker` PostgreSQL database exists.
7. Run migrations:

   `python manage.py migrate`

8. Create an admin user if needed:

   `python manage.py createsuperuser`

9. Start the development server:

   `python manage.py runserver`

Never commit `.env` or other files containing passwords or secret keys.
