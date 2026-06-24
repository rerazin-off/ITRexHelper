from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
            surname='Тестов',
            name='Тест',
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вход в систему')

    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_successful_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'test@example.com',
            'password': 'SecurePass123!',
        })
        self.assertRedirects(response, reverse('ticket_list'))

    def test_failed_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'test@example.com',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный email или пароль')

    def test_successful_registration(self):
        response = self.client.post(reverse('register'), {
            'email': 'new@example.com',
            'surname': 'Новый',
            'name': 'Пользователь',
            'patronymic': '',
            'birth_date': '',
            'contact_phone': '+79991234567',
            'company_name': 'ООО Тест',
            'password1': 'NewSecurePass123!',
            'password2': 'NewSecurePass123!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='new@example.com').exists())
        user = User.objects.get(email='new@example.com')
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertEqual(user.company_name, 'ООО Тест')

    def test_protected_page_redirects_to_login(self):
        response = self.client.get(reverse('ticket_list'))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('ticket_list')}",
        )
