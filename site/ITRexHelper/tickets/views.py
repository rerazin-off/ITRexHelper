from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Ticket, Comment
from django.contrib import messages


@login_required
def ticket_list(request):
    """
    Представление для отображения списка заявок.
    - Клиент видит только свои заявки
    - Сотрудник/Админ видит все заявки
    """
    if request.user.role == 'CLIENT':
        tickets = Ticket.objects.filter(author=request.user)
    else:
        tickets = Ticket.objects.all()
    
    # Фильтрация по статусу (если передан параметр в URL)
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    context = {
        'tickets': tickets,
        'status_choices': Ticket.Status.choices,
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_detail(request, ticket_id):
    """
    Представление для отображения детальной информации о заявке.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверка прав доступа
    if request.user.role == 'CLIENT' and ticket.author != request.user:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_list')
    
    comments = ticket.comments.all()
    
    context = {
        'ticket': ticket,
        'comments': comments,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
@require_http_methods(["POST"])
def ticket_create(request):
    """
    Представление для создания новой заявки.
    """
    title = request.POST.get('title')
    description = request.POST.get('description')
    contact_info = request.POST.get('contact_info', '')
    
    if not title or not description:
        messages.error(request, 'Заполните обязательные поля: тема и описание')
        return redirect('ticket_list')
    
    ticket = Ticket.objects.create(
        author=request.user,
        title=title,
        description=description,
        contact_info=contact_info,
        status=Ticket.Status.NEW
    )
    
    messages.success(request, f'Заявка #{ticket.id} успешно создана')
    return redirect('ticket_detail', ticket_id=ticket.id)


@login_required
@require_http_methods(["POST"])
def ticket_update_status(request, ticket_id):
    """
    Представление для изменения статуса заявки (только для сотрудников/админов).
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверка прав доступа
    if request.user.role == 'CLIENT':
        messages.error(request, 'Только сотрудники могут изменять статус заявки')
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    new_status = request.POST.get('status')
    
    if new_status not in dict(Ticket.Status.choices):
        messages.error(request, 'Недопустимый статус')
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    ticket.status = new_status
    ticket.save()
    
    messages.success(request, f'Статус заявки изменен на "{ticket.get_status_display()}"')
    return redirect('ticket_detail', ticket_id=ticket_id)


@login_required
@require_http_methods(["POST"])
def add_comment(request, ticket_id):
    """
    Представление для добавления комментария к заявке.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверка прав доступа
    if request.user.role == 'CLIENT' and ticket.author != request.user:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    text = request.POST.get('text')
    is_internal = request.POST.get('is_internal') == 'on'
    
    if not text:
        messages.error(request, 'Комментарий не может быть пустым')
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    Comment.objects.create(
        ticket=ticket,
        author=request.user,
        text=text,
        is_internal=is_internal
    )
    
    messages.success(request, 'Комментарий добавлен')
    return redirect('ticket_detail', ticket_id=ticket_id)