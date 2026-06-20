from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .forms import CommentForm, TicketCreateForm
from .models import Comment, Ticket

User = get_user_model()
SUPPORT_TICKET_TITLE = 'Чат поддержки'


def _is_staff(user):
    return user.role in ('STAFF', 'ADMIN')


def _exclude_support_tickets(queryset):
    return queryset.exclude(title=SUPPORT_TICKET_TITLE)


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


def _redirect_home(user):
    if user.role == 'CLIENT':
        return redirect('ticket_list')
    return redirect('admin_dashboard')


@login_required
def ticket_list(request):
    if _is_staff(request.user):
        return redirect('admin_dashboard')

    tickets = _exclude_support_tickets(
        Ticket.objects.filter(author=request.user)
    )

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

    tickets = Ticket.objects.all().order_by('-created_at')[:5]
    all_tickets = Ticket.objects.all()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    context = {
        'active_nav': 'dashboard',
        'tickets': tickets,
        'closed_month': all_tickets.filter(status=Ticket.Status.CLOSED, updated_at__gte=month_start).count(),
        'assigned_count': all_tickets.filter(
            Q(executor=request.user) | Q(status__in=[Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING])
        ).count(),
        'in_progress_count': all_tickets.filter(status=Ticket.Status.IN_PROGRESS).count(),
        'open_count': all_tickets.filter(status__in=[Ticket.Status.NEW, Ticket.Status.WAITING]).count(),
        'unread_comments': Comment.objects.filter(is_internal=False).count(),
    }
    return render(request, 'tickets/admin_dashboard.html', context)


@login_required
def admin_tickets(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    tickets = Ticket.objects.exclude(title=SUPPORT_TICKET_TITLE).select_related('author')

    context = {
        'active_nav': 'tickets',
        'tickets': tickets,
        'tickets_count': tickets.count(),
        'status_choices': Ticket.Status.choices,
    }
    return render(request, 'tickets/admin_tickets.html', context)


@login_required
def admin_analytics(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    tickets = Ticket.objects.all()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    months = []
    bars = []
    for i in range(5, -1, -1):
        start = (month_start - timedelta(days=30 * i)).replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        count = tickets.filter(updated_at__gte=start, updated_at__lt=end, status=Ticket.Status.CLOSED).count()
        months.append(start.strftime('%b'))
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
    }
    return render(request, 'tickets/admin_analytics.html', context)


@login_required
def admin_users(request):
    if not _is_staff(request.user):
        return redirect('ticket_list')

    users = User.objects.all().order_by('surname', 'name')
    search = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')

    if search:
        users = users.filter(
            Q(surname__icontains=search) |
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    context = {
        'active_nav': 'users',
        'users': users,
        'users_count': users.count(),
        'active_count': users.filter(is_active=True).count(),
        'search_query': search,
        'role_filter': role_filter,
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

    if request.user.role == 'CLIENT':
        comments = ticket.comments.filter(is_internal=False)
    else:
        comments = ticket.comments.all()

    status_history = None
    if _is_staff(request.user):
        status_history = ticket.status_history.all()

    context = {
        'ticket': ticket,
        'comments': comments,
        'status_history': status_history,
        'comment_form': CommentForm(),
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
def ticket_update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not _is_staff(request.user):
        messages.error(request, 'Только сотрудники могут изменять статус заявки')
        return redirect('ticket_detail', ticket_id=ticket_id)

    new_status = request.POST.get('status')
    if new_status not in dict(Ticket.Status.choices):
        messages.error(request, 'Недопустимый статус')
        return redirect('admin_tickets')

    old_status = ticket.status
    allowed_transitions = {
        'NEW': ['IN_PROGRESS', 'CANCELED', 'REJECTED', 'WAITING', 'CLOSED'],
        'IN_PROGRESS': ['WAITING', 'CLOSED', 'REJECTED'],
        'WAITING': ['IN_PROGRESS', 'CLOSED'],
    }

    if old_status in allowed_transitions and new_status not in allowed_transitions[old_status]:
        messages.error(request, 'Недопустимый переход статуса')
        return redirect('admin_tickets')

    ticket.status = new_status
    if not ticket.executor:
        ticket.executor = request.user
    ticket.save()
    messages.success(request, f'Статус заявки изменен на "{ticket.get_status_display()}"')
    return redirect('admin_tickets')


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
