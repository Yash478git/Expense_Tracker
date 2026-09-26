from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from .models import (
    Budget,
    Category,
    RecurringTransaction,
    Report,
    Transaction,
    UserProfile,
    EmailOTP,
)
from .views import (
    calculate_next_recurring_date,
    process_due_recurring_transactions,
)


User = get_user_model()


class ExpenseTrackerBaseTestCase(TestCase):
    """Shared test data for Expense Tracker test cases."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!'
        )

        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='OtherPass123!'
        )

        self.expense_category = Category.objects.create(
            name='Food',
            type='expense',
            is_active=True
        )

        self.income_category = Category.objects.create(
            name='Salary',
            type='income',
            is_active=True
        )

        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'phone': '9876543210'}
        )

        self.today = timezone.localdate()


class AuthenticationTests(ExpenseTrackerBaseTestCase):
    def test_login_with_valid_email(self):
        response = self.client.post(
            reverse('login'),
            {
                'email': 'test@example.com',
                'password': 'TestPass123!'
            }
        )

        self.assertRedirects(
            response,
            reverse('dashboard')
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_login_with_invalid_password(self):
        response = self.client.post(
            reverse('login'),
            {
                'email': 'test@example.com',
                'password': 'WrongPassword!'
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_protected_dashboard_requires_login(self):
        response = self.client.get(
            reverse('dashboard')
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_logout(self):
        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

        response = self.client.get(
            reverse('logout')
        )

        self.assertRedirects(
            response,
            reverse('login')
        )


class TransactionTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

    def test_add_expense_transaction(self):
        response = self.client.post(
            reverse('add_transaction'),
            {
                'category': self.expense_category.id,
                'amount': '500.00',
                'type': 'expense',
                'date': self.today.isoformat(),
                'payment_method': 'cash',
                'description': 'Lunch'
            }
        )

        self.assertRedirects(
            response,
            reverse('dashboard')
        )

        transaction = Transaction.objects.get(
            user=self.user
        )

        self.assertEqual(
            transaction.amount,
            500
        )

        self.assertEqual(
            transaction.type,
            'expense'
        )

    def test_add_income_transaction(self):
        response = self.client.post(
            reverse('add_transaction'),
            {
                'category': self.income_category.id,
                'amount': '50000.00',
                'type': 'income',
                'date': self.today.isoformat(),
                'payment_method': 'upi',
                'description': 'Salary'
            }
        )

        self.assertRedirects(
            response,
            reverse('dashboard')
        )

        transaction = Transaction.objects.get(
            user=self.user
        )

        self.assertEqual(
            transaction.type,
            'income'
        )

    def test_dashboard_shows_correct_totals(self):
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount='50000.00',
            type='income',
            date=self.today,
            payment_method='upi',
            description='Salary'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='12000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Monthly expenses'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context['total_income'],
            50000
        )

        self.assertEqual(
            response.context['total_expenses'],
            12000
        )

        self.assertEqual(
            response.context['balance'],
            38000
        )

    def test_transaction_cannot_be_edited_by_another_user(self):
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='500.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Private transaction'
        )

        self.client.logout()

        self.client.login(
            username='other@example.com',
            password='OtherPass123!'
        )

        response = self.client.get(
            reverse(
                'edit_transaction',
                args=[transaction.id]
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_transaction_cannot_be_deleted_by_another_user(self):
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='500.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Private transaction'
        )

        self.client.logout()

        self.client.login(
            username='other@example.com',
            password='OtherPass123!'
        )

        response = self.client.get(
            reverse(
                'delete_transaction',
                args=[transaction.id]
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )


class BudgetTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

        self.budget = Budget.objects.create(
            user=self.user,
            category=self.expense_category,
            limit='10000.00',
            period='monthly',
            start_date=self.today.replace(
                day=1
            ),
            end_date=(
                self.today.replace(day=1)
                + timedelta(days=32)
            ).replace(
                day=1
            ) - timedelta(days=1)
        )

    def test_create_budget(self):
        response = self.client.post(
            reverse('add_budget'),
            {
                'category': self.expense_category.id,
                'limit': '15000.00',
                'period': 'monthly',
                'start_date': self.today.replace(day=1).isoformat(),
                'end_date': self.today.isoformat(),
            }
        )

        self.assertRedirects(
            response,
            reverse('dashboard')
        )

        self.assertTrue(
            Budget.objects.filter(
                user=self.user,
                limit='15000.00'
            ).exists()
        )

    def test_dashboard_detects_exceeded_budget(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='12000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Large expense'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTrue(
            len(response.context['exceeded_budgets']) >= 1
        )

    def test_budget_list_calculates_spending(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='2500.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Food'
        )

        response = self.client.get(
            reverse('budget_list')
        )

        self.assertEqual(
            response.status_code,
            200
        )

        budget = response.context['budgets'][0]

        self.assertEqual(
            budget.spent,
            2500
        )

        self.assertEqual(
            budget.remaining,
            7500
        )


class DashboardInsightTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

        self.month_start = self.today.replace(
            day=1
        )

    def test_savings_rate_is_calculated(self):
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount='50000.00',
            type='income',
            date=self.today,
            payment_method='upi',
            description='Salary'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='20000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Expenses'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        insights = response.context['insights']

        self.assertEqual(
            insights['savings_rate'],
            60
        )

    def test_financial_health_score_is_exposed(self):
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount='50000.00',
            type='income',
            date=self.today,
            payment_method='upi',
            description='Salary'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='10000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Expenses'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        financial_health = response.context[
            'financial_health'
        ]

        self.assertGreaterEqual(
            financial_health['score'],
            0
        )

        self.assertLessEqual(
            financial_health['score'],
            100
        )

        self.assertIn(
            financial_health['status'],
            [
                'Excellent',
                'Healthy',
                'Moderate',
                'Needs Attention'
            ]
        )


    def test_top_spending_category_is_detected(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='8000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Food'
        )

        transport = Category.objects.create(
            name='Transport',
            type='expense',
            is_active=True
        )

        Transaction.objects.create(
            user=self.user,
            category=transport,
            amount='2000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Travel'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        insights = response.context['insights']

        self.assertEqual(
            insights['top_category_name'],
            'Food'
        )

        self.assertEqual(
            insights['top_category_amount'],
            8000
        )

    def test_highest_expense_and_income_are_detected(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='3500.00',
            type='expense',
            date=self.today,
            payment_method='card',
            description='Shopping'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount='75000.00',
            type='income',
            date=self.today,
            payment_method='upi',
            description='Salary'
        )

        response = self.client.get(
            reverse('dashboard')
        )

        insights = response.context['insights']

        self.assertEqual(
            insights['highest_expense'].amount,
            3500
        )

        self.assertEqual(
            insights['highest_income'].amount,
            75000
        )


class DashboardFilterTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

        previous_month = (
            self.today.replace(day=1)
            - timedelta(days=1)
        )

        self.previous_month_date = previous_month

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='1000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Current month'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='2000.00',
            type='expense',
            date=self.previous_month_date,
            payment_method='cash',
            description='Previous month'
        )

    def test_this_month_filter(self):
        response = self.client.get(
            reverse('dashboard'),
            {'period': 'this_month'}
        )

        self.assertEqual(
            response.context['total_expenses'],
            1000
        )

        self.assertEqual(
            response.context['selected_period'],
            'this_month'
        )

    def test_last_month_filter(self):
        response = self.client.get(
            reverse('dashboard'),
            {'period': 'last_month'}
        )

        self.assertEqual(
            response.context['total_expenses'],
            2000
        )

        self.assertEqual(
            response.context['selected_period'],
            'last_month'
        )

    def test_custom_range_filter(self):
        response = self.client.get(
            reverse('dashboard'),
            {
                'period': 'custom',
                'date_from': self.today.isoformat(),
                'date_to': self.today.isoformat(),
            }
        )

        self.assertEqual(
            response.context['total_expenses'],
            1000
        )

        self.assertEqual(
            response.context['selected_period'],
            'custom'
        )


class RecurringTransactionTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

    def test_monthly_next_date_calculation(self):
        calculated = calculate_next_recurring_date(
            date(2026, 9, 23),
            'monthly',
            23
        )

        self.assertEqual(
            calculated,
            date(2026, 10, 23)
        )

    def test_yearly_next_date_calculation(self):
        calculated = calculate_next_recurring_date(
            date(2026, 9, 23),
            'yearly',
            23
        )

        self.assertEqual(
            calculated,
            date(2027, 9, 23)
        )

    def test_due_recurring_transaction_creates_normal_transaction(self):
        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='649.00',
            type='expense',
            payment_method='card',
            description='Recurring Test',
            frequency='monthly',
            day_of_month=self.today.day,
            start_date=self.today,
            next_date=self.today,
            is_active=True
        )

        created_count = process_due_recurring_transactions(
            self.user
        )

        self.assertEqual(
            created_count,
            1
        )

        self.assertTrue(
            Transaction.objects.filter(
                user=self.user,
                description='Recurring Test',
                amount='649.00'
            ).exists()
        )

        recurring.refresh_from_db()

        self.assertGreater(
            recurring.next_date,
            self.today
        )

    def test_recurring_transaction_stops_after_end_date(self):
        end_date = self.today

        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='100.00',
            type='expense',
            payment_method='cash',
            description='Ends Today',
            frequency='monthly',
            day_of_month=self.today.day,
            start_date=self.today,
            end_date=end_date,
            next_date=self.today,
            is_active=True
        )

        created_count = process_due_recurring_transactions(
            self.user
        )

        self.assertEqual(
            created_count,
            1
        )

        recurring.refresh_from_db()

        self.assertFalse(
            recurring.is_active
        )

    def test_pause_recurring_transaction(self):
        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='100.00',
            type='expense',
            payment_method='cash',
            description='Paused Schedule',
            frequency='monthly',
            day_of_month=self.today.day,
            start_date=self.today,
            next_date=self.today,
            is_active=True
        )

        response = self.client.post(
            reverse(
                'toggle_recurring_transaction',
                args=[recurring.id]
            )
        )

        self.assertRedirects(
            response,
            reverse('recurring_transaction_list')
        )

        recurring.refresh_from_db()

        self.assertFalse(
            recurring.is_active
        )

    def test_delete_recurring_transaction(self):
        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='100.00',
            type='expense',
            payment_method='cash',
            description='Delete Me',
            frequency='monthly',
            day_of_month=self.today.day,
            start_date=self.today,
            next_date=self.today,
            is_active=True
        )

        response = self.client.post(
            reverse(
                'delete_recurring_transaction',
                args=[recurring.id]
            )
        )

        self.assertRedirects(
            response,
            reverse('recurring_transaction_list')
        )

        self.assertFalse(
            RecurringTransaction.objects.filter(
                id=recurring.id
            ).exists()
        )


class ProfileAndPasswordTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

    def test_profile_page_loads(self):
        response = self.client.get(
            reverse('profile')
        )

        self.assertEqual(
            response.status_code,
            200
        )

    @patch('tracker.views.send_otp')
    def test_change_password(self, mock_send_otp):
        mock_send_otp.return_value = (
            True,
            'OTP sent successfully.'
        )

        # Create the OTP record that the real view expects
        # send_otp() to have created.
        EmailOTP.objects.create(
            user=self.user,
            email=self.user.email,
            otp_hash=make_password('123456'),
            purpose='password_change',
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            reverse('change_password'),
            {
                'old_password': 'TestPass123!',
                'new_password1': 'NewTestPass456!',
                'new_password2': 'NewTestPass456!',
            }
        )

        self.assertRedirects(
            response,
            reverse('verify_password_change_otp')
        )

        self.user.refresh_from_db()

        # Password must not change before OTP verification.
        self.assertTrue(
            self.user.check_password(
                'TestPass123!'
            )
        )

        self.assertFalse(
            self.user.check_password(
                'NewTestPass456!'
            )
        )

        otp_record = (
            EmailOTP.objects
            .filter(
                user=self.user,
                purpose='password_change',
                is_used=False,
            )
            .order_by('-created_at')
            .first()
        )

        self.assertIsNotNone(
            otp_record
        )

        self.assertIsNotNone(
            otp_record.pending_password_hash
        )

        with patch(
            'tracker.views.verify_otp',
            return_value=(
                True,
                'OTP verified successfully.',
                otp_record,
            )
        ):
            response = self.client.post(
                reverse('verify_password_change_otp'),
                {
                    'otp': '123456',
                }
            )

        self.assertRedirects(
            response,
            reverse('profile')
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(
                'NewTestPass456!'
            )
        )


class ReportTests(ExpenseTrackerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.login(
            username='test@example.com',
            password='TestPass123!'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount='50000.00',
            type='income',
            date=self.today,
            payment_method='upi',
            description='Salary'
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount='10000.00',
            type='expense',
            date=self.today,
            payment_method='cash',
            description='Expenses'
        )

    def test_monthly_report_page_loads(self):
        response = self.client.get(
            reverse('report_view'),
            {'report_type': 'monthly'}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context['total_income'],
            50000
        )

        self.assertEqual(
            response.context['total_expenses'],
            10000
        )

    def test_pdf_export_creates_report_history(self):
        before = Report.objects.count()

        response = self.client.get(
            reverse('export_report_pdf'),
            {'report_type': 'monthly'}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response['Content-Type'],
            'application/pdf'
        )

        self.assertEqual(
            Report.objects.count(),
            before + 1
        )

    def test_excel_export_creates_report_history(self):
        before = Report.objects.count()

        response = self.client.get(
            reverse('export_report_excel'),
            {'report_type': 'monthly'}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIn(
            'spreadsheetml',
            response['Content-Type']
        )

        self.assertEqual(
            Report.objects.count(),
            before + 1
        )
