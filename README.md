


💰 Expense Tracker
A full-stack personal finance management web application developed as a Software Engineering college project using Django and PostgreSQL.

Expense Tracker helps users record income and expenses, organize transactions by category, set spending budgets, monitor financial activity, and generate monthly or yearly reports with PDF and Excel export support.

🎓 Academic Project — Software Engineering Lab / College Project

✨ Features
👤 User Authentication
User registration with name, email, phone number and password

Login using username/email credentials

Secure Django password hashing

Session-based authentication

Protected user-only pages

💸 Transaction Management
Add income and expense transactions

Edit existing transactions

Delete transactions

Search and filter transaction history

Categorize transactions

Record payment method:

Cash

UPI / Wallet

Card

Store transaction descriptions and dates

🎯 Budget Management
Create monthly or yearly budgets

Assign budgets to expense categories

Define spending limits and date ranges

Calculate amount spent and remaining budget

Detect exceeded budgets

📊 Dashboard & Analytics
Total income

Total expenses

Current balance

Recent transaction activity

Budget status and spending information

Visual financial summaries

📑 Reports & Export
Monthly reports

Yearly reports

Category-wise income and expense summaries

PDF report generation

Excel report generation

Store generated report history in the database

🛡️ Administration
Django Admin integration

Custom admin dashboard

Category management

User and application data management

Active/inactive category control

🎨 User Interface
Responsive web interface

Consistent application-wide design system

Custom Expense Tracker favicon

Toast notifications for user actions

Custom 404 error page

Mobile-friendly layouts

🧰 Technology Stack
Layer	Technology
Language	Python
Backend	Django 6.1.1
Database	PostgreSQL
Frontend	HTML5, CSS3, JavaScript
PDF Export	ReportLab
Excel Export	OpenPyXL
Environment Configuration	python-dotenv
Authentication	Django Authentication System
Version Control	Git / GitHub
🏗️ Application Modules
User Registration & Login
        │
        ├── Dashboard
        │     ├── Income Summary
        │     ├── Expense Summary
        │     ├── Balance
        │     └── Analytics
        │
        ├── Transactions
        │     ├── Add
        │     ├── View / Search / Filter
        │     ├── Edit
        │     └── Delete
        │
        ├── Budgets
        │     ├── Create
        │     ├── View
        │     └── Edit
        │
        └── Reports
              ├── Monthly
              ├── Yearly
              ├── PDF Export
              └── Excel Export

                    │
                    ▼
              PostgreSQL Database
🗄️ Database Entities
The application uses Django ORM models backed by PostgreSQL.

User — Django's built-in authentication user

UserProfile — stores additional user information such as phone number

Category — income and expense categories

Transaction — individual income and expense records

Budget — category-based spending limits

Report — generated report metadata and export information

Main Relationships
User ────────< Transaction >──────── Category
 │
 ├───────────< Budget >──────────── Category
 │
 ├───────────< Report
 │
 └──────────── UserProfile
📁 Project Structure
Expense-Tracker/
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── tracker/
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── signals.py
    ├── tests.py
    ├── urls.py
    ├── migrations/
    ├── static/
    │   └── tracker/
    │       ├── css/
    │       │   └── style.css
    │       └── favicon.png
    │
    └── templates/
        ├── 404.html
        ├── admin/
        │   └── base_site.html
        └── tracker/
            ├── login.html
            ├── register.html
            ├── dashboard.html
            ├── transaction_list.html
            ├── add_transaction.html
            ├── edit_transaction.html
            ├── delete_transaction.html
            ├── budget_list.html
            ├── add_budget.html
            ├── edit_budget.html
            ├── report.html
            └── admin_dashboard.html
⚙️ Local Setup
1. Clone the repository
git clone https://github.com/Yash478git/Expense_Tracker.git
cd Expense_Tracker
2. Create a virtual environment
Windows PowerShell:

python -m venv venv
.\venv\Scripts\Activate.ps1
3. Install dependencies
python -m pip install -r requirements.txt
4. Create the environment file
Copy .env.example to .env:

Copy-Item .env.example .env
Open .env and configure your local values:

DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=expense_tracker
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
DB_HOST=localhost
DB_PORT=5432
Important: Never commit .env to GitHub. It contains local secrets and credentials.

5. Create the PostgreSQL database
Create a PostgreSQL database named:

expense_tracker
Make sure PostgreSQL is running and the credentials in .env are correct.

6. Apply migrations
python manage.py migrate
7. Create an admin account
python manage.py createsuperuser
8. Run the development server
python manage.py runserver
Open:

http://127.0.0.1:8000/
🔐 Security Notes
The project uses several Django security mechanisms and application-level controls:

Password hashing through Django authentication

CSRF protection

Login-required views for protected functionality

User ownership filtering for transactions, budgets and reports

PostgreSQL credentials stored through environment variables

Django secret key stored through environment variables

Input validation through Django Forms

Django's built-in authentication and permission system

Sensitive .env files excluded through .gitignore

🧪 Testing & Verification
The application was manually verified for core workflows, including:

Registration and login

Username/email login

Transaction creation, editing and deletion

User data isolation

Budget creation and editing

Inactive category filtering

Report generation

PDF export

Excel export

Django Admin access

Admin/user access separation

Custom 404 page

Responsive UI and favicon display

Run Django's system check with:

python manage.py check
📦 Dependencies
The project currently uses:

Django==6.1.1
openpyxl==3.1.5
psycopg2-binary==2.9.13
python-dotenv>=1.0,<2.0
reportlab==5.0.1
🚀 Future Improvements
Possible extensions for a production-oriented version include:

Automated unit and integration test coverage

Advanced charts and spending trend analysis

Recurring transactions

CSV import/export

Email notifications

Stronger production deployment configuration

PostgreSQL backups and monitoring

REST API support

Cloud deployment

Progressive Web App (PWA) support

👨‍💻 Project Information
Project: Expense Tracker
Type: Software Engineering College Project
Backend: Django
Database: PostgreSQL
Repository: GitHub – Expense Tracker

📄 License
This repository is intended primarily for academic and educational use.

You may study and modify the project for learning purposes. For redistribution or commercial use, contact the project owner.
