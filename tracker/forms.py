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


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Full Name"
    )

    email = forms.EmailField(
        required=True
    )

    phone = forms.CharField(
        max_length=15,
        required=True,
        label="Phone Number"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        if user:
            profile, _ = UserProfile.objects.get_or_create(
                user=user
            )

            self.fields['first_name'].initial = user.first_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = profile.phone

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if self.user:
            email_exists = User.objects.filter(
                email__iexact=email
            ).exclude(
                pk=self.user.pk
            ).exists()

            if email_exists:
                raise forms.ValidationError(
                    "This email address is already in use."
                )

        return email

    def save(self):
        if not self.user:
            raise ValueError(
                "ProfileForm requires a user instance."
            )

        self.user.first_name = self.cleaned_data['first_name']
        self.user.email = self.cleaned_data['email']
        self.user.username = self.cleaned_data['email']

        self.user.save()

        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={
                'phone': self.cleaned_data['phone']
            }
        )

        return self.user


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

        self.fields['category'].queryset = (
            Category.objects.filter(
                is_active=True
            )
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

        self.fields['category'].queryset = (
            Category.objects.filter(
                type='expense',
                is_active=True
            )
        )