from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from tickets.models import Ticket, TicketStatusHistory

SUPPORT_TICKET_TITLE = 'Чат поддержки'

ITREX_CONTRACTOR = {
    'contractor_name': 'ООО «Айти Партнер»',
    'contractor_details': 'ИНН 5259149688, город Нижний Новгород, ул. Коминтерна, д. 10, кв. 120',
}

STATUS_LABELS = {
    'NEW': 'Новая',
    'IN_PROGRESS': 'В работе',
    'WAITING': 'Ожидание клиента',
    'CLOSED': 'Закрыта',
    'REJECTED': 'Отклонена',
    'CANCELED': 'Отменена',
}


def _exclude_support_tickets(queryset):
    return queryset.exclude(title=SUPPORT_TICKET_TITLE)


def collect_analytics_context():
    tickets = _exclude_support_tickets(Ticket.objects.all())
    now = timezone.now()

    total_count = tickets.count()
    in_progress_count = tickets.filter(status=Ticket.Status.IN_PROGRESS).count()

    deadline = now - timedelta(days=7)
    overdue_count = tickets.exclude(
        status__in=[Ticket.Status.CLOSED, Ticket.Status.CANCELED, Ticket.Status.REJECTED]
    ).filter(created_at__lt=deadline).count()

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    tickets_month = tickets.filter(created_at__gte=month_start).count()
    processed_month = tickets.filter(
        status=Ticket.Status.CLOSED,
        updated_at__gte=month_start,
    ).count()

    six_months_ago = now - timedelta(days=180)
    monthly_stats = (
        tickets
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    chart_months = []
    chart_values = []
    for i in range(5, -1, -1):
        month_date = (now - timedelta(days=30 * i)).replace(day=1)
        month_name = month_date.strftime('%B %Y')
        chart_months.append(month_name)

        month_count = 0
        for stat in monthly_stats:
            if stat['month'].strftime('%B %Y') == month_name:
                month_count = stat['count']
                break
        chart_values.append(month_count)

    audit_logs = TicketStatusHistory.objects.select_related('ticket').order_by('-changed_at')[:20]
    audit_rows = [
        {
            'ticket': f"#IT-{log.ticket.id}",
            'old_status': log.old_status or '—',
            'new_status': log.new_status,
            'changed_at': log.changed_at.strftime('%d.%m.%Y %H:%M'),
        }
        for log in audit_logs
    ]

    return {
        'report_date': now.strftime('%d.%m.%Y %H:%M'),
        'total_count': str(total_count),
        'in_progress_count': str(in_progress_count),
        'overdue_count': str(overdue_count),
        'tickets_month': str(tickets_month),
        'processed_month': str(processed_month),
        'chart_months': chart_months,
        'chart_values': chart_values,
        'audit_rows': audit_rows,
        'has_tickets': total_count > 0,
    }


def collect_contract_context(ticket):
    author = ticket.author
    client_name = f"{author.surname} {author.name}"
    if author.patronymic:
        client_name = f"{client_name} {author.patronymic}"

    contact = ticket.contact_info or author.contact_phone or author.email or '—'
    now = timezone.now()

    return {
        **ITREX_CONTRACTOR,
        'contract_number': f"ITR-{ticket.id:05d}",
        'contract_date': now.strftime('%d.%m.%Y'),
        'ticket_id': str(ticket.id),
        'ticket_date': ticket.created_at.strftime('%d.%m.%Y'),
        'ticket_description': ticket.description,
        'ticket_status': STATUS_LABELS.get(ticket.status, ticket.status),
        'client_company': author.company_name or 'Не указано',
        'client_name': client_name,
        'client_contact': contact,
        'executor_name': (
            f"{ticket.executor.surname} {ticket.executor.name}"
            if ticket.executor else 'Не назначен'
        ),
    }
