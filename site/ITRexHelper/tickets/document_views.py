from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from .documents.generator import DocumentGenerationError, generate_pdf_from_template
from .documents.services import collect_analytics_context, collect_contract_context
from .models import Ticket


def _pdf_response(pdf_bytes, filename):
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _is_staff(user):
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or user.role in ['STAFF', 'ADMIN']
    )


@login_required
def download_analytics_report(request):
    """Скачивание PDF-отчёта по аналитике для сотрудника поддержки."""
    if not _is_staff(request.user):
        messages.error(request, 'Доступ запрещён')
        return redirect('ticket_list')

    context = collect_analytics_context()
    if not context['has_tickets']:
        messages.error(request, 'Нет данных о заявках для формирования отчёта')
        return redirect('admin_analytics')

    try:
        pdf_bytes = generate_pdf_from_template('analytics_report.docx', context)
    except DocumentGenerationError as exc:
        messages.error(request, str(exc))
        return redirect('admin_analytics')

    messages.success(request, 'Отчёт успешно сформирован')
    return _pdf_response(pdf_bytes, 'analytics_report.pdf')


def _contract_redirect(request, ticket_id):
    if _is_staff(request.user):
        return redirect('ticket_detail', ticket_id=ticket_id)
    return redirect('ticket_list')


@login_required
def download_ticket_contract(request, ticket_id):
    """Скачивание PDF-договора по завершённой заявке."""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not _is_staff(request.user) and ticket.author_id != request.user.id:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_list')

    if ticket.status != Ticket.Status.CLOSED:
        messages.error(request, 'Договор доступен только для закрытых заявок')
        return _contract_redirect(request, ticket_id)

    context = collect_contract_context(ticket)

    try:
        pdf_bytes = generate_pdf_from_template('contract.docx', context)
    except DocumentGenerationError as exc:
        messages.error(request, str(exc))
        return _contract_redirect(request, ticket_id)

    messages.success(request, 'Договор успешно сформирован')
    return _pdf_response(pdf_bytes, f'contract_ITR-{ticket.id:05d}.pdf')
