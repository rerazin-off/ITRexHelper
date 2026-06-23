from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tickets.documents.generator import generate_pdf_from_template
from tickets.documents.services import collect_analytics_context, collect_contract_context
from tickets.models import Ticket

User = get_user_model()


class DocumentGenerationTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client1',
            email='client1@test.com',
            password='pass12345',
            surname='Иванов',
            name='Иван',
            role='CLIENT',
            company_name='ООО Тест',
        )
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='pass12345',
            surname='Петров',
            name='Пётр',
            role='STAFF',
        )
        self.ticket = Ticket.objects.create(
            author=self.client_user,
            title='Заявка клиента',
            description='Не работает принтер',
            status=Ticket.Status.CLOSED,
        )

    def test_generate_contract_pdf(self):
        context = collect_contract_context(self.ticket)
        pdf_bytes = generate_pdf_from_template('contract.docx', context)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_generate_analytics_pdf(self):
        context = collect_analytics_context()
        pdf_bytes = generate_pdf_from_template('analytics_report.docx', context)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_staff_can_download_analytics_report(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_client_can_download_closed_ticket_contract(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('download_ticket_contract', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_client_cannot_download_open_ticket_contract(self):
        open_ticket = Ticket.objects.create(
            author=self.client_user,
            title='Заявка клиента',
            description='Проблема',
            status=Ticket.Status.NEW,
        )
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('download_ticket_contract', args=[open_ticket.id]))
        self.assertEqual(response.status_code, 302)

    def test_analytics_download_without_tickets_shows_error(self):
        Ticket.objects.all().delete()
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('download_analytics_report'))
        self.assertEqual(response.status_code, 302)
