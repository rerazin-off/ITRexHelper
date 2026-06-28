from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()

STATUS_LABELS = {
    'NEW': 'Новая',
    'IN_PROGRESS': 'В работе',
    'WAITING': 'Открыта',
    'CLOSED': 'Закрыта',
    'REJECTED': 'Отклонена',
    'CANCELED': 'Отменена',
}

STATUS_CLASSES = {
    'NEW': 'status-new',
    'IN_PROGRESS': 'status-in-progress',
    'WAITING': 'status-open',
    'CLOSED': 'status-closed',
    'REJECTED': 'status-overdue',
    'CANCELED': 'status-canceled',
}


@register.filter
def status_label(status):
    return STATUS_LABELS.get(status, status)


@register.filter
def status_class(status):
    return STATUS_CLASSES.get(status, 'status-new')


def _ticket_is_overdue(ticket):
    if ticket.status in ('CLOSED', 'CANCELED', 'REJECTED'):
        return False
    deadline = ticket.created_at + timedelta(days=7)
    return timezone.now() > deadline


@register.filter
def is_overdue(ticket):
    return _ticket_is_overdue(ticket)


@register.filter
def display_status(ticket):
    if _ticket_is_overdue(ticket):
        return 'Просрочена', 'status-overdue'
    return STATUS_LABELS.get(ticket.status, ticket.status), STATUS_CLASSES.get(ticket.status, 'status-new')


@register.filter
def ticket_readonly(ticket):
    return ticket.status in ('CLOSED', 'REJECTED')


@register.filter
def is_staff_user(user):
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or getattr(user, 'role', None) in ('STAFF', 'ADMIN')
    )
