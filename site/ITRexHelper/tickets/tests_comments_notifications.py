from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone

from tickets.models import (
    Ticket,
    Comment,
    Notification,
)

User = get_user_model()


class CommentsAndNotificationsTest(TestCase):
    """Тесты для модуля: Комментарии и уведомления"""
    
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
        self.ticket = Ticket.objects.create(
            author=self.client_user,
            title='Нужна помощь',
            description='Проверить доступ',
        )

    def test_1_comment_creation(self):
        """Тест 1: Создание комментария"""
        Comment.objects.create(ticket=self.ticket, author=self.staff_user, text="Тестовый коммент")
        self.assertEqual(self.ticket.comments.count(), 1)

    def test_2_internal_comment_flag(self):
        """Тест 2: Внутренняя заметка создается с флагом"""
        Comment.objects.create(ticket=self.ticket, author=self.staff_user, text="Секрет", is_internal=True)
        self.assertTrue(Comment.objects.get(ticket=self.ticket).is_internal)

    def test_3_client_cannot_see_internal(self):
        """Тест 3: Клиент не видит внутренние заметки (через view)"""
        Comment.objects.create(ticket=self.ticket, author=self.staff_user, text="Секрет", is_internal=True)
        
        client = Client()
        client.login(username='client', password='testpass123')
        response = client.get(f'/tickets/{self.ticket.id}/')
        
        self.assertNotContains(response, "Секрет")

    def test_4_staff_can_see_internal(self):
        """Тест 4: Сотрудник видит внутренние заметки"""
        Comment.objects.create(ticket=self.ticket, author=self.staff_user, text="Секрет", is_internal=True)
        
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get(f'/tickets/{self.ticket.id}/')
        
        self.assertContains(response, "Секрет")

    def test_5_client_forced_public_comment(self):
        """Тест 5: Клиент не может создать внутренний коммент (принудительно False)"""
        client = Client()
        client.login(username='client', password='testpass123')
        
        response = client.post(
            f'/tickets/{self.ticket.id}/add-comment/',
            {'text': 'Вопрос от клиента', 'is_internal': 'on'},
            follow=True
        )
        self.assertEqual(Comment.objects.filter(ticket=self.ticket, is_internal=True).count(), 0)

    def test_6_create_ticket_generates_notification(self):
        """Тест 6: Создание заявки генерирует уведомление сотрудникам"""
        client = Client()
        client.login(username='client', password='testpass123')
        
        client.post('/tickets/create/', {
            'title': 'Новая заявка',
            'description': 'Описание',
            'contact_info': 'tel'
        })
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.TICKET).count(), 1)

    def test_7_assign_ticket_generates_notification(self):
        """Тест 7: Назначение исполнителя генерирует уведомление клиенту"""
        client = Client()
        client.login(username='staff', password='testpass123')
        
        client.post(f'/tickets/{self.ticket.id}/assign/')
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.STATUS, recipient=self.client_user).count(), 1)

    def test_8_comment_generates_notification(self):
        """Тест 8: Комментарий генерирует уведомление автору заявки"""
        client = Client()
        client.login(username='staff', password='testpass123')
        
        client.post(f'/tickets/{self.ticket.id}/add-comment/', {'text': 'Ответ'})
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.COMMENT).count(), 1)

    def test_9_mark_notification_read(self):
        """Тест 9: Отметка уведомления как прочитанного"""
        notif = Notification.objects.create(recipient=self.client_user, title="Test", message="Msg")
        self.assertFalse(notif.is_read)
        
        client = Client()
        client.login(username='client', password='testpass123')
        client.post(f'/tickets/notifications/{notif.id}/read/')
        
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_10_notification_count_in_context(self):
        """Тест 10: Подсчет непрочитанных уведомлений в контексте"""
        Notification.objects.create(recipient=self.client_user, title="1", message="m", is_read=False)
        Notification.objects.create(recipient=self.client_user, title="2", message="m", is_read=True)
        
        client = Client()
        client.login(username='client', password='testpass123')
        response = client.get('/tickets/')
        
        self.assertEqual(response.context['unread_notifications_count'], 1)