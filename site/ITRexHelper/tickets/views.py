from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import CommentForm, TicketCreateForm
from .models import (
    Comment,
    Notification,
    SupportConversation,
    SupportMessage,
    Ticket,
    TicketStatusHistory,
)


User = get_user_model()

SUPPORT_TICKET_TITLE = "Р§Р°С‚ РїРѕРґРґРµСЂР¶РєРё"
TERMINAL_STATUSES = {
    Ticket.Status.CLOSED,
    Ticket.Status.REJECTED,
    Ticket.Status.CANCELED,
}
READONLY_STATUSES = {
    Ticket.Status.CLOSED,
    Ticket.Status.REJECTED,
}


def _is_staff(user):
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or user.role in ["STAFF", "ADMIN"]
    )


def _staff_users():
    return User.objects.filter(
        Q(role__in=["STAFF", "ADMIN"]) | Q(is_staff=True) | Q(is_superuser=True)
    ).distinct()


def _exclude_support_tickets(queryset):
    return queryset.exclude(title=SUPPORT_TICKET_TITLE)


def _paginate(queryset, request):
    paginator = Paginator(queryset, 10)
    return paginator.get_page(request.GET.get("page"))


def _notify_users(recipients, title, message, kind, actor=None, ticket=None):
    seen = set()
    for recipient in recipients:
        if not recipient or not getattr(recipient, "pk", None) or recipient.pk in seen:
            continue
        seen.add(recipient.pk)
        if actor and recipient.pk == actor.pk:
            continue
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            ticket=ticket,
            kind=kind,
            title=title,
            message=message,
        )


def _get_client_conversation(user):
    conversation = SupportConversation.objects.filter(client=user).order_by("-updated_at").first()
    if conversation:
        return conversation
    return SupportConversation.objects.create(client=user, subject="Чат поддержки")


def _ticket_is_overdue(ticket):
    if ticket.status in TERMINAL_STATUSES:
        return False
    if ticket.deadline:
        return timezone.now() > ticket.deadline
    return timezone.now() > ticket.created_at + timedelta(days=7)


def _common_context(user):
    return {
        "unread_notifications": user.notifications.filter(is_read=False)[:5],
        "unread_notifications_count": user.notifications.filter(is_read=False).count(),
    }


# =============================
# LOGIN
# =============================


def login_view(request):
    if request.user.is_authenticated:
        return redirect("ticket_list")
    return redirect("login")


# =============================
# USER TICKETS
# =============================


@login_required
def ticket_list(request):
    if _is_staff(request.user):
        return redirect("admin_dashboard")

    tickets = Ticket.objects.filter(author=request.user).order_by("-created_at")
    tickets = _exclude_support_tickets(tickets)

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")

    if search_query:
        tickets = tickets.filter(
            Q(description__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(contact_info__icontains=search_query)
        )
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    conversation = SupportConversation.objects.filter(client=request.user).order_by("-updated_at").first()
    chat_comments = []
    if conversation:
        chat_comments = conversation.messages.select_related("author")

    return render(
        request,
        "tickets/ticket_list.html",
        {
            **_common_context(request.user),
            "tickets": tickets,
            "form": TicketCreateForm(),
            "tickets_count": tickets.count(),
            "chat_comments": chat_comments,
            "status_choices": Ticket.Status.choices,
            "search_query": search_query,
            "status_filter": status_filter,
        },
    )


# =============================
# CREATE TICKET
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_create(request):
    form = TicketCreateForm(request.POST)

    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.author = request.user
        ticket.status = Ticket.Status.NEW
        ticket.save()

        TicketStatusHistory.objects.create(
            ticket=ticket,
            new_status=Ticket.Status.NEW,
            changed_by=request.user,
            comment="Создание заявки",
        )

        _notify_users(
            _staff_users(),
            title=f"Новая заявка #IT-{ticket.id}",
            message=f"{request.user} создал(а) новую заявку.",
            kind=Notification.Kind.TICKET,
            actor=request.user,
            ticket=ticket,
        )

        messages.success(request, "Заявка создана")
    else:
        messages.error(request, "Не удалось создать заявку. Проверьте заполнение формы.")

    return redirect("ticket_list")


# =============================
# ADMIN DASHBOARD
# =============================


@login_required
def admin_dashboard(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    tickets = Ticket.objects.select_related("author", "executor").order_by("-created_at")
    assigned = tickets.filter(executor=request.user)

    return render(
        request,
        "tickets/admin_dashboard.html",
        {
            **_common_context(request.user),
            "tickets": assigned[:10],
            "open_count": tickets.filter(status=Ticket.Status.NEW).count(),
            "closed_month": tickets.filter(status=Ticket.Status.CLOSED).count(),
            "assigned_count": assigned.count(),
            "in_progress_count": assigned.filter(status=Ticket.Status.IN_PROGRESS).count(),
            "unread_comments": request.user.notifications.filter(is_read=False).count(),
            "status_choices": Ticket.Status.choices,
            "priority_choices": Ticket.Priority.choices,
        },
    )


# =============================
# ALL TICKETS
# =============================


@login_required
def admin_tickets(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    tickets = Ticket.objects.select_related("author", "executor").order_by("-created_at")
    tickets = _exclude_support_tickets(tickets)

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")

    if search_query:
        tickets = tickets.filter(
            Q(description__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(contact_info__icontains=search_query)
            | Q(author__surname__icontains=search_query)
            | Q(author__name__icontains=search_query)
            | Q(author__company_name__icontains=search_query)
        )
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    tickets_count = tickets.count()
    page_obj = _paginate(tickets, request)
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "tickets/admin_tickets.html",
        {
            **_common_context(request.user),
            "tickets": page_obj,
            "page_obj": page_obj,
            "tickets_count": tickets_count,
            "query_string": query_params.urlencode(),
            "status_choices": Ticket.Status.choices,
            "priority_choices": Ticket.Priority.choices,
            "search_query": search_query,
            "status_filter": status_filter,
            "priority_filter": priority_filter,
        },
    )


# =============================
# ANALYTICS
# =============================


@login_required
def admin_analytics(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    now = timezone.localtime(timezone.now())
    tickets = Ticket.objects.all()

    chart_months = []
    chart_values = []
    for offset in range(5, -1, -1):
        month = now.month - offset
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        month_count = tickets.filter(created_at__year=year, created_at__month=month).count()
        chart_values.append(month_count)
        chart_months.append(f"{month:02d}.{str(year)[-2:]}")

    max_value = max(chart_values) if chart_values else 0
    chart_bars = [
        max(12, round(value / max_value * 100)) if max_value else 12
        for value in chart_values
    ]

    overdue_count = sum(1 for ticket in tickets if _ticket_is_overdue(ticket))

    return render(
        request,
        "tickets/admin_analytics.html",
        {
            **_common_context(request.user),
            "total_count": tickets.count(),
            "tickets_month": tickets.filter(created_at__year=now.year, created_at__month=now.month).count(),
            "processed_month": tickets.filter(
                updated_at__year=now.year,
                updated_at__month=now.month,
                status__in=TERMINAL_STATUSES,
            ).count(),
            "in_progress_count": tickets.filter(status=Ticket.Status.IN_PROGRESS).count(),
            "overdue_count": overdue_count,
            "chart_bars": chart_bars,
            "chart_months": chart_months,
            "audit_logs": TicketStatusHistory.objects.select_related("ticket").order_by("-changed_at")[:20],
        },
    )


# =============================
# DETAIL
# =============================


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related("author", "executor"), id=ticket_id)

    if not _is_staff(request.user) and ticket.author_id != request.user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect("ticket_list")

    comments = ticket.comments.select_related("author")
    if not _is_staff(request.user):
        comments = comments.filter(is_internal=False)

    return render(
        request,
        "tickets/ticket_detail.html",
        {
            **_common_context(request.user),
            "ticket": ticket,
            "comments": comments,
            "status_history": ticket.status_history.select_related("changed_by"),
            "comment_form": CommentForm(),
        },
    )


# =============================
# ASSIGN
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_assign_self(request, ticket_id):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    ticket = get_object_or_404(Ticket, id=ticket_id)
    old_status = ticket.status

    ticket.executor = request.user
    ticket.status = Ticket.Status.IN_PROGRESS
    ticket.save()

    TicketStatusHistory.objects.create(
        ticket=ticket,
        old_status=old_status,
        new_status=Ticket.Status.IN_PROGRESS,
        changed_by=request.user,
        comment="Назначено сотруднику",
    )

    _notify_users(
        [ticket.author],
        title=f"Заявка #IT-{ticket.id} взята в работу",
        message=f"{request.user} назначен(а) исполнителем заявки.",
        kind=Notification.Kind.STATUS,
        actor=request.user,
        ticket=ticket,
    )

    return redirect("admin_tickets")


# =============================
# UPDATE STATUS
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_update_status(request, ticket_id):
    return ticket_admin_update(request, ticket_id)


# =============================
# ADMIN UPDATE
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_admin_update(request, ticket_id):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    ticket = get_object_or_404(Ticket, id=ticket_id)
    next_url = request.POST.get("next") or "admin_tickets"

    if ticket.status in READONLY_STATUSES:
        messages.error(request, "Завершенную или отклоненную заявку нельзя редактировать.")
        return redirect(next_url)

    old_status = ticket.status
    new_status = request.POST.get("status") or ticket.status

    ticket.status = new_status
    ticket.priority = request.POST.get("priority", ticket.priority)
    ticket.description = request.POST.get("description", ticket.description)
    ticket.contact_info = request.POST.get("contact_info", ticket.contact_info)
    ticket.executor = request.user
    ticket.save()

    TicketStatusHistory.objects.create(
        ticket=ticket,
        old_status=old_status,
        new_status=ticket.status,
        changed_by=request.user,
        comment="Обновление заявки",
    )

    if old_status != ticket.status:
        _notify_users(
            [ticket.author],
            title=f"Статус заявки #IT-{ticket.id} изменен",
            message=f"Новый статус: {ticket.get_status_display()}",
            kind=Notification.Kind.STATUS,
            actor=request.user,
            ticket=ticket,
        )
    else:
        _notify_users(
            [ticket.author],
            title=f"Заявка #IT-{ticket.id} обновлена",
            message="Сотрудник поддержки обновил данные заявки.",
            kind=Notification.Kind.TICKET,
            actor=request.user,
            ticket=ticket,
        )

    messages.success(request, "Заявка обновлена.")
    return redirect(next_url)


# =============================
# COMMENTS
# =============================


@login_required
@require_http_methods(["POST"])
def add_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related("author", "executor"), id=ticket_id)

    if not _is_staff(request.user) and ticket.author_id != request.user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect("ticket_list")

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        if not _is_staff(request.user):
            comment.is_internal = False
        comment.save()

        if comment.is_internal:
            recipients = list(_staff_users())
        elif _is_staff(request.user):
            recipients = [ticket.author]
        else:
            recipients = list(_staff_users())
            if ticket.executor:
                recipients.append(ticket.executor)

        _notify_users(
            recipients,
            title=f"Комментарий к заявке #IT-{ticket.id}",
            message=f"{request.user} добавил(а) комментарий.",
            kind=Notification.Kind.COMMENT,
            actor=request.user,
            ticket=ticket,
        )
        messages.success(request, "Комментарий добавлен.")
    else:
        messages.error(request, "Комментарий не может быть пустым.")

    return redirect("ticket_detail", ticket_id=ticket.id)


# =============================
# NOTIFICATIONS
# =============================


@login_required
@require_http_methods(["POST"])
def notification_mark_read(request, notification_id):
    Notification.objects.filter(id=notification_id, recipient=request.user).update(is_read=True)
    return redirect(request.POST.get("next") or "ticket_list")


# =============================
# USERS
# =============================


@login_required
def admin_users(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    return render(
        request,
        "tickets/admin_users.html",
        {
            **_common_context(request.user),
            "users": User.objects.all(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def admin_chat(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")

    if request.method == "POST":
        conversation = get_object_or_404(SupportConversation, id=request.POST.get("conversation_id"))
        text = request.POST.get("text", "").strip()
        if text:
            SupportMessage.objects.create(
                conversation=conversation,
                author=request.user,
                text=text,
            )
            if conversation.assigned_to_id is None:
                conversation.assigned_to = request.user
            conversation.status = SupportConversation.Status.WAITING_CLIENT
            conversation.save()

            _notify_users(
                [conversation.client],
                title="Ответ поддержки",
                message="Сотрудник поддержки ответил в чате.",
                kind=Notification.Kind.CHAT,
                actor=request.user,
                ticket=conversation.ticket,
            )
            messages.success(request, "Сообщение отправлено.")
        return redirect(f"{request.path}?client={conversation.client_id}")

    conversations = SupportConversation.objects.select_related("client", "assigned_to").annotate(
        message_count=Count("messages")
    ).filter(message_count__gt=0).order_by("-updated_at")

    clients = []
    seen_clients = set()
    for conversation in conversations:
        if conversation.client_id in seen_clients:
            continue
        seen_clients.add(conversation.client_id)
        conversation.client.support_conversation = conversation
        conversation.client.latest_support_message = conversation.messages.order_by("-created_at").first()
        clients.append(conversation.client)

    selected_client = None
    selected_conversation = None
    selected_client_id = request.GET.get("client")

    if selected_client_id:
        selected_conversation = conversations.filter(client_id=selected_client_id).first()
    elif clients:
        selected_conversation = conversations.filter(client=clients[0]).first()

    if selected_conversation:
        selected_client = selected_conversation.client

    return render(
        request,
        "tickets/admin_chat.html",
        {
            **_common_context(request.user),
            "clients": clients,
            "selected_client": selected_client,
            "selected_conversation": selected_conversation,
            "messages_list": (
                selected_conversation.messages.select_related("author")
                if selected_conversation
                else []
            ),
            "active_chats": SupportConversation.objects.exclude(
                status=SupportConversation.Status.RESOLVED
            ).count(),
        },
    )


@login_required
@require_http_methods(["POST"])
def support_chat(request):
    if _is_staff(request.user):
        return redirect("admin_chat")

    text = request.POST.get("text", "").strip()
    if not text:
        return redirect("ticket_list")

    conversation = _get_client_conversation(request.user)
    SupportMessage.objects.create(
        conversation=conversation,
        author=request.user,
        text=text,
    )
    conversation.status = SupportConversation.Status.OPEN
    conversation.save()

    _notify_users(
        _staff_users(),
        title="Новое обращение в поддержку",
        message=f"{request.user} написал(а) в чат поддержки.",
        kind=Notification.Kind.CHAT,
        actor=request.user,
    )

    messages.success(request, "Сообщение отправлено в поддержку.")
    return redirect("ticket_list")
