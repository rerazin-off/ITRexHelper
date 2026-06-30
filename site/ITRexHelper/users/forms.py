from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
import re

from .models import CustomUser


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@company.ru',
            'autocomplete': 'email',
            'class': 'form-control',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password',
            'class': 'form-control',
        }),
    )

    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
        'inactive': 'Учётная запись деактивирована.',
    }

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = CustomUser.objects.get(email__iexact=email)
            except CustomUser.DoesNotExist:
                raise ValidationError(self.error_messages['invalid_login'], code='invalid_login')

            self.user_cache = user
            if not user.check_password(password):
                raise ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            self.confirm_login_allowed(user)

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'example@company.ru', 'class': 'form-control'}),
    )
    surname = forms.CharField(
        label='Фамилия',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Иванов', 'class': 'form-control'}),
    )
    name = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Иван', 'class': 'form-control'}),
    )
    patronymic = forms.CharField(
        label='Отчество',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Иванович', 'class': 'form-control'}),
    )
    contact_phone = forms.CharField(
        label='Номер телефона',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67', 'class': 'form-control'}),
    )
    company_name = forms.CharField(
        label='Наименование компании',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ООО Ромашка', 'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Создайте пароль', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль', 'class': 'form-control'}),
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'surname', 'name', 'patronymic',
            'contact_phone', 'company_name', 'password1', 'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if '@' not in email:
            raise ValidationError('Email должен содержать символ @')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone:
            return phone
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^(\+7|8)\d{10}$', cleaned_phone):
            raise ValidationError(
                'Введите корректный номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX'
            )
        if cleaned_phone.startswith('8'):
            cleaned_phone = '+7' + cleaned_phone[1:]
        return cleaned_phone

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')
        if not re.search(r'[A-ZА-Я]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-zа-я]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'\d', password):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Пароль должен содержать специальный символ (!@#$%^&*)')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают')
        return cleaned_data

    def _generate_username(self, email):
        base = email.split('@')[0]
        base = ''.join(ch for ch in base if ch.isalnum() or ch in '@.+-_') or 'user'
        username = base[:150]
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            suffix = str(counter)
            username = f'{base[:150 - len(suffix)]}{suffix}'
            counter += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.username = self._generate_username(user.email)
        user.surname = self.cleaned_data['surname']
        user.name = self.cleaned_data['name']
        user.patronymic = self.cleaned_data.get('patronymic') or ''
        user.contact_phone = self.cleaned_data.get('contact_phone') or ''
        user.company_name = self.cleaned_data['company_name']
        user.role = CustomUser.Role.CLIENT
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'surname', 'name', 'patronymic', 'email',
            'contact_phone', 'company_name', 'birth_date',
        )
        widgets = {
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'surname', 'name', 'patronymic', 'email',
            'contact_phone', 'company_name', 'role', 'is_active',
        )
        widgets = {
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(),
        }

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        if editor and editor.role != CustomUser.Role.ADMIN:
            self.fields['role'].disabled = True
            self.fields['is_active'].disabled = True
