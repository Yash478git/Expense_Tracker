from django.urls import path

from . import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path(
        'register/verify-otp/',
        views.verify_registration_otp,
        name='verify_registration_otp'
    ),
    path('login/', views.user_login, name='login'),
    path(
    'forgot-password/',
    views.forgot_password,
    name='forgot_password'
),
    path(
    'forgot-password/verify-otp/',
    views.verify_password_reset_otp,
    name='verify_password_reset_otp'
),
    path(
    'forgot-password/reset/',
    views.reset_password,
    name='reset_password'
),
    path('profile/', views.profile, name='profile'),
    path(
        'profile/delete-account/',
        views.delete_account,
        name='delete_account'
    ),
    path(
        'profile/delete-account/verify-otp/',
        views.verify_delete_account_otp,
        name='verify_delete_account_otp'
    ),
    path(
    'profile/change-password/',
    views.change_password,
    name='change_password'
),
    path(
    'profile/change-password/verify-otp/',
    views.verify_password_change_otp,
    name='verify_password_change_otp'
),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    

    path(
        'transaction/add/',
        views.add_transaction,
        name='add_transaction'
    ),

    path(
        'transactions/',
        views.transaction_list,
        name='transaction_list'
    ),

    path(
        'transaction/<int:transaction_id>/edit/',
        views.edit_transaction,
        name='edit_transaction'
    ),

    path(
        'transaction/<int:transaction_id>/delete/',
        views.delete_transaction,
        name='delete_transaction'
    ),

    path(
        'budget/add/',
        views.add_budget,
        name='add_budget'
    ),

    path(
        'budgets/',
        views.budget_list,
        name='budget_list'
    ),

    path(
        'budget/<int:budget_id>/edit/',
        views.edit_budget,
        name='edit_budget'
    ),

    path(
        'reports/',
        views.report_view,
        name='report_view'
    ),

    path(
        'reports/export/pdf/',
        views.export_report_pdf,
        name='export_report_pdf'
    ),

    path(
        'reports/export/excel/',
        views.export_report_excel,
        name='export_report_excel'
    ),

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'recurring-transactions/',
        views.recurring_transaction_list,
        name='recurring_transaction_list'
    ),

    path(
        'recurring-transactions/add/',
        views.add_recurring_transaction,
        name='add_recurring_transaction'
    ),

    path(
        'recurring-transactions/<int:recurring_id>/edit/',
        views.edit_recurring_transaction,
        name='edit_recurring_transaction'
    ),

    path(
        'recurring-transactions/<int:recurring_id>/toggle/',
        views.toggle_recurring_transaction,
        name='toggle_recurring_transaction'
    ),

    path(
        'recurring-transactions/<int:recurring_id>/delete/',
        views.delete_recurring_transaction,
        name='delete_recurring_transaction'
    ),
]