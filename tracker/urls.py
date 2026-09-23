from django.urls import path

from . import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.profile, name='profile'),
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
]