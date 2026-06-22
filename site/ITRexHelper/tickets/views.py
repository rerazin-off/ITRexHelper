from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Ticket, TicketStatusHistory, Comment, Notification
from .forms import TicketCreateForm, CommentForm


User = get_user_model()


SUPPORT_TICKET_TITLE = "Чат поддержки"


# =============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================

def _is_staff(user):
    """Проверяет, является ли пользователь сотрудником или админом"""
    return user.role in ["STAFF", "ADMIN"]


def _exclude_support_tickets(queryset):
    """Исключает служебные тикеты поддержки"""
    return queryset.exclude(title=SUPPORT_TICKET_TITLE)


def _paginate(queryset, request, per_page=10):
    """Пагинация с учётом текущей страницы"""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def _get_query_string(request):
    """Возвращает строку запроса без параметра page (для пагинации)"""
    query = request.GET.copy()
    query.pop('page', None)
    return query.urlencode()


<<<<<<< HEAD
# =============================
# АВТОРИЗАЦИЯ
# =============================
=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

def login_view(request):
    """Заглушка для логина - редирект на список заявок"""
    if request.user.is_authenticated:
        if _is_staff(request.user):
            return redirect("admin_dashboard")
        return redirect("ticket_list")
    return redirect("ticket_list")


<<<<<<< HEAD
# =============================
# СПИСОК ЗАЯВОК КЛИЕНТА
# =============================
=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
def ticket_list(request):
    """Список заявок клиента"""
    if _is_staff(request.user):
        return redirect("admin_dashboard")

    tickets = Ticket.objects.filter(author=request.user)
    tickets = _exclude_support_tickets(tickets)

    return render(
        request,
        "tickets/ticket_list.html",
        {
            "tickets": tickets,
            "form": TicketCreateForm(),
            "tickets_count": tickets.count(),
        }
    )


<<<<<<< HEAD
# =============================
# СОЗДАНИЕ ЗАЯВКИ
# =============================
=======


>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
@require_http_methods(["POST"])
def ticket_create(request):
    """Создание новой заявки клиентом"""
    form = TicketCreateForm(request.POST)

    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.author = request.user
        ticket.status = Ticket.Status.NEW
        ticket.save()

        # Записываем в историю
        TicketStatusHistory.objects.create(
            ticket=ticket,
            old_status=None,
            new_status=Ticket.Status.NEW,
            changed_by=request.user,
            comment="Создание заявки"
        )

        messages.success(request, "Заявка успешно создана")
    else:
        messages.error(request, "Ошибка при создании заявки. Проверьте заполнение полей.")

    return redirect("ticket_list")


<<<<<<< HEAD
# =============================
# ГЛАВНАЯ АДМИНА (МОИ ЗАЯВКИ)
# =============================

@login_required
def admin_dashboard(request):
    """Главная страница админа - мои назначенные заявки"""
    if not _is_staff(request.user):
        return redirect("ticket_list")

    all_tickets = _exclude_support_tickets(Ticket.objects.all())

    # Только мои назначенные заявки
    my_tickets = all_tickets.filter(executor=request.user)

    # Все новые заявки на сайте (для статистики)
    open_count = all_tickets.filter(status=Ticket.Status.NEW).count()

    # Мои заявки в работе
    in_progress_count = my_tickets.filter(status=Ticket.Status.IN_PROGRESS).count()

    # Закрыто за текущий месяц
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    closed_month = my_tickets.filter(
        status=Ticket.Status.CLOSED,
        updated_at__gte=month_start
    ).count()

    # Непрочитанные уведомления (для виджета "Необработанные обращения")
    try:
        unread_comments = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    except Exception:
        unread_comments = 0

=======

@login_required
def admin_dashboard(request):
    if not _is_staff(request.user):
        return redirect("ticket_list")
    
    tickets = Ticket.objects.filter(executor=request.user)
    
    tickets = _exclude_support_tickets(tickets)
    
    assigned_count = tickets.count()
    in_progress_count = tickets.filter(status=Ticket.Status.IN_PROGRESS).count()
    closed_month = tickets.filter(status=Ticket.Status.CLOSED).count()
    open_count = Ticket.objects.filter(status=Ticket.Status.NEW).count() 
    
    unread_comments = Comment.objects.filter(
        ticket__in=tickets,
        is_internal=False
    ).exclude(author=request.user).count()
    
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7
    return render(
        request,
        "tickets/admin_dashboard.html",
        {
<<<<<<< HEAD
            "tickets": my_tickets.order_by("-created_at")[:10],
            "open_count": open_count,
            "assigned_count": my_tickets.count(),
            "in_progress_count": in_progress_count,
            "closed_month": closed_month,
            "unread_comments": unread_comments,
=======
            "tickets": tickets,
            "open_count": open_count,
            "closed_month": closed_month,
            "assigned_count": assigned_count,
            "in_progress_count": in_progress_count,
            "unread_comments": unread_comments
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7
        }
    )


<<<<<<< HEAD
# =============================
# ВСЕ ЗАЯВКИ (ДЛЯ СОТРУДНИКОВ)
# =============================
=======

>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
def admin_tickets(request):
    """Все заявки с фильтрацией и пагинацией"""
    if not _is_staff(request.user):
        return redirect("ticket_list")

    tickets = _exclude_support_tickets(Ticket.objects.all())

    # Фильтрация по статусу
    status_filter = request.GET.get("status")
    if status_filter and status_filter != "all":
        tickets = tickets.filter(status=status_filter)

    # Фильтрация по приоритету
    priority_filter = request.GET.get("priority")
    if priority_filter and priority_filter != "all":
        tickets = tickets.filter(priority=priority_filter)

    # Фильтрация по исполнителю
    executor_filter = request.GET.get("executor")
    if executor_filter and executor_filter != "all":
        if executor_filter == "none":
            tickets = tickets.filter(executor__isnull=True)
        else:
            tickets = tickets.filter(executor_id=executor_filter)

    # Поиск по тексту
    search_query = request.GET.get("search")
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(author__surname__icontains=search_query) |
            Q(author__name__icontains=search_query)
        )

    # Сортировка
    sort_by = request.GET.get("sort", "-created_at")
    allowed_sorts = ["created_at", "-created_at", "status", "-status", "priority", "-priority"]
    if sort_by not in allowed_sorts:
        sort_by = "-created_at"
    tickets = tickets.order_by(sort_by)

    # Подсчёт общего количества
    tickets_count = tickets.count()

    # Пагинация
    page_obj = _paginate(tickets, request, per_page=15)

    return render(
        request,
        "tickets/admin_tickets.html",
        {
            "tickets": page_obj,
            "page_obj": page_obj,
            "tickets_count": tickets_count,
            "query_string": _get_query_string(request),
            "status_choices": Ticket.Status.choices,
            "priority_choices": Ticket.Priority.choices,
            "executors": User.objects.filter(role__in=["STAFF", "ADMIN"]),
            "current_status": status_filter or "all",
            "current_priority": priority_filter or "all",
            "current_executor": executor_filter or "all",
            "current_sort": sort_by,
            "search_query": search_query or "",
        }
    )


<<<<<<< HEAD
# =============================
# АНАЛИТИКА
# =============================
=======


>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
def admin_analytics(request):
    """Страница аналитики с графиками и отчётами"""
    if not _is_staff(request.user):
        return redirect("ticket_list")

    tickets = _exclude_support_tickets(Ticket.objects.all())
    now = timezone.now()

    # ====== Общая статистика ======
    total_count = tickets.count()
    in_progress_count = tickets.filter(status=Ticket.Status.IN_PROGRESS).count()

    # Просроченные заявки (созданы > 7 дней назад и не закрыты)
    deadline = now - timedelta(days=7)
    overdue_count = tickets.exclude(
        status__in=[Ticket.Status.CLOSED, Ticket.Status.CANCELED, Ticket.Status.REJECTED]
    ).filter(created_at__lt=deadline).count()

    # ====== Статистика за текущий месяц ======
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    tickets_month = tickets.filter(created_at__gte=month_start).count()
    processed_month = tickets.filter(
        status=Ticket.Status.CLOSED,
        updated_at__gte=month_start
    ).count()

    # ====== График динамики за 6 месяцев ======
    six_months_ago = now - timedelta(days=180)
    monthly_stats = (
        tickets
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Формируем данные для графика
    chart_months = []
    chart_values = []

    # Создаём список всех 6 месяцев (даже если нет данных)
    for i in range(5, -1, -1):
        month_date = (now - timedelta(days=30 * i)).replace(day=1)
        month_name = month_date.strftime("%B %Y")
        chart_months.append(month_name)

        # Ищем значение для этого месяца
        month_count = 0
        for stat in monthly_stats:
            if stat["month"].strftime("%B %Y") == month_name:
                month_count = stat["count"]
                break
        chart_values.append(month_count)

    # Нормализуем высоты для графика (max = 100%)
    max_value = max(chart_values) if chart_values and max(chart_values) > 0 else 1
    chart_bars = [int((v / max_value) * 100) for v in chart_values]

    # ====== Журнал аудита (последние 20 изменений статусов) ======
    audit_logs = TicketStatusHistory.objects.select_related("ticket").order_by("-changed_at")[:20]

    return render(
        request,
        "tickets/admin_analytics.html",
        {
            "total_count": total_count,
            "in_progress_count": in_progress_count,
            "overdue_count": overdue_count,
            "tickets_month": tickets_month,
            "processed_month": processed_month,
            "chart_bars": chart_bars,
            "chart_months": chart_months,
            "audit_logs": audit_logs,
        }
    )


<<<<<<< HEAD
# =============================
# ДЕТАЛЬНАЯ СТРАНИЦА ЗАЯВКИ
# =============================
=======


>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
def ticket_detail(request, ticket_id):
    """Детальный просмотр заявки"""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Проверка прав доступа для клиента
    if request.user.role == "CLIENT" and ticket.author != request.user:
        messages.error(request, "У вас нет доступа к этой заявке")
        return redirect("ticket_list")

    # Клиент не видит внутренние заметки
    if request.user.role == "CLIENT":
        comments = ticket.comments.filter(is_internal=False)
    else:
        comments = ticket.comments.all()

    # История статусов - только для сотрудников
    status_history = None
    if _is_staff(request.user):
        status_history = ticket.status_history.all()

    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "comments": comments,
            "status_history": status_history,
            "comment_form": CommentForm(),
        }
    )


<<<<<<< HEAD
# =============================
# НАЗНАЧИТЬ СЕБЯ ИСПОЛНИТЕЛЕМ
# =============================
=======



>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
@require_http_methods(["POST"])
def ticket_assign_self(request, ticket_id):
    """Сотрудник назначает себя исполнителем заявки"""
    if not _is_staff(request.user):
        messages.error(request, "Только сотрудники могут назначать себя исполнителем")
        return redirect("admin_tickets")

    ticket = get_object_or_404(Ticket, id=ticket_id)

    old_status = ticket.status
    ticket.executor = request.user
    ticket.status = Ticket.Status.IN_PROGRESS
    ticket.save()

    # Записываем в историю
    TicketStatusHistory.objects.create(
        ticket=ticket,
        old_status=old_status,
        new_status=Ticket.Status.IN_PROGRESS,
        changed_by=request.user,
        comment=f"Сотрудник {request.user.surname} {request.user.name} назначил себя исполнителем"
    )

    messages.success(request, "Вы назначены исполнителем")
    return redirect("ticket_detail", ticket_id=ticket_id)


<<<<<<< HEAD
# =============================
# ИЗМЕНЕНИЕ СТАТУСА
# =============================

=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7
@login_required
@require_http_methods(["POST"])
def ticket_update_status(request, ticket_id):
    """Изменение статуса заявки (для сотрудников)"""
    if not _is_staff(request.user):
        messages.error(request, "Только сотрудники могут изменять статус")
        return redirect("ticket_detail", ticket_id=ticket_id)

    ticket = get_object_or_404(Ticket, id=ticket_id)

    old_status = ticket.status
    new_status = request.POST.get("status")

    if not new_status:
        messages.error(request, "Статус не указан")
        return redirect("ticket_detail", ticket_id=ticket_id)

    if new_status not in dict(Ticket.Status.choices):
        messages.error(request, "Недопустимый статус")
        return redirect("ticket_detail", ticket_id=ticket_id)

    # Проверка допустимости перехода
    allowed_transitions = {
        Ticket.Status.NEW: [Ticket.Status.IN_PROGRESS, Ticket.Status.CANCELED, Ticket.Status.REJECTED],
        Ticket.Status.IN_PROGRESS: [Ticket.Status.WAITING, Ticket.Status.CLOSED, Ticket.Status.REJECTED],
        Ticket.Status.WAITING: [Ticket.Status.IN_PROGRESS, Ticket.Status.CLOSED],
    }

    if old_status in allowed_transitions and new_status not in allowed_transitions[old_status]:
        old_display = ticket.get_status_display()
        new_display = dict(Ticket.Status.choices).get(new_status, new_status)
        messages.error(
            request,
            f"Недопустимый переход: из «{old_display}» в «{new_display}»"
        )
        return redirect("ticket_detail", ticket_id=ticket_id)

    ticket.status = new_status
    ticket.save()

    # Записываем в историю
    TicketStatusHistory.objects.create(
        ticket=ticket,
        old_status=old_status,
        new_status=new_status,
        changed_by=request.user,
        comment=f"Статус изменен на «{ticket.get_status_display()}»"
    )

    messages.success(request, f"Статус изменен на «{ticket.get_status_display()}»")
    return redirect("ticket_detail", ticket_id=ticket_id)


<<<<<<< HEAD
# =============================
# ОБНОВЛЕНИЕ ЗАЯВКИ АДМИНОМ
# =============================

=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7
@login_required
@require_http_methods(["POST"])
def ticket_admin_update(request, ticket_id):
    """Полное обновление заявки админом (через модалку)"""
    if not _is_staff(request.user):
        messages.error(request, "Только сотрудники могут редактировать заявки")
        return redirect("ticket_detail", ticket_id=ticket_id)

    ticket = get_object_or_404(Ticket, id=ticket_id)

    old_status = ticket.status

    # Обновляем только переданные поля
    new_status = request.POST.get("status")
    if new_status and new_status != ticket.status:
        if new_status in dict(Ticket.Status.choices):
            ticket.status = new_status

    new_priority = request.POST.get("priority")
    if new_priority and new_priority != ticket.priority:
        if new_priority in dict(Ticket.Priority.choices):
            ticket.priority = new_priority

    new_description = request.POST.get("description")
    if new_description is not None and new_description != ticket.description:
        ticket.description = new_description

    # Назначение исполнителя (если передан ID)
    executor_id = request.POST.get("executor_id")
    if executor_id:
        try:
            executor = User.objects.get(id=executor_id, role__in=["STAFF", "ADMIN"])
            ticket.executor = executor
        except User.DoesNotExist:
            pass

    ticket.save()

    # Записываем в историю только если статус изменился
    if old_status != ticket.status:
        TicketStatusHistory.objects.create(
            ticket=ticket,
            old_status=old_status,
            new_status=ticket.status,
            changed_by=request.user,
            comment="Заявка обновлена через админ-панель"
        )

    messages.success(request, "Заявка успешно обновлена")

    # Редирект на страницу, откуда пришли
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("ticket_detail", ticket_id=ticket_id)


<<<<<<< HEAD
# =============================
# ДОБАВЛЕНИЕ КОММЕНТАРИЯ
# =============================
=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7

@login_required
@require_http_methods(["POST"])
def add_comment(request, ticket_id):
    """Добавление комментария к заявке"""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Проверка прав доступа
    if request.user.role == "CLIENT" and ticket.author != request.user:
        messages.error(request, "У вас нет доступа к этой заявке")
        return redirect("ticket_detail", ticket_id=ticket_id)

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user

        # Защита: клиенты не могут создавать внутренние заметки
        if request.user.role == "CLIENT":
            comment.is_internal = False

        comment.save()
        messages.success(request, "Комментарий добавлен")
    else:
        messages.error(request, "Комментарий не может быть пустым")

    return redirect("ticket_detail", ticket_id=ticket_id)

<<<<<<< HEAD

# =============================
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# =============================

=======
>>>>>>> 6c5cacb5cd341378040da80f3990598b860e76f7
@login_required
def admin_users(request):
    """Список всех пользователей (только для сотрудников)"""
    if not _is_staff(request.user):
        return redirect("ticket_list")

    return render(
        request,
        "tickets/admin_users.html",
        {
            "users": User.objects.all().order_by("role", "surname")
        }
    )



@login_required
def admin_chat(request):
    """Интерфейс чата для сотрудников"""
    if not _is_staff(request.user):
        return redirect("ticket_list")

    return render(request, "tickets/admin_chat.html")



@login_required
def support_chat(request):
    """Заглушка для чата поддержки клиента"""
    return redirect("ticket_list")