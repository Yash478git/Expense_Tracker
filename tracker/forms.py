from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Budget, Category, Transaction, UserProfile


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Name"
    )

    email = forms.EmailField(
        required=True
    )

    phone = forms.CharField(
        max_length=15,
        required=True
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'email',
            'phone',
            'password1',
            'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': self.cleaned_data['phone']
                }
            )

        return user

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'category',
            'amount',
            'type',
            'date',
            'payment_method',
            'description',
        ]
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        )

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'category',
            'limit',
            'period',
            'start_date',
            'end_date',
        ]
        widgets = {
            'start_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'end_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = Category.objects.filter(
            type='expense',
            is_active=True
        )