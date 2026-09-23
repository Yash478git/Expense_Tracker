"""
Seed a realistic regular-user account for testing Expense Tracker.

Run from the project root with:
    python seed_super_test_user.py

This script does NOT create an admin account.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
import random
import sys

# Make the Django project importable when this file is run from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

import django

django.setup()

from django.contrib.auth import get_user_model
from tracker.models import (
    Budget,
    Category,
    RecurringTransaction,
    Report,
    Transaction,
    UserProfile,
)


User = get_user_model()

random.seed(20260923)

DEMO_EMAIL = "supertest@example.com"
DEMO_PASSWORD = "Demo@12345"

TODAY = date.today()
START_DATE = date(TODAY.year - 1, 1, 1)


def get_or_create_category(name, category_type, icon=""):
    category, _ = Category.objects.get_or_create(
        name=name,
        type=category_type,
        defaults={
            "icon": icon,
            "is_active": True,
        },
    )

    if not category.is_active:
        category.is_active = True
        category.save(update_fields=["is_active"])

    return category


def month_range(start, end):
    current = date(start.year, start.month, 1)

    while current <= end:
        yield current

        if current.month == 12:
            current = date(
                current.year + 1,
                1,
                1,
            )
        else:
            current = date(
                current.year,
                current.month + 1,
                1,
            )


def safe_date(year, month, day):
    if month == 12:
        next_month = date(
            year + 1,
            1,
            1,
        )
    else:
        next_month = date(
            year,
            month + 1,
            1,
        )

    last_day = (
        next_month
        - __import__("datetime").timedelta(days=1)
    ).day

    return date(
        year,
        month,
        min(day, last_day),
    )


def create_transaction(
    user,
    category,
    amount,
    transaction_type,
    transaction_date,
    payment_method,
    description,
):
    Transaction.objects.create(
        user=user,
        category=category,
        amount=Decimal(str(amount)),
        type=transaction_type,
        date=transaction_date,
        payment_method=payment_method,
        description=description,
    )


# ---------------------------------------------------------------------
# 1. Regular user account
# ---------------------------------------------------------------------

user, created = User.objects.get_or_create(
    username=DEMO_EMAIL,
    defaults={
        "email": DEMO_EMAIL,
        "first_name": "Demo",
        "last_name": "Tester",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
)

user.email = DEMO_EMAIL
user.first_name = "Demo"
user.last_name = "Tester"
user.is_staff = False
user.is_superuser = False
user.is_active = True
user.set_password(DEMO_PASSWORD)
user.save()

UserProfile.objects.update_or_create(
    user=user,
    defaults={
        "phone": "9876543210",
    },
)


# ---------------------------------------------------------------------
# 2. Categories
# ---------------------------------------------------------------------

categories = {
    "Food": get_or_create_category("Food", "expense", "🍔"),
    "Transport": get_or_create_category("Transport", "expense", "🚗"),
    "Shopping": get_or_create_category("Shopping", "expense", "🛍️"),
    "Bills": get_or_create_category("Bills", "expense", "💡"),
    "Entertainment": get_or_create_category(
        "Entertainment",
        "expense",
        "🎬",
    ),
    "Health": get_or_create_category("Health", "expense", "💊"),
    "Education": get_or_create_category(
        "Education",
        "expense",
        "📚",
    ),
    "Other": get_or_create_category("Other", "expense", "📦"),
    "Salary": get_or_create_category("Salary", "income", "💼"),
    "Freelance": get_or_create_category(
        "Freelance",
        "income",
        "💻",
    ),
    "Business": get_or_create_category(
        "Business",
        "income",
        "🏢",
    ),
    "Investment": get_or_create_category(
        "Investment",
        "income",
        "📈",
    ),
    "Gift": get_or_create_category("Gift", "income", "🎁"),
    "Other Income": get_or_create_category(
        "Other Income",
        "income",
        "💰",
    ),
}


# ---------------------------------------------------------------------
# 3. Remove only previously seeded demo-user data
# ---------------------------------------------------------------------

Report.objects.filter(user=user).delete()
Budget.objects.filter(user=user).delete()
RecurringTransaction.objects.filter(user=user).delete()
Transaction.objects.filter(user=user).delete()


# ---------------------------------------------------------------------
# 4. Realistic transaction history
# ---------------------------------------------------------------------

payment_methods = [
    "cash",
    "upi",
    "card",
]

expense_templates = [
    (
        "Food",
        [250, 320, 180, 450, 550, 700],
        "Food / dining",
    ),
    (
        "Transport",
        [80, 120, 150, 200, 300, 450],
        "Travel / fuel",
    ),
    (
        "Shopping",
        [500, 900, 1500, 2200, 3500],
        "Shopping",
    ),
    (
        "Bills",
        [900, 1200, 1800, 2400, 3200],
        "Monthly bills",
    ),
    (
        "Entertainment",
        [250, 400, 650, 1000, 1500],
        "Entertainment",
    ),
    (
        "Health",
        [300, 500, 850, 1200, 2500],
        "Health expense",
    ),
    (
        "Education",
        [500, 800, 1200, 2000, 4000],
        "Education",
    ),
    (
        "Other",
        [150, 300, 600, 900, 1800],
        "Miscellaneous",
    ),
]

for month_start in month_range(
    START_DATE,
    TODAY,
):
    year = month_start.year
    month = month_start.month

    # Monthly salary.
    salary_day = min(1, 28)
    create_transaction(
        user,
        categories["Salary"],
        62000 + ((month + year) % 5) * 1000,
        "income",
        safe_date(year, month, salary_day),
        "upi",
        "Monthly salary",
    )

    # Regular monthly expenses.
    for category_name, amounts, description in expense_templates:
        occurrences = random.choice([1, 1, 1, 2])

        for occurrence in range(occurrences):
            day = random.choice(
                [3, 5, 8, 11, 15, 18, 21, 24, 27]
            )

            create_transaction(
                user,
                categories[category_name],
                random.choice(amounts),
                "expense",
                safe_date(year, month, day),
                random.choice(payment_methods),
                description,
            )

    # Occasional freelance income.
    if month % 2 == 0:
        create_transaction(
            user,
            categories["Freelance"],
            random.choice(
                [3500, 5000, 7500, 9000]
            ),
            "income",
            safe_date(year, month, 15),
            "upi",
            "Freelance project",
        )

    # Occasional business income.
    if month in [3, 6, 9, 12]:
        create_transaction(
            user,
            categories["Business"],
            random.choice(
                [8000, 12000, 15000, 22000]
            ),
            "income",
            safe_date(year, month, 20),
            "upi",
            "Business income",
        )


# Yearly-style transactions.
for year in range(
    START_DATE.year,
    TODAY.year + 1,
):
    if year == TODAY.year and TODAY < date(year, 7, 1):
        continue

    create_transaction(
        user,
        categories["Investment"],
        random.choice(
            [12000, 15000, 18000, 25000]
        ),
        "income",
        safe_date(year, 4, 10),
        "upi",
        "Annual investment return",
    )

    create_transaction(
        user,
        categories["Bills"],
        random.choice(
            [4500, 6000, 7500]
        ),
        "expense",
        safe_date(year, 1, 10),
        "card",
        "Annual insurance / subscription",
    )

    create_transaction(
        user,
        categories["Shopping"],
        random.choice(
            [5000, 7500, 10000, 15000]
        ),
        "expense",
        safe_date(year, 10, 20),
        "card",
        "Festival / annual shopping",
    )

    create_transaction(
        user,
        categories["Gift"],
        random.choice(
            [2000, 3000, 5000]
        ),
        "income",
        safe_date(year, 11, 5),
        "upi",
        "Festival gift",
    )


# ---------------------------------------------------------------------
# 5. Budgets across several categories
# ---------------------------------------------------------------------

budget_specs = [
    ("Food", 12000),
    ("Transport", 7000),
    ("Shopping", 10000),
    ("Bills", 8000),
    ("Entertainment", 5000),
    ("Health", 5000),
    ("Education", 6000),
]

month_start = TODAY.replace(day=1)

if month_start.month == 12:
    next_month = date(
        month_start.year + 1,
        1,
        1,
    )
else:
    next_month = date(
        month_start.year,
        month_start.month + 1,
        1,
    )

month_end = next_month - __import__("datetime").timedelta(days=1)

for category_name, limit in budget_specs:
    Budget.objects.create(
        user=user,
        category=categories[category_name],
        limit=Decimal(str(limit)),
        period="monthly",
        start_date=month_start,
        end_date=month_end,
    )

# One yearly budget for a broader test.
Budget.objects.create(
    user=user,
    category=categories["Shopping"],
    limit=Decimal("100000.00"),
    period="yearly",
    start_date=date(
        TODAY.year,
        1,
        1,
    ),
    end_date=date(
        TODAY.year,
        12,
        31,
    ),
)


# ---------------------------------------------------------------------
# 6. Recurring transactions
# ---------------------------------------------------------------------

recurring_specs = [
    (
        "Bills",
        2200,
        "Monthly electricity / internet",
        "monthly",
        5,
    ),
    (
        "Entertainment",
        649,
        "Monthly streaming subscription",
        "monthly",
        23,
    ),
    (
        "Education",
        1500,
        "Monthly course subscription",
        "monthly",
        10,
    ),
    (
        "Health",
        3000,
        "Annual health insurance",
        "yearly",
        15,
    ),
    (
        "Salary",
        62000,
        "Annual salary benchmark",
        "yearly",
        1,
    ),
]

for (
    category_name,
    amount,
    description,
    frequency,
    day_of_month,
) in recurring_specs:

    start = safe_date(
        TODAY.year,
        TODAY.month,
        min(day_of_month, TODAY.day),
    )

    if frequency == "yearly":
        next_date = safe_date(
            TODAY.year + 1,
            start.month,
            day_of_month,
        )
    else:
        if TODAY.month == 12:
            next_date = safe_date(
                TODAY.year + 1,
                1,
                day_of_month,
            )
        else:
            next_date = safe_date(
                TODAY.year,
                TODAY.month + 1,
                day_of_month,
            )

    transaction_type = (
        "income"
        if category_name == "Salary"
        else "expense"
    )

    payment_method = (
        "upi"
        if transaction_type == "income"
        else "card"
    )

    RecurringTransaction.objects.create(
        user=user,
        category=categories[category_name],
        amount=Decimal(str(amount)),
        type=transaction_type,
        payment_method=payment_method,
        description=description,
        frequency=frequency,
        day_of_month=day_of_month,
        start_date=start,
        next_date=next_date,
        is_active=True,
    )


# ---------------------------------------------------------------------
# 7. Report history examples
# ---------------------------------------------------------------------

Report.objects.create(
    user=user,
    report_type="monthly",
    export_format="pdf",
    start_date=month_start,
    end_date=month_end,
)

Report.objects.create(
    user=user,
    report_type="monthly",
    export_format="excel",
    start_date=month_start,
    end_date=month_end,
)

Report.objects.create(
    user=user,
    report_type="yearly",
    export_format="pdf",
    start_date=date(TODAY.year, 1, 1),
    end_date=date(TODAY.year, 12, 31),
)


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print()
print("==============================================")
print(" SUPER TEST USER CREATED")
print("==============================================")
print(f"Email / Username : {DEMO_EMAIL}")
print(f"Password         : {DEMO_PASSWORD}")
print(f"Admin?           : {user.is_staff or user.is_superuser}")
print()
print(f"Transactions     : {Transaction.objects.filter(user=user).count()}")
print(f"Budgets          : {Budget.objects.filter(user=user).count()}")
print(
    "Recurring        : "
    f"{RecurringTransaction.objects.filter(user=user).count()}"
)
print(f"Reports          : {Report.objects.filter(user=user).count()}")
print("==============================================")
print()
