from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone

from tickets.models import Ticket

User = get_user_model()


class AnalyticsAndFilteringTest(TestCase):
    """Тесты для модуля: Аналитика и фильтрация"""
    
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
            surname='Аналитик',
            name='Иван',
            role='STAFF',
            is_staff=True
        )
        
        self.ticket_new = Ticket.objects.create(
            author=self.client_user,
            title="Новая",
            description="...",
            status=Ticket.Status.NEW
        )
        self.ticket_work = Ticket.objects.create(
            author=self.client_user,
            title="В работе",
            description="...",
            status=Ticket.Status.IN_PROGRESS,
            priority=Ticket.Priority.HIGH
        )
        self.ticket_closed = Ticket.objects.create(
            author=self.client_user,
            title="Закрыта",
            description="...",
            status=Ticket.Status.CLOSED
        )
        self.ticket_critical = Ticket.objects.create(
            author=self.client_user,
            title="Критичная",
            description="...",
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.CRITICAL
        )

    def test_1_client_access_denied(self):
        """Тест 1: Клиент не имеет доступа к аналитике"""
        client = Client()
        client.login(username='client', password='testpass123')
        response = client.get('/tickets/analytics/')
        self.assertNotEqual(response.status_code, 200)

    def test_2_filter_by_status(self):
        """Тест 2: Фильтрация по статусу"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/all/?status=IN_PROGRESS')
        
        self.assertEqual(response.context['tickets_count'], 1)
        self.assertIn(self.ticket_work, response.context['tickets'])
        self.assertNotIn(self.ticket_new, response.context['tickets'])

    def test_3_filter_by_priority(self):
        """Тест 3: Фильтрация по приоритету"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/all/?priority=CRITICAL')
        
        self.assertEqual(response.context['tickets_count'], 1)
        self.assertIn(self.ticket_critical, response.context['tickets'])

    def test_4_search_by_title(self):
        """Тест 4: Поиск по тексту (названию)"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/all/?q=Критичная')
        
        self.assertEqual(response.context['tickets_count'], 1)
        self.assertIn(self.ticket_critical, response.context['tickets'])

    def test_5_pagination(self):
        """Тест 5: Пагинация (создаем больше 10 заявок)"""
        client = Client()
        client.login(username='staff', password='testpass123')
        
        for i in range(11):
            Ticket.objects.create(
                author=self.client_user,
                title=f"Заявка {i}",
                description="..."
            )
        
        response = client.get('/tickets/all/')
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertTrue(response.context['page_obj'].has_next())

    def test_6_analytics_total_count(self):
        """Тест 6: Общая статистика в аналитике"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/analytics/')
        
        
        self.assertEqual(response.context['total_count'], 4)

    def test_7_analytics_chart_data(self):
        """Тест 7: Данные для графика аналитики не пустые"""
        client = Client()
        client.login(username='staff', password='testpass123')
        response = client.get('/tickets/analytics/')
        
        self.assertIsNotNone(response.context['chart_bars'])
        self.assertEqual(len(response.context['chart_months']), 6)

    def test_8_status_transition_validation(self):
        """Тест 8: Валидация переходов статусов (NEW -> CLOSED нельзя)"""
        ticket = Ticket.objects.create(
            author=self.client_user,
            status=Ticket.Status.NEW
        )
        self.assertFalse(ticket.can_change_status(Ticket.Status.CLOSED))

    def test_9_status_transition_allowed(self):
        """Тест 9: Валидация переходов статусов (NEW -> IN_PROGRESS можно)"""
        ticket = Ticket.objects.create(
            author=self.client_user,
            status=Ticket.Status.NEW
        )
        self.assertTrue(ticket.can_change_status(Ticket.Status.IN_PROGRESS))

    def test_10_overdue_detection(self):
        """Тест 10: Определение просроченной заявки"""
        ticket = Ticket.objects.create(
            author=self.client_user,
            status=Ticket.Status.NEW
        )

        Ticket.objects.filter(id=ticket.id).update(created_at=timezone.now() - timedelta(days=8))
        ticket.refresh_from_db()
        
        from tickets.views import _ticket_is_overdue
        self.assertTrue(_ticket_is_overdue(ticket))