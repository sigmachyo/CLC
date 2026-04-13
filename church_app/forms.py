from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
class RegisterForm(forms.Form):
    """Форма регистрации пользователя"""
    username = forms.CharField(
        max_length=150,
        min_length=3,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'autocomplete': 'email',
        }),
    )
    password1 = forms.CharField(
        min_length=8,
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль (мин 8 символов)',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        min_length=8,
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password',
        }),
    )
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Имя пользователя уже занято')
        return username
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email уже используется')
        return email
    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают')
        return cleaned
class LoginForm(forms.Form):
    """Форма входа"""
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Логин',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Пароль',
            'autocomplete': 'current-password',
        }),
    )
class ProfileEditForm(forms.Form):
    """Форма редактирования профиля"""
    first_name = forms.CharField(
        max_length=150, required=False, label='Имя',
        widget=forms.TextInput(attrs={'placeholder': 'Имя'}),
    )
    last_name = forms.CharField(
        max_length=150, required=False, label='Фамилия',
        widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
    )
class ChangePasswordForm(forms.Form):
    """Форма смены пароля"""
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Текущий пароль'}),
    )
    new_password1 = forms.CharField(
        min_length=8,
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Новый пароль (мин 8 символов)'}),
    )
    new_password2 = forms.CharField(
        min_length=8,
        label='Повторите новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите новый пароль'}),
    )
    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Новые пароли не совпадают')
        return cleaned
class PrayerRequestForm(forms.Form):
    """Форма добавления молитвенной нужды"""
    title = forms.CharField(
        max_length=200,
        label='Тема',
        widget=forms.TextInput(attrs={'placeholder': 'Тема молитвы'}),
    )
    description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'placeholder': 'Опишите вашу нужду...',
            'rows': 4,
        }),
    )
    is_public = forms.BooleanField(
        required=False,
        initial=True,
        label='Показывать публично на молитвенной стене',
    )
