from django.contrib.auth import get_user_model
from django.test import TestCase
from datetime import timedelta
from django.test import Client

from .models import Notification, SupportConversation, SupportMessage, Ticket


class TicketModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testclient',
            email='test@mail.ru',
            password='testpass123',
            surname='Иванов',
            name='Иван',
            role='CLIENT',
        )

    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            author=self.user,
            title='Тестовая заявка',
            description='Описание для теста',
            status=Ticket.Status.NEW,
        )

        self.assertEqual(ticket.title, 'Тестовая заявка')
        self.assertEqual(ticket.status, Ticket.Status.NEW)
        self.assertIsNotNone(ticket.created_at)

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            author=self.user,
            title='Проверка str',
            description='Тест',
        )

        self.assertIn('Проверка str', str(ticket))


class SupportAndNotificationModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username='client',
            password='testpass123',
            surname='Петров',
            name='Петр',
            role='CLIENT',
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            surname='Сидоров',
            name='Сергей',
            role='STAFF',
            is_staff=True,
        )
        self.ticket = Ticket.objects.create(
            author=self.client_user,
            title='Нужна помощь',
            description='Проверить доступ',
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            recipient=self.client_user,
            actor=self.staff_user,
            ticket=self.ticket,
            kind=Notification.Kind.STATUS,
            title='Статус изменен',
            message='Заявка обновлена',
        )

        self.assertFalse(notification.is_read)
        self.assertEqual(notification.ticket, self.ticket)

    def test_support_conversation_creation(self):
        conversation = SupportConversation.objects.create(
            client=self.client_user,
            assigned_to=self.staff_user,
            ticket=self.ticket,
            subject='Вопрос по заявке',
        )
        message = SupportMessage.objects.create(
            conversation=conversation,
            author=self.client_user,
            text='Здравствуйте, нужна консультация.',
        )

        self.assertEqual(conversation.status, SupportConversation.Status.OPEN)
        self.assertEqual(message.conversation, conversation)


