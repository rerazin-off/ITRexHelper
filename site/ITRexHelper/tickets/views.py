from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import Ticket, Comment
from .forms import TicketCreateForm, CommentForm
from django.contrib import messages


@login_required
def ticket_list(request):
    """
    Представление для отображения списка заявок.
    - Клиент видит только свои заявки
    - Сотрудник/Админ видит все заявки
    - Поддерживается фильтрация по статусу и пагинация
    """
    # Фильтрация по роли пользователя
    if request.user.role == 'CLIENT':
        tickets = Ticket.objects.filter(author=request.user)
    else:
        tickets = Ticket.objects.all()
    
    # Фильтрация по статусу (если передан параметр в URL)
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    # Пагинация (по 10 заявок на страницу)
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'status_choices': Ticket.Status.choices,
        'form': TicketCreateForm(),
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
    
    # Клиент не должен видеть внутренние заметки сотрудников
    if request.user.role == 'CLIENT':
        comments = ticket.comments.filter(is_internal=False)
    else:
        comments = ticket.comments.all()
    
    # История изменений статусов (только для сотрудников)
    status_history = None
    if request.user.role != 'CLIENT':
        status_history = ticket.status_history.all()
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'status_history': status_history,
        'comment_form': CommentForm(),
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
@require_http_methods(["POST"])
def ticket_create(request):
    """
    Представление для создания новой заявки.
    Использует ModelForm для безопасной валидации данных.
    """
    form = TicketCreateForm(request.POST)
    
    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.author = request.user
        ticket.status = Ticket.Status.NEW
        ticket.save()
        
        messages.success(request, f'Заявка #{ticket.id} успешно создана')
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    # Если форма невалидна - выводим ошибки
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f'{field}: {error}')
    
    return redirect('ticket_list')


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
    
    # Проверка допустимости перехода статусов
    old_status = ticket.status
    allowed_transitions = {
        'NEW': ['IN_PROGRESS', 'CANCELED', 'REJECTED'],
        'IN_PROGRESS': ['WAITING', 'CLOSED', 'REJECTED'],
        'WAITING': ['IN_PROGRESS', 'CLOSED'],
    }
    
    if old_status in allowed_transitions and new_status not in allowed_transitions[old_status]:
        messages.error(
            request, 
            f'Недопустимый переход статуса: из "{ticket.get_status_display()}" в "{dict(Ticket.Status.choices)[new_status]}"'
        )
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
    Использует ModelForm для безопасной валидации.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверка прав доступа
    if request.user.role == 'CLIENT' and ticket.author != request.user:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        
        # Клиенты не могут создавать внутренние заметки (защита от подделки)
        if request.user.role == 'CLIENT':
            comment.is_internal = False
        
        comment.save()
        messages.success(request, 'Комментарий добавлен')
    else:
        messages.error(request, 'Комментарий не может быть пустым')
    
    return redirect('ticket_detail', ticket_id=ticket_id)