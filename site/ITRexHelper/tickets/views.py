from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from users.forms import AdminUserEditForm

from .forms import CommentForm, TicketCreateForm
from .models import Comment, Ticket, TicketStatusHistory
from django.core.exceptions import FieldError

User = get_user_model()
SUPPORT_TICKET_TITLE = 'Чат поддержки'
READONLY_STATUSES = {Ticket.Status.CLOSED, Ticket.Status.REJECTED}


def _is_staff(user):
    return user.role in ('STAFF', 'ADMIN')


def _is_admin(user):
    return user.role == 'ADMIN'


def _exclude_support_tickets(queryset):
    return queryset.exclude(title=SUPPORT_TICKET_TITLE)


def _ticket_readonly(ticket):
    return ticket.status in READONLY_STATUSES


def _get_or_create_support_ticket(user):
    ticket = Ticket.objects.filter(author=user, title=SUPPORT_TICKET_TITLE).first()
    if ticket:
        return ticket
    return Ticket.objects.create(
        author=user,
        title=SUPPORT_TICKET_TITLE,
        description='Обращение в чат поддержки',
        contact_info=user.contact_phone or user.email,
        status=Ticket.Status.NEW,
    )


def _apply_ticket_filters(queryset, request):
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    executor = request.GET.get('executor')
    author = request.GET.get('author')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('q', '').strip()

    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    if executor:
        queryset = queryset.filter(executor_id=executor)
    if author:
        queryset = queryset.filter(author_id=author)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(author__surname__icontains=search) |
            Q(author__name__icontains=search) |
            Q(contact_info__icontains=search)
        )
    return queryset


def _paginate(queryset, request, per_page=10, default_sort='created_at'):
    sort = request.GET.get('sort', default_sort)
    order = request.GET.get('order', 'desc')
    
    model = queryset.model
    allowed_sorts = [f.name for f in model._meta.get_fields() if f.name in 
                    {'created_at', 'updated_at', 'status', 'priority', 'surname', 'name'}]
    
    if sort not in allowed_sorts:
        sort = default_sort
    
    ordering = sort if order == 'asc' else f'-{sort}'
    
    try:
        queryset = queryset.order_by(ordering)
    except FieldError:
        queryset = queryset.order_by('id')
    
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))


@login_required
def ticket_list(request):
    if _is_staff(request.user):
        return redirect('admin_dashboard')

    tickets = _exclude_support_tickets(Ticket.objects.filter(author=request.user))
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    support_ticket = _get_or_create_support_ticket(request.user)
    chat_comments = support_ticket.comments.filter(is_internal=False).order_by('created_at')

    context = {
        'tickets': tickets,
        'status_choices': Ticket.Status.choices,
        'form': TicketCreateForm(),
        'support_ticket': support_ticket,
        'chat_comments': chat_comments,
        'chat_form': CommentForm(),
        'tickets_count': tickets.count(),
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def admin_dashboard(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    tickets = _exclude_support_tickets(
        Ticket.objects.filter(executor=request.user)
    ).select_related('author')[:20]

    all_tickets = Ticket.objects.all()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    my_tickets = _exclude_support_tickets(Ticket.objects.filter(executor=request.user))

    context = {
        'active_nav': 'dashboard',
        'tickets': tickets,
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
        'closed_month': all_tickets.filter(status=Ticket.Status.CLOSED, updated_at__gte=month_start).count(),
        'assigned_count': my_tickets.count(),
        'in_progress_count': my_tickets.filter(status=Ticket.Status.IN_PROGRESS).count(),
        'open_count': all_tickets.filter(status__in=[Ticket.Status.NEW, Ticket.Status.WAITING]).count(),
        'unread_comments': Comment.objects.filter(is_internal=False).count(),
    }
    return render(request, 'tickets/admin_dashboard.html', context)


@login_required
def admin_tickets(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    tickets = _exclude_support_tickets(
        Ticket.objects.select_related('author', 'executor')
    )
    tickets = _apply_ticket_filters(tickets, request)
    page_obj = _paginate(tickets, request)

    query = request.GET.copy()
    query.pop('page', None)
    context = {
        'active_nav': 'tickets',
        'tickets': page_obj,
        'page_obj': page_obj,
        'tickets_count': tickets.count(),
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
        'staff_users': User.objects.filter(role__in=['STAFF', 'ADMIN']),
        'client_users': User.objects.filter(role='CLIENT'),
        'filters': request.GET,
        'query_string': query.urlencode(),
    }
    return render(request, 'tickets/admin_tickets.html', context)


@login_required
def admin_analytics(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    tickets = Ticket.objects.all()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    bars = []
    for i in range(5, -1, -1):
        start = (month_start - timedelta(days=30 * i)).replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        count = tickets.filter(updated_at__gte=start, updated_at__lt=end, status=Ticket.Status.CLOSED).count()
        bars.append(max(count, 1))

    max_bar = max(bars) if bars else 1
    bars = [int((value / max_bar) * 100) for value in bars]

    context = {
        'active_nav': 'analytics',
        'chart_months': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
        'chart_bars': bars,
        'tickets_month': tickets.filter(created_at__gte=month_start).count(),
        'processed_month': tickets.filter(status=Ticket.Status.CLOSED, updated_at__gte=month_start).count(),
        'in_progress_count': tickets.filter(status=Ticket.Status.IN_PROGRESS).count(),
        'overdue_count': tickets.filter(status__in=[Ticket.Status.NEW, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]).count(),
        'total_count': tickets.count(),
        'audit_logs': TicketStatusHistory.objects.select_related('ticket', 'changed_by')[:10],
    }
    return render(request, 'tickets/admin_analytics.html', context)


@login_required
def admin_users(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    users = User.objects.all()
    search = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')
    selected_user = None
    edit_form = None

    if search:
        users = users.filter(
            Q(surname__icontains=search) |
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    # Проверяем AJAX запрос
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Сортируем пользователей
    users = users.order_by('surname', 'name')
    
    # Пагинация
    page_obj = _paginate(users, request, per_page=10, default_sort='surname')

    # Если AJAX запрос - возвращаем только HTML таблицы
    if is_ajax:
        context = {
            'users': page_obj,
            'page_obj': page_obj,
            'users_count': users.count(),
            'active_count': users.filter(is_active=True).count(),
            'search_query': search,
            'role_filter': role_filter,
        }
        html = render(request, 'tickets/includes/users_table.html', context)
        return JsonResponse({
            'html': html.content.decode('utf-8'),
            'count': users.count()
        })

    # Обычный GET запрос
    selected_id = request.GET.get('user_id')
    if selected_id:
        selected_user = get_object_or_404(User, id=selected_id)
        edit_form = AdminUserEditForm(instance=selected_user, editor=request.user)

    if request.method == 'POST':
        selected_user = get_object_or_404(User, id=request.POST.get('user_id'))
        edit_form = AdminUserEditForm(request.POST, instance=selected_user, editor=request.user)
        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, f'Данные пользователя {selected_user.email} обновлены.')
            return redirect(f"{request.path}?q={search}&role={role_filter}&user_id={selected_user.id}")
        messages.error(request, 'Не удалось сохранить изменения. Проверьте форму.')

    context = {
        'active_nav': 'users',
        'users': page_obj,
        'page_obj': page_obj,
        'users_count': users.count(),
        'active_count': users.filter(is_active=True).count(),
        'search_query': search,
        'role_filter': role_filter,
        'query_string': request.GET.urlencode(),
        'selected_user': selected_user,
        'edit_form': edit_form,
        'is_admin': _is_admin(request.user),
    }
    return render(request, 'tickets/admin_users.html', context)


@login_required
def admin_chat(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    client_ids = Comment.objects.values_list('author_id', flat=True).distinct()
    clients = User.objects.filter(id__in=client_ids, role=User.Role.CLIENT).order_by('surname', 'name')

    selected_id = request.GET.get('client')
    selected_client = None
    messages_list = []
    if selected_id:
        selected_client = get_object_or_404(User, id=selected_id, role=User.Role.CLIENT)
        messages_list = Comment.objects.filter(
            author=selected_client,
            is_internal=False,
        ).select_related('ticket').order_by('created_at')

    context = {
        'active_nav': 'chat',
        'clients': clients,
        'selected_client': selected_client,
        'messages_list': messages_list,
        'active_chats': clients.filter(is_active=True).count(),
    }
    return render(request, 'tickets/admin_chat.html', context)


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user.role == 'CLIENT' and ticket.author != request.user:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_list')

    comments = ticket.comments.filter(is_internal=False) if request.user.role == 'CLIENT' else ticket.comments.all()
    status_history = ticket.status_history.all() if _is_staff(request.user) else None

    context = {
        'ticket': ticket,
        'comments': comments,
        'status_history': status_history,
        'comment_form': CommentForm(),
        'readonly': _ticket_readonly(ticket),
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
@require_http_methods(['POST'])
def ticket_create(request):
    form = TicketCreateForm(request.POST)
    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.author = request.user
        ticket.status = Ticket.Status.NEW
        if not ticket.contact_info:
            ticket.contact_info = request.user.contact_phone or request.user.email
        ticket.save()
        messages.success(request, f'Заявка #{ticket.id} успешно создана')
        return redirect('ticket_list')

    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f'{field}: {error}')
    return redirect('ticket_list')


@login_required
@require_http_methods(['POST'])
def ticket_assign_self(request, ticket_id):
    if not _is_staff(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('ticket_list')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.status != Ticket.Status.NEW:
        messages.error(request, 'Назначить себя можно только для новых заявок.')
        return redirect('admin_tickets')

    ticket.executor = request.user
    ticket.status = Ticket.Status.IN_PROGRESS
    ticket.save()
    messages.success(request, f'Заявка #IT-{ticket.id} назначена вам.')
    return redirect('admin_tickets')


@login_required
@require_http_methods(['POST'])
def ticket_update_status(request, ticket_id):
    return ticket_admin_update(request, ticket_id)


@login_required
@require_http_methods(['POST'])
def ticket_admin_update(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not _is_staff(request.user):
        messages.error(request, 'Только сотрудники могут изменять заявки')
        return redirect('ticket_list')

    if _ticket_readonly(ticket):
        messages.error(request, 'Заявка завершена или отклонена — доступен только просмотр.')
        return redirect(request.POST.get('next') or 'admin_tickets')

    ticket.description = request.POST.get('description', ticket.description)
    ticket.contact_info = request.POST.get('contact_info', ticket.contact_info)
    ticket.priority = request.POST.get('priority', ticket.priority)

    new_status = request.POST.get('status')
    if new_status in dict(Ticket.Status.choices):
        ticket.status = new_status

    if not ticket.executor:
        ticket.executor = request.user

    ticket.save()
    messages.success(request, 'Заявка успешно обновлена.')
    next_url = request.POST.get('next', 'admin_tickets')
    return redirect(next_url)


@login_required
@require_http_methods(['POST'])
def add_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user.role == 'CLIENT' and ticket.author != request.user:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('ticket_list')

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        if request.user.role == 'CLIENT':
            comment.is_internal = False
        comment.save()
        messages.success(request, 'Сообщение отправлено')
    else:
        messages.error(request, 'Сообщение не может быть пустым')

    if ticket.title == SUPPORT_TICKET_TITLE:
        return redirect('ticket_list')
    if _is_staff(request.user):
        return redirect('admin_chat')
    return redirect('ticket_detail', ticket_id=ticket_id)


@login_required
@require_http_methods(['POST'])
def support_chat(request):
    ticket = _get_or_create_support_ticket(request.user)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        comment.is_internal = False
        comment.save()
        messages.success(request, 'Сообщение отправлено в поддержку')
    else:
        messages.error(request, 'Сообщение не может быть пустым')
    return redirect('ticket_list')
