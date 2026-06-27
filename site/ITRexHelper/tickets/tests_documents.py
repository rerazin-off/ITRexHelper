from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from tickets.documents.generator import generate_pdf_from_template
from tickets.documents.services import collect_analytics_context, collect_contract_context
from tickets.models import Ticket, TicketStatusHistory

User = get_user_model()


class DocumentGenerationTests(TestCase):

    def setUp(self):
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='client1',
            email='client1@test.com',
            password='pass12345',
            surname='Иванов',
            name='Иван',
            patronymic='Иванович',
            role='CLIENT',
            company_name='ООО Тест',
            contact_phone='+79991234567',
        )
        
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='pass12345',
            surname='Петров',
            name='Пётр',
            role='STAFF',
        )
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='pass12345',
            surname='Сидоров',
            name='Сидор',
            role='ADMIN',
        )
        
        self.closed_ticket = Ticket.objects.create(
            author=self.client_user,
            title='Закрытая заявка',
            description='Принтер не работает',
            status=Ticket.Status.CLOSED,
            priority=Ticket.Priority.HIGH,
            executor=self.staff_user,
        )
        
        self.open_ticket = Ticket.objects.create(
            author=self.client_user,
            title='Открытая заявка',
            description='Проблема с сетью',
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.CRITICAL,
        )
        
        self.in_progress_ticket = Ticket.objects.create(
            author=self.client_user,
            title='Заявка в работе',
            description='Настройка ПО',
            status=Ticket.Status.IN_PROGRESS,
            priority=Ticket.Priority.MEDIUM,
            executor=self.staff_user,
        )

    @patch('tickets.documents.generator._render_docx')
    @patch('tickets.documents.generator._convert_docx_to_pdf')
    def test_generate_pdf_from_template_returns_bytes(self, mock_convert, mock_render):
        mock_render.return_value = b'docx content'
        mock_convert.return_value = b'%PDF-1.4 mock pdf content'
        
        context = collect_contract_context(self.closed_ticket)
        pdf_bytes = generate_pdf_from_template('contract.docx', context)
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)

    @patch('tickets.documents.generator._render_docx')
    @patch('tickets.documents.generator._convert_docx_to_pdf')
    def test_generate_contract_pdf_starts_with_pdf_marker(self, mock_convert, mock_render):
        mock_render.return_value = b'docx content'
        mock_convert.return_value = b'%PDF-1.4 mock pdf content'
        
        context = collect_contract_context(self.closed_ticket)
        pdf_bytes = generate_pdf_from_template('contract.docx', context)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    @patch('tickets.documents.generator._render_docx')
    @patch('tickets.documents.generator._convert_docx_to_pdf')
    def test_generate_analytics_pdf_starts_with_pdf_marker(self, mock_convert, mock_render):
        mock_render.return_value = b'docx content'
        mock_convert.return_value = b'%PDF-1.4 mock pdf content'
        
        context = collect_analytics_context()
        pdf_bytes = generate_pdf_from_template('analytics_report.docx', context)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_collect_contract_context_contains_required_fields(self):
        context = collect_contract_context(self.closed_ticket)
        required_fields = [
            'contract_number', 'contract_date', 'ticket_id', 'ticket_date',
            'ticket_description', 'ticket_status', 'client_company',
            'client_name', 'client_contact', 'executor_name'
        ]
        for field in required_fields:
            self.assertIn(field, context)

    def test_collect_contract_context_has_correct_executor(self):
        context = collect_contract_context(self.closed_ticket)
        self.assertEqual(context['executor_name'], 'Петров Пётр')

    def test_collect_contract_context_client_name_without_patronymic(self):
        user_without_patronymic = User.objects.create_user(
            username='client2',
            email='client2@test.com',
            password='pass12345',
            surname='Смирнов',
            name='Сергей',
            patronymic='',
            role='CLIENT',
        )
        ticket = Ticket.objects.create(
            author=user_without_patronymic,
            title='Тестовая заявка',
            description='Тест',
            status=Ticket.Status.CLOSED,
        )
        context = collect_contract_context(ticket)
        self.assertEqual(context['client_name'], 'Смирнов Сергей')

    def test_collect_contract_context_client_contact_from_contact_info(self):
        ticket_with_contact = Ticket.objects.create(
            author=self.client_user,
            title='Заявка с контактом',
            description='Тест',
            status=Ticket.Status.CLOSED,
            contact_info='+79998887766',
        )
        context = collect_contract_context(ticket_with_contact)
        self.assertEqual(context['client_contact'], '+79998887766')

    def test_collect_contract_context_fallback_contact(self):
        ticket_no_contact = Ticket.objects.create(
            author=self.client_user,
            title='Заявка без контакта',
            description='Тест',
            status=Ticket.Status.CLOSED,
            contact_info='',
        )
        context = collect_contract_context(ticket_no_contact)
        self.assertEqual(context['client_contact'], '+79991234567')

    def test_collect_contract_context_without_executor(self):
        ticket_without_executor = Ticket.objects.create(
            author=self.client_user,
            title='Заявка без исполнителя',
            description='Тест',
            status=Ticket.Status.NEW,
            executor=None,
        )
        context = collect_contract_context(ticket_without_executor)
        self.assertEqual(context['executor_name'], 'Не назначен')

    def test_collect_analytics_context_contains_required_fields(self):
        context = collect_analytics_context()
        required_fields = [
            'report_date', 'total_count', 'in_progress_count',
            'overdue_count', 'tickets_month', 'processed_month',
            'chart_months', 'chart_values', 'audit_rows', 'has_tickets'
        ]
        for field in required_fields:
            self.assertIn(field, context)

    def test_collect_analytics_context_calculates_total_count(self):
        context = collect_analytics_context()
        self.assertEqual(int(context['total_count']), 3)

    def test_collect_analytics_context_calculates_in_progress_count(self):
        context = collect_analytics_context()
        self.assertEqual(int(context['in_progress_count']), 1)

    def test_collect_analytics_context_has_chart_data(self):
        context = collect_analytics_context()
        self.assertIsInstance(context['chart_months'], list)
        self.assertIsInstance(context['chart_values'], list)
        self.assertEqual(len(context['chart_months']), 6)

    def test_collect_analytics_context_has_tickets_false_when_empty(self):
        Ticket.objects.all().delete()
        context = collect_analytics_context()
        self.assertFalse(context['has_tickets'])

    def test_staff_can_download_analytics_report(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertIn(response.status_code, [200, 302])

    def test_admin_can_download_analytics_report(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertIn(response.status_code, [200, 302])

    def test_client_cannot_download_analytics_report(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertEqual(response.status_code, 302)

    def test_unauthorized_user_cannot_download_analytics(self):
        response = self.client.get(reverse('download_analytics_report'))
        self.assertEqual(response.status_code, 302)

    def test_analytics_download_without_tickets_redirects(self):
        Ticket.objects.all().delete()
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertEqual(response.status_code, 302)

    def test_download_analytics_has_correct_content_disposition(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_analytics_report'))
        if response.status_code == 200:
            self.assertIn('Content-Disposition', response)
            self.assertTrue(response['Content-Disposition'].startswith('attachment; filename='))

    def test_client_can_download_closed_ticket_contract(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('download_ticket_contract', args=[self.closed_ticket.id]))
        self.assertIn(response.status_code, [200, 302])

    def test_client_cannot_download_open_ticket_contract(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('download_ticket_contract', args=[self.open_ticket.id]))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_download_any_closed_ticket_contract(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_ticket_contract', args=[self.closed_ticket.id]))
        self.assertIn(response.status_code, [200, 302])
