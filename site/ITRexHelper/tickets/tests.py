from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Ticket

class TicketModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testclient', email='test@mail.ru', password='testpass123',
            surname='Иванов', name='Иван', role='CLIENT'
        )

    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            author=self.user,
            title='Тестовая заявка',
            description='Описание для теста',
            status='NEW'
        )
        self.assertEqual(ticket.title, 'Тестовая заявка')
        self.assertEqual(ticket.status, 'NEW')
        self.assertIsNotNone(ticket.created_at)

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            author=self.user, title='Проверка str', description='Тест'
        )
        self.assertIn('Проверка str', str(ticket))