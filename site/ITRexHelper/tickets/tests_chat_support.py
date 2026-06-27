from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from tickets.models import (
    SupportConversation,
    SupportMessage,
)

User = get_user_model()


class SupportChatTest(TestCase):
    """Тесты для модуля: Чат поддержки"""
    
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client',
            password='testpass123',
            surname='Петров',
            name='Петр',
            role='CLIENT',
            email='client@test.ru'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            surname='Иванов',
            name='Иван',
            role='STAFF',
            is_staff=True
        )

    def test_1_conversation_creation(self):
        """Тест 1: Создание сессии чата"""
        conv = SupportConversation.objects.create(client=self.client_user)
        self.assertEqual(conv.status, SupportConversation.Status.OPEN)

    def test_2_message_creation(self):
        """Тест 2: Отправка сообщения в чат"""
        conv = SupportConversation.objects.create(client=self.client_user)
        SupportMessage.objects.create(conversation=conv, author=self.client_user, text="Привет")
        self.assertEqual(conv.messages.count(), 1)

    def test_3_client_auto_create_conversation(self):
        """Тест 3: Клиент пишет - создается чат (если нет)"""
        client = Client()
        client.login(username='client', password='testpass123')
        
        response = client.post('/tickets/support-chat/', {'text': 'Нужна помощь'}, follow=True)
        
        self.assertEqual(SupportConversation.objects.count(), 1)
        self.assertEqual(SupportMessage.objects.count(), 1)

    def test_4_client_message_opens_chat(self):
        """Тест 4: Сообщение клиента меняет статус чата на OPEN"""
        conv = SupportConversation.objects.create(
            client=self.client_user, 
            status=SupportConversation.Status.WAITING_CLIENT
        )
        
        client = Client()
        client.login(username='client', password='testpass123')
        client.post('/tickets/support-chat/', {'text': 'Я ответил'}, follow=True)
        
        conv.refresh_from_db()
        self.assertEqual(conv.status, SupportConversation.Status.OPEN)

    def test_5_staff_access_chat(self):
        """Тест 5: Сотрудник имеет доступ к админ-чату"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/chat/')
        self.assertEqual(response.status_code, 200)

    def test_6_staff_replies_to_client(self):
        """Тест 6: Сотрудник отвечает клиенту"""
        conv = SupportConversation.objects.create(client=self.client_user)
        
        client = Client()
        client.login(username='staff', password='testpass123')
        client.post('/tickets/chat/', {
            'conversation_id': conv.id,
            'text': 'Здравствуйте, чем могу помочь?'
        }, follow=True)
        
        self.assertEqual(conv.messages.count(), 1)

    def test_7_staff_reply_changes_status(self):
        """Тест 7: Ответ сотрудника меняет статус на WAITING_CLIENT"""
        conv = SupportConversation.objects.create(client=self.client_user)
        
        client = Client()
        client.login(username='staff', password='testpass123')
        client.post('/tickets/chat/', {
            'conversation_id': conv.id,
            'text': 'Ответ'
        }, follow=True)
        
        conv.refresh_from_db()
        self.assertEqual(conv.status, SupportConversation.Status.WAITING_CLIENT)

    def test_8_client_cannot_access_admin_chat(self):
        """Тест 8: Клиент не может открыть админ-чат"""
        client = Client()
        client.login(username='client', password='testpass123')
        response = client.get('/tickets/chat/')
        self.assertNotEqual(response.status_code, 200)

    def test_9_empty_message_blocked(self):
        """Тест 9: Пустое сообщение не отправляется"""
        client = Client()
        client.login(username='client', password='testpass123')
        
        response = client.post('/tickets/support-chat/', {'text': ''}, follow=True)
        
        self.assertEqual(SupportMessage.objects.count(), 0)

    def test_10_staff_assignment_in_chat(self):
        """Тест 10: При ответе сотрудника он становится assigned_to"""
        conv = SupportConversation.objects.create(client=self.client_user, assigned_to=None)
        
        client = Client()
        client.login(username='staff', password='testpass123')
        client.post('/tickets/chat/', {
            'conversation_id': conv.id,
            'text': 'Беру в работу'
        }, follow=True)
        
        conv.refresh_from_db()
        self.assertEqual(conv.assigned_to, self.staff_user)