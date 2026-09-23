from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash

from .forms import (
    BudgetForm,
    CustomPasswordChangeForm,
    ProfileForm,
    RegistrationForm,
    TransactionForm,
)
from .models import Budget, Category, Transaction, Report

from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from openpyxl import Workbook
from openpyxl.styles import Font

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Registration successful. You can now log in.'
            )
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'tracker/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.is_staff:
                return redirect('admin_dashboard')

            return redirect('dashboard')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'tracker/login.html')

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Profile updated successfully.'
            )

            return redirect('profile')

    else:
        form = ProfileForm(
            user=request.user
        )

    return render(
        request,
        'tracker/profile.html',
        {
            'form': form,
        }
    )

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():
            user = form.save()

            # Keep the user logged in after changing the password.
            update_session_auth_hash(request, user)

            messages.success(
                request,
                'Your password has been changed successfully.'
            )

            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(
        request,
        'tracker/change_password.html',
        {'form': form}
    )
@login_required
def dashboard(request):
    transactions = request.user.transactions.all()

    total_income = transactions.filter(
        type='income'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expenses = transactions.filter(
        type='expense'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = total_income - total_expenses

    recent_transactions = transactions.select_related(
        'category'
    ).order_by('-date', '-created_at')[:5]

    expense_by_category = transactions.filter(
        type='expense'
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')    

    budgets = Budget.objects.filter(
        user=request.user
    ).select_related('category')

    exceeded_budgets = []

    for budget in budgets:
        spent = transactions.filter(
            category=budget.category,
            type='expense',
            date__gte=budget.start_date,
            date__lte=budget.end_date,
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        if spent >= budget.limit:
            exceeded_budgets.append({
                'category': budget.category.name,
                'limit': budget.limit,
                'spent': spent,
                'remaining': budget.limit - spent,
            })

    return render(
        request,
        'tracker/dashboard.html',
        {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'exceeded_budgets': exceeded_budgets,
            'expense_by_category': expense_by_category,
            'recent_transactions': recent_transactions,
        }
    )

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    users_count = User.objects.filter(
        is_staff=False
    ).count()

    transactions_count = Transaction.objects.count()

    budgets_count = Budget.objects.count()

    categories_count = Category.objects.filter(
        is_active=True
    ).count()

    return render(
        request,
        'tracker/admin_dashboard.html',
        {
            'users_count': users_count,
            'transactions_count': transactions_count,
            'budgets_count': budgets_count,
            'categories_count': categories_count,
        }
    )

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            messages.success(
                request,
                'Transaction added successfully.'
            )

            return redirect('dashboard')
    else:
        form = TransactionForm()

    return render(
        request,
        'tracker/add_transaction.html',
        {'form': form}
    )

@login_required
def transaction_list(request):
    transactions = request.user.transactions.select_related(
        'category'
    ).order_by('-date', '-created_at')

    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()
    type_filter = request.GET.get('type', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if search_query:
        transactions = transactions.filter(
            models.Q(description__icontains=search_query)
            | models.Q(category__name__icontains=search_query)
            | models.Q(payment_method__icontains=search_query)
        )
    if category_filter:
        transactions = transactions.filter(
            category_id=category_filter
        )
    if type_filter:
        transactions = transactions.filter(
            type=type_filter
        )
    if date_from:
        transactions = transactions.filter(
            date__gte=date_from
        )

    if date_to:
        transactions = transactions.filter(
            date__lte=date_to
        )
    

    return render(
        request,
        'tracker/transaction_list.html',
        {
            'transactions': transactions,
            'search_query': search_query,
            'categories': Category.objects.filter(is_active=True),
            'category_filter': category_filter,
            'type_filter': type_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    )

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(
        request.user.transactions,
        id=transaction_id
    )

    if request.method == 'POST':
        form = TransactionForm(
            request.POST,
            instance=transaction
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Transaction updated successfully.'
            )

            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        'tracker/edit_transaction.html',
        {
            'form': form,
            'transaction': transaction,
        }
    )

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(
        request.user.transactions,
        id=transaction_id
    )

    if request.method == 'POST':
        transaction.delete()

        messages.success(
            request,
            'Transaction deleted successfully.'
        )

        return redirect('transaction_list')

    return render(
        request,
        'tracker/delete_transaction.html',
        {
            'transaction': transaction,
        }
    )

@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)

        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()

            messages.success(
                request,
                'Budget created successfully.'
            )

            return redirect('dashboard')
    else:
        form = BudgetForm()

    return render(
        request,
        'tracker/add_budget.html',
        {'form': form}
    )

@login_required
def budget_list(request):
    budgets = request.user.budgets.select_related(
        'category'
    ).order_by('-start_date')

    for budget in budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            type='expense',
            date__gte=budget.start_date,
            date__lte=budget.end_date,
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        budget.spent = spent
        budget.remaining = budget.limit - spent
        budget.is_exceeded = spent >= budget.limit

    return render(
        request,
        'tracker/budget_list.html',
        {
            'budgets': budgets,
        }
    )

@login_required
def edit_budget(request, budget_id):
    budget = get_object_or_404(
        request.user.budgets,
        id=budget_id
    )

    if request.method == 'POST':
        form = BudgetForm(
            request.POST,
            instance=budget
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Budget updated successfully.'
            )

            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)

    return render(
        request,
        'tracker/edit_budget.html',
        {
            'form': form,
            'budget': budget,
        }
    )

@login_required
def report_view(request):
    report_type = request.GET.get('report_type', 'monthly')

    today = timezone.localdate()

    if report_type == 'yearly':
        start_date = today.replace(
            month=1,
            day=1
        )
        end_date = today.replace(
            month=12,
            day=31
        )
    else:
        start_date = today.replace(
            day=1
        )

        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1,
                month=1,
                day=1
            )
        else:
            next_month = today.replace(
                month=today.month + 1,
                day=1
            )

        end_date = next_month - timedelta(days=1)

    transactions = request.user.transactions.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    total_income = transactions.filter(
        type='income'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expenses = transactions.filter(
        type='expense'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = total_income - total_expenses
    category_summary = transactions.values(
        'category__name',
        'category__type'
    ).annotate(
        total=Sum('amount')
    ).order_by(
        '-total'
    )

    return render(
        request,
        'tracker/report.html',
        {
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'category_summary': category_summary,
        }
    )

@login_required
def export_report_pdf(request):
    report_type = request.GET.get('report_type', 'monthly')

    today = timezone.localdate()

    if report_type == 'yearly':
        start_date = today.replace(
            month=1,
            day=1
        )
        end_date = today.replace(
            month=12,
            day=31
        )
    else:
        start_date = today.replace(day=1)

        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1,
                month=1,
                day=1
            )
        else:
            next_month = today.replace(
                month=today.month + 1,
                day=1
            )

        end_date = next_month - timedelta(days=1)

    transactions = request.user.transactions.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    total_income = transactions.filter(
        type='income'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expenses = transactions.filter(
        type='expense'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = total_income - total_expenses

    category_summary = transactions.values(
        'category__name',
        'category__type'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'attachment; filename="expense_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            f"Expense Tracker - {report_type.title()} Report",
            styles['Title']
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            f"Period: {start_date} to {end_date}",
            styles['Normal']
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            f"Total Income: ₹{total_income}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Total Expenses: ₹{total_expenses}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Balance: ₹{balance}",
            styles['Normal']
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            "Category-wise Summary",
            styles['Heading2']
        )
    )

    table_data = [
        ['Category', 'Type', 'Total']
    ]

    for item in category_summary:
        table_data.append([
            item['category__name'],
            item['category__type'].title(),
            f"₹{item['total']}",
        ])

    if len(table_data) > 1:
        table = Table(table_data)

        table.setStyle(
            TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ])
        )

        elements.append(table)

    else:
        elements.append(
            Paragraph(
                "No transactions found for this period.",
                styles['Normal']
            )
        )

    document.build(elements)

    Report.objects.create(
        user=request.user,
        report_type=report_type,
        export_format='pdf',
        start_date=start_date,
        end_date=end_date
    )

    return response


@login_required
def export_report_excel(request):
    report_type = request.GET.get('report_type', 'monthly')

    today = timezone.localdate()

    if report_type == 'yearly':
        start_date = today.replace(
            month=1,
            day=1
        )
        end_date = today.replace(
            month=12,
            day=31
        )
    else:
        start_date = today.replace(day=1)

        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1,
                month=1,
                day=1
            )
        else:
            next_month = today.replace(
                month=today.month + 1,
                day=1
            )

        end_date = next_month - timedelta(days=1)

    transactions = request.user.transactions.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    total_income = transactions.filter(
        type='income'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expenses = transactions.filter(
        type='expense'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = total_income - total_expenses

    category_summary = transactions.values(
        'category__name',
        'category__type'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Financial Report'

    worksheet['A1'] = (
        f'Expense Tracker - {report_type.title()} Report'
    )
    worksheet['A1'].font = Font(
        bold=True,
        size=16
    )

    worksheet['A3'] = 'Period'
    worksheet['B3'] = f'{start_date} to {end_date}'

    worksheet['A4'] = 'Total Income'
    worksheet['B4'] = float(total_income)

    worksheet['A5'] = 'Total Expenses'
    worksheet['B5'] = float(total_expenses)

    worksheet['A6'] = 'Balance'
    worksheet['B6'] = float(balance)

    worksheet['A8'] = 'Category'
    worksheet['B8'] = 'Type'
    worksheet['C8'] = 'Total'

    for cell in worksheet[8]:
        cell.font = Font(bold=True)

    row = 9

    for item in category_summary:
        worksheet.cell(
            row=row,
            column=1,
            value=item['category__name']
        )

        worksheet.cell(
            row=row,
            column=2,
            value=item['category__type'].title()
        )

        worksheet.cell(
            row=row,
            column=3,
            value=float(item['total'])
        )

        row += 1

    worksheet.column_dimensions['A'].width = 25
    worksheet.column_dimensions['B'].width = 20
    worksheet.column_dimensions['C'].width = 15

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet'
        )
    )

    response['Content-Disposition'] = (
        'attachment; filename="expense_report.xlsx"'
    )

    workbook.save(response)

    Report.objects.create(
        user=request.user,
        report_type=report_type,
        export_format='excel',
        start_date=start_date,
        end_date=end_date
    )

    return response