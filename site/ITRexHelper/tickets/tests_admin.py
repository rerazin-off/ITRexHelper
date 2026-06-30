from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tickets.documents.services import collect_analytics_context
from tickets.models import Ticket, TicketStatusHistory

User = get_user_model()
SUPPORT_TICKET_TITLE = 'Чат поддержки'


class AdminAccessTests(TestCase):
    """Доступ к страницам администрирования."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client1',
            email='client1@test.com',
            password='pass12345',
            surname='Иванов',
            name='Иван',
            role='CLIENT',
        )
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='pass12345',
            surname='Петров',
            name='Пётр',
            role='STAFF',
        )

    def test_client_cannot_access_admin_tickets(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('admin_tickets'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/tickets/', response.url)

    def test_staff_can_access_admin_tickets(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Все заявки')

    def test_client_cannot_access_admin_analytics(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_admin_analytics(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Аналитика заявок')


class AdminTicketsFilterTests(TestCase):
    """Фильтрация и поиск на странице «Все заявки»."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='pass12345',
            surname='Петров',
            name='Пётр',
            role='STAFF',
        )
        self.client_a = User.objects.create_user(
            username='client_a',
            email='a@test.com',
            password='pass12345',
            surname='Сидоров',
            name='Сидор',
            role='CLIENT',
        )
        self.client_b = User.objects.create_user(
            username='client_b',
            email='b@test.com',
            password='pass12345',
            surname='Козлов',
            name='Козел',
            role='CLIENT',
        )

        self.new_ticket = Ticket.objects.create(
            author=self.client_a,
            title='Заявка клиента',
            description='Проблема с принтером',
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.MEDIUM,
        )
        self.closed_ticket = Ticket.objects.create(
            author=self.client_b,
            title='Заявка клиента',
            description='Настройка сети',
            status=Ticket.Status.CLOSED,
            priority=Ticket.Priority.HIGH,
            executor=self.staff_user,
        )
        self.client.force_login(self.staff_user)

    def test_admin_tickets_filter_by_status(self):
        response = self.client.get(reverse('admin_tickets'), {'status': Ticket.Status.NEW})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Проблема с принтером')
        self.assertNotContains(response, 'Настройка сети')

        response = self.client.get(reverse('admin_tickets'), {'status': Ticket.Status.CLOSED})
        self.assertContains(response, 'Настройка сети')
        self.assertNotContains(response, 'Проблема с принтером')

    def test_admin_tickets_filter_by_priority(self):
        response = self.client.get(reverse('admin_tickets'), {'priority': Ticket.Priority.HIGH})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Настройка сети')
        self.assertNotContains(response, 'Проблема с принтером')

    def test_admin_tickets_filter_by_executor_none(self):
        response = self.client.get(reverse('admin_tickets'), {'executor': 'none'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Проблема с принтером')
        self.assertNotContains(response, 'Настройка сети')

    def test_admin_tickets_filter_by_executor_id(self):
        response = self.client.get(
            reverse('admin_tickets'),
            {'executor': str(self.staff_user.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Настройка сети')
        self.assertNotContains(response, 'Проблема с принтером')

    def test_admin_tickets_search_by_description(self):
        response = self.client.get(reverse('admin_tickets'), {'search': 'принтер'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Проблема с принтером')
        self.assertNotContains(response, 'Настройка сети')

    def test_admin_tickets_search_by_author_surname(self):
        response = self.client.get(reverse('admin_tickets'), {'search': 'Козлов'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Настройка сети')
        self.assertNotContains(response, 'Проблема с принтером')

    def test_admin_tickets_invalid_sort_falls_back_to_default(self):
        response = self.client.get(reverse('admin_tickets'), {'sort': 'invalid_field'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_sort'], '-created_at')

    def test_closed_ticket_shows_contract_download_link(self):
        response = self.client.get(reverse('admin_tickets'), {'status': Ticket.Status.CLOSED})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Скачать договор')
        self.assertContains(
            response,
            reverse('download_ticket_contract', args=[self.closed_ticket.id]),
        )

    def test_open_ticket_does_not_show_contract_download_link(self):
        response = self.client.get(reverse('admin_tickets'), {'status': Ticket.Status.NEW})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Скачать договор')

    def test_admin_user_can_see_contract_download_for_closed_ticket(self):
        admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='pass12345',
            surname='Админов',
            name='Админ',
            role='ADMIN',
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin_tickets'), {'status': Ticket.Status.CLOSED})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Скачать договор')


class AdminAnalyticsStatisticsTests(TestCase):
    """Статистика и данные страницы аналитики."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='pass12345',
            surname='Петров',
            name='Пётр',
            role='STAFF',
        )
        self.client_user = User.objects.create_user(
            username='client1',
            email='client1@test.com',
            password='pass12345',
            surname='Иванов',
            name='Иван',
            role='CLIENT',
        )
        self.client.force_login(self.staff_user)

    def _create_ticket(self, **kwargs):
        defaults = {
            'author': self.client_user,
            'title': 'Заявка клиента',
            'description': 'Описание',
            'status': Ticket.Status.NEW,
            'priority': Ticket.Priority.MEDIUM,
        }
        defaults.update(kwargs)
        return Ticket.objects.create(**defaults)

    def test_analytics_total_count_excludes_support_tickets(self):
        self._create_ticket(description='Обычная заявка')
        Ticket.objects.create(
            author=self.client_user,
            title=SUPPORT_TICKET_TITLE,
            description='Служебный чат',
            status=Ticket.Status.NEW,
        )

        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

        context = collect_analytics_context()
        self.assertEqual(context['total_count'], '1')

    def test_analytics_in_progress_count(self):
        self._create_ticket(status=Ticket.Status.IN_PROGRESS)
        self._create_ticket(status=Ticket.Status.NEW)

        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.context['in_progress_count'], 1)

    def test_analytics_overdue_count(self):
        old_date = timezone.now() - timedelta(days=10)
        ticket = self._create_ticket(status=Ticket.Status.NEW)
        Ticket.objects.filter(pk=ticket.pk).update(created_at=old_date)

        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.context['overdue_count'], 1)

    def test_analytics_context_matches_page_data(self):
        self._create_ticket(status=Ticket.Status.IN_PROGRESS)
        self._create_ticket(status=Ticket.Status.CLOSED)

        page_response = self.client.get(reverse('admin_analytics'))
        doc_context = collect_analytics_context()

        self.assertEqual(str(page_response.context['total_count']), doc_context['total_count'])
        self.assertEqual(
            str(page_response.context['in_progress_count']),
            doc_context['in_progress_count'],
        )

    def test_analytics_page_contains_chart_data(self):
        self._create_ticket()

        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(len(response.context['chart_months']), 6)
        self.assertEqual(len(response.context['chart_bars']), 6)

    def test_analytics_audit_logs_limited_to_twenty(self):
        ticket = self._create_ticket()
        for index in range(25):
            TicketStatusHistory.objects.create(
                ticket=ticket,
                old_status=Ticket.Status.NEW,
                new_status=Ticket.Status.IN_PROGRESS,
                changed_by=self.staff_user,
                comment=f'Изменение {index}',
            )

        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(len(response.context['audit_logs']), 20)
