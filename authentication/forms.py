from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users"""

    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    company_name = forms.CharField(
        max_length=100,
        required=False,
        help_text='Optional. Your default company name for games.'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'company_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'user'  # New users are always regular users
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Form for user login"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
