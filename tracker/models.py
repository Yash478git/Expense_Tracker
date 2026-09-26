from django.db import models


class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('upi', 'UPI / Wallet'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    date = models.DateField()
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type.title()} - ₹{self.amount}"

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    limit = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - ₹{self.limit} ({self.period})"

class Report(models.Model):
    REPORT_TYPES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    report_type = models.CharField(
        max_length=10,
        choices=REPORT_TYPES
    )
    export_format = models.CharField(
        max_length=10,
        choices=EXPORT_FORMATS
    )
    start_date = models.DateField()
    end_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type.title()} Report - {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

class RecurringTransaction(models.Model):
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('upi', 'UPI / Wallet'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='recurring_transactions'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='recurring_transactions'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS
    )

    description = models.TextField(
        blank=True
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES
    )

    day_of_month = models.PositiveSmallIntegerField(
        default=1
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True
    )

    next_date = models.DateField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f'{self.description or self.category.name} '
            f'- ₹{self.amount}'
        )

class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ('registration', 'Registration'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('account_delete', 'Account Deletion'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='email_otps',
        null=True,
        blank=True,
    )

    email = models.EmailField(
        max_length=254
    )

    otp_hash = models.CharField(
        max_length=128
    )

    pending_password_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(
        default=0
    )

    is_used = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['email', 'purpose', 'is_used']
            ),
            models.Index(
                fields=['expires_at']
            ),
        ]

    def __str__(self):
        return (
            f'{self.email} - '
            f'{self.get_purpose_display()}'
        )