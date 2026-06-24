from django.urls import path
<<<<<<< HEAD
from . import views, document_views
=======

from . import views
>>>>>>> 304b811 (Implement support chat, notifications and analytics improvements)


urlpatterns = [
<<<<<<< HEAD
    # ===== Список заявок клиента =====
    path('', views.ticket_list, name='ticket_list'),
    
    # ===== Создание заявки =====
    path('create/', views.ticket_create, name='ticket_create'),
    
    # ===== Просмотр заявки =====
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # ===== Действия с заявкой =====
    path('<int:ticket_id>/assign/', views.ticket_assign_self, name='ticket_assign_self'),
    path('<int:ticket_id>/update-status/', views.ticket_update_status, name='ticket_update_status'),
    path('<int:ticket_id>/update/', views.ticket_admin_update, name='ticket_admin_update'),
    path('<int:ticket_id>/add-comment/', views.add_comment, name='add_comment'),
    
    # ===== Админские страницы =====
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('all/', views.admin_tickets, name='admin_tickets'),
    path('analytics/', views.admin_analytics, name='admin_analytics'),
    path('analytics/download/', document_views.download_analytics_report, name='download_analytics_report'),
    path('<int:ticket_id>/contract/download/', document_views.download_ticket_contract, name='download_ticket_contract'),
    path('users/', views.admin_users, name='admin_users'),
    path('chat/', views.admin_chat, name='admin_chat'),
    path('support-chat/', views.support_chat, name='support_chat'),
    
    # ===== API endpoints (для фронтенда) =====
    path('api/users/', views.api_users_list, name='api_users_list'),
    path('api/statuses/', views.api_ticket_statuses, name='api_statuses'),
    path('api/priorities/', views.api_ticket_priorities, name='api_priorities'),
]
=======

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

    path(
        'notifications/<int:notification_id>/read/',
        views.notification_mark_read,
        name='notification_mark_read'
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
>>>>>>> 304b811 (Implement support chat, notifications and analytics improvements)
