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
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.enums import (
    TA_LEFT,
    TA_CENTER,
    TA_RIGHT,
)

from xml.sax.saxutils import escape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment,
)
from openpyxl.utils import get_column_letter

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


    # =========================================================
    # FETCH REPORT DATA
    # =========================================================

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


    transaction_count = transactions.count()


    category_summary = transactions.values(
        'category__name',
        'category__type'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')


    # =========================================================
    # PDF RESPONSE
    # =========================================================

    response = HttpResponse(
        content_type='application/pdf'
    )

    filename = (
        f'Expense_Tracker_'
        f'{report_type.title()}_Report.pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )


    # =========================================================
    # DOCUMENT
    # =========================================================

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=42,
        bottomMargin=42,
        title=(
            f'Expense Tracker - '
            f'{report_type.title()} Report'
        ),
        author='Expense Tracker',
    )


    # =========================================================
    # COLORS
    # =========================================================

    INDIGO = colors.HexColor('#4F46E5')
    INDIGO_DARK = colors.HexColor('#3730A3')
    INDIGO_LIGHT = colors.HexColor('#EEF2FF')

    TEXT_DARK = colors.HexColor('#111827')
    TEXT_MUTED = colors.HexColor('#6B7280')

    BORDER = colors.HexColor('#E5E7EB')
    ROW_LIGHT = colors.HexColor('#F9FAFB')

    GREEN = colors.HexColor('#059669')
    GREEN_LIGHT = colors.HexColor('#ECFDF5')

    RED = colors.HexColor('#DC2626')
    RED_LIGHT = colors.HexColor('#FEF2F2')

    BLUE_LIGHT = colors.HexColor('#EFF6FF')


    # =========================================================
    # STYLES
    # =========================================================

    styles = getSampleStyleSheet()


    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=0,
    )


    report_type_style = ParagraphStyle(
        'ReportType',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )


    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
    )


    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=TEXT_DARK,
        spaceAfter=4,
    )


    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_MUTED,
    )


    card_label_style = ParagraphStyle(
        'CardLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER,
    )


    income_value_style = ParagraphStyle(
        'IncomeValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=GREEN,
        alignment=TA_CENTER,
    )


    expense_value_style = ParagraphStyle(
        'ExpenseValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=RED,
        alignment=TA_CENTER,
    )


    balance_value_style = ParagraphStyle(
        'BalanceValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=INDIGO,
        alignment=TA_CENTER,
    )


    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT,
    )


    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK,
    )


    table_amount_style = ParagraphStyle(
        'TableAmount',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
    )


    # =========================================================
    # PAGE DECORATION
    # =========================================================

    def draw_page_decor(canvas, doc):
        canvas.saveState()

        page_width, page_height = A4

        # Top accent
        canvas.setFillColor(INDIGO)
        canvas.rect(
            0,
            page_height - 7,
            page_width,
            7,
            stroke=0,
            fill=1
        )

        # Footer line
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(
            36,
            30,
            page_width - 36,
            30
        )

        # Footer text
        canvas.setFillColor(TEXT_MUTED)
        canvas.setFont(
            'Helvetica',
            7.5
        )

        canvas.drawString(
            36,
            18,
            'Expense Tracker • Financial Report'
        )

        canvas.drawRightString(
            page_width - 36,
            18,
            f'Page {doc.page}'
        )

        canvas.restoreState()


    # =========================================================
    # CONTENT
    # =========================================================

    elements = []


    # =========================================================
    # HEADER
    # =========================================================

    user_name = (
        request.user.get_full_name().strip()
        or request.user.username
    )


    header_table = Table(
        [
            [
                Paragraph(
                    'EXPENSE TRACKER',
                    report_title_style
                ),

                Paragraph(
                    f'{report_type.title()} Report',
                    report_type_style
                )
            ]
        ],
        colWidths=[
            350,
            173
        ],
        rowHeights=[70],
    )


    header_table.setStyle(
        TableStyle([
            (
                'BACKGROUND',
                (0, 0),
                (-1, -1),
                INDIGO
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE'
            ),

            (
                'LEFTPADDING',
                (0, 0),
                (-1, -1),
                18
            ),

            (
                'RIGHTPADDING',
                (0, 0),
                (-1, -1),
                18
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                10
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )


    elements.append(header_table)

    elements.append(
        Spacer(1, 14)
    )


    # =========================================================
    # REPORT INFORMATION
    # =========================================================

    info_table = Table(
        [
            [
                Paragraph(
                    f'<b>Prepared for:</b> '
                    f'{escape(user_name)}',
                    small_style
                ),

                Paragraph(
                    f'<b>Period:</b> '
                    f'{start_date.strftime("%d %b %Y")} '
                    f'– '
                    f'{end_date.strftime("%d %b %Y")}',
                    small_style
                )
            ],

            [
                Paragraph(
                    f'<b>Generated:</b> '
                    f'{today.strftime("%d %b %Y")}',
                    small_style
                ),

                Paragraph(
                    f'<b>Transactions:</b> '
                    f'{transaction_count}',
                    small_style
                )
            ]
        ],
        colWidths=[
            261.5,
            261.5
        ],
    )


    info_table.setStyle(
        TableStyle([
            (
                'BACKGROUND',
                (0, 0),
                (-1, -1),
                colors.white
            ),

            (
                'BOX',
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                'INNERGRID',
                (0, 0),
                (-1, -1),
                0.4,
                BORDER
            ),

            (
                'LEFTPADDING',
                (0, 0),
                (-1, -1),
                12
            ),

            (
                'RIGHTPADDING',
                (0, 0),
                (-1, -1),
                12
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                8
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                8
            ),
        ])
    )


    elements.append(info_table)

    elements.append(
        Spacer(1, 18)
    )


    # =========================================================
    # FINANCIAL SUMMARY
    # =========================================================

    elements.append(
        Paragraph(
            'Financial Overview',
            section_style
        )
    )

    elements.append(
        Paragraph(
            'A summary of your financial activity for the selected period.',
            subtitle_style
        )
    )

    elements.append(
        Spacer(1, 9)
    )


    income_text = (
        f'Rs. {total_income:,.2f}'
    )

    expense_text = (
        f'Rs. {total_expenses:,.2f}'
    )

    balance_text = (
        f'Rs. {balance:,.2f}'
    )


    summary_table = Table(
        [
            [
                [
                    Paragraph(
                        'TOTAL INCOME',
                        card_label_style
                    ),

                    Spacer(1, 6),

                    Paragraph(
                        income_text,
                        income_value_style
                    )
                ],

                [
                    Paragraph(
                        'TOTAL EXPENSES',
                        card_label_style
                    ),

                    Spacer(1, 6),

                    Paragraph(
                        expense_text,
                        expense_value_style
                    )
                ],

                [
                    Paragraph(
                        'CURRENT BALANCE',
                        card_label_style
                    ),

                    Spacer(1, 6),

                    Paragraph(
                        balance_text,
                        balance_value_style
                    )
                ]
            ]
        ],
        colWidths=[
            174,
            174,
            174
        ],
    )


    summary_table.setStyle(
        TableStyle([
            (
                'BACKGROUND',
                (0, 0),
                (0, 0),
                GREEN_LIGHT
            ),

            (
                'BACKGROUND',
                (1, 0),
                (1, 0),
                RED_LIGHT
            ),

            (
                'BACKGROUND',
                (2, 0),
                (2, 0),
                INDIGO_LIGHT
            ),

            (
                'BOX',
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                'INNERGRID',
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE'
            ),

            (
                'ALIGN',
                (0, 0),
                (-1, -1),
                'CENTER'
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                14
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                14
            ),

            (
                'LEFTPADDING',
                (0, 0),
                (-1, -1),
                8
            ),

            (
                'RIGHTPADDING',
                (0, 0),
                (-1, -1),
                8
            ),
        ])
    )


    elements.append(summary_table)

    elements.append(
        Spacer(1, 22)
    )


    # =========================================================
    # CATEGORY SUMMARY
    # =========================================================

    elements.append(
        Paragraph(
            'Category-wise Summary',
            section_style
        )
    )

    elements.append(
        Paragraph(
            'Breakdown of income and expenses by category.',
            subtitle_style
        )
    )

    elements.append(
        Spacer(1, 9)
    )


    table_data = [
        [
            Paragraph(
                'CATEGORY',
                table_header_style
            ),

            Paragraph(
                'TYPE',
                table_header_style
            ),

            Paragraph(
                'TOTAL',
                table_header_style
            )
        ]
    ]


    for item in category_summary:

        category_name = escape(
            str(item['category__name'])
        )

        category_type = item[
            'category__type'
        ].title()

        total_value = item['total']


        if item['category__type'] == 'income':

            type_color = '#059669'

        else:

            type_color = '#DC2626'


        table_data.append(
            [
                Paragraph(
                    category_name,
                    table_text_style
                ),

                Paragraph(
                    (
                        f'<font color="{type_color}">'
                        f'<b>{category_type}</b>'
                        f'</font>'
                    ),
                    table_text_style
                ),

                Paragraph(
                    f'Rs. {total_value:,.2f}',
                    table_amount_style
                )
            ]
        )


    if len(table_data) > 1:

        category_table = Table(
            table_data,
            colWidths=[
                230,
                105,
                188
            ],
            repeatRows=1,
        )


        category_table_style = [
            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                INDIGO
            ),

            (
                'TEXTCOLOR',
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                'BOX',
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                'INNERGRID',
                (0, 0),
                (-1, -1),
                0.4,
                BORDER
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE'
            ),

            (
                'LEFTPADDING',
                (0, 0),
                (-1, -1),
                10
            ),

            (
                'RIGHTPADDING',
                (0, 0),
                (-1, -1),
                10
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                8
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                8
            ),
        ]


        # Alternating row backgrounds
        for row_index in range(
            1,
            len(table_data)
        ):

            if row_index % 2 == 0:

                category_table_style.append(
                    (
                        'BACKGROUND',
                        (0, row_index),
                        (-1, row_index),
                        ROW_LIGHT
                    )
                )


        category_table.setStyle(
            TableStyle(category_table_style)
        )


        elements.append(category_table)


    else:

        empty_table = Table(
            [
                [
                    Paragraph(
                        'No transactions found for this period.',
                        small_style
                    )
                ]
            ],
            colWidths=[523],
        )


        empty_table.setStyle(
            TableStyle([
                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, -1),
                    BLUE_LIGHT
                ),

                (
                    'BOX',
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BORDER
                ),

                (
                    'LEFTPADDING',
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    'RIGHTPADDING',
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    'TOPPADDING',
                    (0, 0),
                    (-1, -1),
                    14
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    14
                ),
            ])
        )


        elements.append(empty_table)


    elements.append(
        Spacer(1, 20)
    )


    # =========================================================
    # REPORT NOTE
    # =========================================================

    note_table = Table(
        [
            [
                Paragraph(
                    '<b>Expense Tracker</b><br/>'
                    'This report is generated from the transactions '
                    'recorded in your account for the selected period.',
                    small_style
                )
            ]
        ],
        colWidths=[523],
    )


    note_table.setStyle(
        TableStyle([
            (
                'BACKGROUND',
                (0, 0),
                (-1, -1),
                INDIGO_LIGHT
            ),

            (
                'BOX',
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor('#C7D2FE')
            ),

            (
                'LEFTPADDING',
                (0, 0),
                (-1, -1),
                12
            ),

            (
                'RIGHTPADDING',
                (0, 0),
                (-1, -1),
                12
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                10
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )


    elements.append(note_table)


    # =========================================================
    # BUILD PDF
    # =========================================================

    document.build(
        elements,
        onFirstPage=draw_page_decor,
        onLaterPages=draw_page_decor
    )


    # =========================================================
    # SAVE REPORT HISTORY
    # =========================================================

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


    # =========================================================
    # FETCH REPORT DATA
    # =========================================================

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


    transaction_count = transactions.count()


    category_summary = transactions.values(
        'category__name',
        'category__type'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')


    # =========================================================
    # WORKBOOK
    # =========================================================

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = 'Financial Report'

    worksheet.sheet_view.showGridLines = False


    # =========================================================
    # COLORS
    # =========================================================

    INDIGO = '4F46E5'
    INDIGO_DARK = '3730A3'
    INDIGO_LIGHT = 'EEF2FF'

    GREEN = '059669'
    GREEN_LIGHT = 'ECFDF5'

    RED = 'DC2626'
    RED_LIGHT = 'FEF2F2'

    TEXT_DARK = '111827'
    TEXT_MUTED = '6B7280'

    BORDER_COLOR = 'E5E7EB'
    ROW_LIGHT = 'F9FAFB'

    WHITE = 'FFFFFF'


    # =========================================================
    # REUSABLE STYLES
    # =========================================================

    thin_side = Side(
        style='thin',
        color=BORDER_COLOR
    )


    medium_side = Side(
        style='medium',
        color=INDIGO
    )


    thin_border = Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side
    )


    # =========================================================
    # PAGE SETTINGS
    # =========================================================

    worksheet.freeze_panes = 'A10'

    worksheet.sheet_properties.pageSetUpPr.fitToPage = True

    worksheet.page_setup.fitToWidth = 1

    worksheet.page_setup.fitToHeight = 0

    worksheet.page_margins.left = 0.3
    worksheet.page_margins.right = 0.3
    worksheet.page_margins.top = 0.5
    worksheet.page_margins.bottom = 0.5


    # =========================================================
    # HEADER
    # =========================================================

    worksheet.merge_cells('A1:C2')

    title_cell = worksheet['A1']

    title_cell.value = (
        f'EXPENSE TRACKER\n'
        f'{report_type.title()} Financial Report'
    )

    title_cell.font = Font(
        name='Calibri',
        size=18,
        bold=True,
        color=WHITE
    )

    title_cell.fill = PatternFill(
        'solid',
        fgColor=INDIGO
    )

    title_cell.alignment = Alignment(
        horizontal='left',
        vertical='center',
        wrap_text=True
    )


    for row in worksheet['A1:C2']:

        for cell in row:

            cell.fill = PatternFill(
                'solid',
                fgColor=INDIGO
            )


    worksheet.row_dimensions[1].height = 28
    worksheet.row_dimensions[2].height = 28


    # =========================================================
    # REPORT INFORMATION
    # =========================================================

    worksheet['A4'] = 'Report Information'

    worksheet['A4'].font = Font(
        bold=True,
        size=13,
        color=INDIGO_DARK
    )


    worksheet['A5'] = 'Prepared For'

    worksheet['B5'] = (
        request.user.get_full_name().strip()
        or request.user.username
    )


    worksheet['A6'] = 'Period'

    worksheet['B6'] = (
        f'{start_date.strftime("%d %b %Y")} '
        f'to '
        f'{end_date.strftime("%d %b %Y")}'
    )


    worksheet['A7'] = 'Generated'

    worksheet['B7'] = today.strftime(
        '%d %b %Y'
    )


    worksheet['A8'] = 'Transactions'

    worksheet['B8'] = transaction_count


    for row in range(5, 9):

        worksheet[f'A{row}'].font = Font(
            bold=True,
            color=TEXT_DARK
        )

        worksheet[f'B{row}'].font = Font(
            color=TEXT_MUTED
        )

        worksheet[f'A{row}'].fill = PatternFill(
            'solid',
            fgColor=INDIGO_LIGHT
        )

        worksheet[f'B{row}'].fill = PatternFill(
            'solid',
            fgColor=WHITE
        )

        worksheet[f'A{row}'].border = thin_border
        worksheet[f'B{row}'].border = thin_border


    # =========================================================
    # FINANCIAL SUMMARY
    # =========================================================

    worksheet['A10'] = 'Financial Overview'

    worksheet['A10'].font = Font(
        bold=True,
        size=13,
        color=INDIGO_DARK
    )


    summary_headers = [
        'Total Income',
        'Total Expenses',
        'Current Balance'
    ]


    summary_values = [
        float(total_income),
        float(total_expenses),
        float(balance)
    ]


    for column, (header, value) in enumerate(
        zip(summary_headers, summary_values),
        start=1
    ):

        header_cell = worksheet.cell(
            row=11,
            column=column,
            value=header
        )

        value_cell = worksheet.cell(
            row=12,
            column=column,
            value=value
        )


        header_cell.font = Font(
            bold=True,
            size=10,
            color=WHITE
        )

        header_cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

        value_cell.font = Font(
            bold=True,
            size=15
        )

        value_cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )


        header_cell.border = thin_border
        value_cell.border = thin_border


        if column == 1:

            header_cell.fill = PatternFill(
                'solid',
                fgColor=GREEN
            )

            value_cell.fill = PatternFill(
                'solid',
                fgColor=GREEN_LIGHT
            )

            value_cell.font = Font(
                bold=True,
                size=15,
                color=GREEN
            )


        elif column == 2:

            header_cell.fill = PatternFill(
                'solid',
                fgColor=RED
            )

            value_cell.fill = PatternFill(
                'solid',
                fgColor=RED_LIGHT
            )

            value_cell.font = Font(
                bold=True,
                size=15,
                color=RED
            )


        else:

            header_cell.fill = PatternFill(
                'solid',
                fgColor=INDIGO
            )

            value_cell.fill = PatternFill(
                'solid',
                fgColor=INDIGO_LIGHT
            )

            value_cell.font = Font(
                bold=True,
                size=15,
                color=INDIGO
            )


        value_cell.number_format = (
            '₹#,##0.00'
        )


    worksheet.row_dimensions[11].height = 22
    worksheet.row_dimensions[12].height = 30


    # =========================================================
    # CATEGORY SUMMARY
    # =========================================================

    worksheet['A14'] = 'Category-wise Summary'

    worksheet['A14'].font = Font(
        bold=True,
        size=13,
        color=INDIGO_DARK
    )


    category_headers = [
        'Category',
        'Type',
        'Total'
    ]


    for column, header in enumerate(
        category_headers,
        start=1
    ):

        cell = worksheet.cell(
            row=15,
            column=column,
            value=header
        )

        cell.font = Font(
            bold=True,
            color=WHITE
        )

        cell.fill = PatternFill(
            'solid',
            fgColor=INDIGO
        )

        cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

        cell.border = thin_border


    row = 16


    for item in category_summary:

        category_cell = worksheet.cell(
            row=row,
            column=1,
            value=item['category__name']
        )


        type_cell = worksheet.cell(
            row=row,
            column=2,
            value=item['category__type'].title()
        )


        amount_cell = worksheet.cell(
            row=row,
            column=3,
            value=float(item['total'])
        )


        category_cell.border = thin_border
        type_cell.border = thin_border
        amount_cell.border = thin_border


        category_cell.alignment = Alignment(
            horizontal='left',
            vertical='center'
        )


        type_cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )


        amount_cell.alignment = Alignment(
            horizontal='right',
            vertical='center'
        )


        amount_cell.number_format = (
            '₹#,##0.00'
        )


        # Alternating row background

        if row % 2 == 0:

            for column in range(1, 4):

                worksheet.cell(
                    row=row,
                    column=column
                ).fill = PatternFill(
                    'solid',
                    fgColor=ROW_LIGHT
                )


        # Type colors

        if item['category__type'] == 'income':

            type_cell.font = Font(
                bold=True,
                color=GREEN
            )

            amount_cell.font = Font(
                bold=True,
                color=GREEN
            )

        else:

            type_cell.font = Font(
                bold=True,
                color=RED
            )

            amount_cell.font = Font(
                bold=True,
                color=RED
            )


        row += 1


    # =========================================================
    # EMPTY REPORT STATE
    # =========================================================

    if row == 16:

        worksheet.merge_cells(
            start_row=row,
            start_column=1,
            end_row=row,
            end_column=3
        )


        empty_cell = worksheet.cell(
            row=row,
            column=1
        )

        empty_cell.value = (
            'No transactions found for this period.'
        )

        empty_cell.font = Font(
            italic=True,
            color=TEXT_MUTED
        )

        empty_cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

        empty_cell.fill = PatternFill(
            'solid',
            fgColor=INDIGO_LIGHT
        )

        empty_cell.border = thin_border


    # =========================================================
    # TABLE FILTER
    # =========================================================

    if row > 16:

        worksheet.auto_filter.ref = (
            f'A15:C{row - 1}'
        )


    # =========================================================
    # FOOTER
    # =========================================================

    footer_row = row + 2


    worksheet.merge_cells(
        start_row=footer_row,
        start_column=1,
        end_row=footer_row,
        end_column=3
    )


    footer_cell = worksheet.cell(
        row=footer_row,
        column=1
    )


    footer_cell.value = (
        'Expense Tracker • '
        'Generated financial report'
    )


    footer_cell.font = Font(
        italic=True,
        size=9,
        color=TEXT_MUTED
    )


    footer_cell.alignment = Alignment(
        horizontal='center'
    )


    # =========================================================
    # COLUMN WIDTHS
    # =========================================================

    worksheet.column_dimensions['A'].width = 30
    worksheet.column_dimensions['B'].width = 22
    worksheet.column_dimensions['C'].width = 20


    # =========================================================
    # PRINT AREA
    # =========================================================

    worksheet.print_area = (
        f'A1:C{footer_row}'
    )


    # =========================================================
    # RESPONSE
    # =========================================================

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet'
        )
    )


    filename = (
        f'Expense_Tracker_'
        f'{report_type.title()}_Report.xlsx'
    )


    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )


    workbook.save(response)


    # =========================================================
    # SAVE REPORT HISTORY
    # =========================================================

    Report.objects.create(
        user=request.user,
        report_type=report_type,
        export_format='excel',
        start_date=start_date,
        end_date=end_date
    )


    return response