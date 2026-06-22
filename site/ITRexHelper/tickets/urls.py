from django.urls import path

from . import views


urlpatterns = [

    # список заявок клиента
    path(
        '',
        views.ticket_list,
        name='ticket_list'
    ),


    # создание заявки
    path(
        'create/',
        views.ticket_create,
        name='ticket_create'
    ),


    # просмотр заявки
    path(
        '<int:ticket_id>/',
        views.ticket_detail,
        name='ticket_detail'
    ),


    # назначить себя исполнителем
    path(
        '<int:ticket_id>/assign/',
        views.ticket_assign_self,
        name='ticket_assign_self'
    ),


    # изменение статуса
    path(
        '<int:ticket_id>/update-status/',
        views.ticket_update_status,
        name='ticket_update_status'
    ),


    # изменение заявки админом
    path(
        '<int:ticket_id>/update/',
        views.ticket_admin_update,
        name='ticket_admin_update'
    ),


    # добавить комментарий
    path(
        '<int:ticket_id>/add-comment/',
        views.add_comment,
        name='add_comment'
    ),



    # админские страницы

    path(
        'dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),


    path(
        'all/',
        views.admin_tickets,
        name='admin_tickets'
    ),


    path(
        'analytics/',
        views.admin_analytics,
        name='admin_analytics'
    ),


    path(
        'users/',
        views.admin_users,
        name='admin_users'
    ),


    path(
        'chat/',
        views.admin_chat,
        name='admin_chat'
    ),


    path(
        'support-chat/',
        views.support_chat,
        name='support_chat'
    ),

]