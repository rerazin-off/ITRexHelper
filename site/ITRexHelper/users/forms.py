from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
import re

from .models import CustomUser


class CustomLoginForm(AuthenticationForm):
    """Форма входа: email и пароль (согласно диаграмме состояний модуля авторизации)."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@mail.ru',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password',
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
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )

            self.user_cache = user
            if not user.check_password(password):
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
            self.confirm_login_allowed(user)

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class CustomRegistrationForm(UserCreationForm):
    """
    Форма регистрации клиента.
    Поля соответствуют модели CustomUser и диаграмме классов проекта.
    """

    email = forms.EmailField(
        label='Email (почта)',
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.ru'}),
    )
    surname = forms.CharField(
        label='Фамилия',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Иванов'}),
    )
    name = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Иван'}),
    )
    patronymic = forms.CharField(
        label='Отчество',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Иванович (необязательно)'}),
    )
    birth_date = forms.DateField(
        label='Дата рождения',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    contact_phone = forms.CharField(
        label='Контактный телефон',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        help_text='Введите номер в формате +7 (XXX) XXX-XX-XX или 8XXXXXXXXXX'
    )
    company_name = forms.CharField(
        label='Название компании',
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'ООО «Пример»'}),
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Создайте пароль'}),
        help_text='Пароль должен содержать минимум 8 символов, заглавную и строчную буквы, цифру и специальный символ (!@#$%^&*(),.?":{}|<>)'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'}),
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'surname', 'name', 'patronymic',
            'birth_date', 'contact_phone', 'company_name',
            'password1', 'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        
        # Проверка на наличие @
        if '@' not in email:
            raise ValidationError('Email должен содержать символ @')
        
        # Проверка на уникальность
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        
        return email

    def clean_contact_phone(self):
        """Проверка российского номера телефона"""
        phone = self.cleaned_data.get('contact_phone')
        
        # Если поле необязательное и пустое - пропускаем
        if not phone:
            return phone
        
        # Удаляем все пробелы, скобки, дефисы и другие разделители
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Проверяем, начинается ли номер с +7 или 8, и содержит 11 цифр
        if not re.match(r'^(\+7|8)\d{10}$', cleaned_phone):
            raise ValidationError(
                'Введите корректный российский номер телефона. '
                'Формат: +7 (XXX) XXX-XX-XX или 8XXXXXXXXXX (11 цифр)'
            )
        
        # Приводим к единому формату +7XXXXXXXXXX
        if cleaned_phone.startswith('8'):
            cleaned_phone = '+7' + cleaned_phone[1:]
        
        return cleaned_phone

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Проверка минимальной длины
        if len(password) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')
        
        # Проверка на заглавную букву (латиница и кириллица)
        if not re.search(r'[A-ZА-Я]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву')
        
        # Проверка на строчную букву (латиница и кириллица)
        if not re.search(r'[a-zа-я]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну строчную букву')
        
        # Проверка на цифру
        if not re.search(r'\d', password):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру')
        
        # Проверка на специальный символ
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Пароль должен содержать хотя бы один специальный символ (!@#$%^&*(),.?":{}|<>)')
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Проверка совпадения паролей
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают')
        
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
        user.patronymic = self.cleaned_data.get('patronymic') or None
        user.birth_date = self.cleaned_data.get('birth_date')
        user.contact_phone = self.cleaned_data.get('contact_phone') or None
        user.company_name = self.cleaned_data['company_name']
        user.role = CustomUser.Role.CLIENT
        if commit:
            user.save()
        return user