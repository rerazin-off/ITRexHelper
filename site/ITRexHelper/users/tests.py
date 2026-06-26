from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

User = get_user_model()


def registration_payload(**overrides):
    """Создает валидные данные для регистрации"""
    data = {
        'email': 'new@example.com',
        'surname': 'Иванов',
        'name': 'Иван',
        'patronymic': 'Иванович',
        'birth_date': '1990-01-01',
        'contact_phone': '+79991234567',
        'company_name': 'ООО Тест',
        'password1': 'SecurePass123!',
        'password2': 'SecurePass123!',
    }
    data.update(overrides)
    return data


class RegistrationAuthTests(TestCase):
    """Регистрация и авторизация — 20 простых тестов."""

    def setUp(self):
        self.client = Client()

    # --- ПОЗИТИВНЫЕ ---

    def test_user_appears_in_database_after_registration(self):
        """Пользователь появляется в БД после регистрации"""
        response = self.client.post(reverse('register'), registration_payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_valid_email_passes_registration(self):
        """Валидный email проходит регистрацию"""
        email = 'good.mail@domain.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email
        ))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email=email).exists())

    def test_registration_with_patronymic_saves_user(self):
        """Регистрация с отчеством сохраняет пользователя"""
        email = 'patronymic@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            patronymic='Иванович'
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.patronymic, 'Иванович')

    def test_registration_without_patronymic_saves_user(self):
        """Регистрация без отчества сохраняет пользователя"""
        email = 'no_patronymic@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            patronymic=''
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.patronymic, '')

    def test_registration_with_phone_saves_user(self):
        """Регистрация с телефоном сохраняет пользователя"""
        email = 'phone@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            contact_phone='+79998887766'
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.contact_phone, '+79998887766')

    def test_registration_without_phone_saves_user(self):
        """Регистрация без телефона сохраняет пользователя"""
        email = 'no_phone@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            contact_phone=''
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.contact_phone, '')

    def test_registration_with_company_saves_user(self):
        """Регистрация с компанией сохраняет пользователя"""
        email = 'company@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            company_name='ООО Рога и Копыта'
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.company_name, 'ООО Рога и Копыта')

    def test_registration_without_company_saves_user(self):
        """Регистрация без компании сохраняет пользователя"""
        email = 'no_company@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            company_name=''
        ))
        self.assertEqual(response.status_code, 302, f"Registration failed. Response status: {response.status_code}")
        
        self.assertTrue(User.objects.filter(email=email).exists(),f"User with email {email} was not created")
        
        user = User.objects.get(email=email)
        self.assertEqual(user.company_name, '')

    def test_registration_redirects_to_login_page(self):
        """После успешной регистрации редиректит на страницу логина"""
        response = self.client.post(reverse('register'), registration_payload())
        self.assertRedirects(response, reverse('login'))

    def test_registration_without_birth_date_saves_user(self):
        """Регистрация без даты рождения сохраняет пользователя"""
        email = 'no_birth@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email,
            birth_date=''
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertIsNone(user.birth_date)

    def test_registration_sets_default_role_client(self):
        """При регистрации роль по умолчанию - CLIENT"""
        email = 'role@example.com'
        response = self.client.post(reverse('register'), registration_payload(
            email=email
        ))
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=email)
        self.assertEqual(user.role, User.Role.CLIENT)

    def test_login_success_redirects_to_ticket_list(self):
        """Успешный вход перенаправляет на список тикетов"""
        User.objects.create_user(
            username='login_user',
            email='login@example.com',
            password='SecurePass123!',
            surname='Логинов',
            name='Логин',
        )
        response = self.client.post(reverse('login'), {
            'username': 'login@example.com',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('ticket_list'))

    def test_login_creates_authenticated_session(self):
        """Логин создает аутентифицированную сессию"""
        User.objects.create_user(
            username='session_user',
            email='session@example.com',
            password='SecurePass123!',
            surname='Сессионов',
            name='Сессион',
        )
        self.client.post(reverse('login'), {
            'username': 'session@example.com',
            'password': 'SecurePass123!',
        })
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_redirects_to_login_page(self):
        """Выход перенаправляет на страницу входа"""
        user = User.objects.create_user(
            username='logout_user',
            email='logout@example.com',
            password='SecurePass123!',
            surname='Выходов',
            name='Выход',
        )
        self.client.login(username='logout_user', password='SecurePass123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_register_page_opens_for_guest(self):
        """Страница регистрации открывается для гостя"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_opens_for_guest(self):
        """Страница входа открывается для гостя"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    # --- НЕГАТИВНЫЕ ---

    def test_missing_surname_is_invalid(self):
        """Регистрация без фамилии не проходит"""
        data = registration_payload()
        del data['surname']
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_missing_name_is_invalid(self):
        """Регистрация без имени не проходит"""
        data = registration_payload()
        del data['name']
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_missing_email_is_invalid(self):
        """Регистрация без email не проходит"""
        data = registration_payload()
        del data['email']
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_invalid_email_format_is_rejected(self):
        """Регистрация с невалидным email не проходит"""
        email = 'not-an-email'
        response = self.client.post(reverse('register'), registration_payload(
            email=email
        ))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email=email).exists())

    def test_password_mismatch_is_rejected(self):
        """Регистрация с несовпадающими паролями не проходит"""
        response = self.client.post(reverse('register'), registration_payload(
            password1='SecurePass123!',
            password2='OtherPass123!'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_duplicate_email_is_rejected(self):
        """Регистрация с существующим email не проходит"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='SecurePass123!',
            surname='Существов',
            name='Существ',
        )
        response = self.client.post(reverse('register'), registration_payload(
            email='existing@example.com'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='existing@example.com').count(), 1)

    def test_login_with_wrong_password_fails(self):
        """Вход с неправильным паролем не проходит"""
        User.objects.create_user(
            username='wrong_pass',
            email='wrong@example.com',
            password='SecurePass123!',
            surname='Ошибков',
            name='Ошибка',
        )
        response = self.client.post(reverse('login'), {
            'username': 'wrong@example.com',
            'password': 'Wrong999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_with_unknown_email_fails(self):
        """Вход с неизвестным email не проходит"""
        response = self.client.post(reverse('login'), {
            'username': 'nobody@example.com',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
