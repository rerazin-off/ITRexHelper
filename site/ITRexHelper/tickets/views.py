from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods


from .models import (
    Ticket,
    TicketStatusHistory,
    Comment
)

from .forms import (
    TicketCreateForm,
    CommentForm
)


User = get_user_model()


SUPPORT_TICKET_TITLE = "Чат поддержки"


READONLY_STATUSES = {
    Ticket.Status.CLOSED,
    Ticket.Status.REJECTED
}



def _is_staff(user):

    return user.role in [
        "STAFF",
        "ADMIN"
    ]



def _exclude_support_tickets(queryset):

    return queryset.exclude(
        title=SUPPORT_TICKET_TITLE
    )



def _paginate(queryset, request):

    paginator = Paginator(
        queryset,
        10
    )

    return paginator.get_page(
        request.GET.get("page")
    )



# =============================
# LOGIN
# =============================

def login_view(request):

    if request.user.is_authenticated:

        return redirect(
            "ticket_list"
        )

    return redirect(
        "ticket_list"
    )



# =============================
# USER TICKETS
# =============================


@login_required
def ticket_list(request):


    if _is_staff(request.user):

        return redirect(
            "admin_dashboard"
        )


    tickets = Ticket.objects.filter(
        author=request.user
    )


    tickets = _exclude_support_tickets(
        tickets
    )


    return render(

        request,

        "tickets/ticket_list.html",

        {
            "tickets": tickets,

            "form":
                TicketCreateForm(),

            "tickets_count":
                tickets.count()
        }

    )




# =============================
# CREATE TICKET
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_create(request):


    form = TicketCreateForm(
        request.POST
    )


    if form.is_valid():


        ticket = form.save(
            commit=False
        )


        ticket.author = request.user

        ticket.status = Ticket.Status.NEW

        ticket.save()



        TicketStatusHistory.objects.create(

            ticket=ticket,

            new_status=Ticket.Status.NEW,

            changed_by=request.user,

            comment="Создание заявки"

        )


        messages.success(
            request,
            "Заявка создана"
        )


    return redirect(
        "ticket_list"
    )



# =============================
# ADMIN DASHBOARD
# =============================


@login_required
def admin_dashboard(request):


    if not _is_staff(request.user):

        return redirect(
            "ticket_list"
        )


    tickets = Ticket.objects.all()



    return render(

        request,

        "tickets/admin_dashboard.html",

        {

        "tickets":
            tickets,

        "open_count":
            tickets.filter(
                status=Ticket.Status.NEW
            ).count(),


        "closed_month":
            tickets.filter(
                status=Ticket.Status.CLOSED
            ).count()

        }

    )




# =============================
# ALL TICKETS
# =============================


@login_required
def admin_tickets(request):


    if not _is_staff(request.user):

        return redirect(
            "ticket_list"
        )


    tickets = Ticket.objects.all()


    return render(

        request,

        "tickets/admin_tickets.html",

        {

        "tickets":
            _paginate(
                tickets,
                request
            )

        }

    )




# =============================
# ANALYTICS
# =============================


@login_required
def admin_analytics(request):


    return render(

        request,

        "tickets/admin_analytics.html",

        {

        "total_count":
            Ticket.objects.count()

        }

    )




# =============================
# DETAIL
# =============================


@login_required
def ticket_detail(request, ticket_id):


    ticket = get_object_or_404(

        Ticket,

        id=ticket_id

    )


    return render(

        request,

        "tickets/ticket_detail.html",

        {

        "ticket":
            ticket,


        "comments":
            ticket.comments.all(),


        "status_history":
            ticket.status_history.all(),


        "comment_form":
            CommentForm()

        }

    )





# =============================
# ASSIGN
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_assign_self(request,ticket_id):


    ticket = get_object_or_404(
        Ticket,
        id=ticket_id
    )


    ticket.executor = request.user

    ticket.status = Ticket.Status.IN_PROGRESS

    ticket.save()



    TicketStatusHistory.objects.create(

        ticket=ticket,

        new_status=
        Ticket.Status.IN_PROGRESS,

        changed_by=request.user,

        comment="Назначено сотруднику"

    )


    return redirect(
        "admin_tickets"
    )





# =============================
# UPDATE STATUS
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_update_status(request,ticket_id):


    return ticket_admin_update(
        request,
        ticket_id
    )





# =============================
# ADMIN UPDATE
# =============================


@login_required
@require_http_methods(["POST"])
def ticket_admin_update(request,ticket_id):


    ticket = get_object_or_404(

        Ticket,

        id=ticket_id

    )



    old_status = ticket.status



    new_status = request.POST.get(
        "status"
    )



    if new_status:


        ticket.status = new_status



    ticket.priority = request.POST.get(

        "priority",

        ticket.priority

    )


    ticket.description = request.POST.get(

        "description",

        ticket.description

    )



    ticket.executor = request.user



    ticket.save()



    TicketStatusHistory.objects.create(

        ticket=ticket,

        old_status=old_status,

        new_status=ticket.status,

        changed_by=request.user,

        comment="Обновление заявки"

    )



    return redirect(

        "admin_tickets"

    )




# =============================
# COMMENTS
# =============================


@login_required
@require_http_methods(["POST"])
def add_comment(request,ticket_id):


    ticket=get_object_or_404(

        Ticket,

        id=ticket_id

    )


    form = CommentForm(
        request.POST
    )


    if form.is_valid():

        comment=form.save(
            commit=False
        )


        comment.ticket=ticket

        comment.author=request.user


        comment.save()



    return redirect(

        "ticket_detail",

        ticket_id=ticket.id

    )





# =============================
# USERS
# =============================


@login_required
def admin_users(request):


    return render(

        request,

        "tickets/admin_users.html",

        {

        "users":
            User.objects.all()

        }

    )





@login_required
def admin_chat(request):


    return render(

        request,

        "tickets/admin_chat.html"

    )




@login_required
def support_chat(request):


    return redirect(

        "ticket_list"

    )